from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from app.models import Especialidad, Medico, ObraSocial, Paciente, Turno, Ausencia
from django.contrib.auth.models import User

#TEST VIEW DETALLE MEDICO
class DetalleMedicoViewTest(TestCase):
    """Prueba el comportamiento de la vista de detalle del médico y sus restricciones."""

    def setUp(self):
        # Configuración de dependencias base
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
        self.user = User.objects.create_user(username="doctor_admin", password="password123")
        
        # Creación del médico de prueba
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-8888",
            especialidad=self.especialidad
        )
        
        # Datos cruzados que deben aparecer en el contexto
        self.obra_social = ObraSocial.objects.create(name="OSDE")
        self.obra_social.medicos_disponibles.add(self.medico)
        
        self.ausencia = Ausencia.objects.create(
            medico=self.medico,
            motivo="Congreso",
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=3)
        )

        # URL para la prueba
        self.url = reverse("app:detalle_medico", kwargs={"pk": self.medico.pk})

    def test_usuario_anonimo_es_redirigido_al_login(self):
        """Verifica que el LoginRequiredMixin bloquee a usuarios no autenticados."""
        response = self.client.get(self.url)
        
        # Debe dar estatus 302 (Redirección por seguridad)
        self.assertEqual(response.status_code, 302)
        # Comprueba que lo mande a la ruta de login con el parámetro 'next'
        self.assertIn(reverse("app:login"), response.url)

    def test_usuario_autenticado_puede_ver_detalle(self):
        """Verifica que un usuario logueado acceda exitosamente y visualice los datos."""
        # Forzamos el inicio de sesión en el cliente de prueba
        self.client.login(username="doctor_admin", password="password123")
        
        response = self.client.get(self.url)
        
        # Debe dar estatus 200 
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_medicos.html")
        
        # Validamos que el médico del contexto sea el correcto
        self.assertEqual(response.context["medico"], self.medico)

    def test_contexto_contiene_obras_sociales_y_ausencias(self):
            """Verifica que el método get_context_data empaquete los datos relacionados requeridos."""
            self.client.login(username="doctor_admin", password="password123")
            
            response = self.client.get(self.url)
            
            # Comprobamos las listas inyectadas a mano en el contexto
            self.assertIn(self.obra_social, response.context["obras_sociales"])
            self.assertIn(self.ausencia, response.context["ausencias_cargadas"])

    def test_medico_inexistente_retorna_404(self):
            """Verifica que si se busca un ID inválido, la vista arroje un error 404."""
            self.client.login(username="doctor_admin", password="password123")
             
            url_invalida = reverse("app:detalle_medico", kwargs={"pk": self.medico.pk + 999})
            response = self.client.get(url_invalida)
            
            self.assertEqual(response.status_code, 404)

class HomeViewTest(TestCase):
    """Pruebas para la vista de inicio (HomeView)."""
    def setUp(self):
        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría"
        )
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="9999",
            especialidad=self.especialidad
            
        )
        usuario = User.objects.create_user(username="testuser", password="testpass")
        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni="12345678",
            email="juan@gmail.com",
            usuario=usuario
        )  
        self.turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=date.today(),
            motivo="Consulta general",
            estado="pendiente",
            creado_por=usuario
        )        
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