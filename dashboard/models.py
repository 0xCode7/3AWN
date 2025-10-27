from django.db import models
from django.conf import settings
from authentication.models import *


# Create your models here.
class ConnectionRequest(models.Model):
    STATUS_CHOISES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    careperson = models.ForeignKey(
        CarePerson, on_delete=models.CASCADE, related_name='sent_requests'
    )

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='received_requests'
    )

    status = models.CharField(
        max_length=10, choices=STATUS_CHOISES, default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('careperson', 'patient')

    def clean(self):
        if self.careperson.user.role != 'careperson':
            raise ValidationError("The sender must have role = 'careperson'.")
        if self.patient.user.role != 'patient':
            raise ValidationError("The receiver must have role = 'patient'.")

    def __str__(self):
        return f"{self.careperson.user.full_name} → {self.patient.user.full_name} ({self.status})"
