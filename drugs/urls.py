from django.urls import path
from .views import (
    MedicationListCreateView, MedicationDetailView, DDIPredictView, DrugAlternativesView, HerbalAlternativesView,
    MarkAsTakenView
)

app_name = "drugs"

urlpatterns = [
    # Medications
    path('', MedicationListCreateView.as_view(), name='medications-list-create'),
    path('<int:id>/', MedicationDetailView.as_view(), name='medications-detail'),
    path('<int:id>/mark-as-taken/', MarkAsTakenView.as_view(), name='take-medication-dose'),
    path('alternatives/', DrugAlternativesView.as_view(), name='drug-alternatives'),
    path('alternatives/herbs', HerbalAlternativesView.as_view(), name='herbal-alternatives'),
    path('predict/', DDIPredictView.as_view(), name='ddi-predict'),
]
