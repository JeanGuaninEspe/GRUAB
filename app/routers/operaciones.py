"""
Endpoints para el Registro Operativo y Consulta de Asistencias (Ambulancias, Grúas y Patrullaje).
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.operaciones_service import operaciones_service
from app.schemas.operaciones import (
    AmbulanciaCreate,
    AmbulanciaRead,
    GruaCreate,
    GruaRead,
    PatrullajeCreate,
    PatrullajeRead,
)

router = APIRouter(prefix="/operaciones", tags=["Operaciones"])


# ==========================================
# ENDPOINTS AMBULANCIAS
# ==========================================

@router.post(
    "/ambulancias",
    response_model=AmbulanciaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar asistencia médica de ambulancia",
    description="Inserta un nuevo registro de atención prehospitalaria validando cronología y odometría.",
)
def registrar_ambulancia(
    data: AmbulanciaCreate,
    db: Session = Depends(get_db),
):
    return operaciones_service.registrar_ambulancia(db=db, data=data)


@router.get(
    "/ambulancias",
    response_model=List[AmbulanciaRead],
    status_code=status.HTTP_200_OK,
    summary="Listar asistencias de ambulancias",
    description="Consulta el historial de atenciones médicas registradas con filtros por fecha y turno.",
)
def listar_ambulancias(
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio para filtro de llamada (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin para filtro de llamada (YYYY-MM-DD)"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno operativo (1, 2 o 3)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por unidad vehicular"),
    skip: int = Query(0, ge=0, description="Paginación: registros a omitir"),
    limit: int = Query(50, ge=1, le=200, description="Paginación: límite de registros"),
    db: Session = Depends(get_db),
):
    return operaciones_service.listar_ambulancias(
        db=db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, turno=turno, id_vehiculo=id_vehiculo
    )


# ==========================================
# ENDPOINTS GRÚAS
# ==========================================

@router.post(
    "/gruas",
    response_model=GruaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar asistencia y remolque de grúa",
    description="Inserta una nueva asistencia mecánica o remolque validando odometría y parámetros de traslado.",
)
def registrar_grua(
    data: GruaCreate,
    db: Session = Depends(get_db),
):
    return operaciones_service.registrar_grua(db=db, data=data)


@router.get(
    "/gruas",
    response_model=List[GruaRead],
    status_code=status.HTTP_200_OK,
    summary="Listar asistencias de grúas",
    description="Consulta el historial de remolques y auxilios mecánicos registrados.",
)
def listar_gruas(
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio para filtro (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin para filtro (YYYY-MM-DD)"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno (1, 2 o 3)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por unidad vehicular"),
    skip: int = Query(0, ge=0, description="Paginación: registros a omitir"),
    limit: int = Query(50, ge=1, le=200, description="Paginación: límite de registros"),
    db: Session = Depends(get_db),
):
    return operaciones_service.listar_gruas(
        db=db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, turno=turno, id_vehiculo=id_vehiculo
    )


# ==========================================
# ENDPOINTS PATRULLAJE
# ==========================================

@router.post(
    "/patrullaje",
    response_model=PatrullajeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar bitácora diaria de patrullaje e inspección",
    description="Inserta un recorrido de inspección vial con odometría y control de novedades.",
)
def registrar_patrullaje(
    data: PatrullajeCreate,
    db: Session = Depends(get_db),
):
    return operaciones_service.registrar_patrullaje(db=db, data=data)


@router.get(
    "/patrullaje",
    response_model=List[PatrullajeRead],
    status_code=status.HTTP_200_OK,
    summary="Listar bitácoras de patrullaje vial",
    description="Consulta los recorridos de inspección registrados.",
)
def listar_patrullaje(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio de recorrido (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin de recorrido (YYYY-MM-DD)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por unidad vehicular"),
    skip: int = Query(0, ge=0, description="Paginación: registros a omitir"),
    limit: int = Query(50, ge=1, le=200, description="Paginación: límite de registros"),
    db: Session = Depends(get_db),
):
    return operaciones_service.listar_patrullajes(
        db=db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, id_vehiculo=id_vehiculo
    )
