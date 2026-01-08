from django.contrib import admin
from .models import Medication, Drug, DrugAlternative, ActiveIngredient


# Register your models here.
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    pass


@admin.register(ActiveIngredient)
class ActiveIngredientAdmin(admin.ModelAdmin):
    pass

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(DrugAlternative)
class DrugAlternativeAdmin(admin.ModelAdmin):
    pass
