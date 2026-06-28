from django.db import models
from django.utils import timezone
from app.models.turno import Turno

class Recordatorio(models.Model):
    """Representa un recordatorio asociado a un turno específico."""
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="recordatorios")
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Recordatorio: {self.turno} - {self.fecha.strftime('%d/%m/%Y')}"

    @classmethod
    def validate(cls, turno, mensaje, fecha=None):
        errors = []

        if not isinstance(turno, Turno):
            errors.append("El turno es obligatorio y debe ser válido.")

        if not mensaje or not mensaje.strip():
            errors.append("El mensaje es obligatorio.")

        if fecha and fecha < timezone.now():
            errors.append("La fecha del recordatorio no puede ser anterior al momento actual.")

        return errors

    @classmethod
    def new(cls, turno, mensaje, fecha=None):
        errors = cls.validate(turno, mensaje, fecha)
        if errors:
            return None, errors

        recordatorio = cls.objects.create(
            turno=turno,
            mensaje=mensaje.strip(),
            fecha=fecha or timezone.now()
        )
        return recordatorio, []

    def update(self, mensaje=None, fecha=None):
        nuevo_mensaje = mensaje if mensaje is not None else self.mensaje
        nueva_fecha = fecha if fecha is not None else self.fecha

        errors = self.__class__.validate(self.turno, nuevo_mensaje, nueva_fecha)
        if errors:
            return errors

        self.mensaje = nuevo_mensaje.strip()
        self.fecha = nueva_fecha
        self.save()
        return []