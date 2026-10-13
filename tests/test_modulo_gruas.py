"""
Suite de Pruebas Unitarias y de Integración para el Módulo de Asistencias de Grúas y Reportes IA.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.transaccionales import AsistenciaGrua
from app.models.catalogos import CatPersonal, CatVehiculoConcesion


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_catalogos_endpoints(client):
    # 1. Choferes de grúa
    res_ch = client.get("/api/v1/catalogos/choferes-grua")
    assert res_ch.status_code == 200
    choferes = res_ch.json()
    assert isinstance(choferes, list)
    if len(choferes) > 0:
        assert choferes[0]["rol"] == "CHOFER_GRUA"
        assert choferes[0]["activo"] is True

    # 2. Supervisores
    res_sup = client.get("/api/v1/catalogos/supervisores")
    assert res_sup.status_code == 200
    supervisores = res_sup.json()
    assert isinstance(supervisores, list)
    if len(supervisores) > 0:
        assert supervisores[0]["rol"] == "SUPERVISOR"
        assert supervisores[0]["activo"] is True

    # 3. Vehículos de grúa
    res_veh = client.get("/api/v1/catalogos/vehiculos-grua")
    assert res_veh.status_code == 200
    vehiculos = res_veh.json()
    assert isinstance(vehiculos, list)
    if len(vehiculos) > 0:
        assert vehiculos[0]["tipo_flota"] == "GRUA"
        assert vehiculos[0]["activo"] is True


def test_validacion_cronologica_y_odometria(client):
    # Error: Arribo anterior a llamada
    bad_payload = {
        "codigo_formulario": f"TEST-ERR-CRON-{datetime.now().timestamp()}",
        "id_supervisor": 1,
        "id_chofer": 1,
        "turno": 1,
        "tipo_grua": "PEQUEÑA",
        "ts_llamada": "2026-10-01T10:00:00",
        "ts_arribo": "2026-10-01T09:45:00",
        "ts_termino": "2026-10-01T10:30:00",
        "ts_retorno": "2026-10-01T11:00:00",
        "sector_referencia": "SALIDA PATRICIA PILAR",
        "abscisa_km": 10.0,
        "sentido": "ASCENDENTE",
        "motivo_atencion": "DAÑO MECANICO",
        "odometro_salida_km": 1000.0,
        "odometro_llegada_km": 1020.0,
    }
    res_cron = client.post("/api/v1/asistencias-grua/", json=bad_payload)
    assert res_cron.status_code == 422

    # Error: Odómetro llegada menor que salida
    bad_odo = dict(bad_payload)
    bad_odo["ts_arribo"] = "2026-10-01T10:15:00"
    bad_odo["odometro_salida_km"] = 5000.0
    bad_odo["odometro_llegada_km"] = 4900.0
    res_odo = client.post("/api/v1/asistencias-grua/", json=bad_odo)
    assert res_odo.status_code == 422


def test_listar_asistencias_grua_paginado_y_filtros(client):
    res = client.get("/api/v1/asistencias-grua/?limit=10&skip=0")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) <= 10
    assert data["total"] >= 0

    # Filtro por tipo de grúa
    res_filtro = client.get("/api/v1/asistencias-grua/?tipo_grua=PEQUEÑA&limit=5")
    assert res_filtro.status_code == 200
    for item in res_filtro.json()["items"]:
        assert "PEQUE" in item["tipo_grua"].upper()


def test_reporte_ejecutivo_ia(client):
    payload = {
        "fecha_inicio": "2026-01-01T00:00:00",
        "fecha_fin": "2026-07-31T23:59:59",
    }
    res = client.post("/api/v1/reportes-gruas/ejecutivo-ia", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_auxilios"] > 0
    assert "kpis" in data
    assert "tramo_critico" in data["kpis"]
    assert "tpa_respuesta_min" in data["kpis"]
    assert "tpa_despeje_min" in data["kpis"]
    assert "desglose_mensual" in data
    assert "desglose_sectores" in data
    assert "desglose_cruzado" in data
    assert len(data["resumen_markdown"]) > 50

    # Verificar que los porcentajes mensuales sumen 100% aproximadamente
    total_pct_mensual = sum(m["porcentaje_num"] for m in data["desglose_mensual"])
    assert 99.0 <= total_pct_mensual <= 101.0
