"""
Módulo de enrutadores API para FastAPI.
"""
from app.routers.catalogos import router as catalogos_router
from app.routers.operaciones import router as operaciones_router
from app.routers.analitica import router as analitica_router
from app.routers.reportes_mtop import router as reportes_mtop_router

__all__ = [
    "catalogos_router",
    "operaciones_router",
    "analitica_router",
    "reportes_mtop_router",
]
