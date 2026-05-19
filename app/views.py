"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from pyexpat.errors import messages

from django.views.generic import ListView, TemplateView
from .models import Medico


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
# class NuevoTurnoView(...): ...
# class CancelarTurnoView(...): ...
# class ListaPacientesView(...): ...

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
       messages.success(self.request, f"¡Bienvenido/a al sistema, {self.request.user.username}!")
       return reverse_lazy('app:home')