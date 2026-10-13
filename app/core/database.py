"""
Configuración del motor de base de datos SQLAlchemy, sesiones y dependencias.
"""
from typing import Generator
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("vehiculos_rescate.database")

# Crear motor SQLAlchemy conectado a SQL Server
engine = create_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesión SQLAlchemy como dependencia para FastAPI.
    Garantiza el cierre y rollback automático en caso de error.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error(f"Error en sesión de base de datos: {exc}")
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Verifica la conectividad con la base de datos SQL Server ejecutando una consulta simple.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS status"))
            row = result.fetchone()
            return row is not None and row[0] == 1
    except Exception as exc:
        logger.error(f"Fallo de conexión a SQL Server: {exc}")
        return False
