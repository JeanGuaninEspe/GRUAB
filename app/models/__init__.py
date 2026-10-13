"""
Modelos de base de datos SQLAlchemy para el microservicio de rescate vial.
"""
from app.models.catalogos import CatPersonal, CatVehiculoConcesion
from app.models.transaccionales import AsistenciaAmbulancia, AsistenciaGrua, BitacoraPatrullaje

__all__ = [
    "CatPersonal",
    "CatVehiculoConcesion",
    "AsistenciaAmbulancia",
    "AsistenciaGrua",
    "BitacoraPatrullaje",
]
