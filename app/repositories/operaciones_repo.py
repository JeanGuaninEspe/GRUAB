"""
Repositorio para operaciones transaccionales de asistencias de ambulancias, grúas y patrullaje.
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.models.transaccionales import AsistenciaAmbulancia, AsistenciaGrua, BitacoraPatrullaje
from app.schemas.operaciones import AmbulanciaCreate, GruaCreate, PatrullajeCreate
from app.repositories.base import BaseRepository


class OperacionesRepository:
    # ----------------------------------------------------
    # AMBULANCIAS
    # ----------------------------------------------------
    def get_ambulancia_by_codigo(self, db: Session, codigo_formulario: str) -> Optional[AsistenciaAmbulancia]:
        return db.query(AsistenciaAmbulancia).filter(
            AsistenciaAmbulancia.codigo_formulario == codigo_formulario
        ).first()

    def get_ambulancias(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[AsistenciaAmbulancia]:
        query = db.query(AsistenciaAmbulancia)
        if fecha_inicio:
            query = query.filter(AsistenciaAmbulancia.ts_llamada >= fecha_inicio)
        if fecha_fin:
            query = query.filter(AsistenciaAmbulancia.ts_llamada <= fecha_fin)
        if turno:
            query = query.filter(AsistenciaAmbulancia.turno == turno)
        if id_vehiculo:
            query = query.filter(AsistenciaAmbulancia.id_vehiculo == id_vehiculo)
        return query.order_by(AsistenciaAmbulancia.ts_llamada.desc()).offset(skip).limit(limit).all()

    def create_ambulancia(self, db: Session, data: AmbulanciaCreate) -> AsistenciaAmbulancia:
        db_obj = AsistenciaAmbulancia(
            codigo_formulario=data.codigo_formulario,
            id_supervisor=data.id_supervisor,
            id_paramedico=data.id_paramedico,
            id_chofer=data.id_chofer,
            id_vehiculo=data.id_vehiculo,
            turno=int(data.turno),
            ts_llamada=data.ts_llamada,
            ts_arribo=data.ts_arribo,
            ts_termino=data.ts_termino,
            ts_retorno=data.ts_retorno,
            sector_referencia=data.sector_referencia,
            abscisa_km=data.abscisa_km,
            sentido=data.sentido.value,
            nombre_paciente=data.nombre_paciente,
            rango_edad=data.rango_edad,
            motivo_atencion=data.motivo_atencion,
            tipo_incidente=data.tipo_incidente,
            tipo_accidente=data.tipo_accidente,
            severidad=data.severidad.value,
            destino_paciente=data.destino_paciente,
            usuarios_atendidos=data.usuarios_atendidos,
            servicio_comunidad=data.servicio_comunidad,
            odometro_salida_km=data.odometro_salida_km,
            odometro_llegada_km=data.odometro_llegada_km,
            reportado_mtop=data.reportado_mtop,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ----------------------------------------------------
    # GRÚAS
    # ----------------------------------------------------
    def get_grua_by_codigo(self, db: Session, codigo_formulario: str) -> Optional[AsistenciaGrua]:
        return db.query(AsistenciaGrua).filter(
            AsistenciaGrua.codigo_formulario == codigo_formulario
        ).first()

    def get_gruas(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[AsistenciaGrua]:
        query = db.query(AsistenciaGrua)
        if fecha_inicio:
            query = query.filter(AsistenciaGrua.ts_llamada >= fecha_inicio)
        if fecha_fin:
            query = query.filter(AsistenciaGrua.ts_llamada <= fecha_fin)
        if turno:
            query = query.filter(AsistenciaGrua.turno == turno)
        if id_vehiculo:
            query = query.filter(AsistenciaGrua.id_vehiculo == id_vehiculo)
        return query.order_by(AsistenciaGrua.ts_llamada.desc()).offset(skip).limit(limit).all()

    def create_grua(self, db: Session, data: GruaCreate) -> AsistenciaGrua:
        db_obj = AsistenciaGrua(
            codigo_formulario=data.codigo_formulario,
            id_supervisor=data.id_supervisor,
            id_chofer=data.id_chofer,
            id_vehiculo=data.id_vehiculo,
            turno=int(data.turno),
            tipo_grua=data.tipo_grua.value,
            ts_llamada=data.ts_llamada,
            ts_arribo=data.ts_arribo,
            ts_termino=data.ts_termino,
            ts_retorno=data.ts_retorno,
            sector_referencia=data.sector_referencia,
            abscisa_km=data.abscisa_km,
            sentido=data.sentido.value,
            usuario_reporta=data.usuario_reporta,
            placa_asistida=data.placa_asistida,
            tipo_vehiculo_asistido=data.tipo_vehiculo_asistido,
            usuarios_atendidos=data.usuarios_atendidos,
            motivo_atencion=data.motivo_atencion,
            tipo_accidente=data.tipo_accidente,
            posible_causa=data.posible_causa,
            severidad=data.severidad.value if data.severidad else None,
            km_origen_traslado=data.km_origen_traslado,
            km_destino_traslado=data.km_destino_traslado,
            odometro_salida_km=data.odometro_salida_km,
            odometro_llegada_km=data.odometro_llegada_km,
            reportado_mtop=data.reportado_mtop,
            observaciones=data.observaciones,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ----------------------------------------------------
    # PATRULLAJE
    # ----------------------------------------------------
    def get_patrullaje_by_codigo(self, db: Session, codigo_patrullaje: str) -> Optional[BitacoraPatrullaje]:
        return db.query(BitacoraPatrullaje).filter(
            BitacoraPatrullaje.codigo_patrullaje == codigo_patrullaje
        ).first()

    def get_patrullajes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[BitacoraPatrullaje]:
        query = db.query(BitacoraPatrullaje)
        if fecha_inicio:
            query = query.filter(BitacoraPatrullaje.fecha_recorrido >= fecha_inicio)
        if fecha_fin:
            query = query.filter(BitacoraPatrullaje.fecha_recorrido <= fecha_fin)
        if id_vehiculo:
            query = query.filter(BitacoraPatrullaje.id_vehiculo == id_vehiculo)
        return query.order_by(BitacoraPatrullaje.fecha_recorrido.desc()).offset(skip).limit(limit).all()

    def create_patrullaje(self, db: Session, data: PatrullajeCreate) -> BitacoraPatrullaje:
        db_obj = BitacoraPatrullaje(
            codigo_patrullaje=data.codigo_patrullaje,
            id_supervisor=data.id_supervisor,
            id_chofer=data.id_chofer,
            id_vehiculo=data.id_vehiculo,
            fecha_recorrido=data.fecha_recorrido,
            hora_salida=data.hora_salida,
            hora_retorno=data.hora_retorno,
            ruta_descripcion=data.ruta_descripcion,
            odometro_inicial_km=data.odometro_inicial_km,
            odometro_final_km=data.odometro_final_km,
            novedad_en_via=data.novedad_en_via,
            observaciones=data.observaciones,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


operaciones_repo = OperacionesRepository()
