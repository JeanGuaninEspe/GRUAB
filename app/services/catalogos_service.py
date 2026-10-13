"""
Servicio de negocio para gestión y consulta de Catálogos.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.catalogos_repo import personal_repo, vehiculo_repo
from app.schemas.catalogos import PersonalRead, VehiculoRead


class CatalogosService:
    def listar_personal(
        self,
        db: Session,
        rol: Optional[str] = None,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PersonalRead]:
        personal_list = personal_repo.get_personal(
            db=db, rol=rol, activo=activo, skip=skip, limit=limit
        )
        return [PersonalRead.model_validate(p) for p in personal_list]

    def listar_vehiculos(
        self,
        db: Session,
        tipo_flota: Optional[str] = None,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[VehiculoRead]:
        vehiculos_list = vehiculo_repo.get_vehiculos(
            db=db, tipo_flota=tipo_flota, activo=activo, skip=skip, limit=limit
        )
        return [VehiculoRead.model_validate(v) for v in vehiculos_list]


catalogos_service = CatalogosService()
