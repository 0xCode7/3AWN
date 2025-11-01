from django.urls import path
from .views import SendConnectionRequestView, RespondToConnectionRequestView, PatientIncomingRequestsView, \
    PatientStatisticsView

app_name = "dashboard"

urlpatterns = [
    path('connections/requests', PatientIncomingRequestsView.as_view(), name='income-connection-requests'),
    path('connections/send/', SendConnectionRequestView.as_view(), name='send-connection-request'),
    path('connections/respond/<int:pk>/', RespondToConnectionRequestView.as_view(), name='respond-connection-request'),
    path('patient-dashboard/', PatientStatisticsView.as_view(), name='patient-dashboard')
]
