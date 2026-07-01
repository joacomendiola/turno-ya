"""Vistas iniciales para navegar médicos y pantalla de inicio."""

 
from django.views.generic import CreateView, ListView, TemplateView, DetailView, UpdateView, View
from app.models import Medico, Turno, Paciente, Ausencia, Especialidad, ObraSocial, Recordatorio
from datetime import date, datetime
from django.db.models import Count
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import Http404
from .forms import PacienteForm, TurnoForm
from django.contrib import messages 
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login

class HomeView(LoginRequiredMixin, TemplateView):
    """Vista de inicio. Muestra estadísticas generales y próximos turnos."""

    template_name = "clinica/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if hasattr(user, 'paciente'):
            context['recordatorios_pendientes'] = Turno.objects.filter(
                paciente=user.paciente,
                estado__in=['pendiente', 'confirmado']
            ).count()
            
        context.update({
            "total_medicos": Medico.objects.count(),
            "total_pacientes": Paciente.objects.count(),
            "total_turnos": Turno.objects.count(),
            "turnos_confirmados": Turno.objects.filter(estado="confirmado").count(),
            "turnos_cancelados": Turno.objects.filter(estado="cancelado").count(),
            "prox_turnos": Turno.objects.filter(fecha_hora__gte=date.today()).order_by("fecha_hora")[:5],
            "medicos_por_especialidad": Medico.objects.values("especialidad").annotate(count=Count("id")).order_by("-count"),
            "ausencias_activas": Ausencia.objects.filter(fecha_inicio__lte=date.today(), fecha_fin__gte=date.today()).count(),
            "especialidades": Especialidad.objects.con_medicos_activos().prefetch_related("medico"),
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
        # Agregamos la lista de especialidades para el filtro, solo con las que tienen médicos activos
        context["especialidades"] = Especialidad.objects.con_medicos_activos()
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
        context["ausencias_cargadas"] = medico.ausencia_set.all()  
        return context

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        if hasattr(self.request.user, "medico"):
            return reverse_lazy('app:home')
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
    
   
    def dispatch(self, request, *args, **kwargs):
        # Si NO es médico y NO es admin, lo bloqueamos
        if not (hasattr(request.user, 'medico') or request.user.is_staff):
            raise PermissionDenied("No tienes permisos para ver el directorio de pacientes.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = Paciente.objects.buscar_por_apellido(q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context

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

class DetalleTurnoView(LoginRequiredMixin, DetailView):
    model = Turno
    template_name = 'clinica/detalle_turno.html'
    context_object_name = 'turno'

    def get_object(self, queryset=None):
        turno = super().get_object(queryset)
        user = self.request.user
        if hasattr(user, 'paciente') and turno.paciente == user.paciente:
            return turno
        elif hasattr(user, 'medico') and turno.medico == user.medico:
            return turno
        raise PermissionDenied("No tienes permiso para ver este turno.")
        
class CancelarTurnoView(LoginRequiredMixin, View):
    
    def get(self, request, pk, *args, **kwargs):
        turno = get_object_or_404(Turno, pk=pk)
        return render(request, 'clinica/cancelar_turno.html', {'turno': turno})

    def post(self, request, pk, *args, **kwargs):
        turno = get_object_or_404(Turno, pk=pk)
        user = request.user
        
        es_paciente = hasattr(user, 'paciente') and turno.paciente == user.paciente
        es_medico = hasattr(user, 'medico') and turno.medico == user.medico

        if not (es_paciente or es_medico):
            messages.error(request, "No tienes permiso para cancelar este turno.")
            return redirect('app:lista_turnos')
        errors = turno.update(estado='cancelado')
    
        if not errors:
            messages.success(request, "El turno ha sido cancelado exitosamente.")
        else:
            for error in errors:
                messages.error(request, error)
                
        return redirect('app:lista_turnos')

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['es_medico'] = hasattr(self.request.user, 'medico')
        context['es_paciente'] = hasattr(self.request.user, 'paciente')
        return context
    
    def post(self, request, *args, **kwargs):
        turno_id = request.POST.get('turno_id')
        observaciones = request.POST.get('observaciones')
        
        if turno_id and observaciones is not None:
            turno = get_object_or_404(Turno, id=turno_id)
            if hasattr(request.user, 'medico') and turno.medico == request.user.medico:
                turno.observaciones = observaciones
                turno.save()
                messages.success(request, "Observaciones guardadas correctamente.")
            else:
                messages.error(request, "No tienes permiso para editar este turno.")
                
        return redirect('app:lista_turnos')
    
class AceptarTurnoView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'medico'):
            raise Http404("Solo los médicos pueden aceptar turnos.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk, *args, **kwargs):
        # Mostramos la pantalla de confirmación
        turno = get_object_or_404(Turno, pk=pk)
        return render(request, 'clinica/aceptar_turno.html', {'turno': turno})

    def post(self, request, pk, *args, **kwargs):
        turno = get_object_or_404(Turno, pk=pk)
        
        # Validación extra de seguridad: que el médico sea el dueño de este turno
        if turno.medico != request.user.medico:
            messages.error(request, "No tienes permiso para confirmar este turno.")
            return redirect('app:lista_turnos')

        # Validar que solo se pueda aceptar si turno.estado == "pendiente"
        if turno.estado != 'pendiente':
            messages.error(request, "Este turno ya no está pendiente.")
            return redirect('app:lista_turnos')
        
        errors = turno.update(estado='confirmado')

        if not errors:
            messages.success(request, "Turno confirmado exitosamente.")
        else:
            for error in errors:
                messages.error(request, error)
                
        return redirect('app:lista_turnos')

class RegistrarAusenciaView(LoginRequiredMixin, CreateView):
    model = Ausencia
    fields = ['motivo', 'fecha_inicio', 'fecha_fin']
    template_name = 'clinica/nueva_ausencia.html'
    success_url = reverse_lazy('app:home')

    def dispatch(self, request, *args, **kwargs):
        # Seguridad: Solo los usuarios con perfil de médico pueden acceder
        if not hasattr(request.user, 'medico'):
            raise PermissionDenied("Solo los médicos pueden cargar ausencias.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        
        ausencia, errors = Ausencia.new(
            medico=self.request.user.medico,
            motivo=form.cleaned_data['motivo'],
            fecha_inicio=form.cleaned_data['fecha_inicio'],
            fecha_fin=form.cleaned_data['fecha_fin']
        )
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        sugerencias = []
        turnos = Ausencia.turnos_conflicto(
            self.request.user.medico,
            ausencia.fecha_inicio,
            ausencia.fecha_fin
        )
        
        if turnos.exists():
            sugerencias = ausencia.sugerir_reprogramacion(turnos, ausencia.fecha_fin) 

        if sugerencias:
            messages.warning(
                self.request, 
                "Se encontraron turnos activos dentro del período de ausencia. "
                "Revisa las sugerencias de reprogramación."
            )
            for item in sugerencias:
                messages.warning(
                    self.request,
                    f"Turno de {item['turno'].paciente} el "
                    f"{item['fecha_original'].strftime('%d/%m/%Y %H:%M')} "
                    f"puede moverse a {item['fecha_sugerida'].strftime('%d/%m/%Y')}."
                )

        messages.success(self.request, "Ausencia registrada con éxito.")
        
        return redirect(self.success_url)
    
    def post(self, request, *args, **kwargs):
        # Si la acción del POST es reprogramar un turno en conflicto
        if request.POST.get("accion") == "reprogramar":
            turno_id = request.POST.get("turno_id")
            fecha_sugerida_str = request.POST.get("fecha_sugerida")
            
            try:
                # Obtenemos el turno verificando que pertenezca al médico autenticado (Seguridad)
                turno = Turno.objects.get(pk=turno_id, medico=request.user.medico)
                nueva_fecha = datetime.strptime(fecha_sugerida_str, "%Y-%m-%d %H:%M")
                
                errors = turno.create_proposal(
                    nueva_fecha, 
                    creado_por=request.user, 
                    mensaje="Propuesta generada por ausencia del médico"
                )
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, "Propuesta de reprogramación creada. El paciente deberá confirmarla.")
                    
            except Turno.DoesNotExist:
                messages.error(request, "El turno solicitado no existe o no tiene permisos sobre él.")
            except (ValueError, TypeError):
                messages.error(request, "El formato de la fecha sugerida es inválido.")
                
            return redirect('app:lista_turnos')
            
        return super().post(request, *args, **kwargs)

class AcceptProposalView(LoginRequiredMixin, View):
    def post(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        if not hasattr(request.user, 'paciente') or turno.paciente != request.user.paciente:
            messages.error(request, "No autorizado.")
            return redirect('app:lista_turnos')
        errors = turno.accept_proposal()
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            messages.success(request, "Has aceptado la reprogramación.")
        return redirect('app:lista_turnos')

class RejectProposalView(LoginRequiredMixin, View):
    def post(self, request, pk):
        turno = get_object_or_404(Turno, pk=pk)
        if not hasattr(request.user, 'paciente') or turno.paciente != request.user.paciente:
            messages.error(request, "No autorizado.")
            return redirect('app:lista_turnos')
        turno.reject_proposal()
        messages.success(request, "Has rechazado la propuesta de reprogramación.")
        return redirect('app:lista_turnos')

class RecordatorioListView(LoginRequiredMixin, ListView):
    model = Turno
    template_name = 'clinica/lista_recordatorios.html'
    context_object_name = 'recordatorios'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        turnos = Turno.objects.none()

        if hasattr(user, 'paciente'):
            turnos = Turno.objects.filter(
                paciente=user.paciente,
                estado__in=['pendiente', 'confirmado']
            ).select_related('medico', 'paciente').order_by('fecha_hora')
            
        elif hasattr(user, 'medico'):
            turnos = Turno.objects.filter(
                medico=user.medico,
                estado__in=['pendiente', 'confirmado']
            ).select_related('medico', 'paciente').order_by('fecha_hora')

        
        lista_adaptada = []
        for t in turnos:
            
            if t.propuesta_pendiente:
                mensaje = f"Propuesta de reprogramación: {t.propuesta_mensaje}"
            else:
                # CORRECCIÓN: Armamos el mensaje dependiendo de si es médico o paciente
                if hasattr(user, 'medico'):
                    mensaje = f"Recordatorio: Tienes un turno {t.estado} con el paciente {t.paciente.nombre} {t.paciente.apellido}."
                else:
                    mensaje = f"Recordatorio: Tienes un turno {t.estado} con el Dr. {t.medico.apellido}."

            lista_adaptada.append({
                'turno': t,
                'fecha': t.fecha_hora,
                'mensaje': mensaje
            })

        return lista_adaptada

class PropuestasPacienteView(LoginRequiredMixin, ListView):
    model = Turno
    template_name = 'clinica/lista_propuestas.html'
    context_object_name = 'turnos'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'paciente'):
            return Turno.objects.filter(paciente=user.paciente, propuesta_pendiente=True)
        return Turno.objects.none()

class HistorialPacienteView(LoginRequiredMixin, ListView):
    """Vista exclusiva para médicos y administradores: muestra el historial clínico de un paciente."""
    model = Turno
    template_name = 'clinica/historial_paciente.html'
    context_object_name = 'turnos'
    
    def dispatch(self, request, *args, **kwargs):
        if not (hasattr(request.user, 'medico') or request.user.is_staff):
            raise PermissionDenied("Solo los médicos o administradores pueden acceder al historial.")
        
        self.paciente = get_object_or_404(Paciente, id=self.kwargs['paciente_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Turno.objects.filter(paciente=self.paciente).exclude(estado='cancelado').order_by('-fecha_hora')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paciente'] = self.paciente
        return context