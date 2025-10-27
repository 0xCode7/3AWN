from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ConnectionRequest
from authentication.models import Patient
from .serializers import ConnectionRequestSerializer, ConnectionResponseSerializer, AllConnectionRequestsSerializer


# Return all patient requests
class PatientIncomingRequestsView(generics.ListAPIView):
    serializer_class = AllConnectionRequestsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return all requests where the logged-in user is the patient."""
        user = self.request.user

        try:
            patient = Patient.objects.get(user=user)
        except Patient.DoesNotExist:
            return ConnectionRequest.objects.none()

        return ConnectionRequest.objects.filter(patient=patient, status='pending').order_by('-created_at')


# CarePerson sends a connection request
class SendConnectionRequestView(generics.CreateAPIView):
    serializer_class = ConnectionRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Force the careperson to be the sender
        serializer.save(careperson=self.request.user)


# Patient accepts/rejects a request
class RespondToConnectionRequestView(generics.UpdateAPIView):
    queryset = ConnectionRequest.objects.all()
    serializer_class = ConnectionResponseSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.patient.user != request.user:
            return Response(
                {"error": "Only the target patient can respond to this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": f"Request {serializer.validated_data['status']} successfully."})
