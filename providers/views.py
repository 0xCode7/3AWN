from django.db.models import F, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians
from rest_framework import generics, filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from .models import Pharmacy
from .serializers import PharmacySerializer


class NearbyPharmaciesView(ListAPIView):
    serializer_class = PharmacySerializer

    def get_queryset(self):
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")

        print(lat, lng)
        if not lat or not lng:
            raise ValidationError({
                "detail": "lat and lng are required"
            })

        lat = float(lat)
        lng = float(lng)

        queryset = Pharmacy.objects.annotate(
            distance=ACos(
                Cos(Radians(lat)) *
                Cos(Radians(F('latitude'))) *
                Cos(Radians(F('longitude')) - Radians(lng)) +
                Sin(Radians(lat)) *
                Sin(Radians(F('latitude')))
            ) * 6371
        ).filter(distance__lte=10).order_by("distance")

        return queryset



class PharmacyListView(generics.ListAPIView):

    serializer_class = PharmacySerializer

    queryset = Pharmacy.objects.all()

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = [
        "name",
        "address",
    ]

    ordering_fields = [
        "name",
    ]

    ordering = ["name"]
