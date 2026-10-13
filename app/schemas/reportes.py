"""
Esquemas Pydantic v2 para la generación y exportación de reportes ministeriales MTOP.
"""
from enum import Enum
from pydantic import BaseModel, Field


class ServicioReporteEnum(str, Enum):
    AMBULANCIA = "ambulancia"
    GRUA = "grua"
    PATRULLAJE = "patrullaje"


class ReporteMTOPMetadata(BaseModel):
    servicio: ServicioReporteEnum
    mes: int = Field(..., ge=1, le=12, description="Mes del reporte (1-12)")
    anio: int = Field(..., ge=2000, le=2100, description="Año del reporte (YYYY)")
    total_registros: int
    nombre_archivo: str
