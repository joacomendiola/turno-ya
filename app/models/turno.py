from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from app.models.medico import Medico
from app.models.paciente import Paciente
from app.models.ausencia import Ausencia

class Turno(models.Model):
    ESTADOS = [('pendiente', 'Pendiente'), ('confirmado', 'Confirmado'), ('cancelado', 'Cancelado')]
    
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(default=timezone.now)
    motivo = models.TextField()
    observaciones = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    propuesta_fecha = models.DateTimeField(null=True, blank=True)
    propuesta_pendiente = models.BooleanField(default=False)
    propuesta_mensaje = models.TextField(null=True, blank=True)
    propuesta_creado_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='propuestas_creadas'
    )
    class Meta:
        unique_together = ('medico', 'fecha_hora')

    def __str__(self):
        return f"Turno {self.id} - {self.paciente}"

    def clean(self):
        if self.estado == 'cancelado':
            return
            
        errors = Turno.validate(self.medico, self.fecha_hora, self.pk)
        if errors:
            raise ValidationError({'fecha_hora': errors})

    @classmethod
    def validate(cls, medico, fecha_hora, exclude_id=None):
        errors = []

        query = cls.objects.filter(medico=medico, fecha_hora=fecha_hora).exclude(estado='cancelado')
        if exclude_id:
            query = query.exclude(pk=exclude_id)
            
        if query.exists():
            errors.append("El médico ya tiene un turno asignado en ese horario.")
            
        fecha_turno = fecha_hora.date()
        ausencia_activa = False
        
        for ausencia in medico.ausencia_set.all():
            inicio = ausencia.fecha_inicio
            fin = ausencia.fecha_fin
            
            if hasattr(inicio, 'date'): inicio = inicio.date()
            if hasattr(fin, 'date'): fin = fin.date()
            
            try:
                if inicio <= fecha_turno <= fin:
                    ausencia_activa = True
                    break
            except TypeError:
                continue
                
        if ausencia_activa:
            errors.append("El médico se encuentra ausente o de licencia en la fecha solicitada.")
            
        return errors

    @classmethod
    def new(cls, medico, paciente, fecha_hora, motivo, usuario):
        errors = cls.validate(medico, fecha_hora)
        if errors:
            return None, errors
        from django.db import IntegrityError
        try:
            turno = cls.objects.create(
                medico=medico, 
                paciente=paciente, 
                fecha_hora=fecha_hora, 
                motivo=motivo, 
                creado_por=usuario
            )
            return turno, []
        except IntegrityError:
            return None, ["El médico ya tiene un turno asignado en ese horario."]

    def update(self, **kwargs):
        medico = kwargs.get('medico', self.medico)
        fecha_hora = kwargs.get('fecha_hora', self.fecha_hora)
        estado = kwargs.get('estado', self.estado) 
        
        if estado != 'cancelado':
            errors = self.validate(medico, fecha_hora, self.pk)
            if errors:
                return errors
                
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.save()
        return []
    
    # "Propuesta de reprogramación para el caso de solapamiento con ausencia del médico, creacion, aceptación y rechazo de la propuesta"
    def create_proposal(self, fecha, creado_por=None, mensaje=None):
        self.propuesta_fecha = fecha
        self.propuesta_pendiente = True
        self.propuesta_mensaje = mensaje or ""
        self.propuesta_creado_por = creado_por
        self.save()
        # Notificar creando un Recordatorio 
        from app.models.recordatorio import Recordatorio
        Recordatorio.objects.create(
            turno=self,
            mensaje=f"Propuesta de reprogramación a {fecha.strftime('%d/%m/%Y %H:%M')}. {self.propuesta_mensaje}",
            fecha=timezone.now()
        )
        return []
    
    def accept_proposal(self):
        if not self.propuesta_pendiente or not self.propuesta_fecha:
            return ["No hay propuesta pendiente."]
        errors = self.update(fecha_hora=self.propuesta_fecha)
        if errors:
            return errors
        # limpiar campos de propuesta
        self.propuesta_fecha = None
        self.propuesta_pendiente = False
        self.propuesta_mensaje = None
        self.propuesta_creado_por = None
        self.save()
        return []

    def reject_proposal(self):
        self.propuesta_fecha = None
        self.propuesta_pendiente = False
        self.propuesta_mensaje = None
        self.propuesta_creado_por = None
        self.save()
        return []
