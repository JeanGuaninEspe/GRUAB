"""
Repositorio para operaciones transaccionales de asistencias de ambulancias, grúas y patrullaje.
"""
from typing import Optional, List, Dict, Any
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from app.models.transaccionales import AsistenciaAmbulancia, AsistenciaGrua, BitacoraPatrullaje
from app.models.catalogos import CatVehiculoConcesion
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

    # ----------------------------------------------------
    # BÚSQUEDAS DETERMINISTAS PARA AGENTE IA (SOLO SELECT)
    # ----------------------------------------------------
    def buscar_asistencias(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        tipo_servicio: Optional[str] = None,
        zona: Optional[str] = None,
        estado: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retorna registros detallados de asistencias exclusivamente con SELECT
        filtrados por fecha, tipo de servicio, zona geográfica y severidad/estado.
        """
        svc = (tipo_servicio or "todos").lower().strip()
        resultados: List[Dict[str, Any]] = []

        dt_inicio = datetime.combine(fecha_inicio, time.min) if fecha_inicio else None
        dt_fin = datetime.combine(fecha_fin, time.max) if fecha_fin else None

        if svc in ("ambulancia", "ambulancias", "todos"):
            q_amb = db.query(AsistenciaAmbulancia)
            if dt_inicio:
                q_amb = q_amb.filter(AsistenciaAmbulancia.ts_llamada >= dt_inicio)
            if dt_fin:
                q_amb = q_amb.filter(AsistenciaAmbulancia.ts_llamada <= dt_fin)
            if zona:
                q_amb = q_amb.filter(
                    (AsistenciaAmbulancia.sector_referencia.ilike(f"%{zona}%")) |
                    (AsistenciaAmbulancia.sentido.ilike(f"%{zona}%"))
                )
            if estado:
                q_amb = q_amb.filter(
                    (AsistenciaAmbulancia.severidad.ilike(f"%{estado}%")) |
                    (AsistenciaAmbulancia.tipo_incidente.ilike(f"%{estado}%"))
                )
            for amb in q_amb.order_by(AsistenciaAmbulancia.ts_llamada.desc()).limit(limit).all():
                resultados.append({
                    "tipo_servicio": "AMBULANCIA",
                    "codigo_formulario": amb.codigo_formulario,
                    "fecha_hora": amb.ts_llamada.isoformat() if amb.ts_llamada else None,
                    "sector": amb.sector_referencia,
                    "abscisa_km": float(amb.abscisa_km) if amb.abscisa_km is not None else None,
                    "sentido": amb.sentido,
                    "motivo_atencion": amb.motivo_atencion,
                    "tipo_incidente": amb.tipo_incidente,
                    "severidad": amb.severidad,
                    "paciente": amb.nombre_paciente,
                })

        if svc in ("grua", "gruas", "todos"):
            q_gru = db.query(AsistenciaGrua)
            if dt_inicio:
                q_gru = q_gru.filter(AsistenciaGrua.ts_llamada >= dt_inicio)
            if dt_fin:
                q_gru = q_gru.filter(AsistenciaGrua.ts_llamada <= dt_fin)
            if zona:
                q_gru = q_gru.filter(
                    (AsistenciaGrua.sector_referencia.ilike(f"%{zona}%")) |
                    (AsistenciaGrua.sentido.ilike(f"%{zona}%"))
                )
            if estado:
                q_gru = q_gru.filter(
                    (AsistenciaGrua.severidad.ilike(f"%{estado}%")) |
                    (AsistenciaGrua.tipo_grua.ilike(f"%{estado}%")) |
                    (AsistenciaGrua.motivo_atencion.ilike(f"%{estado}%"))
                )
            for gru in q_gru.order_by(AsistenciaGrua.ts_llamada.desc()).limit(limit).all():
                resultados.append({
                    "tipo_servicio": "GRUA",
                    "codigo_formulario": gru.codigo_formulario,
                    "fecha_hora": gru.ts_llamada.isoformat() if gru.ts_llamada else None,
                    "sector": gru.sector_referencia,
                    "abscisa_km": float(gru.abscisa_km) if gru.abscisa_km is not None else None,
                    "sentido": gru.sentido,
                    "tipo_grua": gru.tipo_grua,
                    "placa_asistida": gru.placa_asistida,
                    "tipo_vehiculo": gru.tipo_vehiculo_asistido,
                    "motivo_atencion": gru.motivo_atencion,
                    "severidad": gru.severidad,
                })

        resultados.sort(key=lambda r: r.get("fecha_hora") or "", reverse=True)
        return resultados[:limit]

    def buscar_unidad(
        self,
        db: Session,
        id_o_placa: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Busca información de una unidad o vehículo (SELECT) por código interno,
        placa o id en la flota de concesión (dbo.cat_vehiculos_concesion) y registros
        de asistencias relacionadas.
        """
        if not id_o_placa:
            return []

        criterio = id_o_placa.strip()
        criterio_limpio = criterio.replace("-", "").replace(" ", "").upper()
        resultados: List[Dict[str, Any]] = []

        # 1. Búsqueda en catálogo de vehículos de la concesión
        q_veh = db.query(CatVehiculoConcesion)
        if criterio.isdigit():
            v_id = q_veh.filter(CatVehiculoConcesion.id_vehiculo == int(criterio)).first()
            if v_id:
                resultados.append({
                    "tipo_registro": "FLOTA_CONCESION",
                    "id_vehiculo": v_id.id_vehiculo,
                    "codigo_interno": v_id.codigo_interno,
                    "placa": v_id.placa,
                    "tipo_flota": v_id.tipo_flota,
                    "descripcion": v_id.descripcion,
                    "activo": v_id.activo,
                })

        vehiculos = q_veh.filter(
            (CatVehiculoConcesion.codigo_interno.ilike(f"%{criterio}%")) |
            (CatVehiculoConcesion.placa.ilike(f"%{criterio}%")) |
            (CatVehiculoConcesion.placa.ilike(f"%{criterio_limpio}%"))
        ).limit(limit).all()

        for v in vehiculos:
            if not any(r.get("id_vehiculo") == v.id_vehiculo for r in resultados):
                resultados.append({
                    "tipo_registro": "FLOTA_CONCESION",
                    "id_vehiculo": v.id_vehiculo,
                    "codigo_interno": v.codigo_interno,
                    "placa": v.placa,
                    "tipo_flota": v.tipo_flota,
                    "descripcion": v.descripcion,
                    "activo": v.activo,
                })

        # 2. Búsqueda por placa asistida en grúas
        q_gru = db.query(AsistenciaGrua).filter(
            (AsistenciaGrua.placa_asistida.ilike(f"%{criterio}%")) |
            (AsistenciaGrua.placa_asistida.ilike(f"%{criterio_limpio}%")) |
            (AsistenciaGrua.codigo_formulario.ilike(f"%{criterio}%"))
        ).order_by(AsistenciaGrua.ts_llamada.desc()).limit(limit).all()

        for g in q_gru:
            resultados.append({
                "tipo_registro": "ASISTENCIA_GRUA",
                "codigo_formulario": g.codigo_formulario,
                "placa_asistida": g.placa_asistida,
                "tipo_vehiculo": g.tipo_vehiculo_asistido,
                "fecha_hora": g.ts_llamada.isoformat() if g.ts_llamada else None,
                "sector": g.sector_referencia,
                "motivo_atencion": g.motivo_atencion,
                "severidad": g.severidad,
            })

        # 3. Búsqueda por código de formulario en ambulancias
        q_amb = db.query(AsistenciaAmbulancia).filter(
            AsistenciaAmbulancia.codigo_formulario.ilike(f"%{criterio}%")
        ).order_by(AsistenciaAmbulancia.ts_llamada.desc()).limit(limit).all()

        for a in q_amb:
            resultados.append({
                "tipo_registro": "ASISTENCIA_AMBULANCIA",
                "codigo_formulario": a.codigo_formulario,
                "fecha_hora": a.ts_llamada.isoformat() if a.ts_llamada else None,
                "sector": a.sector_referencia,
                "motivo_atencion": a.motivo_atencion,
                "severidad": a.severidad,
            })

        return resultados[:limit]


operaciones_repo = OperacionesRepository()
