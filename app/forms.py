from django import forms
from .models import Turno
from datetime import date

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        # IMPORTANTE: Ajustar los campos según el modelo real de Turno
        fields = ("medico", "paciente", "fecha", "hora", "estado")

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and fecha.weekday() in (5, 6):  # 5 = Sábado, 6 = Domingo
            raise forms.ValidationError("No se permiten turnos los fines de semana.")
        return fecha
    
