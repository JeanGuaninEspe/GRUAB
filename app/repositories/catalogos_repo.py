"""
Repositorio para acceso a datos de Catálogos Maestros (Personal y Vehículos).
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.catalogos import CatPersonal, CatVehiculoConcesion
from app.repositories.base import BaseRepository


class PersonalRepository(BaseRepository[CatPersonal]):
    def __init__(self):
        super().__init__(CatPersonal)

    def get_personal(
        self,
        db: Session,
        rol: Optional[str] = None,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CatPersonal]:
        query = db.query(CatPersonal)
        if rol is not None:
            query = query.filter(CatPersonal.rol == rol.upper())
        if activo is not None:
            query = query.filter(CatPersonal.activo == activo)
        return query.order_by(CatPersonal.nombre_completo.asc()).offset(skip).limit(limit).all()


class VehiculoRepository(BaseRepository[CatVehiculoConcesion]):
    def __init__(self):
        super().__init__(CatVehiculoConcesion)

    def get_vehiculos(
        self,
        db: Session,
        tipo_flota: Optional[str] = None,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CatVehiculoConcesion]:
        query = db.query(CatVehiculoConcesion)
        if tipo_flota is not None:
            query = query.filter(CatVehiculoConcesion.tipo_flota == tipo_flota.upper())
        if activo is not None:
            query = query.filter(CatVehiculoConcesion.activo == activo)
        return query.order_by(CatVehiculoConcesion.codigo_interno.asc()).offset(skip).limit(limit).all()


personal_repo = PersonalRepository()
vehiculo_repo = VehiculoRepository()
