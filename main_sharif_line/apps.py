from django.apps import AppConfig


class MainSharifLineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_sharif_line'

    def ready(self):
        import main_sharif_line.signals
