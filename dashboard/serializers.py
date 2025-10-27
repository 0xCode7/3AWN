from rest_framework import serializers
from authentication.models import CarePerson, Patient
from .models import ConnectionRequest


class AllConnectionRequestsSerializer(serializers.ModelSerializer):
    careperson = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'careperson', 'patient', 'status', 'created_at']

    def get_careperson(self, obj):
        """Show careperson info in list"""
        return {
            "id": obj.careperson.id,
            "full_name": obj.careperson.user.full_name,
            "email": obj.careperson.user.email,
        }

    def get_patient(self, obj):
        """Show patient info in list"""
        return {
            "id": obj.patient.id,
            "full_name": obj.patient.user.full_name,
            "code": obj.patient.code,
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
            patient = Patient.objects.get(code=patient_code)
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
