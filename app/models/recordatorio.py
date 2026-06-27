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
