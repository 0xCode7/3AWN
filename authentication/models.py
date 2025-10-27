import uuid, random, string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('careperson', 'Care Person'),
    )

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=20, blank=True)
    reset_code = models.CharField(max_length=6, null=True)
    reset_token = models.CharField(max_length=255, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"3awn-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError("Invalid role. Must be 'patient' or 'careperson'.")

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    medical_history = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, blank=False, null=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"PT-{''.join(random.choices(string.ascii_letters + string.digits, k=8))}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.user.role != 'patient':
            raise ValidationError("Linked user must have role = 'patient'")

    def __str__(self):
        return f"Patient: {self.user.full_name}"


class CarePerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='careperson_profile')
    patients = models.ManyToManyField(Patient, blank=True, related_name='carepersons')

    def clean(self):
        if self.user.role != 'careperson':
            raise ValidationError("Linked user must have role = 'careperson'")

    def __str__(self):
        return f"CarePerson: {self.user.full_name}"
