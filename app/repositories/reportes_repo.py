"""
Repositorio para extracción de datos de las vistas ministeriales MTOP:
- dbo.vw_mtop_ambulancias
- dbo.vw_mtop_gruas
- dbo.vw_mtop_patrullaje
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.schemas.reportes import ServicioReporteEnum


class ReportesRepository:
    VIEW_MAPPING = {
        ServicioReporteEnum.AMBULANCIA: "dbo.vw_mtop_ambulancias",
        ServicioReporteEnum.GRUA: "dbo.vw_mtop_gruas",
        ServicioReporteEnum.PATRULLAJE: "dbo.vw_mtop_patrullaje",
    }

    def _get_view_date_column(self, db: Session, view_name: str) -> Optional[str]:
        """
        Detecta dinámicamente la columna de tipo DATE o DATETIME de la vista para filtrar por mes/año.
        """
        pure_name = view_name.replace("dbo.", "")
        sql = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
        """
        rows = db.execute(text(sql), {"table_name": pure_name}).fetchall()
        candidate_cols = []
        for row in rows:
            col_name = row[0]
            data_type = row[1].lower()
            if any(dt in data_type for dt in ["date", "time"]):
                candidate_cols.append(col_name)

        # Priorizar nombres conocidos
        for pref in ["fecha", "ts_llamada", "fecha_recorrido", "fecha_atencion", "ts_registro"]:
            for col in candidate_cols:
                if pref in col.lower():
                    return col

        return candidate_cols[0] if candidate_cols else None

    def get_datos_mtop_df(
        self,
        db: Session,
        servicio: ServicioReporteEnum,
        mes: int,
        anio: int
    ) -> pd.DataFrame:
        """
        Consulta la vista correspondiente del MTOP y retorna un DataFrame de pandas.
        """
        view_name = self.VIEW_MAPPING.get(servicio)
        if not view_name:
            raise ValueError(f"Servicio no soportado: {servicio}")

        date_col = self._get_view_date_column(db, view_name)

        if date_col:
            sql = f"""
                SELECT *
                FROM {view_name}
                WHERE MONTH({date_col}) = :mes AND YEAR({date_col}) = :anio
            """
            params = {"mes": mes, "anio": anio}
        else:
            # Fallback en caso de que no se detecte columna fecha
            sql = f"SELECT * FROM {view_name}"
            params = {}

        result = db.execute(text(sql), params)
        columns = list(result.keys())
        data = [list(row) for row in result.fetchall()]

        df = pd.DataFrame(data, columns=columns)
        return df


reportes_repo = ReportesRepository()
