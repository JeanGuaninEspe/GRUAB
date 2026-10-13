"""
Esquemas Pydantic v2 para el Registro Operativo de Asistencias y Patrullajes con Validaciones Estrictas.
"""
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TurnoEnum(IntEnum):
    TURNO_1 = 1
    TURNO_2 = 2
    TURNO_3 = 3


class SentidoEnum(str, Enum):
    ASCENDENTE = "ASCENDENTE"
    DESCENDENTE = "DESCENDENTE"
    BIDIRECCIONAL = "BIDIRECCIONAL"


class SeveridadEnum(str, Enum):
    LEVE = "LEVE"
    GRAVE = "GRAVE"
    FATAL = "FATAL"


class TipoGruaEnum(str, Enum):
    PEQUENA = "PEQUEÑA"
    GRANDE = "GRANDE"
    PLATAFORMA = "PLATAFORMA"


# ==========================================
# ESQUEMAS PARA AMBULANCIAS
# ==========================================

class AmbulanciaBase(BaseModel):
    codigo_formulario: str = Field(..., min_length=1, max_length=100, description="Código único de la hoja de atención médica")
    id_supervisor: Optional[int] = Field(None, gt=0, description="ID del supervisor a cargo")
    id_paramedico: Optional[int] = Field(None, gt=0, description="ID del paramédico actuante")
    id_chofer: Optional[int] = Field(None, gt=0, description="ID del chofer de la ambulancia")
    id_vehiculo: Optional[int] = Field(None, gt=0, description="ID del vehículo ambulancia")
    turno: Optional[int] = Field(None, description="Turno operativo (1, 2 o 3)")

    ts_llamada: Optional[datetime] = Field(None, description="Fecha y hora de recepción de la llamada de emergencia")
    ts_arribo: Optional[datetime] = Field(None, description="Fecha y hora de arribo al lugar del incidente")
    ts_termino: Optional[datetime] = Field(None, description="Fecha y hora de culminación de la atención o traslado")
    ts_retorno: Optional[datetime] = Field(None, description="Fecha y hora de retorno a la base operativa")

    sector_referencia: Optional[str] = Field(None, max_length=500, description="Sector o punto de referencia vial")
    abscisa_km: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3, description="Kilómetro de la vía (abscisa)")
    sentido: Optional[str] = Field(None, description="Sentido de la calzada")

    nombre_paciente: Optional[str] = Field(None, max_length=500, description="Nombre del paciente asistido")
    rango_edad: Optional[str] = Field(None, max_length=100, description="Rango de edad del paciente (ej: '18-35 años', 'Adulto mayor')")
    motivo_atencion: Optional[str] = Field(None, max_length=2000, description="Motivo médico o circunstancia de la atención")
    tipo_incidente: Optional[str] = Field(None, max_length=500, description="Clasificación del incidente vial")
    tipo_accidente: Optional[str] = Field(None, max_length=500, description="Tipo de accidente (colisión, volcamiento, etc.)")
    severidad: Optional[str] = Field(None, description="Severidad del estado del paciente o evento")
    destino_paciente: Optional[str] = Field(None, max_length=500, description="Hospital o casa de salud de destino")
    usuarios_atendidos: Optional[int] = Field(default=1, ge=0, description="Número de personas asistidas")
    servicio_comunidad: Optional[bool] = Field(default=False, description="Indica si fue un servicio fuera de la franja o apoyo comunitario")

    odometro_salida_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2, description="Lectura del odómetro al salir de la base")
    odometro_llegada_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2, description="Lectura del odómetro al retornar a la base")
    reportado_mtop: Optional[bool] = Field(default=False, description="Bandera de sincronización o reporte ministerial")


class AmbulanciaCreate(BaseModel):
    codigo_formulario: str = Field(..., min_length=1, max_length=100, description="Código único de la hoja de atención médica")
    id_supervisor: int = Field(..., gt=0, description="ID del supervisor a cargo")
    id_paramedico: int = Field(..., gt=0, description="ID del paramédico actuante")
    id_chofer: int = Field(..., gt=0, description="ID del chofer de la ambulancia")
    id_vehiculo: int = Field(..., gt=0, description="ID del vehículo ambulancia")
    turno: TurnoEnum = Field(..., description="Turno operativo (1, 2 o 3)")

    ts_llamada: datetime = Field(..., description="Fecha y hora de recepción de la llamada")
    ts_arribo: datetime = Field(..., description="Fecha y hora de arribo al lugar")
    ts_termino: datetime = Field(..., description="Fecha y hora de término de atención")
    ts_retorno: datetime = Field(..., description="Fecha y hora de retorno a base")

    sector_referencia: str = Field(..., min_length=1, max_length=500, description="Sector o punto de referencia")
    abscisa_km: Decimal = Field(..., ge=0, max_digits=7, decimal_places=3, description="Kilómetro de la vía")
    sentido: SentidoEnum = Field(..., description="Sentido de la calzada")

    nombre_paciente: Optional[str] = Field(None, max_length=500)
    rango_edad: Optional[str] = Field(None, max_length=100)
    motivo_atencion: str = Field(..., min_length=1, max_length=2000)
    tipo_incidente: Optional[str] = Field(None, max_length=500)
    tipo_accidente: Optional[str] = Field(None, max_length=500)
    severidad: SeveridadEnum = Field(..., description="Severidad (LEVE, GRAVE, FATAL)")
    destino_paciente: Optional[str] = Field(None, max_length=500)
    usuarios_atendidos: int = Field(default=1, ge=1)
    servicio_comunidad: bool = Field(default=False)

    odometro_salida_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)
    odometro_llegada_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)
    reportado_mtop: bool = Field(default=False)

    @model_validator(mode="after")
    def validar_cronologia_y_odometria(self) -> "AmbulanciaCreate":
        if self.ts_arribo < self.ts_llamada:
            raise ValueError("El timestamp de arribo (ts_arribo) no puede ser anterior a la llamada (ts_llamada).")
        if self.ts_termino < self.ts_arribo:
            raise ValueError("El timestamp de término (ts_termino) no puede ser anterior al arribo (ts_arribo).")
        if self.ts_retorno < self.ts_termino:
            raise ValueError("El timestamp de retorno (ts_retorno) no puede ser anterior al término (ts_termino).")

        if self.odometro_llegada_km < self.odometro_salida_km:
            raise ValueError(
                f"El odómetro de llegada ({self.odometro_llegada_km} km) no puede ser menor que el de salida ({self.odometro_salida_km} km)."
            )
        return self


class AmbulanciaRead(AmbulanciaBase):
    id_asistencia: int = Field(..., description="Identificador único del registro de asistencia")
    km_recorridos: Optional[Decimal] = Field(None, description="Kilómetros calculados recorridos")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESQUEMAS PARA GRÚAS
# ==========================================

class GruaBase(BaseModel):
    codigo_formulario: str = Field(..., min_length=1, max_length=100, description="Código único de la orden de grúa")
    id_supervisor: Optional[int] = Field(None, gt=0, description="ID del supervisor a cargo")
    id_chofer: Optional[int] = Field(None, gt=0, description="ID del operador de grúa")
    id_vehiculo: Optional[int] = Field(None, gt=0, description="ID de la unidad de grúa de la concesión")
    turno: Optional[int] = Field(None, description="Turno operativo (1, 2 o 3)")
    tipo_grua: Optional[str] = Field(None, description="Tipo de grúa utilizada")

    ts_llamada: Optional[datetime] = Field(None, description="Fecha y hora de la llamada de solicitud")
    ts_arribo: Optional[datetime] = Field(None, description="Fecha y hora de llegada al punto")
    ts_termino: Optional[datetime] = Field(None, description="Fecha y hora de término de maniobra")
    ts_retorno: Optional[datetime] = Field(None, description="Fecha y hora de retorno a base")

    sector_referencia: Optional[str] = Field(None, max_length=500, description="Sector o referencia")
    abscisa_km: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3, description="Kilómetro del evento")
    sentido: Optional[str] = Field(None, description="Sentido vial")

    usuario_reporta: Optional[str] = Field(None, max_length=500)
    placa_asistida: Optional[str] = Field(None, max_length=50)
    tipo_vehiculo_asistido: Optional[str] = Field(None, max_length=150)
    usuarios_atendidos: Optional[int] = Field(default=1, ge=0)

    motivo_atencion: Optional[str] = Field(None, max_length=2000)
    tipo_accidente: Optional[str] = Field(None, max_length=500)
    posible_causa: Optional[str] = Field(None, max_length=1000)
    severidad: Optional[str] = Field(None)

    km_origen_traslado: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3)
    km_destino_traslado: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3)

    odometro_salida_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2)
    odometro_llegada_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2)
    reportado_mtop: Optional[bool] = Field(default=False)
    observaciones: Optional[str] = Field(None, max_length=5000)


class GruaCreate(BaseModel):
    codigo_formulario: str = Field(..., min_length=1, max_length=100, description="Código único de la orden de grúa")
    id_supervisor: int = Field(..., gt=0, description="ID del supervisor a cargo")
    id_chofer: int = Field(..., gt=0, description="ID del operador de grúa")
    id_vehiculo: Optional[int] = Field(None, gt=0, description="ID de la unidad de grúa (opcional si es externa)")
    turno: TurnoEnum = Field(..., description="Turno operativo (1, 2 o 3)")
    tipo_grua: TipoGruaEnum = Field(..., description="Tipo de grúa utilizada")

    ts_llamada: datetime = Field(..., description="Fecha y hora de la llamada de solicitud")
    ts_arribo: datetime = Field(..., description="Fecha y hora de llegada al punto")
    ts_termino: datetime = Field(..., description="Fecha y hora de término de maniobra")
    ts_retorno: datetime = Field(..., description="Fecha y hora de retorno a base")

    sector_referencia: str = Field(..., min_length=1, max_length=500, description="Sector o referencia")
    abscisa_km: Decimal = Field(..., ge=0, max_digits=7, decimal_places=3, description="Kilómetro del evento")
    sentido: SentidoEnum = Field(..., description="Sentido vial")

    usuario_reporta: Optional[str] = Field(None, max_length=500)
    placa_asistida: Optional[str] = Field(None, max_length=50)
    tipo_vehiculo_asistido: Optional[str] = Field(None, max_length=150)
    usuarios_atendidos: int = Field(default=1, ge=1)

    motivo_atencion: str = Field(..., min_length=1, max_length=2000)
    tipo_accidente: Optional[str] = Field(None, max_length=500)
    posible_causa: Optional[str] = Field(None, max_length=1000)
    severidad: Optional[SeveridadEnum] = Field(None)

    km_origen_traslado: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3)
    km_destino_traslado: Optional[Decimal] = Field(None, ge=0, max_digits=7, decimal_places=3)

    odometro_salida_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)
    odometro_llegada_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)
    reportado_mtop: bool = Field(default=False)
    observaciones: Optional[str] = Field(None, max_length=5000)

    @model_validator(mode="after")
    def validar_cronologia_y_odometria(self) -> "GruaCreate":
        if self.ts_arribo < self.ts_llamada:
            raise ValueError("El timestamp de arribo (ts_arribo) no puede ser anterior a la llamada (ts_llamada).")
        if self.ts_termino < self.ts_arribo:
            raise ValueError("El timestamp de término (ts_termino) no puede ser anterior al arribo (ts_arribo).")
        if self.ts_retorno < self.ts_termino:
            raise ValueError("El timestamp de retorno (ts_retorno) no puede ser anterior al término (ts_termino).")

        if self.odometro_llegada_km < self.odometro_salida_km:
            raise ValueError(
                f"El odómetro de llegada ({self.odometro_llegada_km} km) no puede ser menor que el de salida ({self.odometro_salida_km} km)."
            )
        return self


class GruaRead(GruaBase):
    id_asistencia_grua: int = Field(..., description="Identificador único de la asistencia de grúa")
    km_recorridos: Optional[Decimal] = Field(None, description="Kilómetros calculados recorridos")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESQUEMAS PARA PATRULLAJE
# ==========================================

class PatrullajeBase(BaseModel):
    codigo_patrullaje: str = Field(..., min_length=1, max_length=100, description="Código de la bitácora de patrullaje")
    id_supervisor: Optional[int] = Field(None, gt=0, description="ID del supervisor de turno")
    id_chofer: Optional[int] = Field(None, gt=0, description="ID del patrullero conductor")
    id_vehiculo: Optional[int] = Field(None, gt=0, description="ID de la patrulla asignada")

    fecha_recorrido: Optional[date] = Field(None, description="Fecha de ejecución del patrullaje")
    hora_salida: Optional[time] = Field(None, description="Hora de salida al recorrido")
    hora_retorno: Optional[time] = Field(None, description="Hora de regreso del recorrido")

    ruta_descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción del tramo o ruta inspeccionada")
    odometro_inicial_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2)
    odometro_final_km: Optional[Decimal] = Field(None, ge=0, max_digits=9, decimal_places=2)

    novedad_en_via: Optional[bool] = Field(default=False)
    observaciones: Optional[str] = Field(None, max_length=5000)


class PatrullajeCreate(BaseModel):
    codigo_patrullaje: str = Field(..., min_length=1, max_length=100, description="Código de la bitácora")
    id_supervisor: int = Field(..., gt=0, description="ID del supervisor de turno")
    id_chofer: int = Field(..., gt=0, description="ID del patrullero conductor")
    id_vehiculo: int = Field(..., gt=0, description="ID de la patrulla asignada")

    fecha_recorrido: date = Field(..., description="Fecha del patrullaje")
    hora_salida: time = Field(..., description="Hora de salida")
    hora_retorno: time = Field(..., description="Hora de regreso")

    ruta_descripcion: str = Field(..., min_length=1, max_length=1000)
    odometro_inicial_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)
    odometro_final_km: Decimal = Field(..., ge=0, max_digits=9, decimal_places=2)

    novedad_en_via: bool = Field(default=False)
    observaciones: Optional[str] = Field(None, max_length=5000)

    @model_validator(mode="after")
    def validar_horarios_y_odometria(self) -> "PatrullajeCreate":
        if self.odometro_final_km < self.odometro_inicial_km:
            raise ValueError(
                f"El odómetro final ({self.odometro_final_km} km) no puede ser menor que el inicial ({self.odometro_inicial_km} km)."
            )
        return self


class PatrullajeRead(PatrullajeBase):
    id_patrullaje: int = Field(..., description="Identificador único del registro de patrullaje")
    km_recorridos: Optional[Decimal] = Field(None, description="Kilómetros calculados recorridos")

    model_config = ConfigDict(from_attributes=True)
