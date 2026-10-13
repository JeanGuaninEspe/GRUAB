import os
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_service import pdf_service, LOGO_PATH

client = TestClient(app)


def test_logo_file_exists():
    """Verifica que el logo oficial de COSAD exista en el proyecto."""
    assert os.path.exists(LOGO_PATH), f"No se encontró el logo oficial en {LOGO_PATH}"


def test_logo_endpoint():
    """Verifica que el endpoint /logo-cosad.webp sirva la imagen corporativa."""
    response = client.get("/logo-cosad.webp")
    assert response.status_code == 200
    assert "image/webp" in response.headers.get("content-type", "")
    assert len(response.content) > 0


def test_generar_informe_ia_pdf():
    """Verifica la generación del PDF de operaciones con gráficos embebidos y título limpio."""
    stats = {
        "periodo": "2024-01-01 a 2024-12-31",
        "ambulancias_total": 600,
        "gruas_total": 4000,
        "asistencias_totales_combinadas": 4600,
        "asistencias_top_tramos": [
            {"sector": "Sector El Chasqui", "asistencias_totales": 850, "porcentaje": "18.5%"},
            {"sector": "Sector Alóag", "asistencias_totales": 720, "porcentaje": "15.7%"}
        ],
        "gruas_top_motivos": [
            {"motivo": "Falla Mecánica", "cantidad": 2200, "porcentaje": "55.0%"},
            {"motivo": "Neumático Desinflado", "cantidad": 980, "porcentaje": "24.5%"}
        ]
    }
    texto_ia = (
        "### Resumen de Operaciones Viales\n"
        "Durante el período analizado se registraron **4,600 asistencias totales**.\n\n"
        "- **Ambulancias:** 600 atenciones prehospitalarias.\n"
        "- **Grúas:** 4,000 rescates viales.\n\n"
        "El tramo con mayor incidencia crítica corresponde al **Sector El Chasqui**."
    )

    pdf_buffer, filename = pdf_service.generar_informe_ia_pdf(
        respuesta_ia=texto_ia,
        estadisticas=stats
    )

    assert filename.startswith("informe_operaciones_asistencias_viales_")
    assert filename.endswith(".pdf")
    pdf_bytes = pdf_buffer.getvalue()
    # Con gráficos de matplotlib integrados en alta definición, el PDF debe superar los 15KB
    assert len(pdf_bytes) > 15000
    assert pdf_bytes.startswith(b"%PDF")


def test_exportar_pdf_directo_endpoint():
    """Verifica el endpoint POST /api/v1/ai/exportar-pdf."""
    payload = {
        "respuesta_ia": "Análisis de prueba para exportación directa en PDF.",
        "estadisticas": {
            "periodo": "Últimos 30 días",
            "ambulancias_total": 45,
            "gruas_total": 210,
            "asistencias_totales_combinadas": 255
        }
    }
    response = client.post("/api/v1/ai/exportar-pdf", json=payload)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert response.headers.get("X-Es-Reporte-Pdf") == "true"
    assert response.content.startswith(b"%PDF")


def test_exportar_reporte_mtop_pdf_endpoint():
    """Verifica el endpoint GET /api/v1/reportes-mtop/exportar-pdf con base de datos simulada."""
    mock_df = pd.DataFrame([
        {
            "FECHA": "2025-03-01",
            "CÓDIGO": "AMB-001",
            "SECTOR": "Sector El Chasqui",
            "KM": 42.5,
            "ESTADO PACIENTE": "ESTABLE",
            "MOTIVO": "Evaluación médica"
        }
    ])
    with patch("app.routers.reportes_mtop.reportes_repo.get_datos_mtop_df", return_value=mock_df):
        response = client.get("/api/v1/reportes-mtop/exportar-pdf?servicio=ambulancia&mes=3&anio=2025")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert "reporte_mtop_ambulancia_2025_03.pdf" in response.headers.get("content-disposition", "")
