
# 3. Paciente
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.contrib.auth.models import User

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

        if not nombre or not nombre.strip():
            errors.append("El nombre es obligatorio.")

        if not apellido or not apellido.strip():
            errors.append("El apellido es obligatorio.")

        if not email or not email.strip():
            errors.append("El email es obligatorio.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("El email no tiene un formato válido.")

        if not dni:
            errors.append("El DNI es obligatorio.")
        elif len(str(dni)) < 7 or len(str(dni)) > 8:
            errors.append("El DNI debe tener entre 7 y 8 dígitos.")
        return errors
    

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
