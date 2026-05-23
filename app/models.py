"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 1. Especialidad primero, porque Medico depende de ella
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

# 2. Medico usa Especialidad
class Medico(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"Dr/a. {self.apellido}, {self.nombre}"

    # ... [mantener aquí tus métodos validate, new, update de Medico] ...

# 3. Paciente y Turno al final
class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI: {self.dni})"

    @classmethod
    def validate(cls, nombre, apellido, dni, email):
        errors = []
        if not dni or not dni.strip():
            errors.append("El DNI es obligatorio.")
        return errors

    @classmethod
    def new(cls, nombre, apellido, dni, email, usuario):
        errors = cls.validate(nombre, apellido, dni, email)
        if errors:
            return None, errors
        paciente = cls.objects.create(nombre=nombre, apellido=apellido, dni=dni, email=email, usuario=usuario)
        return paciente, []

class Turno(models.Model):
    ESTADOS = [('pendiente', 'Pendiente'), ('confirmado', 'Confirmado'), ('cancelado', 'Cancelado')]
    
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(default=timezone.now)
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Turno {self.id} - {self.paciente}"

class Ausencia(models.Model):
    # Definir campos pendientes aquí
    pass

class ObraSocial(models.Model):
    # Definir campos pendientes aquí
    pass