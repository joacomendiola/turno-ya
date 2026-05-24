"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from multiprocessing import context
from pyexpat.errors import messages

from django.views.generic import DetailView, ListView, TemplateView
from .models import Medico

from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404


class HomeView(TemplateView):
    """Vista de inicio. Por ahora vacía — completar con estadísticas."""

    template_name = "clinica/home.html"


class ListaMedicosView(ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"

class DetailMedicoView (DetailView):
    template_name = "clinica/detalle_medico.html"
    model = Medico
    context_object_name = "medico"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medico = context["medico"]
        context["obras_sociales"] = medico.obras_sociales.all()
        #context["ausencias_cargadas"] = medico.ausencias.all()  # si se implementa el modelo de Ausencia
        return context
    
# TODO: implementar las siguientes vistas:
# class ListaTurnosView(...): ...
# class NuevoTurnoView(...): ...
# class CancelarTurnoView(...): ...
# class ListaPacientesView(...): ...

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