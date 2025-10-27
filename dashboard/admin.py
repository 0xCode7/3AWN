from django.contrib import admin
from .models import ConnectionRequest


# Register your models here.
@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    pass
