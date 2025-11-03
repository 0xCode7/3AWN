from rest_framework import serializers
from authentication.models import CarePerson, Patient
from authentication.serializers import UserSerializer
from .models import ConnectionRequest


class AllConnectionRequestsSerializer(serializers.ModelSerializer):
    careperson = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'careperson', 'status', 'created_at']

    def get_careperson(self, obj):
        """Show patient info in list"""
        return {
            "id": obj.careperson.id,
            "full_name": obj.careperson.user.full_name,
        }


class ConnectionRequestSerializer(serializers.ModelSerializer):
    # Accept patient code instead of ID
    patient_code = serializers.CharField(write_only=True)
    patient = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'patient_code', 'patient', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at', 'patient']

    def get_patient(self, obj):
        """Return basic patient info in response"""
        return {
            "id": obj.patient.id,
            "full_name": obj.patient.user.full_name,
            "code": obj.patient.code
        }

    def create(self, validated_data):
        request = self.context['request']
        careperson = CarePerson.objects.get(user=request.user)
        patient_code = validated_data.pop('patient_code')

        try:
            patient = Patient.objects.get(code=str(patient_code))
        except Patient.DoesNotExist:
            raise serializers.ValidationError({"patient_code": "Invalid patient code"})

        existing_request = ConnectionRequest.objects.filter(
            careperson=careperson,
            patient=patient,
            status='pending'
        ).first()
        if existing_request:
            raise serializers.ValidationError(
                {"message": "A pending request already exists for this patient."}
            )

        validated_data['careperson'] = careperson
        validated_data['patient'] = patient
        return super().create(validated_data)


class ConnectionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionRequest
        fields = ['status']
        extra_kwargs = {
            'status': {'required': True}
        }

    def validate_status(self, value):
        if value not in ['accepted', 'rejected']:
            raise serializers.ValidationError("Status must be 'accepted' or 'rejected'.")
        return value


class DayAdherenceSerializer(serializers.Serializer):
    day = serializers.CharField()
    taken = serializers.IntegerField()
    missed = serializers.IntegerField()
    adherence_rate = serializers.FloatField()


class RecentActivitySerializer(serializers.Serializer):
    medication = serializers.CharField()
    status = serializers.CharField()
    time = serializers.DateTimeField()


class PatientStatisticsSerializer(serializers.Serializer):
    patient = serializers.CharField()
    overview = serializers.DictField()
    weekly_adherence = DayAdherenceSerializer(many=True)
    recent_activity = RecentActivitySerializer(many=True)

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user']