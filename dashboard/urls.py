from django.urls import path
from .views import SendConnectionRequestView, RespondToConnectionRequestView, PatientIncomingRequestsView

urlpatterns = [
    path('connections/', PatientIncomingRequestsView.as_view(), name='income-connection-requests'),
    path('connections/request/', SendConnectionRequestView.as_view(), name='send-connection-request'),
    path('connections/respond/<int:pk>/', RespondToConnectionRequestView.as_view(), name='respond-connection-request'),
]
