
from django.db import models
from app.models.medico import Medico


class ObraSocial(models.Model): 
    name=models.CharField(max_length=100, unique=True, default="Nombre default")
    sitioWeb=models.URLField(blank=True, unique=True, null=True)
    requiereToken=models.BooleanField(default=False)
    medicos_disponibles=models.ManyToManyField(Medico, blank=False, related_name="obras_sociales") 

    class Meta:
        verbose_name_plural = "Obras Sociales"
        # Declaramos dos restricciones completamente independientes
        constraints = [
        
            models.UniqueConstraint(
                fields=['name'], 
                name='error_base_datos_obra_social_nombre_ya_existe'
            ),
            models.UniqueConstraint(
                fields=['sitioWeb'], 
                name='error_base_datos_obra_social_sitio_web_duplicado'
            )
        ]

    def __str__(self):
            return f"Obra social: {self.name}"
    
    @classmethod
    def validate(cls, name, sitioWeb, requiereToken, medicos_disponibles):
        errors = []
        if not name or not name.strip():
            errors.append("El nombre de la obra social es obligatorio.")
        
        if not isinstance(requiereToken, bool):
            errors.append("El campo 'requiereToken' debe ser un valor verdadero o falso.")
        
        if not isinstance(medicos_disponibles, (list, tuple)):
            errors.append("El campo 'medicos_disponibles' debe ser una lista de médicos.")
        elif len(medicos_disponibles) == 0:
            errors.append("Debe seleccionar al menos un médico disponible.")    
        return errors

    @classmethod
    def new(cls, name: str, sitioWeb: str, requiereToken: bool, medicos_disponibles: list[Medico]):
        errors = cls.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return None, errors

        obra_social = cls.objects.create(
            name=name.strip(),
            sitioWeb=sitioWeb.strip() if sitioWeb else None,
            requiereToken=requiereToken,
        )
        obra_social.medicos_disponibles.set(medicos_disponibles)
        return obra_social, errors

    
    def update(self, name: str, sitioWeb: str, requiereToken: bool, medicos_disponibles: list[Medico]):
        errors = self.__class__.validate(name, sitioWeb, requiereToken, medicos_disponibles)
        if errors:
            return errors

        self.name = name.strip()
        self.sitioWeb = sitioWeb.strip() if sitioWeb else None
        self.requiereToken = requiereToken
        self.medicos_disponibles.set(medicos_disponibles)
        self.save()
        return errors
