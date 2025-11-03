from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Medication, Drug, DrugAlternative
from .serializers import MedicationSerializer, DrugSerializer, DrugAlternativeSerializer
from .ddi_model import predict_ddi_api

@extend_schema(tags=["Drugs"])
class MedicationListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ Check if medication already exists
        if Medication.objects.filter(user=request.user, name__iexact=serializer.validated_data["name"]).exists():
            return Response(
                {"detail": "Medication already exists for this user."},
                status=status.HTTP_200_OK
            )

        # ✅ Save new medication
        medication = serializer.save(user=self.request.user)

        # ✅ Get user's existing meds (excluding the new one)
        user_meds = Medication.objects.filter(user=self.request.user).exclude(id=medication.id)
        interactions = []

        # ✅ Get active ingredient of new medication
        try:
            drug_obj = Drug.objects.get(name__iexact=medication.name)
            new_active = drug_obj.active_ingredient
        except Drug.DoesNotExist:
            new_active = medication.name

        # ✅ Check interaction with all previous medications
        for med in user_meds:
            try:
                existing_drug = Drug.objects.get(name__iexact=med.name)
                existing_active = existing_drug.active_ingredient
            except Drug.DoesNotExist:
                existing_active = med.name

            result = predict_ddi_api(new_active, existing_active)

            if result.get("label") == "yes":
                interactions.append({
                    "with": med.name,
                    "severity": result["message"],
                    "probability": result["probability"],
                    "severity_category": result["severity_category"]
                })

        headers = self.get_success_headers(serializer.data)

        # ✅ Return medication + interactions
        return Response(
            {**serializer.data, "severity_check": interactions},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

@extend_schema(tags=["Drugs"])
class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

@extend_schema(tags=["Drugs"])
class DrugAlternativesView(generics.ListAPIView):
    serializer_class = DrugAlternativeSerializer

    def get_queryset(self):
        params = self.request.query_params

        query = params.get('name')
        drug_id = params.get('id')

        if query:
            drug = Drug.objects.filter(name__iexact=query).first()
        elif drug_id:
            drug = Drug.objects.filter(id=drug_id).first()
        else:
            return Drug.objects.none()

        # If no matching drug found → return empty queryset
        if not drug:
            return Drug.objects.none()

        print(drug)
        # Return drugs with same active ingredient but exclude current drug
        return DrugAlternative.objects.filter(
            drug_id=drug.id
        ).exclude(id=drug.id)

@extend_schema(tags=["Drugs"])
class HerbalAlternativesView(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        params = request.query_params
        query = params.get('name')
        drug_id = params.get('id')

        if query:
            drug = Drug.objects.filter(name__icontains=query).first()
        elif drug_id:
            drug = Drug.objects.filter(id=drug_id).first()
        else:
            return Response({"error": "Missing 'name' or 'id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        if not drug:
            return Response({"error": "Drug not found."}, status=status.HTTP_404_NOT_FOUND)

        herbal_alternatives = DrugAlternative.objects.filter(drug=drug).exclude(herbal_alternatives__isnull=True)

        herbs = set()
        for alt in herbal_alternatives:
            if alt.herbal_alternatives:
                herbs.update([h.strip() for h in alt.herbal_alternatives.split(',') if h.strip()])

        return Response({
            "drug": drug.name,
            "herbal_alternatives": sorted(list(herbs))
        }, status=status.HTTP_200_OK)

@extend_schema(tags=["Drugs"])
class MarkAsTakenView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        try:
            medication = Medication.objects.get(pk=id, user=request.user)
        except Medication.DoesNotExist:
            return Response(
                {"error": "Medication not found or not authorized."},
                status=status.HTTP_404_NOT_FOUND
            )

        dose_number = request.data.get('dose_number')

        if dose_number is None:
            return Response({"error": "dose_number is required."}, status=status.HTTP_400_BAD_REQUEST)

        today_str = timezone.localdate().isoformat()
        dose_data = medication.dose_taken or {}

        if today_str not in dose_data:
            dose_data[today_str] = {}

        dose_key = f"dose-{dose_number}"
        dose_data[today_str][dose_key] = True

        medication.dose_taken = dose_data
        medication.save(update_fields=["dose_taken"])

        return Response({
            "message": f"{medication.name} dose {dose_number} marked as taken.",
            "date": today_str,
            "dose_taken": dose_data[today_str]
        }, status=status.HTTP_200_OK)

@extend_schema(tags=["Drugs"])
class DDIPredictView(APIView):
    def post(self, request):
        drug_a = request.data.get("drug_a", "").strip()
        drug_b = request.data.get("drug_b", "").strip()

        if not drug_a or not drug_b:
            return Response(
                {"error": "Both drug_a and drug_b are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = predict_ddi_api(drug_a, drug_b)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
