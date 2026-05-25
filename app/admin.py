"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico, Especialidad, Paciente, Turno

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

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Pacientes."""
    
    # Columnas que se muestran en el listado principal
    list_display = ("nombre",)
    
    # Buscador interactivo por texto
    search_fields = ("nombre",)
    
    # Número de elementos por página
    list_per_page = 25

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Turnos."""
    
    # Columnas que se muestran en el listado principal
    list_display = ("fecha",)
    
    # Filtro lateral para segmentar rápidamente
    list_filter = ("fecha",)
    
    # Hierarquía de fechas
    date_hierarchy = "fecha"
    
    # Número de elementos por página
    list_per_page = 50
