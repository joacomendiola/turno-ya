"""Pruebas unitarias de los modelos del sistema TurnoYa."""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from app.models import Medico, Paciente, Turno, Especialidad, Ausencia, ObraSocial
from django.db import IntegrityError
from datetime import date, timedelta


class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""
    
    def setUp(self):
        # Configura las especialidades reales requeridas por la clave foránea
        self.esp_pediatria = Especialidad.objects.create(nombre="Pediatría")
        self.esp_cardiologia = Especialidad.objects.create(nombre="Cardiología")
        self.esp_clinica = Especialidad.objects.create(nombre="Clínica Médica")

        # Crea un médico base utilizando la relación con Pediatría
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad=self.esp_pediatria,
        )
    def test_validate_datos_correctos_retorna_lista_vacia(self):
        # MODIFICADO: Pasa la instancia objeto 'self.esp_cardiologia'
        errors = Medico.validate("Ana", "García", "MP-0001", self.esp_cardiologia)
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        # MODIFICADO: Pasa la instancia objeto 'self.esp_cardiologia'
        errors = Medico.validate("", "García", "MP-0001", self.esp_cardiologia)
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_vacia_retorna_error(self):
        # MODIFICADO: Pasa la instancia objeto 'self.esp_cardiologia'
        errors = Medico.validate("Ana", "García", "", self.esp_cardiologia)
        self.assertTrue(len(errors) > 0)

    def test_validate_especialidad_invalida_retorna_error(self):
        # NUEVO: Comprueba que el método rechace un string en lugar de un objeto Especialidad
        errors = Medico.validate("Ana", "García", "MP-0001", "Cardiología String")
        self.assertTrue(len(errors) > 0)

    # --- new ---

    def test_new_crea_medico_con_datos_validos(self):
        medico, errors = Medico.new("Carlos", "López", "MP-1234", self.esp_clinica)
        self.assertEqual(errors, [])
        self.assertIsNotNone(medico)
        self.assertEqual(medico.apellido, "López")
        self.assertTrue(Medico.objects.filter(matricula="MP-1234").exists())
    
    # --- update ---
    
    def test_update_modifica_datos_correctamente(self):
        errors = self.medico.update("Laura", "Romero", "MP-9999", self.esp_cardiologia)
        self.assertEqual(errors, [])
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.especialidad, self.esp_cardiologia)

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.medico.update("", "", "", "")
        self.assertTrue(len(errors) > 0)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.nombre, "Laura")  


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

class AusenciaModelTest(TestCase):

    """Verifica el modelo Ausencia, especialmente la validación de fechas y solapamientos entre ausencias del mismo médico."""
    
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")

        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="9999",
            especialidad=self.especialidad,
        )

    def test_validate_ausencia_solapada_retorna_error(self):
        hoy = date.today()
        primera, errors_primera = Ausencia.new(
            medico=self.medico,
            motivo="Licencia médica",
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=10),
        )
        self.assertEqual(errors_primera, [])
        self.assertIsNotNone(primera)

        _, errors_segunda = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=12),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors_segunda)

    def test_validate_fecha_inicio_posterior_a_fin_retorna_error(self):
        hoy = date.today()
        _, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=20),
            fecha_fin=hoy + timedelta(days=10),
        )
        self.assertIn("La fecha de inicio no puede ser posterior a la fecha de fin.", errors)

     # --- str ---

    def test_str_muestra_medico_y_fechas(self):
        hoy = date.today()
        ausencia, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=5),
        )
        self.assertEqual(errors, [])
        self.assertIn("Romero", str(ausencia))
        self.assertIn(str(hoy + timedelta(days=1)), str(ausencia))
        self.assertIn(str(hoy + timedelta(days=5)), str(ausencia))
    
    # --- validate ---
    def test_validate_con_fechas_invalidas_retorna_error(self):
        hoy = date.today()
        errors = Ausencia.validate(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=20),
            fecha_fin=hoy + timedelta(days=10),
        )
        self.assertIn("La fecha de inicio no puede ser posterior a la fecha de fin.", errors)


    # --- new ---

    def test_new_crea_ausencia_con_datos_validos(self):
        hoy = date.today()
        inicio = hoy + timedelta(days=1)
        fin = hoy + timedelta(days=5)

        ausencia, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=inicio,
            fecha_fin=fin,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(ausencia)
        self.assertTrue(Ausencia.objects.filter(id=ausencia.id).exists())

    def test_new_con_solapamiento_retorna_error(self):
        hoy = date.today()
        Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=5),
        )
        _, errors = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=hoy + timedelta(days=4),
            fecha_fin=hoy + timedelta(days=10),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors)


    def test_update_modifica_ausencia_correctamente(self):
        hoy = date.today()
        ausencia, _ = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=5),
        )
        errors = ausencia.update(
            motivo="Licencia extendida",
            fecha_inicio=hoy + timedelta(days=2),
            fecha_fin=hoy + timedelta(days=6),
        )
        self.assertEqual(errors, [])
        ausencia.refresh_from_db()
        self.assertEqual(ausencia.motivo, "Licencia extendida")
        self.assertEqual(ausencia.fecha_inicio, hoy + timedelta(days=2))

    def test_update_con_solapamiento_retorna_error(self):
        hoy = date.today()
        primera, _ = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=hoy + timedelta(days=1),
            fecha_fin=hoy + timedelta(days=5),
        )
        segunda, _ = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=hoy + timedelta(days=6),
            fecha_fin=hoy + timedelta(days=10),
        )
        errors = segunda.update(
            motivo="Vacaciones modificadas",
            fecha_inicio=hoy + timedelta(days=4),
            fecha_fin=hoy + timedelta(days=12),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors)

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
#///////////////////////////////////////////
#TESTS PARA OBRA SOCIAL

class ObraSocialModelTest(TestCase):

    def setUp(self):
        #Crea una instancia real
        self.especialidad_test = Especialidad.objects.create(nombre="Cardiología")

        #Pasa la instancia de especialidad creada al Medico para cumplir la relación FK
        self.medico_referencia = Medico.objects.create(
            nombre="Carlos",
            apellido="Gómez",
            matricula="M-5543",
            especialidad=self.especialidad_test
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

class ObraSocialSeparatedConstraintsTest(TestCase):

    def setUp(self):
        
        self.especialidad_test = Especialidad.objects.create(nombre="Pediatría")
        self.medico = Medico.objects.create(
            nombre="Luis", 
            apellido="Sosa", 
            matricula="M-4432", 
            especialidad=self.especialidad_test
        )

    def test_evita_nombres_duplicados(self):
        # Verifica que la base de datos rechace dos obras sociales con el mismo nombre
        obra1 = ObraSocial.objects.create(name="OSDE", sitioWeb="https://osde.com.ar")
        obra1.medicos_disponibles.set([self.medico])

        # Intentamos crear otra con distinto sitio web pero mismo nombre; debe fallar
        with self.assertRaises(IntegrityError):
            obra2 = ObraSocial.objects.create(name="OSDE", sitioWeb="https://otraosde.com.ar")
            obra2.medicos_disponibles.set([self.medico])

    def test_evita_sitios_web_duplicados(self):
        # Verifica que la base de datos rechace dos obras sociales con el mismo sitio web
        obra1 = ObraSocial.objects.create(name="OSDE", sitioWeb="https://osde.com.ar")
        obra1.medicos_disponibles.set([self.medico])

        # Intentamos crear otra con distinto nombre pero mismo sitio web; debe fallar
        with self.assertRaises(IntegrityError):
            obra2 = ObraSocial.objects.create(name="PAMI", sitioWeb="https://osde.com.ar")
            obra2.medicos_disponibles.set([self.medico])
# TODO: agregar tests para Paciente y Turno cuando los implementen
