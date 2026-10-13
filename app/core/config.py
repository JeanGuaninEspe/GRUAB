"""
Configuración global de la aplicación y parámetros de conexión a SQL Server.
Utiliza Pydantic Settings para cargar y validar variables de entorno.
"""
import urllib.parse
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Metadatos del microservicio
    PROJECT_NAME: str = "Microservicio de Gestión y Analítica de Rescate Vial"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Parámetros de conexión Microsoft SQL Server
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_SERVER: str = r"192.168.80.161\VIALPROD"
    DB_NAME: str = "VehiculosRescate"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "**Syst3m2026"
    DB_ENCRYPT: str = "no"
    DB_TRUST_SERVER_CERTIFICATE: str = "yes"

    # Configuración del Connection Pool de SQLAlchemy
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Configuración de CORS
    CORS_ORIGINS: Union[str, List[str]] = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """
        Construye la cadena de conexión SQLAlchemy mssql+pyodbc escapando correctamente
        los caracteres especiales en contraseñas o nombres de servidor.
        """
        odbc_str = (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_SERVER};"
            f"DATABASE={self.DB_NAME};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            f"Encrypt={self.DB_ENCRYPT};"
            f"TrustServerCertificate={self.DB_TRUST_SERVER_CERTIFICATE};"
        )
        return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_str)}"

    @property
    def parsed_cors_origins(self) -> List[str]:
        """
        Retorna la lista de orígenes permitidos para CORS.
        """
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
