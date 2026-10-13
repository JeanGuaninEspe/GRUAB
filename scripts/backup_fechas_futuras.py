import sys
import os
import json
from decimal import Decimal
from datetime import datetime, date, time
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal

def default_json(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def main():
    db = SessionLocal()
    try:
        query = """
        SELECT *
        FROM dbo.asistencias_grua
        WHERE 
            ts_llamada > GETDATE()
            OR ts_arribo > GETDATE()
            OR ts_termino > GETDATE()
            OR ts_retorno > GETDATE()
        """
        rows = db.execute(text(query)).mappings().fetchall()
        data = [dict(r) for r in rows]
        
        backup_path = os.path.join(os.path.dirname(__file__), "backup_fechas_futuras.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=default_json)
        print(f"Respaldo generado con éxito en: {backup_path}")
        print(f"Total registros respaldados: {len(data)}")
        for r in data:
            print(f"- ID {r['id_asistencia_grua']} | Código: {r['codigo_formulario']} | Placa: {r['placa_asistida']} | Fecha llamada: {r['ts_llamada']}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
