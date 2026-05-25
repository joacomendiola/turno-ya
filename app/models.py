"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

# 1. Especialidad
class EspecialidadManager(models.Manager):
    def con_medicos_activos(self):
        return self.annotate(num_medicos=models.Count("medico")).filter(num_medicos__gt=0)

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    objects = EspecialidadManager()

    def __str__(self):
        return self.nombre

    def validate(self):
        errors = []
        if not self.nombre or not self.nombre.strip():
            errors.append("El nombre de la especialidad es obligatorio.")
        return errors
        
    @classmethod
    def new(cls, **kwargs):
        especialidad = cls(**kwargs)
        errors = especialidad.validate()
        if errors:
            return None, errors
        especialidad.save()
        return especialidad, []
        
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        errors = self.validate()
        if errors:
            return errors
        self.save()
        return []

# 2. Medico
class Medico(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.PositiveIntegerField(unique=True) 
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"Dr/a. {self.apellido}, {self.nombre}"

# 3. Paciente
class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.BigIntegerField(unique=True) 
    email = models.EmailField(unique=True)
    telefono = models.BigIntegerField(blank=True, null=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI: {self.dni})"

    @classmethod
    def validate(cls, nombre, apellido, dni, email):
        errors = []
        if not dni:
            errors.append("El DNI es obligatorio.")
        return errors

    @classmethod
    def new(cls, nombre, apellido, dni, email, usuario):
        errors = cls.validate(nombre, apellido, dni, email)
        if errors:
            return None, errors
        paciente = cls.objects.create(nombre=nombre, apellido=apellido, dni=dni, email=email, usuario=usuario)
        return paciente, []

# 4. Turno
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
        
        # 1. Validación de fecha en el pasado
        if fecha_hora < timezone.now():
            errors.append("La fecha del turno no puede ser en el pasado.")
        
        # 2. Validación de turno duplicado (overlapping)
        query = cls.objects.filter(medico=medico, fecha_hora=fecha_hora).exclude(estado='cancelado')
        if exclude_id:
            query = query.exclude(pk=exclude_id)
            
        if query.exists():
            errors.append("El médico ya tiene un turno asignado en ese horario.")
            
        # Validación de Ausencia (Tarea 3.2)
        # Extraemos solo la fecha (sin la hora) para cruzarla con los días de licencia
        fecha_turno = fecha_hora.date()
        
        # Buscamos si el médico tiene registrada una ausencia que incluya el día del turno
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
        
        turno = cls.objects.create(
            medico=medico, paciente=paciente, fecha_hora=fecha_hora, motivo=motivo, creado_por=usuario
        )
        return turno, []

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

# 5. Ausencia y ObraSocial
class Ausencia(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Ausencia: {self.medico} ({self.fecha_inicio} al {self.fecha_fin})"

class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre

    @classmethod
    def new(cls, nombre, codigo):
        obra_social = cls.objects.create(nombre=nombre, codigo=codigo)
        return obra_social, []