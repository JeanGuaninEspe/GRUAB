import json
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_service import ai_service
from app.core.database import SessionLocal
from app.repositories.analitica_repo import analitica_repo
from app.repositories.operaciones_repo import operaciones_repo

client = TestClient(app)


def test_endpoint_consultar_schema_response():
    """
    Verifica que el endpoint POST /api/v1/ai/consultar responda con el esquema exacto:
    - respuesta (str)
    - accion_ejecutada (str)
    - datos_fuente (list o dict)
    """
    response = client.post(
        "/api/v1/ai/consultar",
        json={"pregunta": "Hola, ¿cómo puedes ayudarme?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "respuesta" in data
    assert "accion_ejecutada" in data
    assert "datos_fuente" in data
    assert isinstance(data["respuesta"], str)
    assert len(data["respuesta"]) > 0


@pytest.mark.anyio
async def test_fase1_extraccion_json_cuantas_ambulancias_hoy():
    """
    Criterio de Aceptación 1:
    Si se pregunta '¿Cuántas ambulancias atendieron hoy?',
    el sistema extrae accion='resumen_operativo', parametros={'tipo_servicio': 'ambulancia'}.
    """
    db = SessionLocal()
    try:
        # Mock de Ollama para simular la respuesta de Qwen 2.5 7B en Fase 1 y Fase 3
        mock_resp_f1 = MagicMock()
        mock_resp_f1.status_code = 200
        mock_resp_f1.json.return_value = {
            "message": {
                "content": json.dumps({
                    "accion": "resumen_operativo",
                    "parametros": {
                        "tipo_servicio": "ambulancia",
                        "zona": None,
                        "estado": None,
                        "fecha_inicio": "2026-10-13",
                        "fecha_fin": "2026-10-13",
                        "id_o_placa": None
                    }
                })
            }
        }

        mock_resp_f3 = MagicMock()
        mock_resp_f3.status_code = 200
        mock_resp_f3.json.return_value = {
            "message": {
                "content": "El día de hoy se registraron 0 atenciones de ambulancia según los registros oficiales."
            }
        }

        with patch("httpx.AsyncClient.post", side_effect=[mock_resp_f1, mock_resp_f3]) as mock_post:
            res = await ai_service.consultar(
                pregunta="¿Cuántas ambulancias atendieron hoy?",
                db=db
            )

            # Verificar que Fase 1 y Fase 3 usen estrictamente temperature=0.0
            assert mock_post.call_count == 2
            for call_args in mock_post.call_args_list:
                payload = call_args.kwargs.get("json") or call_args[1].get("json")
                assert payload["options"]["temperature"] == 0.0

            assert res["accion_ejecutada"] == "analitica_repo.get_resumen_operativo"
            assert isinstance(res["datos_fuente"], dict)
            assert "total_ambulancias" in res["datos_fuente"]
            assert "0 atenciones" in res["respuesta"] or "0" in res["respuesta"]
    finally:
        db.close()


@pytest.mark.anyio
async def test_fase1_fallback_json_malformado_no_rompe_api():
    """
    Requerimiento D:
    Si el LLM devuelve un JSON malformado en Fase 1, implementar un fallback determinista
    con try/except que no rompa la API y devuelva un mensaje de error claro solicitando reformular.
    """
    db = SessionLocal()
    try:
        mock_resp_bad = MagicMock()
        mock_resp_bad.status_code = 200
        mock_resp_bad.json.return_value = {
            "message": {
                "content": "Esto no es un JSON {accion: rota, parametro sin cerrar"
            }
        }

        with patch("httpx.AsyncClient.post", return_value=mock_resp_bad):
            res = await ai_service.consultar(
                pregunta="Texto extraño que produce un error en el modelo",
                db=db
            )

            assert res["accion_ejecutada"] == "error_clasificacion"
            assert res["datos_fuente"] is None
            assert "reformule su pregunta" in res["respuesta"]
    finally:
        db.close()


@pytest.mark.anyio
async def test_fase2_buscar_vehiculo_inexistente_criterio_aceptacion():
    """
    Criterio de Aceptación 2:
    Si se pregunta por un vehículo inexistente, el sistema responde que no existe
    registro en la base de datos, sin inventar historias o datos ficticios.
    """
    db = SessionLocal()
    try:
        mock_resp_f1 = MagicMock()
        mock_resp_f1.status_code = 200
        mock_resp_f1.json.return_value = {
            "message": {
                "content": json.dumps({
                    "accion": "buscar_unidad",
                    "parametros": {
                        "tipo_servicio": "todos",
                        "id_o_placa": "XYZ-9999",
                        "zona": None,
                        "estado": None,
                        "fecha_inicio": None,
                        "fecha_fin": None
                    }
                })
            }
        }

        mock_resp_f3 = MagicMock()
        mock_resp_f3.status_code = 200
        mock_resp_f3.json.return_value = {
            "message": {
                "content": "No constan registros en el sistema para el vehículo con placa XYZ-9999."
            }
        }

        with patch("httpx.AsyncClient.post", side_effect=[mock_resp_f1, mock_resp_f3]) as mock_post:
            res = await ai_service.consultar(
                pregunta="¿Dónde está el vehículo con placa XYZ-9999?",
                db=db
            )

            # Verificar que la consulta a SQL arrojó lista vacía y se inyectó el aviso estricto
            assert res["accion_ejecutada"] == "operaciones_repo.buscar_unidad"
            assert res["datos_fuente"] == []

            # Verificar el prompt cerrado enviado en Fase 3
            fase3_call = mock_post.call_args_list[1]
            fase3_payload = fase3_call.kwargs.get("json") or fase3_call[1].get("json")
            user_msg = fase3_payload["messages"][0]["content"]
            assert "DATOS: No se encontraron registros coincidentes en la base de datos." in user_msg
            assert "No inventes números, placas, horas, operarios ni diagnósticos" in user_msg
            assert "No constan registros" in res["respuesta"]
    finally:
        db.close()


@pytest.mark.anyio
async def test_fase2_buscar_vehiculo_existente_devuelve_datos_reales():
    """
    Verifica que la búsqueda de una unidad existente devuelva los datos reales de SQL Server.
    """
    db = SessionLocal()
    try:
        res = operaciones_repo.buscar_unidad(db, "AMB-01")
        assert len(res) >= 1
        item = res[0]
        assert item["codigo_interno"] == "AMB-01"
        assert item["placa"] == "AMB-0101"
        assert item["tipo_flota"] == "AMBULANCIA"
    finally:
        db.close()


@pytest.mark.anyio
async def test_fase2_resumen_operativo_sql_counts():
    """
    Verifica que analitica_repo.get_resumen_operativo retorne los conteos exactos de la BD.
    """
    db = SessionLocal()
    try:
        res = analitica_repo.get_resumen_operativo(db, tipo_servicio="ambulancia")
        assert "total_ambulancias" in res
        assert res["total_ambulancias"] >= 0

        res_gru = analitica_repo.get_resumen_operativo(db, tipo_servicio="grua")
        assert "total_gruas" in res_gru
        assert res_gru["total_gruas"] >= 0
    finally:
        db.close()


def test_endpoint_post_consultar_vehiculo_inexistente_integration():
    """
    Prueba de integración en el endpoint POST /api/v1/ai/consultar
    con vehículo inexistente.
    """
    response = client.post(
        "/api/v1/ai/consultar",
        json={"pregunta": "¿Qué información hay sobre el vehículo con placa FAKE-0000?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["accion_ejecutada"] == "operaciones_repo.buscar_unidad"
    assert data["datos_fuente"] == []
    # La respuesta debe indicar que no constan registros
    assert any(term in data["respuesta"].lower() for term in ["no constan", "no se encontraron", "no existe"])


def test_endpoint_parsear_despacho():
    """
    Verifica que POST /api/v1/ai/parsear-despacho devuelva la estructura normalizada
    incluso si se activa el fallback o se conecta a Qwen 2.5 7B.
    """
    response = client.post(
        "/api/v1/ai/parsear-despacho",
        json={"texto_reporte": "Despacho urgente grúa en Km 18 sentido ascendente, auto varado con placa PCA-1234 por recalentamiento de motor."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "tipo_asistencia" in data
    assert "ubicacion_referencia" in data
    assert "tramo_ruta" in data
    assert "abscisa_km" in data
    assert "sentido" in data
    assert "prioridad" in data
    assert "descripcion_falla_o_motivo" in data
    assert "placa_vehiculo" in data
    assert data["tipo_asistencia"] == "grua"


def test_endpoint_diagnostico_dashboard():
    """
    Verifica que POST /api/v1/ai/diagnostico-dashboard devuelva resumen y metricas_base.
    """
    response = client.post(
        "/api/v1/ai/diagnostico-dashboard",
        json={"fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "resumen" in data
    assert "metricas_base" in data
    assert isinstance(data["resumen"], str)
    assert len(data["resumen"]) > 0
    assert isinstance(data["metricas_base"], dict)

