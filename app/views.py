"""Vistas iniciales para navegar médicos y pantalla de inicio."""

 
from django.views.generic import CreateView, ListView, TemplateView, DetailView, UpdateView
from .models import Medico, Turno, Paciente, Ausencia, Especialidad
from datetime import date
from django.db.models import Count
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import Http404
from .forms import PacienteForm, TurnoForm
from django.contrib import messages 
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login

class HomeView(LoginRequiredMixin, TemplateView):
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
            "prox_turnos": Turno.objects.filter(fecha_hora__gte=date.today()).order_by("fecha_hora")[:5],
            "medicos_por_especialidad": Medico.objects.values("especialidad").annotate(count=Count("id")).order_by("-count"),
            "ausencias_activas": Ausencia.objects.filter(fecha_inicio__lte=date.today(), fecha_fin__gte=date.today()).count()
        })
        return context

class ListaMedicosView(LoginRequiredMixin, ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"

    def get_queryset(self):
        queryset = super().get_queryset()
        especialidad_id = self.request.GET.get('especialidad')
        # Si vino el parametro en la URL y no esta vacio, filtramos
        if especialidad_id:
            queryset = queryset.filter(especialidad_id=especialidad_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Enviamos todas las especialidades disponibles para renderizar el <select>
        context["especialidades"] = Especialidad.objects.all()
        return context

class DetalleMedicoView(LoginRequiredMixin, DetailView):
    """Muestra el detalle de un médico, incluyendo su agenda."""

    template_name = "clinica/detalle_medico.html"
    model = Medico
    context_object_name = "medico"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medico = context["medico"]
        context["obras_sociales"] = medico.obras_sociales.all()
        context["ausencias_cargadas"] = medico.ausencia_set.all()  # si se implementa el modelo de Ausencia
        return context

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

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Ya estás registrado y logueado.")
            return redirect('app:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user=form.save()
        login(self.request, user)
        messages.success(self.request, "¡Registro exitoso! Ahora puedes iniciar sesión.")
        return redirect('app:registro_paciente')
    
# Vistas de Gestión de Pacientes y Perfil
class RegistroPacienteView(LoginRequiredMixin, CreateView):
    template_name = 'clinica/registro_paciente.html'
    form_class = PacienteForm
    success_url = reverse_lazy('app:home')

    def dispatch(self, request, *args, **kwargs):
        # Si el usuario ya tiene un perfil de paciente, lo redirigimos a su perfil
        if hasattr(request.user, 'paciente'):
            messages.info(request, "Ya tienes un perfil de paciente registrado.")
            return redirect('app:home')
        return super().dispatch(request, *args, **kwargs)

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
        paciente = getattr(self.request.user, 'paciente', None)
        if not paciente:
            raise Http404("El usuario no tiene perfil de paciente registrado.")
        return paciente

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
        
        # Validar que el usuario tenga perfil de paciente antes de acceder
        if not hasattr(self.request.user, 'paciente'):
            messages.error(self.request, "Debes tener un perfil de paciente para cancelar un turno.")
            return redirect(self.success_url)
        
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
        user = self.request.user
        if hasattr(user, 'paciente'):
            return Turno.objects.filter(paciente=user.paciente)
        elif hasattr(user, 'medico'):
            return Turno.objects.filter(medico=user.medico)
        return Turno.objects.none()
    
class AceptarTurnoView(LoginRequiredMixin, UpdateView):
    model = Turno
    template_name = 'clinica/aceptar_turno.html'
    fields = []
    success_url = reverse_lazy('app:lista_turnos')

    def get_queryset(self):
        #Restringe los turnos únicamente al paciente logueado.
        user = self.request.user
        if hasattr(user, 'paciente'):
            return Turno.objects.filter(paciente=user.paciente)
        # Si no es paciente (ej: es médico o admin), no ve ningún turno en esta vista
        return Turno.objects.none()

    def form_valid(self, form):
        # 1. Validar que el usuario tenga perfil de paciente
        if not hasattr(self.request.user, 'paciente'):
            raise PermissionDenied("Solo los pacientes pueden aceptar turnos.")

        turno = self.get_object()

        # 2. Validar que el turno pertenezca a request.user.paciente 
        # (Ya lo cubre el get_queryset, pero lo reforzamos acá por seguridad)
        if turno.paciente != self.request.user.paciente:
            raise PermissionDenied("Este turno no te pertenece.")

        # 3. Validar que solo se pueda aceptar si turno.estado == "pendiente"
        if turno.estado != 'pendiente':
            messages.error(self.request, "Este turno ya no está pendiente.")
            return redirect(self.success_url)

        # Si pasa todas las validaciones, mutamos el estado y guardamos
        turno.estado = 'confirmado'
        turno.save()

        messages.success(self.request, "El turno ha sido confirmado exitosamente.")
        return redirect(self.success_url)
