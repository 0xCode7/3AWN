from django.db import models
from authentication.models import User


class Drug(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active_ingredient = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} -> {self.active_ingredient}"

class Medication(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    time = models.TimeField()
    type = models.CharField(max_length=60, default='Tablet')
    times_per_day = models.IntegerField(default=1)
    duration_in_days = models.IntegerField(default=7)
    start_date = models.DateField(auto_now_add=True)
    dose_taken = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if self.time:
            self.time = self.time.replace(second=0, microsecond=0)
        super().save(*args, **kwargs)
