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
        errors = self.validate(self.nombre, self.apellido, str(self.dni), self.email)
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

class Ausencia(models.Model):

    """Representa una ausencia o licencia de un médico."""

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)                        #Agrego nulos para poder hacer la migración sin problemas
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField(default=date.today)
    
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

class Paciente(models.Model):
    nombre = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.nombre or "Paciente sin nombre"
 # TODO: agrego campo mínimo para utilizar el admin, ajustar según modelo real

class Turno(models.Model):
    fecha = models.DateField(null=True, blank=True)
    def __str__(self):
        return str(self.fecha) if self.fecha else "Turno sin fecha"

 # TODO: agrego campo mínimo para utilizar el formulario de turno, ajustar según modelo real
