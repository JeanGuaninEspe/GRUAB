"""
Modelos SQLAlchemy para las Tablas Transaccionales de Operaciones Viales:
- Asistencias de Ambulancia (dbo.asistencias_ambulancia)
- Asistencias de Grúa (dbo.asistencias_grua)
- Bitácoras de Patrullaje (dbo.bitacora_patrullaje)
"""
from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Boolean,
    Numeric,
    DateTime,
    Date,
    Time,
    ForeignKey,
    FetchedValue,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class AsistenciaAmbulancia(Base):
    __tablename__ = "asistencias_ambulancia"
    __table_args__ = {"schema": "dbo"}

    id_asistencia = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo_formulario = Column(String(100), unique=True, nullable=False, index=True)

    # Llaves foráneas a personal y vehículo (permiten NULL en registros históricos si aplica)
    id_supervisor = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_paramedico = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_chofer = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_vehiculo = Column(Integer, ForeignKey("dbo.cat_vehiculos_concesion.id_vehiculo"), nullable=True)

    turno = Column(SmallInteger, nullable=True)  # 1, 2, 3
    ts_llamada = Column(DateTime, nullable=True)
    ts_arribo = Column(DateTime, nullable=True)
    ts_termino = Column(DateTime, nullable=True)
    ts_retorno = Column(DateTime, nullable=True)

    sector_referencia = Column(String(500), nullable=True)
    abscisa_km = Column(Numeric(7, 3), nullable=True)
    sentido = Column(String(50), nullable=True)  # ASCENDENTE, DESCENDENTE, BIDIRECCIONAL

    nombre_paciente = Column(String(500), nullable=True)
    rango_edad = Column(String(100), nullable=True)
    motivo_atencion = Column(String(2000), nullable=True)
    tipo_incidente = Column(String(500), nullable=True)
    tipo_accidente = Column(String(500), nullable=True)
    severidad = Column(String(50), nullable=True)  # LEVE, GRAVE, FATAL
    destino_paciente = Column(String(500), nullable=True)
    usuarios_atendidos = Column(Integer, default=1, nullable=True)
    servicio_comunidad = Column(Boolean, default=False, nullable=True)

    odometro_salida_km = Column(Numeric(9, 2), nullable=True)
    odometro_llegada_km = Column(Numeric(9, 2), nullable=True)
    # Columna calculada y persistida en SQL Server (odometro_llegada_km - odometro_salida_km)
    km_recorridos = Column(Numeric(9, 2), server_default=FetchedValue())

    reportado_mtop = Column(Boolean, default=False, nullable=True)

    # Relaciones ORM
    supervisor = relationship("CatPersonal", foreign_keys=[id_supervisor], back_populates="ambulancias_supervisadas")
    paramedico = relationship("CatPersonal", foreign_keys=[id_paramedico], back_populates="ambulancias_paramedico")
    chofer = relationship("CatPersonal", foreign_keys=[id_chofer], back_populates="ambulancias_chofer")
    vehiculo = relationship("CatVehiculoConcesion", back_populates="asistencias_ambulancia")


class AsistenciaGrua(Base):
    __tablename__ = "asistencias_grua"
    __table_args__ = {"schema": "dbo"}

    id_asistencia_grua = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo_formulario = Column(String(100), unique=True, nullable=False, index=True)

    id_supervisor = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_chofer = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_vehiculo = Column(Integer, ForeignKey("dbo.cat_vehiculos_concesion.id_vehiculo"), nullable=True)

    turno = Column(SmallInteger, nullable=True)  # 1, 2, 3
    tipo_grua = Column(String(50), nullable=True)  # PEQUEÑA, GRANDE, PLATAFORMA

    ts_llamada = Column(DateTime, nullable=True)
    ts_arribo = Column(DateTime, nullable=True)
    ts_termino = Column(DateTime, nullable=True)
    ts_retorno = Column(DateTime, nullable=True)

    sector_referencia = Column(String(500), nullable=True)
    abscisa_km = Column(Numeric(7, 3), nullable=True)
    sentido = Column(String(50), nullable=True)  # ASCENDENTE, DESCENDENTE, BIDIRECCIONAL

    usuario_reporta = Column(String(500), nullable=True)
    placa_asistida = Column(String(50), nullable=True)
    tipo_vehiculo_asistido = Column(String(150), nullable=True)
    usuarios_atendidos = Column(Integer, default=1, nullable=True)

    motivo_atencion = Column(String(2000), nullable=True)
    tipo_accidente = Column(String(500), nullable=True)
    posible_causa = Column(String(1000), nullable=True)
    severidad = Column(String(50), nullable=True)  # LEVE, GRAVE, FATAL

    km_origen_traslado = Column(Numeric(7, 3), nullable=True)
    km_destino_traslado = Column(Numeric(7, 3), nullable=True)

    odometro_salida_km = Column(Numeric(9, 2), nullable=True)
    odometro_llegada_km = Column(Numeric(9, 2), nullable=True)
    # Columna calculada y persistida en SQL Server (odometro_llegada_km - odometro_salida_km)
    km_recorridos = Column(Numeric(9, 2), server_default=FetchedValue())

    reportado_mtop = Column(Boolean, default=False, nullable=True)
    observaciones = Column(String(5000), nullable=True)

    # Relaciones ORM
    supervisor = relationship("CatPersonal", foreign_keys=[id_supervisor], back_populates="gruas_supervisadas")
    chofer = relationship("CatPersonal", foreign_keys=[id_chofer], back_populates="gruas_chofer")
    vehiculo = relationship("CatVehiculoConcesion", back_populates="asistencias_grua")


class BitacoraPatrullaje(Base):
    __tablename__ = "bitacora_patrullaje"
    __table_args__ = {"schema": "dbo"}

    id_patrullaje = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo_patrullaje = Column(String(100), unique=True, nullable=False, index=True)

    id_supervisor = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_chofer = Column(Integer, ForeignKey("dbo.cat_personal.id_personal"), nullable=True)
    id_vehiculo = Column(Integer, ForeignKey("dbo.cat_vehiculos_concesion.id_vehiculo"), nullable=True)

    fecha_recorrido = Column(Date, nullable=True)
    hora_salida = Column(Time, nullable=True)
    hora_retorno = Column(Time, nullable=True)

    ruta_descripcion = Column(String(1000), nullable=True)
    odometro_inicial_km = Column(Numeric(9, 2), nullable=True)
    odometro_final_km = Column(Numeric(9, 2), nullable=True)
    # Columna calculada y persistida en SQL Server (odometro_final_km - odometro_inicial_km)
    km_recorridos = Column(Numeric(9, 2), server_default=FetchedValue())

    novedad_en_via = Column(Boolean, default=False, nullable=True)
    observaciones = Column(String(5000), nullable=True)

    # Relaciones ORM
    supervisor = relationship("CatPersonal", foreign_keys=[id_supervisor], back_populates="patrullajes_supervisados")
    chofer = relationship("CatPersonal", foreign_keys=[id_chofer], back_populates="patrullajes_chofer")
    vehiculo = relationship("CatVehiculoConcesion", back_populates="bitacoras_patrullaje")
