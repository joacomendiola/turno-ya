"""Pruebas unitarias del modelo Medico."""

from django.test import TestCase
from app.models import Especialidad, Medico,ObraSocial
from django.urls import reverse


class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad="Pediatría",
        )

    # --- __str__ y métodos simples ---

    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Romero", str(self.medico))
        self.assertIn("Laura", str(self.medico))

    def test_nombre_completo(self):
        self.assertEqual(self.medico.nombre_completo(), "Laura Romero")

    def test_cantidad_turnos_inicial_es_cero(self):
        self.assertEqual(self.medico.cantidad_turnos(), 0)

    # --- validate ---

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = Medico.validate("Ana", "García", "MP-0001", "Cardiología")
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        errors = Medico.validate("", "García", "MP-0001", "Cardiología")
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_vacia_retorna_error(self):
        errors = Medico.validate("Ana", "García", "", "Cardiología")
        self.assertTrue(len(errors) > 0)

    # --- new ---

    def test_new_crea_medico_con_datos_validos(self):
        medico, errors = Medico.new("Carlos", "López", "MP-1234", "Clínica Médica")
        self.assertEqual(errors, [])
        self.assertIsNotNone(medico)
        self.assertEqual(medico.apellido, "López")
        self.assertTrue(Medico.objects.filter(matricula="MP-1234").exists())

    def test_new_con_datos_invalidos_retorna_errores_y_no_crea(self):
        count_antes = Medico.objects.count()
        medico, errors = Medico.new("", "", "", "")
        self.assertIsNone(medico)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Medico.objects.count(), count_antes)

    # --- update ---

    def test_update_modifica_datos_correctamente(self):
        errors = self.medico.update("Laura", "Romero", "MP-9999", "Cardiología")
        self.assertEqual(errors, [])
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.especialidad, "Cardiología")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.medico.update("", "", "", "")
        self.assertTrue(len(errors) > 0)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.nombre, "Laura")  # sin cambios



class EspecialidadModelTest(TestCase):

    def test_new_crea_especialidad_con_datos_validos(self):
        """Verifica que se pueda crear una especialidad con datos correctos."""
        especialidad, errors = Especialidad.new(nombre="Pediatría", descripcion="Cuidado infantil")
        self.assertIsNotNone(especialidad)
        self.assertEqual(len(errors), 0)
        self.assertEqual(especialidad.nombre, "Pediatría")
    
    def test_validate_nombre_vacio_retorna_error(self):
        """Edge case: El método validate debe rechazar nombres vacíos o con puros espacios."""
        especialidad, errors = Especialidad.new(nombre="   ")
        self.assertIsNone(especialidad)
        self.assertIn("El nombre de la especialidad es obligatorio.", errors)

    def test_update_modifica_datos_correctamente(self):
        """Verifica que el método update guarde los cambios si pasa la validación."""
        especialidad, _ = Especialidad.new(nombre="Traumatología")
        errors = especialidad.update(descripcion="Especialistas en huesos")
        self.assertEqual(len(errors), 0)
        self.assertEqual(especialidad.descripcion, "Especialistas en huesos")

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


# TODO: agregar tests para Paciente y Turno cuando los implementen
#TESTS PARA OBRA SOCIAL

class ObraSocialModelTest(TestCase):

    def setUp(self):
        # Configura un médico de prueba en la base de datos antes de ejecutar cada test.
        self.medico_referencia = Medico.objects.create(
            nombre="Carlos",
            apellido="Gómez",
            matricula="M-5543",
            especialidad="Cardiología"
        )
        self.lista_medicos_valida = [self.medico_referencia]

    def test_new_crea_obra_social_con_datos_validos(self):
        # Verifica la creación exitosa de una obra social con datos y relaciones correctas.
        obra_social, errors = ObraSocial.new(
            name="OSDE",
            sitioWeb="https://osde.com.ar",
            requiereToken=True,
            medicos_disponibles=self.lista_medicos_valida
        )
        
        self.assertIsNotNone(obra_social)
        self.assertEqual(len(errors), 0)
        self.assertEqual(obra_social.name, "OSDE")
        self.assertEqual(obra_social.medicos_disponibles.count(), 1)

    def test_validate_detecta_nombre_vacio(self):
        # Comprueba que el método validate rechace nombres que contengan solo espacios.
        errors = ObraSocial.validate(
            name="   ",
            sitioWeb="https://test.com",
            requiereToken=False,
            medicos_disponibles=self.lista_medicos_valida
        )
        
        self.assertIn("El nombre de la obra social es obligatorio.", errors)

    def test_validate_detecta_tipos_invalidos(self):
        # Valida que se capturen errores si los tipos de datos no coinciden con lo esperado.
        errors = ObraSocial.validate(
            name="PAMI",
            sitioWeb="https://pami.org",
            requiereToken="Texto Inválido",
            medicos_disponibles="No Soy Una Lista"
        )
        
        self.assertIn("El campo 'requiereToken' debe ser un valor verdadero o falso.", errors)
        self.assertIn("El campo 'medicos_disponibles' debe ser una lista de médicos.", errors)

    def test_update_modifica_datos_existentes(self):
        # Verifica que el método update reescriba los datos y guarde los cambios en la BD.
        obra_social, _ = ObraSocial.new(
            name="Sancor Salud",
            sitioWeb="https://sancor.com",
            requiereToken=False,
            medicos_disponibles=self.lista_medicos_valida
        )
        
        errors = obra_social.update(
            name="Sancor Salud Modificado",
            sitioWeb="https://sancormodificado.com",
            requiereToken=True,
            medicos_disponibles=self.lista_medicos_valida
        )
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(obra_social.name, "Sancor Salud Modificado")
        self.assertTrue(obra_social.requiereToken)