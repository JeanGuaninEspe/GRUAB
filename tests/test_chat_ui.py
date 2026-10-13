from datetime import date, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import ai_service
from app.services.pdf_service import pdf_service

client = TestClient(app)

def test_chat_html_file_exists():
    import os
    from app.routers.ai_router import CHAT_HTML_PATH
    assert os.path.exists(CHAT_HTML_PATH), f"El archivo {CHAT_HTML_PATH} no existe."

def test_chat_direct_route():
    response = client.get("/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "VialBot" in response.text or "Asistente" in response.text

def test_ai_router_chat_endpoint():
    response = client.get("/api/v1/ai/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_ai_analizar_jornada_json_response(monkeypatch):
    async def mock_procesar_peticion(*args, **kwargs):
        return {
            "solicita_exportacion": False,
            "respuesta_ia": "Todo operando con normalidad en el peaje.",
            "datos_crudos": {"ambulancias": []},
            "estadisticas": None
        }

    monkeypatch.setattr(ai_service, "procesar_peticion", mock_procesar_peticion)

    response = client.post(
        "/api/v1/ai/analizar-jornada",
        json={"pregunta": "Como estuvo el dia hoy?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "respuesta_ia" in data
    assert "Todo operando con normalidad" in data["respuesta_ia"]

def test_ai_analizar_jornada_excel_export(monkeypatch):
    async def mock_procesar_peticion(*args, **kwargs):
        return {
            "solicita_exportacion": True,
            "formato_exportacion": "excel",
            "respuesta_ia": "Reporte de jornada generado en Excel.",
            "datos_crudos": {
                "ambulancias": [{"id": 1, "sector": "Peaje", "novedad": "Sin novedad"}],
                "gruas": [],
                "patrullajes": []
            },
            "modulos_solicitados": ["ambulancias"],
            "estadisticas": {"total": 1}
        }

    monkeypatch.setattr(ai_service, "procesar_peticion", mock_procesar_peticion)

    response = client.post(
        "/api/v1/ai/analizar-jornada",
        json={"pregunta": "Descargar excel de ambulancias"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment; filename=\"informe_operaciones.xlsx\"" in response.headers["content-disposition"]

def test_resolucion_fechas_hibrida_dateutil():
    """Valida la función resolver_rango_fechas_python con precisión de microsegundos."""
    ahora = datetime.now()

    # 1. MES_PASADO
    ini_mp, fin_mp = ai_service.resolver_rango_fechas_python({"tipo_filtro": "MES_PASADO"})
    assert ini_mp.day == 1
    assert ini_mp.hour == 0 and ini_mp.minute == 0 and ini_mp.second == 0
    assert fin_mp < ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    assert fin_mp.hour == 23 and fin_mp.minute == 59 and fin_mp.second == 59

    # 2. ULTIMOS_DIAS
    ini_ud, fin_ud = ai_service.resolver_rango_fechas_python({"tipo_filtro": "ULTIMOS_DIAS", "dias_atras": 5})
    assert (fin_ud.date() - ini_ud.date()).days == 5

    # 3. ANIO_ESPECIFICO
    ini_anio, fin_anio = ai_service.resolver_rango_fechas_python({"tipo_filtro": "ANIO_ESPECIFICO", "anio_especifico": 2025})
    assert ini_anio.year == 2025 and ini_anio.month == 1 and ini_anio.day == 1
    assert fin_anio.year == 2025 and fin_anio.month == 12 and fin_anio.day == 31

def test_heuristica_resolucion_anios_e_historico():
    """Valida que la heurística resuelva consultas de años pasados, meses anteriores y todo el histórico."""
    hoy = date.today()

    # 1. Prueba 'ultimos 4 anios'
    res = ai_service._resolver_intencion_heuristica("estadisticas de los ultimos 4 anos de ambulancias y gruas")
    assert res is not None
    f_inicio, f_fin, formato, modulos = res
    assert f_fin.date() == hoy
    assert f_inicio.year == (hoy.year - 4)
    assert "ambulancias" in modulos and "gruas" in modulos

    # 2. Prueba 'mes pasado' / 'mes anterior'
    res_mes_pasado = ai_service._resolver_intencion_heuristica("como estuvo el mes pasado?")
    assert res_mes_pasado is not None
    f_ini_mp, f_fin_mp, _, _ = res_mes_pasado
    assert f_ini_mp.date() < hoy
    assert f_fin_mp.date() < hoy
    assert f_ini_mp.day == 1

    # 3. Prueba 'historico'
    res_hist = ai_service._resolver_intencion_heuristica("dame todo el historico de atenciones")
    assert res_hist is not None
    f_inicio_h, f_fin_h, formato_h, modulos_h = res_hist
    assert f_inicio_h.date() == date(2020, 1, 1)

    # 4. Prueba formato 'pdf'
    res_pdf = ai_service._resolver_intencion_heuristica("genera un informe en pdf del mes actual")
    assert res_pdf is not None
    _, _, formato_pdf, _ = res_pdf
    assert formato_pdf == "pdf"

def test_heuristica_anio_especifico_y_sin_alucinaciones():
    """Valida la detección de años calendarios específicos y la respuesta 100% basada en datos reales."""
    prompt = "En el año 2026, se observa que las llamadas a ambulancias se concentran en sectores específicos"
    res = ai_service._resolver_intencion_heuristica(prompt)
    assert res is not None
    f_ini, f_fin, formato, modulos = res
    assert f_ini.date() == date(2026, 1, 1)
    assert f_fin.date() == date(2026, 12, 31)
    assert modulos == ["ambulancias"]

    # Simular estadísticas reales
    stats_prueba = {
        "periodo": "Desde 2026-01-01 hasta 2026-12-31",
        "ambulancias_total": 204,
        "ambulancias_top_sectores": [
            {"sector": "PEAJE EL CONGOMA", "atenciones": 73, "porcentaje": "35.8%"},
            {"sector": "GASOLINERA TERPEL", "atenciones": 19, "porcentaje": "9.3%"}
        ],
        "ambulancias_top_incidentes": [
            {"tipo": "Trauma", "cantidad": 139, "porcentaje": "68.1%"},
            {"tipo": "Clinico", "cantidad": 32, "porcentaje": "15.7%"}
        ],
        "ambulancias_severidad": {"LEVE": 169, "GRAVE": 26, "FATAL": 9}
    }

    # Verificar que el respaldo no alucine con clima o curvas
    resp_directa = ai_service._generar_respuesta_directa_respaldo(prompt, stats_prueba)
    assert "niebla" not in resp_directa.lower()
    assert "lluvia" not in resp_directa.lower()
    assert "curvas cerradas" not in resp_directa.lower()
    assert "pendientes prolongadas" not in resp_directa.lower()
    assert "PEAJE EL CONGOMA" in resp_directa
    assert "35.8%" in resp_directa
    assert "Trauma" in resp_directa

    # Verificar generación de gráfico
    grafico = pdf_service._generar_grafico_operaciones(stats_prueba)
    assert grafico is not None

def test_openai_compatible_endpoints_for_open_webui(monkeypatch):
    """Valida los endpoints compatibles con OpenAI (/models y /chat/completions) para conectar Open WebUI con SQL Server."""
    # 1. Test GET /api/v1/ai/models
    res_models = client.get("/api/v1/ai/models")
    assert res_models.status_code == 200
    models_data = res_models.json()
    assert "data" in models_data
    assert any(m["id"] == "vialbot-sql" for m in models_data["data"])

    # 2. Test POST /api/v1/ai/chat/completions con mock
    async def mock_procesar_peticion(*args, **kwargs):
        return {
            "solicita_exportacion": False,
            "respuesta_ia": "Se registraron 204 atenciones médicas en el año 2026.",
            "datos_crudos": {},
            "estadisticas": {"periodo": "Año 2026"}
        }

    monkeypatch.setattr(ai_service, "procesar_peticion", mock_procesar_peticion)

    res_chat = client.post(
        "/api/v1/ai/chat/completions",
        json={
            "model": "vialbot-sql",
            "messages": [
                {"role": "user", "content": "Cuantas ambulancias atendieron en 2026?"}
            ]
        }
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert "choices" in chat_data
    assert len(chat_data["choices"]) > 0
    assert "204 atenciones" in chat_data["choices"][0]["message"]["content"]
