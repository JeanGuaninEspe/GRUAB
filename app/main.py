"""
Punto de entrada principal para la aplicación FastAPI.
Configura middlewares, CORS, manejadores globales de excepciones y enrutadores.
"""
import os
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import check_db_connection
from app.routers import (
    catalogos_router,
    operaciones_router,
    analitica_router,
    reportes_mtop_router,
)
from app.routers.ai_router import router as ai_router, CHAT_HTML_PATH
from app.api.v1 import api_router as api_v1_router
from app.services.pdf_service import LOGO_PATH

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("vehiculos_rescate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación: inicialización y apagado.
    """
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION} en modo [{settings.ENVIRONMENT}]")
    db_connected = check_db_connection()
    if db_connected:
        logger.info("Conexión exitosa a Microsoft SQL Server (Instancia VIALPROD / VehiculosRescate)")
    else:
        logger.warning("No se pudo establecer conexión inicial a SQL Server. Verifique las credenciales y el estado de la red.")
    yield
    logger.info(f"Deteniendo {settings.PROJECT_NAME}...")


# Instanciación de la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Microservicio RESTful de alto rendimiento para la gestión de operaciones viales "
        "(Ambulancias, Grúas y Patrullaje), analítica de respuesta/puntos negros y generación "
        "de reportes ejecutivos ministeriales MTOP en formato Excel y PDF con imagen corporativa COSAD 25."
    ),
    openapi_tags=[
        {"name": "Catálogos", "description": "Consulta de personal activo y flota vehicular de la concesión."},
        {"name": "Operaciones", "description": "Registro transaccional y consulta de asistencias y patrullajes viales."},
        {"name": "Analítica Vial", "description": "KPIs de tiempos de respuesta y análisis geoespacial de tramos críticos."},
        {"name": "Reportes MTOP", "description": "Generación y descarga de informes oficiales en Excel y PDF con Logo de COSAD 25."},
        {"name": "Analítica e Inteligencia Artificial (Ollama)", "description": "Agente autónomo local Qwen 2.5 para analítica e informes ejecutivos."},
        {"name": "Monitoreo", "description": "Verificación de salud del servicio y conectividad con SQL Server."},
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==========================================
# MIDDLEWARE DE SEGURIDAD Y CORS
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# MANEJADORES GLOBALES DE EXCEPCIONES
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Captura y formatea de forma amigable los errores de validación de esquemas Pydantic v2.
    """
    errores = []
    for error in exc.errors():
        campo = " -> ".join(str(loc) for loc in error.get("loc", []))
        errores.append({
            "campo": campo,
            "mensaje": error.get("msg"),
            "tipo": error.get("type"),
        })
    logger.warning(f"Error de validación en {request.method} {request.url.path}: {errores}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "Error de validación en la solicitud",
            "detalles": errores,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Captura errores de base de datos SQLAlchemy / SQL Server evitando exponer detalles sensibles.
    """
    logger.error(f"Error en base de datos al acceder a {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error en el servidor de base de datos SQL Server",
            "mensaje": "Ocurrió un problema al procesar la transacción o consultar la base de datos.",
        },
    )


# ==========================================
# REGISTRO DE ENRUTADORES
# ==========================================

app.include_router(catalogos_router, prefix=settings.API_V1_STR)
app.include_router(operaciones_router, prefix=settings.API_V1_STR)
app.include_router(analitica_router, prefix=settings.API_V1_STR)
app.include_router(reportes_mtop_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# ==========================================
# INTERFAZ CHATBOT, RECURSOS Y MONITOREO
# ==========================================

@app.get(
    "/logo-cosad.webp",
    include_in_schema=False,
    summary="Logo oficial de COSAD 25",
)
def get_logo_cosad():
    """Sirve el logo corporativo oficial de COSAD 25."""
    if os.path.exists(LOGO_PATH):
        return FileResponse(LOGO_PATH, media_type="image/webp")
    return JSONResponse({"error": "Logo no encontrado"}, status_code=404)


@app.get(
    "/chat",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def chat_direct_route():
    """Acceso directo al Chatbot UI en /chat."""
    if os.path.exists(CHAT_HTML_PATH):
        with open(CHAT_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h3>Interfaz del Chatbot cargándose...</h3>")


@app.get(
    "/",
    tags=["Monitoreo"],
    summary="Información y bienvenida al microservicio",
)
def root(request: Request) -> Any:
    # Si la petición proviene de un navegador web, redirigir automáticamente a /chat
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/chat", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return {
        "sistema": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "entorno": settings.ENVIRONMENT,
        "interfaz_chat": "/chat",
        "documentacion_swagger": "/docs",
        "documentacion_redoc": "/redoc",
        "api_v1": settings.API_V1_STR,
    }


@app.get(
    "/health",
    tags=["Monitoreo"],
    summary="Estado de salud del microservicio y base de datos",
    description="Comprueba la operatividad de la API y ejecuta un ping de verificación a SQL Server.",
)
def health_check() -> Dict[str, Any]:
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_ok,
        "database_server": settings.DB_SERVER,
        "database_name": settings.DB_NAME,
    }
