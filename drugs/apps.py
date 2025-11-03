from django.apps import AppConfig


class DrugsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drugs'

    def ready(self):
        from .ai_model.ddi_model import load_ddi_model
        load_ddi_model()
