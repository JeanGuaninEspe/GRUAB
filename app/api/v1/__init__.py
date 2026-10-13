"""
API v1 Router Configuration
"""
from fastapi import APIRouter
from app.api.v1.endpoints.catalogos import router as catalogos_router
from app.api.v1.endpoints.asistencias_grua import router as asistencias_grua_router
from app.api.v1.endpoints.reportes_gruas import router as reportes_gruas_router

api_router = APIRouter()
api_router.include_router(catalogos_router, prefix="/catalogos", tags=["Catálogos"])
api_router.include_router(asistencias_grua_router, prefix="/asistencias-grua", tags=["Asistencias de Grúas"])
api_router.include_router(reportes_gruas_router, prefix="/reportes-gruas", tags=["Reportes y Analítica con IA"])
