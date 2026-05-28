"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico, Especialidad, Paciente, Turno

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Especialidades."""
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Médicos."""
    list_display = ("apellido", "nombre", "matricula", "especialidad")
    list_filter = ("especialidad",)
    search_fields = ("apellido", "nombre", "matricula")

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Pacientes."""
    list_display = ("apellido", "nombre", "dni", "email", "telefono")
    search_fields = ("apellido", "nombre", "dni")

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Turnos."""
    list_display = ("paciente", "medico", "fecha_hora", "estado")
    list_filter = ("estado", "medico", "fecha_hora")
    search_fields = ("paciente__apellido", "medico__apellido")
    date_hierarchy = "fecha_hora"

