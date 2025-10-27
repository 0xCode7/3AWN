from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Patient, CarePerson

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'patient':
            Patient.objects.get_or_create(user=instance)
        elif instance.role == 'careperson':
            CarePerson.objects.get_or_create(user=instance)