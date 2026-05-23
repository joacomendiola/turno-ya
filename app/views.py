"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from pyexpat.errors import messages

from django.views.generic import CreateView, DeleteView, ListView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Medico, Turno, Paciente
from datetime import date
from django.db.models import Count
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
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