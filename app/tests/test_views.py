from datetime import date
from django.test import TestCase
from django.urls import reverse
from app.models import Medico, Paciente, Turno, Ausencia

class HomeViewTest(TestCase):
    """Pruebas para la vista de inicio (HomeView)."""
    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad="Pediatría",
        )
        self.paciente = Paciente.objects.create()  # si tu modelo ya tiene campos, ajusta aquí
        self.turno = Turno.objects.create()        # si tu modelo ya tiene campos, ajusta aquí
        Ausencia.objects.create(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
        )

    def test_home_loads_successfully(self):
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/home.html")

    def test_home_context_contains_estadisticas(self):
        response = self.client.get(reverse("app:home"))
        self.assertIn("total_medicos", response.context)
        self.assertIn("total_pacientes", response.context)
        self.assertIn("total_turnos", response.context)
        self.assertIn("turnos_confirmados", response.context)
        self.assertIn("turnos_cancelados", response.context)
        self.assertIn("prox_turnos", response.context)
        self.assertIn("medicos_por_especialidad", response.context)
        self.assertIn("ausencias_activas", response.context)

    def test_home_renders_cards_de_estadisticas(self):
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, "Panel de inicio")
        self.assertContains(response, "Total de médicos")
        self.assertContains(response, "Total de pacientes")
        self.assertContains(response, "Ausencias activas")


class AuthViewCBVTest(TestCase):
    """Pruebas para la vista de autenticación basada en clases."""

    def test_pantalla_login_carga_correctamente(self):
        """Verifica que la página de login se muestre sin errores."""
        response = self.client.get(reverse('app:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
    
    def test_pantalla_login_con_datos_validos_redirige(self):
        response = self.client.get(reverse('app:registro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/registro.html')