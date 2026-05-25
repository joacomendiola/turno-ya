"""Rutas de la aplicación principal."""

from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    # Públicas
    path("", views.HomeView.as_view(), name="home"),
    path("medicos/", views.ListaMedicosView.as_view(), name="lista_medicos"),
    
    # Autenticación
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
    
    # Protegidas (Requieren perfil de Paciente / Login)
    path('pacientes/registro/', views.RegistroPacienteView.as_view(), name='registro_paciente'),
    path('pacientes/perfil/', views.PerfilPacienteView.as_view(), name='perfil_paciente'), #3.3
    path('pacientes/', views.ListaPacientesView.as_view(), name='lista_pacientes'),
    
    # Turnos
    path('turnos/', views.ListaTurnosView.as_view(), name='lista_turnos'),
    path('turnos/nuevo/', views.NuevoTurnoView.as_view(), name='nuevo_turno'),
    path("turnos/<int:pk>/cancelar/", views.CancelarTurnoView.as_view(), name="cancelar_turno"),
]
    # TODO futuros:
    # path("medicos/<int:pk>/", views.DetalleMedicoView.as_view(), name="detalle_medico"),