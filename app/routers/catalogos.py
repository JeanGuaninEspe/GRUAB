"""
Endpoints para la consulta y administración de Catálogos Maestros (Personal y Vehículos).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.catalogos_service import catalogos_service
from app.schemas.catalogos import PersonalRead, VehiculoRead, RolPersonalEnum, TipoFlotaEnum

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get(
    "/personal",
    response_model=List[PersonalRead],
    status_code=status.HTTP_200_OK,
    summary="Listar personal de la concesión",
    description="Obtiene el listado de personal con filtros opcionales por rol y estado activo.",
)
def listar_personal(
    rol: Optional[RolPersonalEnum] = Query(None, description="Filtrar por rol operativo del personal"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Cantidad máxima de registros a retornar"),
    db: Session = Depends(get_db),
):
    rol_str = rol.value if rol else None
    return catalogos_service.listar_personal(
        db=db, rol=rol_str, activo=activo, skip=skip, limit=limit
    )


@router.get(
    "/vehiculos",
    response_model=List[VehiculoRead],
    status_code=status.HTTP_200_OK,
    summary="Listar flota de vehículos de la concesión",
    description="Obtiene el inventario de flota vehicular con filtros por tipo y disponibilidad.",
)
def listar_vehiculos(
    tipo_flota: Optional[TipoFlotaEnum] = Query(None, description="Filtrar por tipo de flota (AMBULANCIA, GRUA, PATRULLA)"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Cantidad máxima de registros a retornar"),
    db: Session = Depends(get_db),
):
    tipo_flota_str = tipo_flota.value if tipo_flota else None
    return catalogos_service.listar_vehiculos(
        db=db, tipo_flota=tipo_flota_str, activo=activo, skip=skip, limit=limit
    )
