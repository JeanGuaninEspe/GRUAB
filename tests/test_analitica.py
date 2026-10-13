"""
Pruebas unitarias para el servicio de analítica avanzada, modelos de scoring y despliegue táctico.
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.services.analitica_service import AnaliticaService
from app.schemas.analitica import NivelRiesgoEnum


def test_analitica_calculos_kpis():
    service = AnaliticaService()
    mock_db = MagicMock()

    mock_rows = [
        {
            "tipo_servicio": "AMBULANCIA",
            "codigo_formulario": "AMB-001",
            "fecha": "2026-08-01",
            "turno": 1,
            "abscisa_km": Decimal("20.0"),
            "sentido": "ASCENDENTE",
            "tiempo_despacho_arribo_min": 10.0,
            "tiempo_en_sitio_min": 30.0,
            "ciclo_total_min": 60.0,
            "km_recorridos": 40.0,
        },
        {
            "tipo_servicio": "AMBULANCIA",
            "codigo_formulario": "AMB-002",
            "fecha": "2026-08-02",
            "turno": 2,
            "abscisa_km": Decimal("35.0"),
            "sentido": "DESCENDENTE",
            "tiempo_despacho_arribo_min": 20.0,
            "tiempo_en_sitio_min": 40.0,
            "ciclo_total_min": 80.0,
            "km_recorridos": 50.0,
        },
        {
            "tipo_servicio": "GRUA",
            "codigo_formulario": "GRU-001",
            "fecha": "2026-08-02",
            "turno": 1,
            "abscisa_km": Decimal("10.0"),
            "sentido": "ASCENDENTE",
            "tiempo_despacho_arribo_min": 15.0,
            "tiempo_en_sitio_min": 25.0,
            "ciclo_total_min": 50.0,
            "km_recorridos": 30.0,
        },
    ]

    with patch("app.services.analitica_service.analitica_repo.get_kpi_tiempos_atencion", return_value=mock_rows):
        response = service.obtener_kpis_tiempos_respuesta(db=mock_db)
        assert response.total_registros == 3
        assert response.promedio_despacho_arribo_min == 15.0
        assert response.promedio_sitio_min == 31.67
        assert response.total_km_recorridos == 120.0
        assert len(response.resumen_por_servicio) == 2


def test_scoring_tramos_criticos_clustering():
    service = AnaliticaService()
    mock_db = MagicMock()

    mock_eventos = [
        {
            "tipo_servicio": "AMBULANCIA",
            "codigo_formulario": "AMB-101",
            "ts_llamada": datetime(2026, 8, 1, 14, 30),
            "abscisa_km": Decimal("24.2"),
            "sentido": "ASCENDENTE",
            "motivo_atencion": "Colisión frontal",
            "tipo_accidente": "Choque",
            "severidad": "FATAL",
            "km_recorridos": Decimal("20.0"),
        },
        {
            "tipo_servicio": "AMBULANCIA",
            "codigo_formulario": "AMB-102",
            "ts_llamada": datetime(2026, 8, 2, 16, 0),
            "abscisa_km": Decimal("24.8"),
            "sentido": "ASCENDENTE",
            "motivo_atencion": "Volcamiento",
            "tipo_accidente": "Volcamiento",
            "severidad": "GRAVE",
            "km_recorridos": Decimal("25.0"),
        },
        {
            "tipo_servicio": "GRUA",
            "codigo_formulario": "GRU-101",
            "ts_llamada": datetime(2026, 8, 3, 10, 0),
            "abscisa_km": Decimal("85.0"),
            "sentido": "DESCENDENTE",
            "motivo_atencion": "Avería mecánica",
            "tipo_accidente": None,
            "posible_causa": "Falla de motor",
            "severidad": "LEVE",
            "km_recorridos": Decimal("15.0"),
        },
    ]

    with patch("app.services.analitica_service.analitica_repo.get_eventos_combinados", return_value=mock_eventos):
        response = service.obtener_scoring_tramos_criticos(db=mock_db, tamano_tramo_km=5.0)

        assert response.total_eventos_evaluados == 3
        assert response.total_tramos_analizados == 2

        # El tramo Km 20-25 debe ser el más crítico debido a 1 FATAL + 1 GRAVE (ICV = 10 + 5 = 15)
        top_tramo = response.top_tramos_criticos[0]
        assert top_tramo.km_inicio == 20.0
        assert top_tramo.km_fin == 25.0
        assert top_tramo.total_fatales == 1
        assert top_tramo.total_graves == 1
        assert top_tramo.total_ambulancias == 2
        assert top_tramo.indice_criticidad >= 15.0
        assert top_tramo.sentido_predominante == "ASCENDENTE"


def test_patrones_temporales_horas_y_dias():
    service = AnaliticaService()
    mock_db = MagicMock()

    mock_eventos = [
        # Sábado (weekday 5) a las 14:00
        {
            "tipo_servicio": "AMBULANCIA",
            "ts_llamada": datetime(2026, 8, 1, 14, 15),  # 2026-08-01 es Sábado
            "abscisa_km": Decimal("20.0"),
            "severidad": "GRAVE",
        },
        # Sábado a las 14:30
        {
            "tipo_servicio": "GRUA",
            "ts_llamada": datetime(2026, 8, 1, 14, 45),
            "abscisa_km": Decimal("30.0"),
            "severidad": "LEVE",
        },
        # Lunes (weekday 0) a las 08:00
        {
            "tipo_servicio": "AMBULANCIA",
            "ts_llamada": datetime(2026, 8, 3, 8, 10),
            "abscisa_km": Decimal("40.0"),
            "severidad": "LEVE",
        },
    ]

    with patch("app.services.analitica_service.analitica_repo.get_eventos_combinados", return_value=mock_eventos):
        response = service.obtener_patrones_temporales(db=mock_db)

        assert response.total_eventos_analizados == 3
        assert "14:00 - 15:00" in response.hora_pico_maxima
        assert "Sábado" in response.dia_pico_maximo
        assert response.eventos_fin_de_semana == 2
        assert response.eventos_entre_semana == 1
        assert response.porcentaje_fin_de_semana == 66.67


def test_plan_despliegue_estrategico_y_dashboard():
    service = AnaliticaService()
    mock_db = MagicMock()

    mock_eventos = [
        {
            "tipo_servicio": "AMBULANCIA",
            "codigo_formulario": "AMB-201",
            "ts_llamada": datetime(2026, 8, 1, 19, 0),
            "abscisa_km": Decimal("24.0"),
            "sentido": "ASCENDENTE",
            "motivo_atencion": "Colisión",
            "tipo_accidente": "Choque",
            "severidad": "FATAL",
            "km_recorridos": Decimal("30.0"),
        }
    ]

    with patch("app.services.analitica_service.analitica_repo.get_eventos_combinados", return_value=mock_eventos):
        with patch("app.services.analitica_service.analitica_repo.get_kpi_tiempos_atencion", return_value=[]):
            with patch("app.services.analitica_service.analitica_repo.get_conteo_patrullajes", return_value=12):
                plan = service.obtener_plan_despliegue_estrategico(db=mock_db)
                assert plan.total_recomendaciones >= 1
                assert "AMBULANCIA" in plan.recomendaciones[0].recurso_recomendado or "PATRULLA" in plan.recomendaciones[0].recurso_recomendado

                dashboard = service.obtener_dashboard_ejecutivo(db=mock_db)
                assert dashboard.total_patrullajes == 12
                assert dashboard.tramo_mas_critico is not None
                assert "Km 20.0 - Km 25.0" in dashboard.tramo_mas_critico.tramo_label
