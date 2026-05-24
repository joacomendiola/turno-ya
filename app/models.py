"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from tokenize import String
from xml.parsers.expat import errors
from django.db import models


class Medico(models.Model):
    """Representa a un profesional médico disponible para turnos."""
    related_name = "medico"
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

# ==========================================
# Para que el grupo importe sin errores, creamos vacios hasta que se implementen los modelos faltantes.
# ==========================================
class ObraSocial(models.Model): 
    name=models.CharField(max_length=100, unique=True, default="Nombre default")
    sitioWeb=models.URLField(blank=True, unique=True, null=True)
    requiereToken=models.BooleanField(default=False)
    medicos_disponibles=models.ManyToManyField(Medico, blank=False) 

    class Meta:
        verbose_name_plural = "Obras Sociales"
        # Declaramos dos restricciones completamente independientes
        constraints = [
        
            models.UniqueConstraint(
                fields=['name'], 
                name='error_base_datos_obra_social_nombre_ya_existe'
            ),
            models.UniqueConstraint(
                fields=['sitioWeb'], 
                name='error_base_datos_obra_social_sitio_web_duplicado'
            )
        ]

    def __str__(self):
            return f"Obra social: {self.name}"
    
    @classmethod
    def validate(cls, name, sitioWeb, requiereToken, medicos_disponibles):
        errors = []
        if not name or not name.strip():
            errors.append("El nombre de la obra social es obligatorio.")
        
        if not isinstance(requiereToken, bool):
            errors.append("El campo 'requiereToken' debe ser un valor verdadero o falso.")
        
        if not isinstance(medicos_disponibles, (list, tuple)):
            errors.append("El campo 'medicos_disponibles' debe ser una lista de médicos.")
        elif len(medicos_disponibles) == 0:
            errors.append("Debe seleccionar al menos un médico disponible.")    
        return errors

    @classmethod
    def new(cls, name: str, sitioWeb: str, requiereToken: False, medicos_disponibles: list[Medico]):
        errors = cls.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return None, errors

        obra_social = cls.objects.create(
            name=name.strip(),
            sitioWeb=sitioWeb.strip(),
            requiereToken=requiereToken,
        )
        obra_social.medicos_disponibles.set(medicos_disponibles)
        return obra_social, errors

    
    def update(self, name: str, sitioWeb: str, requiereToken: False, medicos_disponibles: list[Medico]):
        errors = self.__class__.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return errors

        self.name = name.strip()
        self.sitioWeb = sitioWeb.strip()
        self.requiereToken = requiereToken
        self.medicos_disponibles.set(medicos_disponibles)
        self.save()
        return errors
    
# ==========================================
# Para que el grupo importe sin errores, creamos vacios hasta que se implementen los modelos faltantes.
# ==========================================
class Paciente(models.Model): pass
class Turno(models.Model): pass
class Ausencia(models.Model): pass

# class Especialidad(models.Model): ...  ← extraer especialidad a FK
    