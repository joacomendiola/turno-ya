"""Configuración de Django para la aplicación principal."""

from django.apps import AppConfig


class AppConfig(AppConfig):
    """Define el nombre interno y el nombre visible de la app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = "Clínica"
