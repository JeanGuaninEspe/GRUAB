"""
Modelos SQLAlchemy para los Catálogos Maestros de Personal y Vehículos de la Concesión.
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class CatPersonal(Base):
    __tablename__ = "cat_personal"
    __table_args__ = {"schema": "dbo"}

    id_personal = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(String(30), nullable=False)  # SUPERVISOR, PARAMEDICO, CHOFER_AMBULANCIA, CHOFER_GRUA, PATRULLERO
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones inversas opcionales
    ambulancias_supervisadas = relationship(
        "AsistenciaAmbulancia", foreign_keys="AsistenciaAmbulancia.id_supervisor", back_populates="supervisor"
    )
    ambulancias_paramedico = relationship(
        "AsistenciaAmbulancia", foreign_keys="AsistenciaAmbulancia.id_paramedico", back_populates="paramedico"
    )
    ambulancias_chofer = relationship(
        "AsistenciaAmbulancia", foreign_keys="AsistenciaAmbulancia.id_chofer", back_populates="chofer"
    )

    gruas_supervisadas = relationship(
        "AsistenciaGrua", foreign_keys="AsistenciaGrua.id_supervisor", back_populates="supervisor"
    )
    gruas_chofer = relationship(
        "AsistenciaGrua", foreign_keys="AsistenciaGrua.id_chofer", back_populates="chofer"
    )

    patrullajes_supervisados = relationship(
        "BitacoraPatrullaje", foreign_keys="BitacoraPatrullaje.id_supervisor", back_populates="supervisor"
    )
    patrullajes_chofer = relationship(
        "BitacoraPatrullaje", foreign_keys="BitacoraPatrullaje.id_chofer", back_populates="chofer"
    )


class CatVehiculoConcesion(Base):
    __tablename__ = "cat_vehiculos_concesion"
    __table_args__ = {"schema": "dbo"}

    id_vehiculo = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo_interno = Column(String(20), nullable=False, unique=True)
    placa = Column(String(10), nullable=False)
    tipo_flota = Column(String(20), nullable=False)  # AMBULANCIA, GRUA, PATRULLA
    descripcion = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones inversas
    asistencias_ambulancia = relationship("AsistenciaAmbulancia", back_populates="vehiculo")
    asistencias_grua = relationship("AsistenciaGrua", back_populates="vehiculo")
    bitacoras_patrullaje = relationship("BitacoraPatrullaje", back_populates="vehiculo")
