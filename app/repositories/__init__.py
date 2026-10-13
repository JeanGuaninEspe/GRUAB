"""
Módulo de repositorios de acceso a datos para SQL Server.
"""
from app.repositories.base import BaseRepository
from app.repositories.catalogos_repo import personal_repo, vehiculo_repo, PersonalRepository, VehiculoRepository
from app.repositories.operaciones_repo import operaciones_repo, OperacionesRepository
from app.repositories.analitica_repo import analitica_repo, AnaliticaRepository
from app.repositories.reportes_repo import reportes_repo, ReportesRepository

__all__ = [
    "BaseRepository",
    "personal_repo",
    "vehiculo_repo",
    "PersonalRepository",
    "VehiculoRepository",
    "operaciones_repo",
    "OperacionesRepository",
    "analitica_repo",
    "AnaliticaRepository",
    "reportes_repo",
    "ReportesRepository",
]
