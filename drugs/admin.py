from django.contrib import admin
from .models import Medication, Drug, DrugAlternative


# Register your models here.
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    pass


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    pass


@admin.register(DrugAlternative)
class DrugAlternativeAdmin(admin.ModelAdmin):
    pass
