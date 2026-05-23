"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from datetime import date

class Medico(models.Model):
    """Representa a un profesional médico disponible para turnos."""

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        """Retorna una etiqueta legible para listados y admin."""
        return f"Dr/a. {self.apellido}, {self.nombre}"

    def nombre_completo(self):
        """Retorna nombre y apellido concatenados."""
        return f"{self.nombre} {self.apellido}"

    def cantidad_turnos(self):
        """Retorna la cantidad total de turnos asociados a este médico."""
        if not hasattr(self, "turno_set"):
            return 0
        return self.turno_set.count()

    @classmethod
    def validate(cls, nombre, apellido, matricula, especialidad):
        """
        Valida los datos del médico. Retorna una lista de errores.
        Si la lista está vacía, los datos son válidos.
        """
        errors = []

        if not nombre or not nombre.strip():
            errors.append("El nombre es obligatorio.")

        if not apellido or not apellido.strip():
            errors.append("El apellido es obligatorio.")

        if not matricula or not matricula.strip():
            errors.append("La matrícula es obligatoria.")

        if not especialidad or not especialidad.strip():
            errors.append("La especialidad es obligatoria.")

        return errors

    @classmethod
    def new(cls, nombre, apellido, matricula, especialidad):
        """
        Crea y persiste un nuevo médico si los datos son válidos.
        Retorna (instancia, errors). Si hay errores, instancia es None.
        """
        errors = cls.validate(nombre, apellido, matricula, especialidad)
        if errors:
            return None, errors

        medico = cls.objects.create(
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            matricula=matricula.strip(),
            especialidad=especialidad.strip(),
        )
        return medico, []

    def update(self, nombre, apellido, matricula, especialidad):
        """
        Actualiza los datos del médico si los datos son válidos.
        Retorna una lista de errores. Si está vacía, la actualización fue exitosa.
        """
        errors = self.__class__.validate(nombre, apellido, matricula, especialidad)
        if errors:
            return errors

        self.nombre = nombre.strip()
        self.apellido = apellido.strip()
        self.matricula = matricula.strip()
        self.especialidad = especialidad.strip()
        self.save()
        return []

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


class Ausencia(models.Model):

    """Representa una ausencia o licencia de un médico."""

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    class Meta:
        ordering = ["-fecha_inicio"]
    
    def __str__(self):
        return f"Ausencia {self.medico.apellido} ({self.fecha_inicio} - {self.fecha_fin})"

    @classmethod
    def validate(cls, medico, motivo, fecha_inicio, fecha_fin, exclude_id=None):
        """
        Valida los datos de la ausencia.
        Retorna una lista de errores. Si está vacía, los datos son válidos.
        """
        errors = []

        if not motivo or not motivo.strip():
            errors.append("El motivo es obligatorio.")

        if not fecha_inicio:
            errors.append("La fecha de inicio es obligatoria.")

        if not fecha_fin:
            errors.append("La fecha de fin es obligatoria.")

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            errors.append("La fecha de inicio no puede ser posterior a la fecha de fin.")

        if fecha_inicio and fecha_inicio < date.today():
            errors.append("La fecha de inicio no puede ser anterior a hoy.")

        if fecha_fin and fecha_fin < date.today():
            errors.append("La fecha de fin no puede ser anterior a hoy.")

        # Validar solapamiento
        if medico and fecha_inicio and fecha_fin:
            ausencias_solapadas = cls.objects.filter(
                medico=medico,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
            )
            if exclude_id:
                ausencias_solapadas = ausencias_solapadas.exclude(id=exclude_id)
            
            if ausencias_solapadas.exists():
                errors.append("Ya existe una ausencia del médico en ese rango de fechas.")

        return errors

    @classmethod
    def new(cls, medico, motivo, fecha_inicio, fecha_fin):
        """
        Crea y persiste una nueva ausencia si los datos son válidos.
        Retorna (instancia, errors). Si hay errores, instancia es None.
        """
        errors = cls.validate(medico, motivo, fecha_inicio, fecha_fin)
        if errors:
            return None, errors

        ausencia = cls.objects.create(
            medico=medico,
            motivo=motivo.strip(),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return ausencia, []

    def update(self, motivo, fecha_inicio, fecha_fin):
        """
        Actualiza los datos de la ausencia si los datos son válidos.
        Retorna una lista de errores. Si está vacía, la actualización fue exitosa.
        """
        errors = self.__class__.validate(
            self.medico, motivo, fecha_inicio, fecha_fin, exclude_id=self.id
        )
        if errors:
            return errors

        self.motivo = motivo.strip()
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.save()
        return []
# ==========================================
# Para que el grupo importe sin errores, creamos vacios hasta que se implementen los modelos faltantes.
# ==========================================
class ObraSocial(models.Model): pass
class Paciente(models.Model): pass
class Turno(models.Model): pass
