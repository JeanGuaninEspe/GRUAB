"""
Esquemas Pydantic v2 para la gestión de Catálogos (Personal y Vehículos).
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RolPersonalEnum(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    PARAMEDICO = "PARAMEDICO"
    CHOFER_AMBULANCIA = "CHOFER_AMBULANCIA"
    CHOFER_GRUA = "CHOFER_GRUA"
    PATRULLERO = "PATRULLERO"


class TipoFlotaEnum(str, Enum):
    AMBULANCIA = "AMBULANCIA"
    GRUA = "GRUA"
    PATRULLA = "PATRULLA"


# Esquemas para Personal
class PersonalBase(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=150, description="Nombre y apellido completo")
    rol: RolPersonalEnum = Field(..., description="Rol operativo asignado")
    activo: bool = Field(default=True, description="Estado de disponibilidad en el sistema")


class PersonalCreate(PersonalBase):
    pass


class PersonalRead(PersonalBase):
    id_personal: int = Field(..., description="Identificador único del personal")

    model_config = ConfigDict(from_attributes=True)


# Esquemas para Vehículos
class VehiculoBase(BaseModel):
    codigo_interno: str = Field(..., min_length=2, max_length=20, description="Código de identificación interno institucional")
    placa: str = Field(..., min_length=6, max_length=10, description="Placa oficial de circulación")
    tipo_flota: TipoFlotaEnum = Field(..., description="Tipo de vehículo de asistencia")
    descripcion: Optional[str] = Field(None, max_length=100, description="Descripción técnica o modelo del vehículo")
    activo: bool = Field(default=True, description="Estado operativo del vehículo")


class VehiculoCreate(VehiculoBase):
    pass


class VehiculoRead(VehiculoBase):
    id_vehiculo: int = Field(..., description="Identificador único del vehículo")

    model_config = ConfigDict(from_attributes=True)
