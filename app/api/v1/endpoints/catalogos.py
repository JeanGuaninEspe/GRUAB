"""
Endpoints de Catálogos para el Módulo de Grúas:
- GET /api/v1/catalogos/choferes-grua: Personal con rol='CHOFER_GRUA' y activo=True
- GET /api/v1/catalogos/supervisores: Personal con rol='SUPERVISOR' y activo=True
- GET /api/v1/catalogos/vehiculos-grua: Flota con tipo_flota='GRUA' y activo=True
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.catalogos import CatPersonal, CatVehiculoConcesion
from app.schemas.catalogos import PersonalRead, VehiculoRead

router = APIRouter()


@router.get(
    "/choferes-grua",
    response_model=List[PersonalRead],
    status_code=status.HTTP_200_OK,
    summary="Listar choferes y operadores de grúa activos",
    description="Retorna el personal registrado en cat_personal con rol 'CHOFER_GRUA' y estado activo.",
)
def get_choferes_grua(db: Session = Depends(get_db)) -> List[PersonalRead]:
    personal = (
        db.query(CatPersonal)
        .filter(CatPersonal.rol == "CHOFER_GRUA", CatPersonal.activo == True)
        .order_by(CatPersonal.nombre_completo.asc())
        .all()
    )
    return [PersonalRead.model_validate(p) for p in personal]


@router.get(
    "/supervisores",
    response_model=List[PersonalRead],
    status_code=status.HTTP_200_OK,
    summary="Listar supervisores de operaciones activos",
    description="Retorna el personal registrado en cat_personal con rol 'SUPERVISOR' y estado activo.",
)
def get_supervisores(db: Session = Depends(get_db)) -> List[PersonalRead]:
    supervisores = (
        db.query(CatPersonal)
        .filter(CatPersonal.rol == "SUPERVISOR", CatPersonal.activo == True)
        .order_by(CatPersonal.nombre_completo.asc())
        .all()
    )
    return [PersonalRead.model_validate(p) for p in supervisores]


@router.get(
    "/vehiculos-grua",
    response_model=List[VehiculoRead],
    status_code=status.HTTP_200_OK,
    summary="Listar unidades vehiculares de grúa activas",
    description="Retorna las unidades vehiculares de la concesión con tipo_flota 'GRUA' y estado activo.",
)
def get_vehiculos_grua(db: Session = Depends(get_db)) -> List[VehiculoRead]:
    vehiculos = (
        db.query(CatVehiculoConcesion)
        .filter(CatVehiculoConcesion.tipo_flota == "GRUA", CatVehiculoConcesion.activo == True)
        .order_by(CatVehiculoConcesion.codigo_interno.asc())
        .all()
    )
    return [VehiculoRead.model_validate(v) for v in vehiculos]
