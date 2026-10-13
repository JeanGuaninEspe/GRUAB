import sys
import os
from datetime import datetime, date
from sqlalchemy import text

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal

def main():
    db = SessionLocal()
    try:
        # 1. Check current DB server datetime
        res = db.execute(text("SELECT GETDATE() AS db_now, CAST(GETDATE() AS DATE) AS db_today")).fetchone()
        db_now = res.db_now
        db_today = res.db_today
        print(f"=== REVISIÓN DE FECHAS FUTURAS ===")
        print(f"Servidor SQL Server DateTime actual: {db_now}")
        print(f"Servidor SQL Server Fecha actual: {db_today}")
        
        # 2. Check foreign keys pointing to asistencias_grua, asistencias_ambulancia, bitacora_patrullaje
        fks_query = """
        SELECT 
            fk.name AS FK_name,
            OBJECT_NAME(fk.parent_object_id) AS child_table,
            OBJECT_NAME(fk.referenced_object_id) AS parent_table
        FROM sys.foreign_keys fk
        WHERE OBJECT_NAME(fk.referenced_object_id) IN ('asistencias_grua', 'asistencias_ambulancia', 'bitacora_patrullaje')
        """
        fks = db.execute(text(fks_query)).fetchall()
        print(f"\nTablas dependientes (FKs):")
        for fk in fks:
            print(f" - {fk.FK_name}: {fk.child_table} -> {fk.parent_table}")
        if not fks:
            print(" - (No hay tablas secundarias referenciando a estas tablas)")

        # 3. Check asistencias_grua with future dates
        gruas_future_query = """
        SELECT 
            id_asistencia_grua, 
            codigo_formulario, 
            ts_llamada, 
            ts_arribo, 
            ts_termino, 
            ts_retorno
        FROM dbo.asistencias_grua
        WHERE 
            ts_llamada > GETDATE()
            OR ts_arribo > GETDATE()
            OR ts_termino > GETDATE()
            OR ts_retorno > GETDATE()
        ORDER BY ts_llamada DESC
        """
        gruas_future = db.execute(text(gruas_future_query)).fetchall()
        print(f"\n[asistencias_grua] Registros con fechas futuras (> {db_today}): {len(gruas_future)}")
        for r in gruas_future[:10]:
            print(f"  ID: {r.id_asistencia_grua} | Formulario: {r.codigo_formulario} | Llamada: {r.ts_llamada} | Arribo: {r.ts_arribo}")
        if len(gruas_future) > 10:
            print(f"  ... y {len(gruas_future) - 10} más.")

        # 4. Check asistencias_ambulancia with future dates
        amb_future_query = """
        SELECT 
            id_asistencia, 
            codigo_formulario, 
            ts_llamada, 
            ts_arribo, 
            ts_termino, 
            ts_retorno
        FROM dbo.asistencias_ambulancia
        WHERE 
            ts_llamada > GETDATE()
            OR ts_arribo > GETDATE()
            OR ts_termino > GETDATE()
            OR ts_retorno > GETDATE()
        ORDER BY ts_llamada DESC
        """
        amb_future = db.execute(text(amb_future_query)).fetchall()
        print(f"\n[asistencias_ambulancia] Registros con fechas futuras (> {db_today}): {len(amb_future)}")
        for r in amb_future[:10]:
            print(f"  ID: {r.id_asistencia} | Formulario: {r.codigo_formulario} | Llamada: {r.ts_llamada} | Arribo: {r.ts_arribo}")
        if len(amb_future) > 10:
            print(f"  ... y {len(amb_future) - 10} más.")

        # 5. Check bitacora_patrullaje with future dates
        pat_future_query = """
        SELECT 
            id_patrullaje, 
            codigo_patrullaje, 
            fecha_recorrido, 
            hora_salida
        FROM dbo.bitacora_patrullaje
        WHERE 
            fecha_recorrido > CAST(GETDATE() AS DATE)
        ORDER BY fecha_recorrido DESC
        """
        pat_future = db.execute(text(pat_future_query)).fetchall()
        print(f"\n[bitacora_patrullaje] Registros con fechas futuras (> {db_today}): {len(pat_future)}")
        for r in pat_future[:10]:
            print(f"  ID: {r.id_patrullaje} | Código: {r.codigo_patrullaje} | Fecha: {r.fecha_recorrido} | Salida: {r.hora_salida}")

        # Check total counts in each table
        tot_gruas = db.execute(text("SELECT COUNT(*) FROM dbo.asistencias_grua")).scalar()
        tot_amb = db.execute(text("SELECT COUNT(*) FROM dbo.asistencias_ambulancia")).scalar()
        tot_pat = db.execute(text("SELECT COUNT(*) FROM dbo.bitacora_patrullaje")).scalar()
        print(f"\nTotales actuales en BD:")
        print(f" - Grúas: {tot_gruas}")
        print(f" - Ambulancias: {tot_amb}")
        print(f" - Patrullajes: {tot_pat}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
