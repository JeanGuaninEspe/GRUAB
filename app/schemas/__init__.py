"""
Módulo de esquemas de validación Pydantic v2.
"""
from app.schemas.catalogos import (
    RolPersonalEnum,
    TipoFlotaEnum,
    PersonalBase,
    PersonalCreate,
    PersonalRead,
    VehiculoBase,
    VehiculoCreate,
    VehiculoRead,
)
from app.schemas.operaciones import (
    TurnoEnum,
    SentidoEnum,
    SeveridadEnum,
    TipoGruaEnum,
    AmbulanciaBase,
    AmbulanciaCreate,
    AmbulanciaRead,
    GruaBase,
    GruaCreate,
    GruaRead,
    PatrullajeBase,
    PatrullajeCreate,
    PatrullajeRead,
)
from app.schemas.analitica import (
    KPITiemposItem,
    KPIServicioResumen,
    KPITiemposRespuestaResponse,
    PuntoNegroItem,
    PuntosNegrosResponse,
)
from app.schemas.reportes import ServicioReporteEnum, ReporteMTOPMetadata

__all__ = [
    "RolPersonalEnum",
    "TipoFlotaEnum",
    "PersonalBase",
    "PersonalCreate",
    "PersonalRead",
    "VehiculoBase",
    "VehiculoCreate",
    "VehiculoRead",
    "TurnoEnum",
    "SentidoEnum",
    "SeveridadEnum",
    "TipoGruaEnum",
    "AmbulanciaBase",
    "AmbulanciaCreate",
    "AmbulanciaRead",
    "GruaBase",
    "GruaCreate",
    "GruaRead",
    "PatrullajeBase",
    "PatrullajeCreate",
    "PatrullajeRead",
    "KPITiemposItem",
    "KPIServicioResumen",
    "KPITiemposRespuestaResponse",
    "PuntoNegroItem",
    "PuntosNegrosResponse",
    "ServicioReporteEnum",
    "ReporteMTOPMetadata",
]
