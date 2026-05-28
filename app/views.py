"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from pyexpat.errors import messages

from django.views.generic import CreateView, DeleteView, ListView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Medico, Turno, Paciente
from datetime import date
from django.db.models import Count
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import TurnoForm


class HomeView(TemplateView):
    """Vista de inicio. Muestra estadísticas generales y próximos turnos."""

    template_name = "clinica/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "total_medicos": Medico.objects.count(),
            "total_pacientes": Paciente.objects.count(),
            "total_turnos": Turno.objects.count(),
            "turnos_confirmados": Turno.objects.filter(estado="confirmado").count(),
            "turnos_cancelados": Turno.objects.filter(estado="cancelado").count(),
            "prox_turnos": Turno.objects.filter(fecha__gte=date.today()).order_by("fecha", "hora")[:5],
            "medicos_por_especialidad": Medico.objects.values("especialidad").annotate(count=Count("id")).order_by("-count"),
        })
        return context


class ListaMedicosView(LoginRequiredMixin, ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"

class DetalleMedicoView(LoginRequiredMixin, DetailView):
    """Muestra el detalle de un médico, incluyendo su agenda."""

    template_name = "clinica/detalle_medico.html"
    model = Medico
    context_object_name = "medico"

class ListaTurnosView(LoginRequiredMixin, ListView):
    """Lista los turnos de un médico."""
    model = Turno
    template_name = "clinica/lista_turnos.html"
    context_object_name = "turnos"

class NuevoTurnoView(LoginRequiredMixin, CreateView):
    """Permite crear un nuevo turno para un médico."""

    model = Turno
    form_class = TurnoForm
    template_name = "clinica/nuevo_turno.html"
    success_url = reverse_lazy("app:lista_turnos")

    def form_valid(self, form):
        messages.success(self.request, "Turno creado correctamente.")
        return super().form_valid(form)

class CancelarTurnoView(LoginRequiredMixin, DeleteView):
    """Permite cancelar un turno existente."""

    template_name = "clinica/cancelar_turno.html"

class ListaPacientesView(LoginRequiredMixin, ListView):
    """Lista los pacientes de un médico."""

    template_name = "clinica/lista_pacientes.html"
    model = Paciente
    context_object_name = "pacientes"

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

# Vistas de Gestión de Pacientes y Perfil
class RegistroPacienteView(LoginRequiredMixin, CreateView):
    template_name = 'clinica/registro_paciente.html'
    form_class = PacienteForm
    success_url = reverse_lazy('app:home')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, "Perfil de paciente registrado correctamente.")
        return super().form_valid(form)

class PerfilPacienteView(LoginRequiredMixin, UpdateView):
    """Vista para que el paciente edite su propio perfil."""
    model = Paciente
    form_class = PacienteForm
    template_name = 'clinica/perfil_paciente.html'
    success_url = reverse_lazy('app:home')

    def get_object(self, queryset=None):
        return self.request.user.paciente

    def form_valid(self, form):
        messages.success(self.request, "Perfil actualizado correctamente.")
        return super().form_valid(form)

class ListaPacientesView(LoginRequiredMixin, ListView):
    model = Paciente
    template_name = 'clinica/lista_pacientes.html'
    context_object_name = 'pacientes'

# Vistas de Gestión de Turnos
class NuevoTurnoView(LoginRequiredMixin, CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'clinica/nuevo_turno.html'
    success_url = reverse_lazy('app:lista_turnos')

    def form_valid(self, form):
        if not hasattr(self.request.user, 'paciente'):
            messages.error(self.request, "Debes registrar tus datos de paciente antes de pedir un turno.")
            return redirect('app:registro_paciente')

        turno, errors = Turno.new(
            medico=form.cleaned_data['medico'],
            paciente=self.request.user.paciente,
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
        
class CancelarTurnoView(LoginRequiredMixin, UpdateView):
    model = Turno
    template_name = 'clinica/cancelar_turno.html'
    fields = []
    success_url = reverse_lazy('app:lista_turnos')

    def form_valid(self, form):
        turno = self.get_object()
        if turno.paciente != self.request.user.paciente:
            messages.error(self.request, "No tienes permiso para cancelar este turno.")
            return redirect(self.success_url)

        errors = turno.update(estado='cancelado')
        if not errors:
            messages.success(self.request, "El turno ha sido cancelado exitosamente.")
            return redirect(self.success_url)
        else:
            for error in errors:
                messages.error(self.request, error)
            return self.form_invalid(form)

class ListaTurnosView(LoginRequiredMixin, ListView):
    model = Turno
    template_name = 'clinica/lista_turnos.html'
    context_object_name = 'turnos'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'paciente'):
            return Turno.objects.filter(paciente=self.request.user.paciente)
        return Turno.objects.none()