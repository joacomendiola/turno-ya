
from django.db import models
from datetime import date, timedelta
from app.models.medico import Medico, Turno

class Ausencia(models.Model):

    """Representa una ausencia o licencia de un médico."""

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)
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
    @classmethod
    def turnos_conflicto(cls, medico, fecha_inicio, fecha_fin):
        """Busca turnos activos del médico dentro del rango de ausencia."""
        return Turno.objects.filter(
            medico=medico,
            estado__in=["pendiente", "confirmado"],
            fecha_hora__date__gte=max(fecha_inicio, date.today()),
            fecha_hora__date__lte=fecha_fin,
        )

    @classmethod
    def sugerencias_reprogramacion(cls, turnos, fecha_fin):
        """Genera sugerencias simples de reprogramación para los turnos en conflicto."""
        fecha_sugerida = fecha_fin + timedelta(days=1)
        return [
            {
                "turno": turno,
                "fecha_original": turno.fecha_hora,
                "fecha_sugerida": fecha_sugerida,
            }
            for turno in turnos
        ]