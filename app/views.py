"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from django.views.generic import ListView, TemplateView, DetailView
from .models import Medico, Turno, Paciente


class HomeView(TemplateView):
    """Vista de inicio. Por ahora vacía — completar con estadísticas."""

    template_name = "clinica/home.html"
    context_object_name = "home_data"


class ListaMedicosView(ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"

class DetalleMedicoView(DetailView):
    """Muestra el detalle de un médico, incluyendo su agenda."""

    template_name = "clinica/detalle_medico.html"
    model = Medico
    context_object_name = "medico"

class ListaTurnosView(ListView):
    """Lista los turnos de un médico."""
    model = Turno
    template_name = "clinica/lista_turnos.html"
    context_object_name = "turnos"

class NuevoTurnoView(TemplateView):
    """Permite crear un nuevo turno para un médico."""

    template_name = "clinica/nuevo_turno.html"

class CancelarTurnoView(TemplateView):
    """Permite cancelar un turno existente."""

    template_name = "clinica/cancelar_turno.html"

class ListaPacientesView(ListView):
    """Lista los pacientes de un médico."""

    template_name = "clinica/lista_pacientes.html"
    model = Paciente
    context_object_name = "pacientes"



# TODO: implementar las siguientes vistas:
# class DetalleMedicoView(...): ...
# class ListaTurnosView(...): ...
# class NuevoTurnoView(...): ...
# class CancelarTurnoView(...): ...
# class ListaPacientesView(...): ...