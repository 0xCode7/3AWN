from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Medication, Drug
from .serializers import MedicationSerializer
from .ddi_model import predict_ddi


class MedicationListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        medication = serializer.save(user=self.request.user)

        interactions = []
        user_meds = Medication.objects.filter(user=self.request.user).exclude(id=medication.id)

        try:
            drug_obj = Drug.objects.get(name__iexact=medication.name)
            new_active = drug_obj.active_ingredient
        except Drug.DoesNotExist:
            new_active = medication.name

        for med in user_meds:
            try:
                existing_drug = Drug.objects.get(name__iexact=med.name)
                existing_active = existing_drug.active_ingredient
            except Drug.DoesNotExist:
                existing_active = med.name

            result = predict_ddi(new_active, existing_active)
            if result["label"] == "yes":
                interactions.append({
                    "with": med.name,
                    "severity": result["message"],
                    "probability": result["probability"]
                })

        headers = self.get_success_headers(serializer.data)
        return Response(
            {**serializer.data, "severity_check": interactions},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)


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
            result = predict_ddi(drug_a, drug_b)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
