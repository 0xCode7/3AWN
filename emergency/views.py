from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from .models import EmergencyContact
from .serializers import EmergencyContactSerializer, EmergencyContact


@extend_schema(tags=["Emergency"])
class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Emergency"])
class EmergencyContactDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)
