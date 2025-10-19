import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
# Create your models here.

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=20, blank=True)
    reset_code = models.CharField(max_length=6, null=True)
    reset_token = models.CharField(max_length=255, null=True)

    def save(self, *args, **kwargs):
        if not self.username:
            # Generate something like 3awn-a1b2c3
            self.username = f"3awn-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)