from rest_framework import serializers
from .models import Pharmacy

class PharmacySerializer(serializers.ModelSerializer):

    distance = serializers.FloatField(read_only=True)

    class Meta:
        model = Pharmacy

        fields = [
            'id',
            'name',
            'address',
            'latitude',
            'longitude',
            'website',
            'distance'
        ]