from django import forms
from .models import Paciente, Turno

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono']
        # El campo 'usuario' lo asignaremos automáticamente en la vista

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['medico', 'fecha_hora', 'motivo']
        # El campo 'paciente' lo asignaremos automáticamente en la vista    