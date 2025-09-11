from django.urls import path
from .views import (
    MedicationListCreateView, MedicationDetailView,
)

urlpatterns = [
    # Medications
    path('', MedicationListCreateView.as_view(), name='medications-list-create'),
    path('<int:id>/', MedicationDetailView.as_view(), name='medications-detail'),

]