from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Medication, Drug
from .serializers import MedicationSerializer, DDIPredictSerializer
from .ddi_model import clf, preprocess_input, severity_messages

class MedicationListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        medication = serializer.save(user=self.request.user)

        # check interactions
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

            features = preprocess_input(new_active, existing_active)
            if features is not None:
                severity_prediction = clf.predict([features])[0]
                severity_message = severity_messages.get(severity_prediction)
                if severity_prediction > 0:
                    interactions.append({
                        "with": med.name,
                        "severity": severity_message
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
        drug_a = request.data.get("drug_a", "")
        drug_b = request.data.get("drug_b", "")

        # Preprocess input
        features = preprocess_input(drug_a, drug_b)
        if features is None:
            return Response({"error": "Drug not found in model. Please use generic names."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Predict
        severity_prediction = clf.predict([features])[0]
        severity_message = severity_messages.get(severity_prediction, "Unknown interaction level.")
        return Response({"severity": severity_message})
