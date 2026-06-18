"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
#from tokenize import String
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date

class Medico(models.Model):
    """Representa a un profesional médico disponible para turnos."""

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.ForeignKey("Especialidad", on_delete=models.PROTECT, related_name="medico")
    
    #Agrego relación con usuario
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="medico")

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

        if not isinstance(especialidad, Especialidad):
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
            especialidad=especialidad,
        )
        return medico, errors

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
        self.especialidad = especialidad
        self.save()
        return errors

# 1. Especialidad
class EspecialidadManager(models.Manager):
    def con_medicos_activos(self):
        return self.annotate(num_medicos=models.Count("medico")).filter(num_medicos__gt=0)
from datetime import date

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

# 3. Paciente
class PacienteManager(models.Manager):
    def buscar_por_apellido(self, apellido):
        return self.filter(apellido__icontains=apellido)

class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.BigIntegerField(unique=True) 
    email = models.EmailField(unique=True)
    telefono = models.BigIntegerField(blank=True, null=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = PacienteManager()

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

    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        errors = self.validate(self.nombre, self.apellido, self.dni, self.email)
        if errors:
            return errors
        self.save()
        return []

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

class Ausencia(models.Model):

    """Representa una ausencia o licencia de un médico."""

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)                        #Agrego nulos para poder hacer la migración sin problemas
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField(default=date.today)
    
    class Meta:
        ordering = ["-fecha_inicio"]
    
    def __str__(self):
        medico_label = self.medico.apellido if self.medico else "Sin médico"
        return f"Ausencia {medico_label} ({self.fecha_inicio} - {self.fecha_fin})"

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
class ObraSocial(models.Model): 
    name=models.CharField(max_length=100, unique=True, default="Nombre default")
    sitioWeb=models.URLField(blank=True, unique=True, null=True)
    requiereToken=models.BooleanField(default=False)
    medicos_disponibles=models.ManyToManyField(Medico, blank=False, related_name="obras_sociales") 

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
    def new(cls, name: str, sitioWeb: str, requiereToken: bool, medicos_disponibles: list[Medico]):
        errors = cls.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return None, errors

        obra_social = cls.objects.create(
            name=name.strip(),
            sitioWeb=sitioWeb.strip() if sitioWeb else None,
            requiereToken=requiereToken,
        )
        obra_social.medicos_disponibles.set(medicos_disponibles)
        return obra_social, errors

    
    def update(self, name: str, sitioWeb: str, requiereToken: bool, medicos_disponibles: list[Medico]):
        errors = self.__class__.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return errors

        self.name = name.strip()
        self.sitioWeb = sitioWeb.strip() if sitioWeb else None
        self.requiereToken = requiereToken
        self.medicos_disponibles.set(medicos_disponibles)
        self.save()
        return errors


class Recordatorio(models.Model):
    """Representa un recordatorio asociado a un turno específico."""
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="recordatorios")
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Recordatorio: {self.turno} - {self.fecha.strftime('%d/%m/%Y')}"