"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico, Especialidad, Turno, Paciente

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Especialidades."""
    
    # Columnas que se muestran en el listado principal
    list_display = ("nombre", "descripcion")
    
    # Buscador interactivo por texto
    search_fields = ("nombre",)

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Médicos."""
    
    # Columnas visibles ordenadas de forma limpia
    list_display = ("apellido", "nombre", "matricula", "especialidad")
    
    # Filtro lateral para segmentar rápidamente
    list_filter = ("especialidad",)
    
    # Permite buscar médicos por sus datos clave o matrícula
    search_fields = ("apellido", "nombre", "matricula")

class TurnoInline(admin.TabularInline):
    model = Turno
    fields = ("fecha", "hora", "medico", "estado")  # ajustar según campos reales
    readonly_fields = ()
    extra = 0
    show_change_link = True

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "documento")  # ajustar según campos de Paciente
    search_fields = ("apellido", "nombre", "documento", "email")
    list_filter = ("obra_social",)  # ajustar si aplica
    inlines = (TurnoInline,)
    list_per_page = 25

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "medico", "paciente", "estado")
    list_filter = ("estado", "medico", "fecha")
    search_fields = ("paciente__apellido", "paciente__nombre", "medico__apellido", "medico__nombre")
    date_hierarchy = "fecha"
    list_per_page = 50
