from rest_framework import serializers
from .models import Medication
from datetime import date


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ['user']

        def create(self, validated_data):
            today_str = date.today().isoformat()
            validated_data["dose_taken"] = {
                today_str: {f"dose-{i + 1}": True for i in range(validated_data.get("times_per_day", 1))}}
            return super().create(validated_data)


class DDIPredictSerializer(serializers.Serializer):
    drug1 = serializers.CharField(max_length=255)
    drug2 = serializers.CharField(max_length=255)
