
# 4. Turno
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
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('medico', 'fecha_hora')

    def __str__(self):
        return f"Turno {self.id} - {self.paciente}"

    def clean(self):
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
            
        # 2. Validación de Ausencia (Tarea 3.2)
        fecha_turno = fecha_hora.date()
        ausencia_activa = medico.ausencia_set.filter(
            fecha_inicio__lte=fecha_turno,
            fecha_fin__gte=fecha_turno
        ).exists()
        
        if ausencia_activa:
            errors.append("El médico se encuentra ausente o de licencia en la fecha solicitada.")
            
        return errors

    @classmethod
    def new(cls, medico, paciente, fecha_hora, motivo, usuario):
        errors = cls.validate(medico, fecha_hora)
        if errors:
            return None, errors
        
        # Atrapamos fallos directos de unicidad de la BD para transformarlos en errores limpios
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
        errors = self.validate(medico, fecha_hora, self.pk)
        if errors:
            return errors
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.save()
        return []
