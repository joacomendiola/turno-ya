"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from pyexpat.errors import messages

from django.views.generic import ListView, TemplateView
from .models import Medico, Paciente, Turno

from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import PacienteForm, TurnoForm
from django.shortcuts import redirect
from django.db import transaction


class HomeView(TemplateView):
    """Vista de inicio. Por ahora vacía — completar con estadísticas."""

    template_name = "clinica/home.html"


class ListaMedicosView(ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"


# TODO: implementar las siguientes vistas:
# class DetalleMedicoView(...): ...
# class ListaTurnosView(...): ...
# class CancelarTurnoView(...): ...

#VISTA de registro de pacientes y solicitud de turnos, además de login/logout y registro de usuarios
class RegistroPacienteView(CreateView):
    """Vista para el registro de nuevos pacientes."""
    template_name = 'clinica/registro_paciente.html'
    form_class = PacienteForm
    success_url = reverse_lazy('app:login')

    def form_valid(self, form):
        # Nota: Aquí asumo que el sistema captura usuario y password también.
        # Si usas UserCreationForm para el usuario base, deberás combinar formularios.
        paciente = form.save(commit=False)
        # Lógica para asignar el usuario logueado o crear uno nuevo
        paciente.save()
        messages.success(self.request, "Paciente registrado correctamente.")
        return redirect(self.success_url)
    
    #Vista de turnos pendientes para el paciente logueado
class ListaPacientesView(ListView):
    """Listado de pacientes para gestión administrativa."""
    model = Paciente
    template_name = 'clinica/lista_pacientes.html'
    context_object_name = 'pacientes'
class NuevoTurnoView(CreateView):
    """Vista para la solicitud de un nuevo turno médico."""
    model = Turno
    form_class = TurnoForm
    template_name = 'clinica/nuevo_turno.html'
    success_url = reverse_lazy('app:lista_turnos')

    def form_valid(self, form):
        # Usamos el método .new del modelo como exige el patrón obligatorio
        turno, errors = Turno.new(
            medico=form.cleaned_data['medico'],
            paciente=self.request.user.paciente, # Asume que el usuario tiene un perfil de paciente
            fecha_hora=form.cleaned_data['fecha_hora'],
            motivo=form.cleaned_data['motivo'],
            usuario=self.request.user
        )
        if not errors:
            messages.success(self.request, "Turno solicitado con éxito.")
            return redirect(self.success_url)
        else:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)
        
class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
       messages.success(self.request, f"¡Bienvenido/a al sistema, {self.request.user.username}!")
       return reverse_lazy('app:home')
    
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('app:login')

class RegistroView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/registro.html'
    success_url = reverse_lazy('app:login')

    def form_valid(self, form):
        messages.success(self.request, "¡Registro exitoso! Ahora puedes iniciar sesión.")
        return super().form_valid(form)
    
