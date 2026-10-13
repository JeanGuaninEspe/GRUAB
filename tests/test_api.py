"""
Pruebas de integración de la API FastAPI y endpoints HTTP.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Microservicio de Gestión y Analítica de Rescate Vial" in data["sistema"]
    assert data["api_v1"] == "/api/v1"


def test_health_endpoint():
    with patch("app.main.check_db_connection", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["database_connected"] is True


def test_validation_error_handler():
    response = client.post("/api/v1/operaciones/ambulancias", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "detalles" in data
    assert len(data["detalles"]) > 0


def test_exportar_excel_endpoint_mocked():
    import pandas as pd
    mock_df = pd.DataFrame([{"col1": "val1", "col2": 100}])

    with patch("app.routers.reportes_mtop.reportes_repo.get_datos_mtop_df", return_value=mock_df):
        with patch("app.routers.reportes_mtop.get_db", return_value=MagicMock()):
            response = client.get("/api/v1/reportes-mtop/exportar-excel?servicio=ambulancia&mes=8&anio=2026")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "attachment; filename=" in response.headers["content-disposition"]


def test_endpoints_analitica_avanzada_mocked():
    from app.schemas.analitica import (
        TramosScoringResponse,
        PatronesTemporalesResponse,
        RecomendacionesDespliegueResponse,
        DashboardEjecutivoResponse,
    )
    from datetime import datetime

    mock_scoring = TramosScoringResponse(
        criterio_agrupacion_km=5.0,
        total_tramos_analizados=1,
        total_eventos_evaluados=5,
        resumen_niveles_riesgo={"EXTREMO": 1, "ALTO": 0, "MEDIO": 0, "BAJO": 0},
        top_tramos_criticos=[],
    )

    mock_patrones = PatronesTemporalesResponse(
        total_eventos_analizados=5,
        hora_pico_maxima="14:00 - 15:00",
        dia_pico_maximo="Sábado",
        eventos_fin_de_semana=4,
        eventos_entre_semana=1,
        porcentaje_fin_de_semana=80.0,
        distribucion_por_franja={"Madrugada (00-06h)": 0, "Mañana (06-12h)": 1, "Tarde (12-18h)": 3, "Noche (18-24h)": 1},
        distribucion_por_hora=[],
        distribucion_por_dia=[],
    )

    mock_despliegue = RecomendacionesDespliegueResponse(
        fecha_generacion=datetime.now(),
        total_recomendaciones=1,
        estrategia_general="Despliegue preventivo",
        recomendaciones=[],
    )

    mock_dashboard = DashboardEjecutivoResponse(
        total_asistencias_historicas=10,
        total_ambulancias=4,
        total_gruas=6,
        total_patrullajes=20,
        tasa_accidentabilidad_porcentaje=40.0,
        tasa_asistencia_mecanica_porcentaje=60.0,
        km_totales_atendidos=150.0,
        tiempo_promedio_llegada_min=14.5,
        tiempo_promedio_sitio_min=30.0,
        tiempo_promedio_ciclo_min=55.0,
        tramo_mas_critico=None,
        franja_horaria_mas_critica="Tarde",
        dia_mas_critico="Sábado",
        recomendacion_ejecutiva="Mantener patrullaje",
    )

    with patch("app.routers.analitica.analitica_service.obtener_scoring_tramos_criticos", return_value=mock_scoring):
        res = client.get("/api/v1/analitica/tramos-criticos-scoring?tamano_tramo_km=5.0")
        assert res.status_code == 200
        assert res.json()["criterio_agrupacion_km"] == 5.0

    with patch("app.routers.analitica.analitica_service.obtener_patrones_temporales", return_value=mock_patrones):
        res = client.get("/api/v1/analitica/patrones-temporales")
        assert res.status_code == 200
        assert res.json()["dia_pico_maximo"] == "Sábado"

    with patch("app.routers.analitica.analitica_service.obtener_plan_despliegue_estrategico", return_value=mock_despliegue):
        res = client.get("/api/v1/analitica/recomendaciones-despliegue")
        assert res.status_code == 200
        assert res.json()["total_recomendaciones"] == 1

    with patch("app.routers.analitica.analitica_service.obtener_dashboard_ejecutivo", return_value=mock_dashboard):
        res = client.get("/api/v1/analitica/dashboard-ejecutivo")
        assert res.status_code == 200
        assert res.json()["total_asistencias_historicas"] == 10
