from datetime import timedelta

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Medication, Drug, DrugAlternative, ActiveIngredient
from .serializers import (
    MedicationSerializer,
    DrugAlternativeSerializer,
    DDIPredictSerializer
)

from drugs.services.ddi_model import predict_ddi
from drugs.utils.ddi import classify_severity
from drugs.services.pubchem import get_smiles_from_pubchem
from .services.smiles_resolver import resolve_smiles_for_medication


# =========================
# Medication List & Create
# =========================
@extend_schema(tags=["Drugs"])
class MedicationListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(
            user=self.request.user,
            is_finished=False
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Prevent duplicates
        if Medication.objects.filter(
                user=request.user,
                name__iexact=serializer.validated_data["name"]
        ).exists():
            return Response(
                {"detail": "Medication already exists for this user."},
                status=status.HTTP_200_OK
            )

        medication = serializer.save(user=request.user)

        user_meds = Medication.objects.filter(
            user=request.user
        ).exclude(id=medication.id)

        interactions = []

        # =========================
        # Resolve NEW medication SMILES
        # =========================
        new_smiles = resolve_smiles_for_medication(medication.name)

        if not new_smiles:
            headers = self.get_success_headers(serializer.data)
            return Response(
                {**serializer.data, "severity_check": []},
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        # =========================
        # Check interactions
        # =========================
        for med in user_meds:
            existing_smiles = resolve_smiles_for_medication(med.name)

            if not existing_smiles:
                continue

            max_score = 0.0

            for s1 in new_smiles:
                for s2 in existing_smiles:
                    score = predict_ddi(s1, s2)
                    max_score = max(max_score, score)

            if max_score >= 0.7:
                interactions.append({
                    "with": med.name,
                    "interaction_probability": round(max_score, 4),
                    "risk_level": classify_severity(max_score)
                })

        headers = self.get_success_headers(serializer.data)

        return Response(
            {**serializer.data, "severity_check": interactions},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


# =========================
# Medication Detail
# =========================
@extend_schema(tags=["Drugs"])
class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)


# =========================
# Drug Alternatives
# =========================
@extend_schema(tags=["Drugs"])
class DrugAlternativesView(generics.ListAPIView):
    serializer_class = DrugAlternativeSerializer

    def get_queryset(self):
        params = self.request.query_params
        name = params.get("name")
        drug_id = params.get("id")

        drug = None
        if name:
            drug = Drug.objects.filter(name__iexact=name).first()
        elif drug_id:
            drug = Drug.objects.filter(id=drug_id).first()

        if not drug:
            return DrugAlternative.objects.none()

        return DrugAlternative.objects.filter(drug=drug)


# =========================
# Herbal Alternatives
# =========================
@extend_schema(tags=["Drugs"])
class HerbalAlternativesView(GenericAPIView):

    def get(self, request):
        params = request.query_params
        name = params.get("name")
        drug_id = params.get("id")

        drug = None
        if name:
            drug = Drug.objects.filter(name__icontains=name).first()
        elif drug_id:
            drug = Drug.objects.filter(id=drug_id).first()

        if not drug:
            return Response(
                {"error": "Drug not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        alternatives = DrugAlternative.objects.filter(
            drug=drug,
            herbal_alternatives__isnull=False
        )

        herbs = set()
        for alt in alternatives:
            herbs.update(
                h.strip()
                for h in alt.herbal_alternatives.split(",")
                if h.strip()
            )

        return Response({
            "drug": drug.name,
            "herbal_alternatives": sorted(list(herbs))
        })


# =========================
# Mark Dose as Taken
# =========================
@extend_schema(tags=["Drugs"])
class MarkAsTakenView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        try:
            medication = Medication.objects.get(
                id=id,
                user=request.user
            )
        except Medication.DoesNotExist:
            return Response(
                {"error": "Medication not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        dose_number = request.data.get("dose_number")
        if dose_number is None:
            return Response(
                {"error": "dose_number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.localdate()
        today_str = today.isoformat()

        dose_data = medication.dose_taken or {}
        dose_data.setdefault(today_str, {})
        dose_data[today_str][f"dose-{dose_number}"] = True

        medication.dose_taken = dose_data
        medication.save(update_fields=["dose_taken"])

        end_date = medication.start_date + timedelta(
            days=medication.duration_in_days - 1
        )

        all_taken = all(
            taken for day in dose_data.values()
            for taken in day.values()
        )

        if today >= end_date and all_taken:
            medication.is_finished = True
            medication.save(update_fields=["is_finished"])
            return Response({
                "message": f"{medication.name} treatment completed."
            })

        return Response({
            "message": f"{medication.name} dose {dose_number} marked as taken.",
            "date": today_str
        })


# =========================
# DDI Predict API
# =========================
@extend_schema(tags=["Drugs"])
class DDIPredictView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DDIPredictSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name_a = serializer.validated_data["drug_a"]
        name_b = serializer.validated_data["drug_b"]

        smiles_a = []
        smiles_b = []

        # ===== Active Ingredient A =====
        try:
            ai_a = ActiveIngredient.objects.get(name__iexact=name_a)
            smiles_a.append(ai_a.smiles) if ai_a.smiles else smiles_a.append(get_smiles_from_pubchem(name_a))
        except ActiveIngredient.DoesNotExist:
            smiles = get_smiles_from_pubchem(name_a)
            if smiles:
                smiles_a.append(smiles)

        # ===== Active Ingredient B =====
        try:
            ai_b = ActiveIngredient.objects.get(name__iexact=name_b)
            smiles_b.append(ai_b.smiles) if ai_b.smiles else smiles_b.append(get_smiles_from_pubchem(name_b))
        except ActiveIngredient.DoesNotExist:
            smiles = get_smiles_from_pubchem(name_b)
            if smiles:
                smiles_b.append(smiles)

        # ===== Validation =====
        if not smiles_a or not smiles_b:
            return Response(
                {"error": "Could not resolve SMILES for one or both active ingredients."},
                status=400
            )

        # ===== DDI Prediction =====
        max_score = 0.0
        for s1 in smiles_a:
            for s2 in smiles_b:
                score = predict_ddi(s1, s2)
                max_score = max(max_score, score)

        return Response({
            "active_ingredient_a": name_a,
            "active_ingredient_b": name_b,
            "interaction_probability": round(max_score, 4),
            "risk_level": classify_severity(max_score),
            "smiles_source": {
                "active_ingredient_a": "db" if len(smiles_a) else "pubchem",
                "active_ingredient_b": "db" if len(smiles_b) else "pubchem"
            }
        })