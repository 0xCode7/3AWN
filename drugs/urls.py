from django.urls import path
from .views import (
    MedicationListCreateView, MedicationDetailView, DDIPredictView,
)

urlpatterns = [
    # Medications
    path('', MedicationListCreateView.as_view(), name='medications-list-create'),
    path('<int:id>/', MedicationDetailView.as_view(), name='medications-detail'),
    path('predict/', DDIPredictView.as_view(), name='ddi-predict'),

]