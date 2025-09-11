from django.db import models
from authentication.models import User

# Create your models here.

class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.user.email})"
