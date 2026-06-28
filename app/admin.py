"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico, Especialidad, Paciente, Turno, Recordatorio, Ausencia, ObraSocial

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Especialidades."""
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)
    fieldsets = (
        ("Información de la especialidad", {
            "fields": ("nombre", "descripcion"),
        }),
    )


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Médicos."""
    list_display = ("apellido", "nombre", "matricula", "especialidad")
    list_filter = ("especialidad",)
    search_fields = ("apellido", "nombre", "matricula")
    fieldsets = (
        ("Datos personales", {
            "fields": ("nombre", "apellido", "matricula"),
        }),
        ("Especialidad", {
            "fields": ("especialidad",),
        }),
    )


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Pacientes."""
    list_display = ("apellido", "nombre", "dni", "email", "telefono")
    search_fields = ("apellido", "nombre", "dni")
    fieldsets = (
        ("Datos personales", {
            "fields": ("nombre", "apellido", "dni"),
        }),
        ("Contacto", {
            "fields": ("email", "telefono"),
        }),
        ("Usuario asociado", {
            "fields": ("usuario",),
            "classes": ("collapse",),
        }),
    )
@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Turnos."""
    list_display = ("paciente", "medico", "fecha_hora", "estado")
    list_filter = ("estado", "medico", "fecha_hora")
    search_fields = ("paciente__apellido", "medico__apellido")
    date_hierarchy = "fecha_hora"
    fieldsets = (
        ("Información del turno", {
            "fields": ("paciente", "medico", "fecha_hora", "motivo", "estado"),
        }),
        ("Auditoría", {
            "fields": ("creado_por",),
            "classes": ("collapse",),
        }),
    )
@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ("turno", "fecha", "mensaje_corto")
    list_filter = ("fecha",)
    search_fields = ("turno__paciente__apellido", "mensaje")
    fieldsets = (
        ("Información del recordatorio", {
            "fields": ("turno", "fecha", "mensaje"),
        }),
    )
    def mensaje_corto(self, obj):
        return obj.mensaje[:50] + "..." if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = "Mensaje"

@admin.register(ObraSocial)
class ObraSocialAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Obras Sociales."""
    list_display = ("name", "requiereToken", "sitioWeb")
    search_fields = ("name",)
    list_filter = ("requiereToken",)

@admin.register(Ausencia)
class AusenciaAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Ausencias."""
    list_display = ("medico", "fecha_inicio", "fecha_fin", "motivo")
    list_filter = ("medico", "fecha_inicio", "fecha_fin")
    search_fields = ("medico__apellido", "medico__nombre", "motivo")
    date_hierarchy = "fecha_inicio"