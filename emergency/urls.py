from django.urls import path
from .views import (
    EmergencyContactListCreateView, EmergencyContactDetailView
)

urlpatterns = [
    # Emergency Contacts
    path('contacts/', EmergencyContactListCreateView.as_view(), name='emergency-contacts-list-create'),
    path('contacts/<int:id>/', EmergencyContactDetailView.as_view(), name='emergency-contacts-detail'),
]
