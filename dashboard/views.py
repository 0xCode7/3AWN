from datetime import timedelta
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drugs.models import Medication
from .models import ConnectionRequest
from authentication.models import Patient
from authentication.serializers import PatientSerializer, CarePersonSerializer, CarePersonMiniSerializer
from .serializers import ConnectionRequestSerializer, ConnectionResponseSerializer, AllConnectionRequestsSerializer, \
    PatientStatisticsSerializer


# Return all patient requests
@extend_schema(tags=["Dashboard"])
class PatientIncomingRequestsView(generics.ListAPIView):
    serializer_class = AllConnectionRequestsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return all requests where the logged-in user is the patient."""
        user = self.request.user

        try:
            patient = Patient.objects.get(user=user.id)
        except Patient.DoesNotExist:
            return ValidationError({"message": ["User Doesn't exist"]})

        return ConnectionRequest.objects.filter(patient=patient, status='pending').order_by('-created_at')


# CarePerson sends a connection request
@extend_schema(tags=["Dashboard"])
class SendConnectionRequestView(generics.CreateAPIView):
    serializer_class = ConnectionRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Force the careperson to be the sender
        serializer.save(careperson=self.request.user)


# Patient accepts/rejects a request
@extend_schema(tags=["Dashboard"])
class RespondToConnectionRequestView(generics.UpdateAPIView):
    queryset = ConnectionRequest.objects.all()
    serializer_class = ConnectionResponseSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.patient.user != request.user:
            return Response(
                {"error": "Only the target patient can respond to this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": f"Request {serializer.validated_data['status']} successfully."})


# User Report
@extend_schema(tags=["Dashboard"])
class PatientStatisticsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        user = request.user
        if user.role == 'patient':
            return user.patient_profile

        if user.role == 'careperson':
            patient_id = request.query_params.get('patient_id')
            if not patient_id:
                return user.careperson_profile
            try:
                return user.careperson_profile.patients.get(id=int(patient_id))
            except Patient.DoesNotExist:
                raise ValidationError({"patient_id": "Patient not found or unauthorized"})

        raise ValidationError({"role": ["Invalid role"]})

    def get(self, request, *args, **kwargs):
        patient = self.get_patient(request)
        user = patient.user
        medications = Medication.objects.filter(user=user, is_finished=False)

        total_taken = 0
        total_missed = 0
        recent_activity = []
        weekly_data = []

        today = timezone.localdate()

        # حساب الجرعات المأخوذة والمفقودة
        for med in medications:
            for date_key, doses in med.dose_taken.items():
                if isinstance(doses, dict):
                    # يوم فيه أكثر من جرعة
                    for status in doses.values():
                        if status:
                            total_taken += 1
                        else:
                            total_missed += 1
                elif isinstance(doses, bool):
                    # يوم فيه جرعة واحدة مخزنة كـ bool
                    if doses:
                        total_taken += 1
                    else:
                        total_missed += 1

        # إعداد recent_activity
        for med in medications:
            for date_key, doses in med.dose_taken.items():
                if isinstance(doses, dict):
                    for dose_key, status in doses.items():
                        recent_activity.append({
                            "medication": med.name,
                            "status": "Taken" if status else "Missed",
                            "time": dose_key,
                            "datetime": dose_key
                        })
                elif isinstance(doses, bool):
                    recent_activity.append({
                        "medication": med.name,
                        "status": "Taken" if doses else "Missed",
                        "time": date_key,
                        "datetime": date_key
                    })

        recent_activity = sorted(
            recent_activity,
            key=lambda x: x["datetime"],
            reverse=True
        )[:8]

        # بيانات الأسبوع الأخير
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = str(date)
            taken = missed = 0

            for med in medications:
                if date_str in med.dose_taken:
                    doses_for_day = med.dose_taken[date_str]
                    if isinstance(doses_for_day, dict):
                        for status in doses_for_day.values():
                            if status:
                                taken += 1
                            else:
                                missed += 1
                    elif isinstance(doses_for_day, bool):
                        if doses_for_day:
                            taken += 1
                        else:
                            missed += 1

            total = taken + missed
            weekly_data.append({
                "day": date_str,
                "taken": taken,
                "missed": missed,
                "adherence_rate": round((taken / total) * 100, 2) if total > 0 else 0
            })

        total_doses = total_taken + total_missed
        adherence_rate = round((total_taken / total_doses) * 100, 2) if total_doses > 0 else 0

        payload = {
            "patient": patient.user.full_name,
            "overview": {
                "adherence_rate": adherence_rate,
                "taken_doses": total_taken,
                "missed_doses": total_missed,
                "active_medications": medications.count(),
            },
            "weekly_adherence": weekly_data,
            "recent_activity": recent_activity,
        }

        serializer = PatientStatisticsSerializer(payload)
        return Response(serializer.data)


@extend_schema(tags=['Dashboard'])
class MyPatientsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role != 'careperson':
            raise ValidationError({"message": "Invalid role"})

        patients = user.careperson_profile.patients.all()

        if not patients:
            raise ValidationError({"message": "There is no monitored patients"})

        return patients


@extend_schema(tags=['Dashboard'])
class MyCarepersonsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CarePersonMiniSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role != 'patient':
            raise ValidationError({'message': 'Invalid Role'})

        carepersons = user.patient_profile.carepersons.all()
        if not carepersons:
            raise ValidationError({"message": "There is no carepersons"})

        return carepersons
