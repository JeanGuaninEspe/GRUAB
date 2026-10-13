"""
Endpoints Transaccionales para Asistencias de Grúas:
- POST /api/v1/asistencias-grua/: Creación con validación estricta de cronología y odometría
- GET /api/v1/asistencias-grua/: Consulta paginada con filtros por rango de fechas, sector, tipo de grúa y severidad
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.transaccionales import AsistenciaGrua
from app.models.catalogos import CatPersonal, CatVehiculoConcesion
from app.schemas.operaciones import GruaCreate, GruaRead

router = APIRouter()


class AsistenciaGruaPaginadaResponse(BaseModel):
    total: int = Field(..., description="Total de registros encontrados con los filtros aplicados")
    skip: int = Field(..., description="Desplazamiento aplicado")
    limit: int = Field(..., description="Límite por página")
    items: List[GruaRead] = Field(..., description="Listado de asistencias de grúa")


@router.post(
    "/",
    response_model=GruaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva asistencia de grúa",
    description=(
        "Registra un nuevo servicio de grúa en dbo.asistencias_grua. "
        "Valida cronología estricta (ts_llamada <= ts_arribo <= ts_termino <= ts_retorno), "
        "odometría (odometro_llegada_km >= odometro_salida_km) y unicidad de código_formulario. "
        "km_recorridos es calculado y persistido en base de datos."
    ),
)
def crear_asistencia_grua(
    data: GruaCreate,
    db: Session = Depends(get_db),
) -> GruaRead:
    # 1. Validar unicidad del código de formulario
    existente = (
        db.query(AsistenciaGrua)
        .filter(AsistenciaGrua.codigo_formulario == data.codigo_formulario.strip())
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El código de formulario '{data.codigo_formulario}' ya está registrado.",
        )

    # 2. Validar integridad de personal supervisor
    if data.id_supervisor:
        supervisor = db.query(CatPersonal).filter(CatPersonal.id_personal == data.id_supervisor).first()
        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supervisor con ID {data.id_supervisor} no encontrado.",
            )
        if not supervisor.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El supervisor {supervisor.nombre_completo} no está activo.",
            )

    # 3. Validar integridad de chofer de grúa
    if data.id_chofer:
        chofer = db.query(CatPersonal).filter(CatPersonal.id_personal == data.id_chofer).first()
        if not chofer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chofer con ID {data.id_chofer} no encontrado.",
            )
        if not chofer.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El chofer {chofer.nombre_completo} no está activo.",
            )

    # 4. Validar vehículo de grúa si fue especificado
    if data.id_vehiculo:
        vehiculo = db.query(CatVehiculoConcesion).filter(CatVehiculoConcesion.id_vehiculo == data.id_vehiculo).first()
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unidad de grúa con ID {data.id_vehiculo} no encontrada.",
            )
        if not vehiculo.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La unidad de grúa {vehiculo.codigo_interno} no está activa.",
            )

    # 5. Instanciar y persistir (km_recorridos es calculado en SQL Server)
    nueva_grua = AsistenciaGrua(
        codigo_formulario=data.codigo_formulario.strip(),
        id_supervisor=data.id_supervisor,
        id_chofer=data.id_chofer,
        id_vehiculo=data.id_vehiculo,
        turno=int(data.turno),
        tipo_grua=data.tipo_grua.value,
        ts_llamada=data.ts_llamada,
        ts_arribo=data.ts_arribo,
        ts_termino=data.ts_termino,
        ts_retorno=data.ts_retorno,
        sector_referencia=data.sector_referencia.strip() if data.sector_referencia else None,
        abscisa_km=data.abscisa_km,
        sentido=data.sentido.value if hasattr(data.sentido, "value") else str(data.sentido),
        usuario_reporta=data.usuario_reporta.strip() if data.usuario_reporta else None,
        placa_asistida=data.placa_asistida.strip().upper() if data.placa_asistida else None,
        tipo_vehiculo_asistido=data.tipo_vehiculo_asistido.strip() if data.tipo_vehiculo_asistido else None,
        usuarios_atendidos=data.usuarios_atendidos,
        motivo_atencion=data.motivo_atencion.strip() if data.motivo_atencion else None,
        tipo_accidente=data.tipo_accidente.strip() if data.tipo_accidente else None,
        posible_causa=data.posible_causa.strip() if data.posible_causa else None,
        severidad=data.severidad.value if data.severidad else None,
        km_origen_traslado=data.km_origen_traslado,
        km_destino_traslado=data.km_destino_traslado,
        odometro_salida_km=data.odometro_salida_km,
        odometro_llegada_km=data.odometro_llegada_km,
        reportado_mtop=data.reportado_mtop,
        observaciones=data.observaciones.strip() if data.observaciones else None,
    )

    db.add(nueva_grua)
    db.commit()
    db.refresh(nueva_grua)

    return GruaRead.model_validate(nueva_grua)


@router.get(
    "/",
    response_model=AsistenciaGruaPaginadaResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar asistencias de grúa con filtros y paginación",
    description="Consulta asistencias de grúa con filtros por fecha de llamada, sector, tipo de grúa, severidad y búsqueda rápida.",
)
def listar_asistencias_grua(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha/hora inicial de llamada (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha/hora final de llamada (ISO format)"),
    sector_referencia: Optional[str] = Query(None, description="Filtrar por sector de referencia (búsqueda parcial)"),
    tipo_grua: Optional[str] = Query(None, description="Filtrar por tipo de grúa (PEQUEÑA, GRANDE, PLATAFORMA)"),
    severidad: Optional[str] = Query(None, description="Filtrar por severidad (LEVE, GRAVE, FATAL)"),
    placa_asistida: Optional[str] = Query(None, description="Filtrar por placa asistida (búsqueda parcial)"),
    codigo_formulario: Optional[str] = Query(None, description="Filtrar por código de formulario"),
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(50, ge=1, le=500, description="Cantidad máxima de registros por página"),
    db: Session = Depends(get_db),
) -> AsistenciaGruaPaginadaResponse:
    query = db.query(AsistenciaGrua)

    if fecha_inicio:
        query = query.filter(AsistenciaGrua.ts_llamada >= fecha_inicio)
    if fecha_fin:
        query = query.filter(AsistenciaGrua.ts_llamada <= fecha_fin)
    if sector_referencia and sector_referencia.strip():
        query = query.filter(AsistenciaGrua.sector_referencia.ilike(f"%{sector_referencia.strip()}%"))
    if tipo_grua and tipo_grua.strip():
        query = query.filter(AsistenciaGrua.tipo_grua == tipo_grua.strip())
    if severidad and severidad.strip():
        query = query.filter(AsistenciaGrua.severidad == severidad.strip())
    if placa_asistida and placa_asistida.strip():
        query = query.filter(AsistenciaGrua.placa_asistida.ilike(f"%{placa_asistida.strip()}%"))
    if codigo_formulario and codigo_formulario.strip():
        query = query.filter(AsistenciaGrua.codigo_formulario.ilike(f"%{codigo_formulario.strip()}%"))

    total = query.count()
    items = query.order_by(AsistenciaGrua.ts_llamada.desc()).offset(skip).limit(limit).all()

    return AsistenciaGruaPaginadaResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[GruaRead.model_validate(it) for it in items],
    )
