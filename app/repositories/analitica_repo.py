"""
Repositorio para consultas analíticas sobre las vistas y tablas de SQL Server:
- dbo.vw_kpi_tiempos_atencion
- dbo.vw_analitica_puntos_negros
- Tablas transaccionales para modelado de scoring y clustering espacial/temporal.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session


class AnaliticaRepository:
    def get_kpi_tiempos_atencion(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Consulta la vista dbo.vw_kpi_tiempos_atencion con filtros parametrizados.
        """
        clauses = ["1 = 1"]
        params: Dict[str, Any] = {"limit": limit}

        if fecha_inicio:
            clauses.append("fecha >= :fecha_inicio")
            params["fecha_inicio"] = fecha_inicio

        if fecha_fin:
            clauses.append("fecha <= :fecha_fin")
            params["fecha_fin"] = fecha_fin

        if servicio:
            clauses.append("UPPER(tipo_servicio) = :servicio")
            params["servicio"] = servicio.upper()

        if turno:
            clauses.append("turno = :turno")
            params["turno"] = turno

        sql = f"""
            SELECT TOP (:limit)
                tipo_servicio,
                codigo_formulario,
                fecha,
                turno,
                abscisa_km,
                sentido,
                tiempo_despacho_arribo_min,
                tiempo_en_sitio_min,
                ciclo_total_min,
                km_recorridos
            FROM dbo.vw_kpi_tiempos_atencion
            WHERE {" AND ".join(clauses)}
            ORDER BY fecha DESC, codigo_formulario DESC
        """

        result = db.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result.fetchall()]
        return rows

    def get_puntos_negros(
        self,
        db: Session,
        severidad: Optional[str] = None,
        causa: Optional[str] = None,
        sentido: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Consulta la vista dbo.vw_analitica_puntos_negros para mapeo de tramos críticos.
        """
        clauses = ["1 = 1"]
        params: Dict[str, Any] = {"limit": limit}

        if severidad:
            clauses.append("UPPER(severidad) = :severidad")
            params["severidad"] = severidad.upper()

        if causa:
            clauses.append("UPPER(posible_causa) LIKE :causa")
            params["causa"] = f"%{causa.upper()}%"

        if sentido:
            clauses.append("UPPER(sentido) = :sentido")
            params["sentido"] = sentido.upper()

        sql = f"""
            SELECT TOP (:limit)
                km_tramo,
                sentido,
                tipo_accidente,
                posible_causa,
                severidad,
                total_eventos
            FROM dbo.vw_analitica_puntos_negros
            WHERE {" AND ".join(clauses)}
            ORDER BY total_eventos DESC, km_tramo ASC
        """

        result = db.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result.fetchall()]
        return rows

    def get_eventos_combinados(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extrae y unifica todos los eventos transaccionales de ambulancias y grúas con georreferenciación (KM)
        y fecha/hora para análisis espacial y modelos de scoring de riesgo.
        """
        clauses_amb = ["abscisa_km IS NOT NULL"]
        clauses_gru = ["abscisa_km IS NOT NULL"]
        params: Dict[str, Any] = {}

        if fecha_inicio:
            clauses_amb.append("ts_llamada >= :fecha_inicio")
            clauses_gru.append("ts_llamada >= :fecha_inicio")
            params["fecha_inicio"] = fecha_inicio

        if fecha_fin:
            clauses_amb.append("ts_llamada <= :fecha_fin")
            clauses_gru.append("ts_llamada <= :fecha_fin")
            params["fecha_fin"] = fecha_fin

        if turno:
            clauses_amb.append("turno = :turno")
            clauses_gru.append("turno = :turno")
            params["turno"] = turno

        if id_vehiculo:
            clauses_amb.append("id_vehiculo = :id_vehiculo")
            clauses_gru.append("id_vehiculo = :id_vehiculo")
            params["id_vehiculo"] = id_vehiculo

        parts = []
        if not servicio or servicio.upper() in ["AMBULANCIA", "AMBULANCIAS"]:
            parts.append(f"""
                SELECT 
                    'AMBULANCIA' AS tipo_servicio,
                    codigo_formulario,
                    ts_llamada,
                    abscisa_km,
                    sentido,
                    motivo_atencion,
                    tipo_accidente,
                    NULL AS posible_causa,
                    severidad,
                    NULL AS tipo_vehiculo_asistido,
                    km_recorridos,
                    turno,
                    id_vehiculo
                FROM dbo.asistencias_ambulancia
                WHERE {" AND ".join(clauses_amb)}
            """)

        if not servicio or servicio.upper() in ["GRUA", "GRUAS"]:
            parts.append(f"""
                SELECT 
                    'GRUA' AS tipo_servicio,
                    codigo_formulario,
                    ts_llamada,
                    abscisa_km,
                    sentido,
                    motivo_atencion,
                    tipo_accidente,
                    posible_causa,
                    severidad,
                    tipo_vehiculo_asistido,
                    km_recorridos,
                    turno,
                    id_vehiculo
                FROM dbo.asistencias_grua
                WHERE {" AND ".join(clauses_gru)}
            """)

        if not parts:
            return []

        sql = " UNION ALL ".join(parts) + " ORDER BY ts_llamada DESC"
        result = db.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result.fetchall()]
        return rows

    def get_conteo_patrullajes(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_vehiculo: Optional[int] = None,
    ) -> int:
        """
        Retorna la cantidad total de recorridos de patrullaje registrados con filtros.
        """
        try:
            clauses = ["1 = 1"]
            params: Dict[str, Any] = {}
            if fecha_inicio:
                clauses.append("fecha_recorrido >= :fecha_inicio")
                params["fecha_inicio"] = fecha_inicio
            if fecha_fin:
                clauses.append("fecha_recorrido <= :fecha_fin")
                params["fecha_fin"] = fecha_fin
            if id_vehiculo:
                clauses.append("id_vehiculo = :id_vehiculo")
                params["id_vehiculo"] = id_vehiculo

            sql = f"SELECT COUNT(*) FROM dbo.bitacora_patrullaje WHERE {' AND '.join(clauses)}"
            result = db.execute(text(sql), params).scalar()
            return int(result or 0)
        except Exception:
            return 0


analitica_repo = AnaliticaRepository()
