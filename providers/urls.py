from django.urls import path
from .views import PharmacyListView, NearbyPharmaciesView

app_name = "providers"

urlpatterns = [
    path('pharmacies/', PharmacyListView.as_view(), name='pharmacy-list-view'),
    path('pharmacies/nearby/', NearbyPharmaciesView.as_view(), name='nearby-pharmacy-view'),
]
