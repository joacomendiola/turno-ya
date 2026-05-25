"""Pruebas unitarias de los modelos del sistema TurnoYa."""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from app.models import Medico, Paciente, Turno, Especialidad, Ausencia
import datetime

class MedicoModelTest(TestCase):
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
        self.medico = Medico.objects.create(
            nombre="Laura", apellido="Romero", matricula=9999, especialidad=self.especialidad
        )

    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Romero", str(self.medico))
        self.assertIn("Laura", str(self.medico))

class EspecialidadModelTest(TestCase):
    def test_new_crea_especialidad_con_datos_validos(self):
        especialidad, errors = Especialidad.new(nombre="Pediatría", descripcion="Cuidado infantil")
        self.assertEqual(len(errors), 0)
        self.assertEqual(especialidad.nombre, "Pediatría")

class PacienteModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

    def test_creacion_paciente_valido(self):
        paciente, errors = Paciente.new("Juan", "Pérez", 12345678, "juan@gmail.com", self.user)
        self.assertEqual(errors, [])
        self.assertIsNotNone(paciente)

class TurnoModelTest(TestCase):
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="General")
        self.medico = Medico.objects.create(nombre="Dr", apellido="House", matricula=1, especialidad=self.especialidad)
        self.user = User.objects.create_user(username="paciente1")
        self.paciente = Paciente.objects.create(nombre="P", apellido="P", dni=123, email="p@p.com", usuario=self.user)

    def test_creacion_turno_valido(self):
        fecha = timezone.now() + datetime.timedelta(days=1)
        turno, errors = Turno.new(self.medico, self.paciente, fecha, "Dolor", self.user)
        self.assertEqual(errors, [])
        self.assertEqual(turno.estado, 'pendiente')

    def test_turno_duplicado_falla(self):
        """Tarea 3.4: Validar que no existan dos turnos para el mismo médico a la misma hora"""
        fecha = timezone.now() + datetime.timedelta(days=1)
        Turno.new(self.medico, self.paciente, fecha, "Consulta", self.user)
        
        # Intentar segundo turno misma hora
        turno, errors = Turno.new(self.medico, self.paciente, fecha, "Otro", self.user)
        self.assertIn("El médico ya tiene un turno asignado en ese horario.", errors)

    def test_turno_en_fecha_ausencia_falla(self):
        """Tarea 3.2: Validar que no se puede sacar turno si el médico está de licencia"""
        fecha_turno = timezone.now() + datetime.timedelta(days=5)
        # Creamos una ausencia que cubre esa fecha
        Ausencia.objects.create(
            medico=self.medico, 
            fecha_inicio=timezone.now().date(), 
            fecha_fin=fecha_turno.date() + datetime.timedelta(days=1)
        )
        
        turno, errors = Turno.new(self.medico, self.paciente, fecha_turno, "Consulta", self.user)
        self.assertIn("El médico se encuentra ausente o de licencia en la fecha solicitada.", errors)

class AuthViewCBVTest(TestCase):
    def test_pantalla_login_carga_correctamente(self):
        response = self.client.get(reverse('app:login'))
        self.assertEqual(response.status_code, 200)
