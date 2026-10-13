# Microservicio de Gestión y Analítica de Rescate Vial

Microservicio RESTful de alto rendimiento desarrollado en **Python 3.11+** con **FastAPI**, **SQLAlchemy** (driver `pyodbc`), **Pydantic v2** y **Microsoft SQL Server**, diseñado para la gestión operativa y analítica de vehículos de asistencia vial (Ambulancias, Grúas y Patrullas) para concesiones viales.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110+)
* **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
* **ORM & Acceso a Datos:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) con `pyodbc`
* **Validación y Configuración:** [Pydantic v2](https://docs.pydantic.dev/) y `pydantic-settings`
* **Analítica y Reportes:** [Pandas](https://pandas.pydata.org/) y [OpenPyXL](https://openpyxl.readthedocs.io/)
* **Motor de Base de Datos:** Microsoft SQL Server (Instancia `VIALPROD`)

---

## 📁 Estructura del Proyecto

```text
VehiculosRC/
├── app/
│   ├── core/
│   │   ├── config.py             # Configuración Pydantic Settings con lectura de .env
│   │   └── database.py           # Motor SQLAlchemy, SessionLocal y dependencia get_db
│   ├── models/                   # Modelos ORM SQLAlchemy mapeados a dbo.*
│   │   ├── catalogos.py          # CatPersonal, CatVehiculoConcesion
│   │   └── transaccionales.py    # AsistenciaAmbulancia, AsistenciaGrua, BitacoraPatrullaje
│   ├── schemas/                  # Esquemas de validación Pydantic v2 (Create, Read, Filters)
│   │   ├── catalogos.py
│   │   ├── operaciones.py
│   │   ├── analitica.py
│   │   └── reportes.py
│   ├── repositories/             # Capa de persistencia y consultas a tablas y vistas
│   │   ├── base.py
│   │   ├── catalogos_repo.py
│   │   ├── operaciones_repo.py
│   │   ├── analitica_repo.py
│   │   └── reportes_repo.py
│   ├── services/                 # Lógica de negocio, validaciones y exportación Excel
│   │   ├── catalogos_service.py
│   │   ├── operaciones_service.py
│   │   ├── analitica_service.py
│   │   └── excel_service.py
│   ├── routers/                  # Enrutadores API por módulo
│   │   ├── catalogos.py          # /api/v1/catalogos
│   │   ├── operaciones.py        # /api/v1/operaciones
│   │   ├── analitica.py          # /api/v1/analitica
│   │   └── reportes_mtop.py      # /api/v1/reportes-mtop
│   ├── __init__.py
│   └── main.py                   # Instancia FastAPI, CORS, middlewares y OpenAPI docs
├── .env.example
├── .env
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuración y Variables de Entorno

El archivo `.env` contiene los parámetros de conexión y pooling para SQL Server:

```env
PROJECT_NAME="Microservicio de Gestión y Analítica de Rescate Vial"
VERSION="1.0.0"
API_V1_STR="/api/v1"
ENVIRONMENT="development"
DEBUG=True

# Conexión a Microsoft SQL Server
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=192.168.80.161\VIALPROD
DB_NAME=VehiculosRescate
DB_USER=sa
DB_PASSWORD=**Syst3m2026
DB_ENCRYPT=no
DB_TRUST_SERVER_CERTIFICATE=yes

# Connection Pool SQLAlchemy
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

CORS_ORIGINS=*
```

> **Nota:** La contraseña y parámetros con caracteres especiales se escapan automáticamente mediante `urllib.parse.quote_plus` en `app/core/config.py`.

---

## 🚀 Instalación y Ejecución

### 1. Crear entorno virtual e instalar dependencias

```bash
# Con uv (recomendado por velocidad)
uv venv --python 3.11 .venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# O con python estándar
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Iniciar el servidor de desarrollo

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acceso a la documentación interactiva:
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 Catálogo de Endpoints de la API

### 1. Catálogos (`/api/v1/catalogos`)
* `GET /personal`: Lista el personal con filtros por `rol` (`SUPERVISOR`, `PARAMEDICO`, `CHOFER_AMBULANCIA`, `CHOFER_GRUA`, `PATRULLERO`) y estado `activo`.
* `GET /vehiculos`: Lista la flota con filtros por `tipo_flota` (`AMBULANCIA`, `GRUA`, `PATRULLA`) y `activo`.

### 2. Operaciones (`/api/v1/operaciones`)
* `POST /ambulancias`: Registro de hoja de atención prehospitalaria (validación de timestamps y odómetros).
* `GET /ambulancias`: Historial de asistencias de ambulancias con filtros por fecha y turno.
* `POST /gruas`: Registro de asistencia mecánica o remolque (validación de placa y kilometrajes).
* `GET /gruas`: Historial de remolques y auxilios de grúas.
* `POST /patrullaje`: Registro de bitácora diaria de recorrido de inspección vial.
* `GET /patrullaje`: Historial de patrullajes.

### 3. Analítica, Modelos de Scoring y Toma de Decisiones (`/api/v1/analitica`)
* `GET /tiempos-respuesta`: Consume `dbo.vw_kpi_tiempos_atencion` y calcula tiempos promedio de despacho-arribo, permanencia en sitio, ciclo total y desglose por tipo de servicio.
* `GET /puntos-negros`: Consume `dbo.vw_analitica_puntos_negros` para mapear y priorizar tramos de alta criticidad por severidad y posible causa.
* `GET /tramos-criticos-scoring`: **Modelo Ponderado de Scoring de Peligrosidad Vial e Identificación de Hotspots**. Agrupa espacialmente las asistencias cada `N` kilómetros (ej. `tamano_tramo_km=5.0` o `1.0`), calcula el **Índice de Criticidad Vial (ICV)** ponderando fatalidades, eventos graves y auxilios mecánicos, clasifica en niveles de riesgo (`EXTREMO`, `ALTO`, `MEDIO`, `BAJO`) y entrega recomendaciones tácticas preventivas.
* `GET /patrones-temporales`: Análisis multidimensional de siniestralidad y demanda por hora del día (0-23h), días de la semana (Lunes-Domingo), horas pico y comparativa fin de semana vs entre semana.
* `GET /recomendaciones-despliegue`: **Plan de Despliegue Estratégico de Recursos**. Recomienda el posicionamiento preventivo óptimo de ambulancias medicalizadas, grúas pesadas y patrullas en los tramos críticos durante las franjas horarias de mayor accidentabilidad.
* `GET /dashboard-ejecutivo`: Resumen ejecutivo consolidado de alto nivel con métricas clave, tasas de accidentabilidad vs auxilios mecánicos, el tramo #1 más peligroso y la directriz operativa principal.

### 4. Reportes Ministeriales MTOP (`/api/v1/reportes-mtop`)
* `GET /exportar-excel`: Genera y descarga directamente un archivo Excel profesional (`.xlsx`) en memoria con formato institucional MTOP a partir de `dbo.vw_mtop_ambulancias`, `dbo.vw_mtop_gruas` o `dbo.vw_mtop_patrullaje` filtrado por `mes` (1-12) y `anio`.
