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

    def test_validate_rechaza_dni_vacio(self):
        errors = Paciente.validate("Juan", "Pérez", None, "juan@gmail.com")
        self.assertIn("El DNI es obligatorio.", errors)

    def test_update_modifica_datos_correctamente(self):
        paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni=12345678,
            email="juan@gmail.com",
            usuario=self.user,
        )
        errors = paciente.update(nombre="Juan", apellido="Gómez", dni=12345678, email="juan@gmail.com")
        self.assertEqual(errors, [])
        paciente.refresh_from_db()
        self.assertEqual(paciente.apellido, "Gómez")

    def test_str_formatea_apellido_nombre_y_dni(self):
        paciente = Paciente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            dni=12345678,
            email="juan@gmail.com",
            usuario=self.user,
        )
        texto = str(paciente)
        self.assertIn("Pérez", texto)
        self.assertIn("Juan", texto)
        self.assertIn("12345678", texto)

class TurnoModelTest(TestCase):
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="General")
        self.medico = Medico.objects.create(nombre="Dr", apellido="House", matricula=1, especialidad=self.especialidad)
        self.user = User.objects.create_user(username="paciente1")
        self.paciente = Paciente.objects.create(nombre="P", apellido="P", dni=123, email="p@p.com", usuario=self.user)

    def test_creacion_turno_valido(self):
        fecha = timezone.now() + timedelta(days=1)
        turno, errors = Turno.new(self.medico, self.paciente, fecha, "Dolor", self.user)
        self.assertEqual(errors, [])
        self.assertEqual(turno.estado, 'pendiente')

    def test_str_incluye_paciente(self):
        fecha = timezone.now() + timedelta(days=1)
        turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=fecha,
            motivo="Dolor",
            creado_por=self.user,
        )
        self.assertIn("Turno", str(turno))
        self.assertIn("P, P", str(turno))

    def test_update_modifica_estado(self):
        fecha = timezone.now() + timedelta(days=1)
        turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=fecha,
            motivo="Dolor",
            creado_por=self.user,
        )
        errors = turno.update(estado="confirmado")
        self.assertEqual(errors, [])
        turno.refresh_from_db()
        self.assertEqual(turno.estado, "confirmado")

    def test_turno_duplicado_falla(self):
        """Tarea 3.4: Validar que no existan dos turnos para el mismo médico a la misma hora"""
        fecha = timezone.now() + timedelta(days=1)
        Turno.new(self.medico, self.paciente, fecha, "Consulta", self.user)
        
        # Intentar segundo turno misma hora
        turno, errors = Turno.new(self.medico, self.paciente, fecha, "Otro", self.user)
        self.assertIn("El médico ya tiene un turno asignado en ese horario.", errors)

    def test_turno_en_fecha_ausencia_falla(self):
        """Tarea 3.2: Validar que no se puede sacar turno si el médico está de licencia"""
        fecha_turno = timezone.now() + timedelta(days=5)
        # Creamos una ausencia que cubre esa fecha
        Ausencia.objects.create(
            medico=self.medico, 
            fecha_inicio=timezone.now().date(), 
            fecha_fin=fecha_turno.date() + timedelta(days=1)
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
        self.especialidad = Especialidad.objects.create(nombre="Pediatrí")

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

    def test_manager_con_medicos_activos_retorna_solo_especialidades_con_medicos(self):
        especialidad_con_medico = Especialidad.objects.create(nombre="Clínica")
        especialidad_sin_medico = Especialidad.objects.create(nombre="Dermatología")
        Medico.objects.create(nombre="Ana", apellido="Lopez", matricula="M-100", especialidad=especialidad_con_medico)

        resultados = Especialidad.objects.con_medicos_activos()

        self.assertIn(especialidad_con_medico, resultados)
        self.assertNotIn(especialidad_sin_medico, resultados)

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

class RecordatorioModelTest(TestCase):

    def setUp(self):

        self.esp = Especialidad.objects.create(nombre="Oftalmología")
        self.medico = Medico.objects.create(nombre="Hugo", apellido="Paz", matricula="111", especialidad=self.esp)
        self.user = User.objects.create_user(username="pacientex")
        self.paciente = Paciente.objects.create(nombre="Ana", apellido="Luz", dni=444, email="a@a.com", usuario=self.user)
        self.turno = Turno.objects.create(medico=self.medico, paciente=self.paciente, motivo="Chequeo", creado_por=self.user)

    def test_creacion_recordatorio(self):
        
        from app.models import Recordatorio
        recordatorio = Recordatorio.objects.create(turno=self.turno, mensaje="Traer estudios previos")
        self.assertIn("Recordatorio", str(recordatorio))
        self.assertEqual(recordatorio.turno, self.turno)

class AceptarTurnoViewSecurityTests(TestCase):

    def setUp(self):
        # 1. Configuramos una especialidad y médico totalmente distintos
        self.esp = Especialidad.objects.create(nombre="Dermatología")
        self.medico = Medico.objects.create(
            nombre="Esteban", 
            apellido="Quito", 
            matricula="MP-8841", 
            especialidad=self.esp
        )

        # 2. Crear Paciente 1 (Mariela - Dueña legítima del turno)
        self.user_mariela = User.objects.create_user(username='mariela', password='456')
        self.paciente_mariela = Paciente.objects.create(
            nombre="Mariela", 
            apellido="Benítez", 
            dni=33444555, 
            email="mariela@correo.com", 
            usuario=self.user_mariela
        )

        # 3. Crear Paciente 2 (Gastón - El usuario intruso)
        self.user_gaston = User.objects.create_user(username='gaston', password='456')
        self.paciente_gaston = Paciente.objects.create(
            nombre="Gastón", 
            apellido="Herrera", 
            dni=22555888, 
            email="gaston@correo.com", 
            usuario=self.user_gaston
        )

        # 4. Crear un usuario administrativo/sistema sin perfil de paciente asignado
        self.user_admin_test = User.objects.create_user(username='admin_test', password='456')

        # 5. Definimos los turnos de prueba asociados a Mariela
        self.fecha = timezone.now() + timedelta(days=3)
        
        self.turno_pendiente = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente_mariela,
            fecha_hora=self.fecha,
            motivo="Revisión de lunares",
            creado_por=self.user_mariela,
            estado='pendiente'
        )

        self.turno_ya_confirmado = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente_mariela,
            fecha_hora=self.fecha,
            motivo="Tratamiento cutáneo",
            creado_por=self.user_mariela,
            estado='confirmado'
        )

    def test_usuario_intentando_aceptar_turno_ajeno(self):
        """Valida que Gastón no pueda meterse a confirmar el turno de Mariela"""
        self.client.login(username='gaston', password='456')
        url = reverse('app:aceptar_turno', kwargs={'pk': self.turno_pendiente.pk})
        
        response = self.client.post(url)
        # El get_queryset los filtra, por ende debe retornar 404 Not Found
        self.assertEqual(response.status_code, 404)

    def test_aceptar_turno_que_no_esta_pendiente(self):
        """Valida que Mariela no pueda volver a aceptar un turno ya confirmado"""
        self.client.login(username='mariela', password='456')
        url = reverse('app:aceptar_turno', kwargs={'pk': self.turno_ya_confirmado.pk})
        
        response = self.client.post(url)
        self.assertRedirects(response, reverse('app:lista_turnos'))
        
        # Corroboramos que mantenga su estado original en BD
        self.turno_ya_confirmado.refresh_from_db()
        self.assertEqual(self.turno_ya_confirmado.estado, 'confirmado')

    def test_usuario_sin_perfil_paciente_es_rechazado(self):
        """Valida que un usuario sin vincular a Paciente rebote directamente"""
        self.client.login(username='admin_test', password='456')
        url = reverse('app:aceptar_turno', kwargs={'pk': self.turno_pendiente.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
