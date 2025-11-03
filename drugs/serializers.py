from rest_framework import serializers
from .models import Medication,Drug, DrugAlternative
from datetime import date


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = '__all__'

class DrugAlternativeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='substitute')
    active_ingredient = serializers.CharField(source="drug.active_ingredient")
    class Meta:
        model = DrugAlternative
        fields = ["id", "name", "active_ingredient"]

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        today_str = date.today().isoformat()
        validated_data["dose_taken"] = {
            today_str: {f"dose-{i + 1}": False for i in range(validated_data.get("times_per_day", 1))}}
        return super().create(validated_data)


class DDIPredictSerializer(serializers.Serializer):
    drug1 = serializers.CharField(max_length=255)
    drug2 = serializers.CharField(max_length=255)
