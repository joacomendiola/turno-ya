from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Paciente, Turno

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono']
        # El campo 'usuario' lo asignaremos automáticamente en la vista

    # Validación personalizada 1
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni and 8 > len(str(dni)) < 7 :
            raise ValidationError("El DNI debe tener entre 7 y 8 dígitos.")
        return dni

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['medico', 'fecha_hora', 'motivo']
        widgets = {
            # Mejora UX: muestra un selector de fecha y hora real en HTML5
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    # Validación personalizada 2
    def clean_fecha_hora(self):
        fecha = self.cleaned_data.get('fecha_hora')
        if fecha and fecha < timezone.now():
            raise ValidationError("No puedes solicitar un turno en una fecha pasada.")
        return fecha
