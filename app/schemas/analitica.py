"""
Esquemas Pydantic v2 para Analítica Avanzada, Modelos de Scoring, Tiempos de Respuesta,
Hotspots de Accidentabilidad y Recomendaciones de Despliegue Táctico.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class NivelRiesgoEnum(str, Enum):
    EXTREMO = "EXTREMO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


# ==========================================
# ESQUEMAS BÁSICOS DE KPIS Y PUNTOS NEGROS
# ==========================================

class KPITiemposItem(BaseModel):
    tipo_servicio: str = Field(..., description="Tipo de servicio (AMBULANCIA, GRUA, PATRULLAJE)")
    codigo_formulario: str = Field(..., description="Código del formulario o bitácora")
    fecha: Optional[date] = Field(None, description="Fecha de atención del evento")
    turno: Optional[int] = Field(None, description="Turno operativo")
    abscisa_km: Optional[Decimal] = Field(None, description="Ubicación kilométrica")
    sentido: Optional[str] = Field(None, description="Sentido vial")
    tiempo_despacho_arribo_min: Optional[float] = Field(None, description="Minutos transcurridos desde llamada hasta arribo")
    tiempo_en_sitio_min: Optional[float] = Field(None, description="Minutos transcurridos durante la atención en sitio")
    ciclo_total_min: Optional[float] = Field(None, description="Minutos totales del ciclo operativo hasta retorno")
    km_recorridos: Optional[float] = Field(None, description="Distancia total recorrida en kilómetros")

    model_config = ConfigDict(from_attributes=True)


class KPIServicioResumen(BaseModel):
    tipo_servicio: str
    total_eventos: int
    promedio_despacho_arribo_min: Optional[float]
    promedio_sitio_min: Optional[float]
    promedio_ciclo_total_min: Optional[float]
    total_km_recorridos: Optional[float]


class KPITiemposRespuestaResponse(BaseModel):
    total_registros: int = Field(..., description="Cantidad total de asistencias en el periodo filtrado")
    promedio_despacho_arribo_min: Optional[float] = Field(None, description="Tiempo medio global de despacho a arribo en minutos")
    promedio_sitio_min: Optional[float] = Field(None, description="Tiempo medio global de permanencia y maniobra en sitio")
    promedio_ciclo_total_min: Optional[float] = Field(None, description="Tiempo medio global del ciclo operativo completo")
    total_km_recorridos: Optional[float] = Field(None, description="Suma total de kilómetros recorridos por la flota")
    resumen_por_servicio: List[KPIServicioResumen] = Field(default_factory=list, description="Consolidado por tipo de servicio")
    detalles: List[KPITiemposItem] = Field(default_factory=list, description="Listado detallado de registros de la vista KPI")


class PuntoNegroItem(BaseModel):
    km_tramo: Decimal = Field(..., description="Kilómetro o tramo de la vía")
    sentido: str = Field(..., description="Sentido de circulación")
    tipo_accidente: Optional[str] = Field(None, description="Tipo o clasificación de accidente")
    posible_causa: Optional[str] = Field(None, description="Causa probable del siniestro")
    severidad: Optional[str] = Field(None, description="Severidad del evento (LEVE, GRAVE, FATAL)")
    total_eventos: int = Field(..., description="Cantidad total de siniestros registrados en este punto")

    model_config = ConfigDict(from_attributes=True)


class PuntosNegrosResponse(BaseModel):
    total_tramos_criticos: int = Field(..., description="Total de tramos o puntos negros identificados")
    total_eventos_acumulados: int = Field(..., description="Suma de eventos acumulados en estos tramos")
    tramos: List[PuntoNegroItem] = Field(default_factory=list, description="Lista de puntos negros ordenados por criticidad")


# ==========================================
# ESQUEMAS AVANZADOS: MODELO DE SCORING Y HOTSPOTS
# ==========================================

class TramoScoringItem(BaseModel):
    km_inicio: float = Field(..., description="Kilómetro inicial del tramo agrupado")
    km_fin: float = Field(..., description="Kilómetro final del tramo agrupado")
    tramo_label: str = Field(..., description="Etiqueta legible del tramo (ej. 'Km 20.0 - 25.0')")
    total_eventos: int = Field(..., description="Total de eventos y asistencias ocurridas en este tramo")
    total_ambulancias: int = Field(default=0, description="Total de asistencias médicas")
    total_gruas: int = Field(default=0, description="Total de remolques y auxilios mecánicos")
    total_fatales: int = Field(default=0, description="Accidentes con fatalidades")
    total_graves: int = Field(default=0, description="Accidentes graves con heridos o daños mayores")
    total_leves: int = Field(default=0, description="Incidentes o siniestros leves")
    indice_criticidad: float = Field(..., description="Índice ponderado de peligrosidad vial (ICV)")
    nivel_riesgo: NivelRiesgoEnum = Field(..., description="Clasificación del nivel de riesgo del tramo")
    sentido_predominante: Optional[str] = Field(None, description="Sentido vial con mayor concentración de siniestros")
    principal_tipo_accidente: Optional[str] = Field(None, description="Tipo de accidente más frecuente")
    principal_motivo_o_causa: Optional[str] = Field(None, description="Causa o motivo recurrente")
    franja_horaria_mayor_incidencia: Optional[str] = Field(None, description="Horario de mayor siniestralidad")
    recomendacion_tactica: Optional[str] = Field(None, description="Medida preventiva sugerida para este tramo")


class TramosScoringResponse(BaseModel):
    criterio_agrupacion_km: float = Field(..., description="Tamaño del intervalo de agrupación en kilómetros")
    total_tramos_analizados: int = Field(..., description="Cantidad total de tramos evaluados")
    total_eventos_evaluados: int = Field(..., description="Total de asistencias y siniestros procesados")
    resumen_niveles_riesgo: Dict[str, int] = Field(..., description="Conteo de tramos por nivel de riesgo (EXTREMO, ALTO, etc.)")
    top_tramos_criticos: List[TramoScoringItem] = Field(default_factory=list, description="Ranking de tramos ordenados por mayor peligrosidad")


# ==========================================
# ESQUEMAS PARA PATRONES TEMPORALES Y HORARIOS PICO
# ==========================================

class PatronHoraItem(BaseModel):
    hora: int = Field(..., ge=0, le=23, description="Hora del día (0 a 23)")
    franja_label: str = Field(..., description="Etiqueta horaria (ej. '14:00 - 15:00')")
    total_eventos: int
    total_ambulancias: int
    total_gruas: int
    total_accidentes_graves_o_fatales: int
    porcentaje: float


class PatronDiaItem(BaseModel):
    dia_nombre: str = Field(..., description="Nombre del día (Lunes, Martes, etc.)")
    total_eventos: int
    total_ambulancias: int
    total_gruas: int
    porcentaje: float


class PatronesTemporalesResponse(BaseModel):
    total_eventos_analizados: int
    hora_pico_maxima: str = Field(..., description="Hora de mayor demanda o siniestralidad")
    dia_pico_maximo: str = Field(..., description="Día con mayor índice de ocurrencia")
    eventos_fin_de_semana: int = Field(..., description="Total eventos en Viernes, Sábado y Domingo")
    eventos_entre_semana: int = Field(..., description="Total eventos de Lunes a Jueves")
    porcentaje_fin_de_semana: float
    distribucion_por_franja: Dict[str, int] = Field(..., description="Madrugada (00-06h), Mañana (06-12h), Tarde (12-18h), Noche (18-24h)")
    distribucion_por_hora: List[PatronHoraItem]
    distribucion_por_dia: List[PatronDiaItem]


# ==========================================
# ESQUEMAS PARA PLAN DE DESPLIEGUE ESTRATÉGICO
# ==========================================

class RecomendacionDespliegueItem(BaseModel):
    prioridad: int = Field(..., description="Nivel de prioridad (1 = Máxima)")
    recurso_recomendado: str = Field(..., description="Tipo de unidad a posicionar (AMBULANCIA, GRÚA, PATRULLA)")
    tramo_cobertura: str = Field(..., description="Tramo o punto kilométrico de posicionamiento")
    horario_optimo: str = Field(..., description="Ventana de tiempo y días recomendados")
    diagnostico_problema: str = Field(..., description="Hallazgo estadístico que fundamenta la acción")
    accion_preventiva: str = Field(..., description="Acción táctica u operativa requerida")
    impacto_esperado: str = Field(..., description="Beneficio operativo proyectado (ej. reducir tiempo de arribo)")


class RecomendacionesDespliegueResponse(BaseModel):
    fecha_generacion: datetime
    total_recomendaciones: int
    estrategia_general: str
    recomendaciones: List[RecomendacionDespliegueItem]


# ==========================================
# ESQUEMA DASHBOARD EJECUTIVO
# ==========================================

class DashboardEjecutivoResponse(BaseModel):
    total_asistencias_historicas: int
    total_ambulancias: int
    total_gruas: int
    total_patrullajes: int
    tasa_accidentabilidad_porcentaje: float
    tasa_asistencia_mecanica_porcentaje: float
    km_totales_atendidos: float
    tiempo_promedio_llegada_min: float
    tiempo_promedio_sitio_min: float
    tiempo_promedio_ciclo_min: float
    tramo_mas_critico: Optional[TramoScoringItem]
    franja_horaria_mas_critica: str
    dia_mas_critico: str
    recomendacion_ejecutiva: str
