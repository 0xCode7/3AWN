from django.contrib import admin
from .models import User, Patient, CarePerson


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass

@admin.register(CarePerson)
class CarePersonAdmin(admin.ModelAdmin):
    pass
