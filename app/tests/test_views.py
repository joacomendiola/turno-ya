from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import (
    Especialidad,
    Medico,
    ObraSocial,
    Paciente,
    Turno,
    Ausencia,
    Recordatorio,
)

# TEST VIEW DETALLE MEDICO
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
        self.assertTemplateUsed(response, "clinica/detalle_medico.html")
        
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
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
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
            fecha_fin=date.today()
        )
        # Loguear el cliente de pruebas para acceder a HomeView (requiere login)
        self.client.login(username="testuser", password="testpass")

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
        self.assertContains(response, "¡BIENVENIDOS!")
        self.assertContains(response, "Total de Médicos")
        self.assertContains(response, "Total de Pacientes")
        self.assertContains(response, "Ausencias Activas")


class AuthViewCBVTest(TestCase):
    """Pruebas para la vista de autenticación basada en clases."""

    def test_pantalla_login_carga_correctamente(self):
        response = self.client.get(reverse("app:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_pantalla_registro_carga_correctamente(self):
        response = self.client.get(reverse("app:registro"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/registro.html")


class TemplateCoverageTest(TestCase):
    """Cobertura básica de templates para vistas sin tests previos."""

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="General")
        self.user_medico = User.objects.create_user(username="medico", password="pass")
        self.medico = Medico.objects.create(
            nombre="Ana",
            apellido="García",
            matricula="M-123",
            especialidad=self.especialidad,
            usuario=self.user_medico
        )
        self.user_paciente = User.objects.create_user(username="paciente", password="pass")
        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni=12345678,
            email="juan@mail.com",
            usuario=self.user_paciente
        )
        self.turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=date.today() + timedelta(days=1),
            motivo="Consulta",
            creado_por=self.user_paciente
        )
        self.ausencia = Ausencia.objects.create(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date.today() + timedelta(days=2),
            fecha_fin=date.today() + timedelta(days=4),
        )

    def test_lista_medicos_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_medicos.html")
        self.assertContains(response, "Directorio de Médicos")

    def test_lista_pacientes_template(self):
        self.client.login(username="medico", password="pass")
        response = self.client.get(reverse("app:lista_pacientes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_pacientes.html")
        self.assertContains(response, "Directorio de Pacientes")

    def test_registro_paciente_template(self):
        new_user = User.objects.create_user(username="nuevo", password="pass")
        self.client.login(username="nuevo", password="pass")
        response = self.client.get(reverse("app:registro_paciente"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/registro_paciente.html")
        self.assertContains(response, "Registro de nuevo paciente")

    def test_perfil_paciente_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:perfil_paciente"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/perfil_paciente.html")

    def test_nuevo_turno_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:nuevo_turno"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/nuevo_turno.html")
        self.assertContains(response, "Agendar Turno Médico")

    def test_nueva_ausencia_template(self):
        self.client.login(username="medico", password="pass")
        response = self.client.get(reverse("app:registrar_ausencia"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/nueva_ausencia.html")
        self.assertContains(response, "Registrar Ausencia")

    def test_lista_turnos_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_turnos.html")
        self.assertContains(response, "Mis Turnos")

    def test_lista_recordatorios_template(self):
        Recordatorio.objects.create(
            turno=self.turno,
            mensaje="Recuerda tu turno",
            fecha=date.today()
        )
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:lista_recordatorios"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_recordatorios.html")
        self.assertContains(response, "Recordatorios")

    def test_detalle_turno_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:detalle_turno", kwargs={"pk": self.turno.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/detalle_turno.html")
        self.assertContains(response, "Detalle del Turno")

    def test_aceptar_turno_template(self):
        self.client.login(username="medico", password="pass")
        response = self.client.get(reverse("app:aceptar_turno", kwargs={"pk": self.turno.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/aceptar_turno.html")

    def test_cancelar_turno_template(self):
        self.client.login(username="paciente", password="pass")
        response = self.client.get(reverse("app:cancelar_turno", kwargs={"pk": self.turno.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/cancelar_turno.html")
    
class HistorialPacienteViewTests(TestCase):
    def setUp(self):
        # Creamos la estructura base para la prueba
        self.user_medico = User.objects.create_user(username='doc_antonio', password='password123')
        self.especialidad = Especialidad.objects.create(nombre='Pediatria')
        self.medico = Medico.objects.create(nombre='Antonio', apellido='Banderas', matricula='2026', especialidad=self.especialidad, usuario=self.user_medico)
        
        self.user_paciente = User.objects.create_user(username='paciente_gaston', password='password123')
        self.paciente = Paciente.objects.create(nombre='Gastón', apellido='Mendiola', dni='12345678', email='gaston@email.com', usuario=self.user_paciente)

    def test_medico_autenticado_puede_ver_historial(self):
        self.client.login(username='doc_antonio', password='password123')
        response = self.client.get(reverse('app:historial_paciente', kwargs={'paciente_id': self.paciente.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial Clínico")

    def test_paciente_no_puede_ver_historial_y_da_error(self):
        self.client.login(username='paciente_gaston', password='password123')
        response = self.client.get(reverse('app:historial_paciente', kwargs={'paciente_id': self.paciente.id}))
        # Valida que rebote con un código de error de permiso denegado (403)
        self.assertEqual(response.status_code, 403)