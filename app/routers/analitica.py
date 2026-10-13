"""
Endpoints para Analítica de Rendimiento, KPIs de Tiempos de Respuesta,
Modelos de Scoring de Peligrosidad Vial, Hotspots y Recomendaciones de Despliegue Operativo.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analitica_service import analitica_service
from app.schemas.analitica import (
    KPITiemposRespuestaResponse,
    PuntosNegrosResponse,
    TramosScoringResponse,
    PatronesTemporalesResponse,
    RecomendacionesDespliegueResponse,
    DashboardEjecutivoResponse,
)
from app.schemas.operaciones import SentidoEnum, SeveridadEnum

router = APIRouter(prefix="/analitica", tags=["Analítica y KPIs"])


# ==========================================
# 1. TIEMPOS DE RESPUESTA
# ==========================================
@router.get(
    "/tiempos-respuesta",
    response_model=KPITiemposRespuestaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar KPIs y tiempos de respuesta operativa",
    description=(
        "Consume la vista dbo.vw_kpi_tiempos_atencion y entrega promedios calculados de despacho-arribo, "
        "tiempo en sitio y ciclo total, junto con el resumen por servicio y detalle de eventos."
    ),
)
def obtener_tiempos_respuesta(
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio para el análisis (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para el análisis (YYYY-MM-DD)"),
    servicio: Optional[str] = Query(None, description="Filtrar por tipo de servicio (AMBULANCIA, GRUA, PATRULLAJE)"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno operativo (1, 2 o 3)"),
    limit: int = Query(500, ge=1, le=2000, description="Límite máximo de registros a analizar"),
    db: Session = Depends(get_db),
):
    return analitica_service.obtener_kpis_tiempos_respuesta(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        servicio=servicio,
        turno=turno,
        limit=limit,
    )


# ==========================================
# 2. PUNTOS NEGROS (VISTA OFICIAL)
# ==========================================
@router.get(
    "/puntos-negros",
    response_model=PuntosNegrosResponse,
    status_code=status.HTTP_200_OK,
    summary="Identificar y priorizar puntos negros de accidentabilidad",
    description=(
        "Consume la vista dbo.vw_analitica_puntos_negros para mapear tramos viales críticos con alta frecuencia de siniestros."
    ),
)
def obtener_puntos_negros(
    severidad: Optional[SeveridadEnum] = Query(None, description="Filtrar por severidad (LEVE, GRAVE, FATAL)"),
    causa: Optional[str] = Query(None, description="Filtrar por palabra clave en posible causa"),
    sentido: Optional[SentidoEnum] = Query(None, description="Filtrar por sentido de la vía"),
    limit: int = Query(100, ge=1, le=500, description="Límite de tramos críticos a listar"),
    db: Session = Depends(get_db),
):
    severidad_str = severidad.value if severidad else None
    sentido_str = sentido.value if sentido else None
    return analitica_service.obtener_puntos_negros(
        db=db,
        severidad=severidad_str,
        causa=causa,
        sentido=sentido_str,
        limit=limit,
    )


# ==========================================
# 3. MODELO DE SCORING Y HOTSPOTS (CLUSTERING POR KM)
# ==========================================
@router.get(
    "/tramos-criticos-scoring",
    response_model=TramosScoringResponse,
    status_code=status.HTTP_200_OK,
    summary="Modelo de Scoring de Peligrosidad Vial y Hotspots por Tramo Kilométrico",
    description=(
        "Agrupa espacialmente todas las asistencias y accidentes por intervalos configurables de kilómetros "
        "(ej. cada 1km, 2km o 5km) y calcula el Índice Ponderado de Criticidad Vial (ICV), clasificando "
        "cada tramo en EXTREMO, ALTO, MEDIO o BAJO riesgo junto a una recomendación táctica preventiva."
    ),
)
def obtener_tramos_criticos_scoring(
    tamano_tramo_km: float = Query(5.0, ge=0.5, le=50.0, description="Intervalo en kilómetros para la agrupación espacial (ej. 1.0, 2.0, 5.0)"),
    fecha_inicio: Optional[date] = Query(None, description="Filtrar eventos desde (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Filtrar eventos hasta (YYYY-MM-DD)"),
    servicio: Optional[str] = Query(None, description="Filtrar por servicio (AMBULANCIA, GRUA)"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno operativo (1, 2 o 3)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por vehículo"),
    top_n: int = Query(15, ge=1, le=100, description="Cantidad de tramos críticos a retornar en el ranking"),
    db: Session = Depends(get_db),
):
    return analitica_service.obtener_scoring_tramos_criticos(
        db=db,
        tamano_tramo_km=tamano_tramo_km,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        servicio=servicio,
        turno=turno,
        id_vehiculo=id_vehiculo,
        top_n=top_n,
    )


# ==========================================
# 4. PATRONES TEMPORALES Y HORARIOS PICO
# ==========================================
@router.get(
    "/patrones-temporales",
    response_model=PatronesTemporalesResponse,
    status_code=status.HTTP_200_OK,
    summary="Análisis de patrones temporales, horas pico y días de mayor accidentabilidad",
    description=(
        "Entrega la distribución horaria (0 a 23h), días de la semana (Lunes a Domingo), franjas horarias "
        "y la proporción fin de semana vs entre semana para dimensionar turnos y guardias."
    ),
)
def obtener_patrones_temporales(
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    servicio: Optional[str] = Query(None, description="Filtrar por tipo de servicio"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno operativo (1, 2 o 3)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por vehículo"),
    db: Session = Depends(get_db),
):
    return analitica_service.obtener_patrones_temporales(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        servicio=servicio,
        turno=turno,
        id_vehiculo=id_vehiculo,
    )


# ==========================================
# 5. RECOMENDACIONES DE DESPLIEGUE TÁCTICO
# ==========================================
@router.get(
    "/recomendaciones-despliegue",
    response_model=RecomendacionesDespliegueResponse,
    status_code=status.HTTP_200_OK,
    summary="Plan de despliegue estratégico de ambulancias, grúas y patrullas",
    description=(
        "Genera recomendaciones priorizadas y fundamentadas estadísticamente sobre dónde ubicar "
        "las bases móviles y patrullas preventivas en función de la criticidad y horarios pico."
    ),
)
def obtener_recomendaciones_despliegue(
    db: Session = Depends(get_db),
):
    return analitica_service.obtener_plan_despliegue_estrategico(db=db)


# ==========================================
# 6. DASHBOARD EJECUTIVO
# ==========================================
@router.get(
    "/dashboard-ejecutivo",
    response_model=DashboardEjecutivoResponse,
    status_code=status.HTTP_200_OK,
    summary="Dashboard analítico consolidado para toma de decisiones ejecutivas",
    description=(
        "Visión integral con métricas clave de volumen, tiempos de respuesta, tasa de accidentabilidad, "
        "el tramo vial de mayor riesgo actual y la directriz operativa recomendada."
    ),
)
def obtener_dashboard_ejecutivo(
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    servicio: Optional[str] = Query(None, description="Filtrar por tipo de servicio"),
    turno: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por turno operativo (1, 2 o 3)"),
    id_vehiculo: Optional[int] = Query(None, description="Filtrar por vehículo"),
    db: Session = Depends(get_db),
):
    return analitica_service.obtener_dashboard_ejecutivo(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        servicio=servicio,
        turno=turno,
        id_vehiculo=id_vehiculo,
    )
