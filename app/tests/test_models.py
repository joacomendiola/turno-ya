"""Pruebas unitarias del modelo Medico."""

from django.test import TestCase
from app.models import Medico
from app.models import Especialidad
from django.urls import reverse
from datetime import date
from app.models import Ausencia


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


class AusenciaModelTest(TestCase):

    """Verifica el modelo Ausencia, especialmente la validación de fechas y solapamientos entre ausencias del mismo médico."""
    
    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad="Pediatría",
        )

    def test_validate_ausencia_solapada_retorna_error(self):
        primera, errors_primera = Ausencia.new(
            medico=self.medico,
            motivo="Licencia médica",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 10),
        )
        self.assertEqual(errors_primera, [])
        self.assertIsNotNone(primera)

        _, errors_segunda = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=date(2026, 5, 5),
            fecha_fin=date(2026, 5, 12),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors_segunda)

    def test_validate_fecha_inicio_posterior_a_fin_retorna_error(self):
        _, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 20),
            fecha_fin=date(2026, 5, 10),
        )
        self.assertIn("La fecha de inicio no puede ser posterior a la fecha de fin.", errors)

     # --- str ---

    def test_str_muestra_medico_y_fechas(self):
        ausencia, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 5),
        )
        self.assertEqual(errors, [])
        self.assertIn("Romero", str(ausencia))
        self.assertIn("2026-05-01", str(ausencia))
        self.assertIn("2026-05-05", str(ausencia))
    
    # --- validate ---

    def test_validate_con_fechas_invalidas_retorna_error(self):
        errors = Ausencia.validate(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 20),
            fecha_fin=date(2026, 5, 10),
        )
        self.assertIn("La fecha de inicio no puede ser posterior a la fecha de fin.", errors)


    # --- new ---

    def test_new_crea_ausencia_con_datos_validos(self):
        ausencia, errors = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 5),
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(ausencia)
        self.assertTrue(Ausencia.objects.filter(id=ausencia.id).exists())

    def test_new_con_solapamiento_retorna_error(self):
        Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 5),
        )
        _, errors = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=date(2026, 5, 4),
            fecha_fin=date(2026, 5, 10),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors)


    # --- update ---

    def test_update_modifica_ausencia_correctamente(self):
        ausencia, _ = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 5),
        )
        errors = ausencia.update(
            motivo="Licencia extendida",
            fecha_inicio=date(2026, 5, 2),
            fecha_fin=date(2026, 5, 6),
        )
        self.assertEqual(errors, [])
        ausencia.refresh_from_db()
        self.assertEqual(ausencia.motivo, "Licencia extendida")
        self.assertEqual(ausencia.fecha_inicio, date(2026, 5, 2))

    def test_update_con_solapamiento_retorna_error(self):
        primera, _ = Ausencia.new(
            medico=self.medico,
            motivo="Licencia",
            fecha_inicio=date(2026, 5, 1),
            fecha_fin=date(2026, 5, 5),
        )
        segunda, _ = Ausencia.new(
            medico=self.medico,
            motivo="Vacaciones",
            fecha_inicio=date(2026, 5, 10),
            fecha_fin=date(2026, 5, 15),
        )
        errors = segunda.update(
            motivo="Vacaciones modificadas",
            fecha_inicio=date(2026, 5, 4),
            fecha_fin=date(2026, 5, 12),
        )
        self.assertIn("Ya existe una ausencia del médico en ese rango de fechas.", errors)

# TODO: agregar tests para Paciente y Turno cuando los implementen
