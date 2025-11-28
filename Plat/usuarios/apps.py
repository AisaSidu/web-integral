# usuarios/apps.py
from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    name = 'usuarios'

    def ready(self):
        # importa signals para que se conecten
        import usuarios.signals  # noqa
