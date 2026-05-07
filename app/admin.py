"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico

# TODO: reemplazar por @admin.register con list_display, list_filter, search_fields
admin.site.register(Medico)