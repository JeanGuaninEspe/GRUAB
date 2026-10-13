import pytest
from datetime import date, datetime
from app.services.ai_service import ai_service, ajustar_porcentajes_a_100


def test_extraccion_temporal_enero_a_julio():
    """Verifica que 'enero a julio' resuelva exactamente desde el 1 de enero hasta el 31 de julio con microsegundos."""
    frases = [
        "enero a julio",
        "de enero a julio",
        "desde enero hasta julio",
        "entre enero y julio",
        "enero a julio 2026",
        "de enero a julio de 2026",
        "enero - julio 2026",
    ]
    for f in frases:
        res = ai_service._resolver_intencion_heuristica(f)
        assert res is not None, f"Fallo al resolver la frase: {f}"
        dt_ini, dt_fin, fmt, mods = res
        assert dt_ini.month == 1
        assert dt_ini.day == 1
        assert dt_ini.hour == 0 and dt_ini.minute == 0 and dt_ini.second == 0
        assert dt_fin.month == 7
        assert dt_fin.day == 31
        assert dt_fin.hour == 23 and dt_fin.minute == 59 and dt_fin.second == 59


def test_extraccion_temporal_semestre_y_trimestre():
    """Verifica la resolución de semestres y trimestres."""
    res_sem = ai_service._resolver_intencion_heuristica("primer semestre 2026")
    assert res_sem is not None
    dt_i, dt_f, _, _ = res_sem
    assert dt_i.year == 2026 and dt_i.month == 1 and dt_i.day == 1
    assert dt_f.year == 2026 and dt_f.month == 6 and dt_f.day == 30

    res_tri = ai_service._resolver_intencion_heuristica("3er trimestre 2026")
    assert res_tri is not None
    dt_i, dt_f, _, _ = res_tri
    assert dt_i.month == 7 and dt_f.month == 9 and dt_f.day == 30


def test_aviso_disponibilidad_cuando_faltan_meses():
    """
    Verifica que si se solicita un rango (ej: enero a julio) pero la base de datos
    solo tiene registros para enero y febrero, se active el aviso explícito de disponibilidad.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 7, 31, 23, 59, 59, 999999)

    # Datos simulados solo en enero y febrero
    datos_crudos = {
        "gruas": [
            {"fecha": "2026-01-15", "motivo": "Falla mecánica", "sector": "KM 10"},
            {"fecha": "2026-02-20", "motivo": "Colisión", "sector": "PEAJE EL CONGOMA"}
        ],
        "ambulancias": [],
        "patrullajes": []
    }

    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)

    assert stats.get("aviso_disponibilidad") is not None
    aviso = stats["aviso_disponibilidad"]
    assert "Aviso de disponibilidad: Solo se encontraron datos entre" in aviso
    assert "15/01/2026" in aviso
    assert "20/02/2026" in aviso


def test_cuadre_matematico_y_cierre_100():
    """
    Verifica que la agregación por tipología agrupe categorías huérfanas bajo 'Otros / No especificado'
    y que la suma de cantidades y porcentajes sea matemáticamente exacta al total general y 100.0%.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 1, 31, 23, 59, 59)

    # Simular 176 eventos con 7 categorías diferentes y nulos
    gruas = []
    # 80 Falla mecánica
    gruas.extend([{"fecha": "2026-01-05", "motivo": "Falla mecánica", "sector": "KM 1"}] * 80)
    # 50 Choque
    gruas.extend([{"fecha": "2026-01-06", "motivo": "Choque", "sector": "KM 2"}] * 50)
    # 30 Neumático
    gruas.extend([{"fecha": "2026-01-07", "motivo": "Neumático", "sector": "KM 3"}] * 30)
    # 9 Batería
    gruas.extend([{"fecha": "2026-01-08", "motivo": "Batería", "sector": "KM 4"}] * 9)
    # 4 Volcamiento (cola / huérfana)
    gruas.extend([{"fecha": "2026-01-09", "motivo": "Volcamiento", "sector": "KM 5"}] * 4)
    # 2 Incendio (cola / huérfana)
    gruas.extend([{"fecha": "2026-01-10", "motivo": "Incendio", "sector": "KM 6"}] * 2)
    # 1 Nulo / sin motivo
    gruas.extend([{"fecha": "2026-01-11", "motivo": None, "sector": "KM 7"}] * 1)

    assert len(gruas) == 176

    datos_crudos = {"gruas": gruas, "ambulancias": [], "patrullajes": []}
    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)

    assert stats["gruas_total"] == 176
    motivos = stats["gruas_top_motivos"]

    # Suma de cantidades debe ser exactamente 176
    suma_cantidades = sum(m["cantidad"] for m in motivos)
    assert suma_cantidades == 176

    # Suma de porcentajes debe ser exactamente 100.0%
    suma_porcentajes = sum(float(m["porcentaje"].replace("%", "")) for m in motivos)
    assert round(suma_porcentajes, 1) == 100.0

    # Debe contener la categoría agrupada 'Otros / No especificado'
    nombres_motivos = [m["motivo"] for m in motivos]
    assert "Otros / No especificado" in nombres_motivos
    otros_item = next(m for m in motivos if m["motivo"] == "Otros / No especificado")
    assert otros_item["cantidad"] == (4 + 2 + 1)  # 7


def test_desglose_mensual_cuando_rango_multimes():
    """
    Verifica que al solicitar más de un mes se genere obligatoriamente el desglose mensual
    con formato Mes | Total | % sumando 100.0%.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 3, 31, 23, 59, 59)

    datos_crudos = {
        "gruas": [
            {"fecha": "2026-01-10", "motivo": "Falla", "sector": "S1"},
            {"fecha": "2026-01-15", "motivo": "Falla", "sector": "S1"},
            {"fecha": "2026-02-10", "motivo": "Falla", "sector": "S1"},
            {"fecha": "2026-03-20", "motivo": "Falla", "sector": "S1"},
        ],
        "ambulancias": [],
        "patrullajes": []
    }

    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)

    assert stats["rango_multimes"] is True
    desglose = stats["desglose_mensual"]
    assert len(desglose) == 3
    assert desglose[0]["mes"] == "Enero 2026"
    assert desglose[0]["total"] == 2
    assert desglose[1]["mes"] == "Febrero 2026"
    assert desglose[1]["total"] == 1
    assert desglose[2]["mes"] == "Marzo 2026"
    assert desglose[2]["total"] == 1

    suma_pct = sum(float(m["porcentaje"].replace("%", "")) for m in desglose)
    assert round(suma_pct, 1) == 100.0

    # Mes pico identificado
    assert stats["mes_pico"]["mes"] == "Enero 2026"
    assert stats["mes_pico"]["total"] == 2


def test_formato_sectores_cantidad_y_porcentaje():
    """
    Verifica que los sectores calculen tanto cantidad absoluta como porcentaje relativo:
    'Sector: Cantidad (XX.X%)' y que el Top 1 se identifique programáticamente.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 1, 31, 23, 59, 59)

    datos_crudos = {
        "gruas": [
            {"fecha": "2026-01-01", "motivo": "Falla", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-01-02", "motivo": "Falla", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-01-03", "motivo": "Falla", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-01-04", "motivo": "Falla", "sector": "GASOLINERA TERPEL"},
        ],
        "ambulancias": [],
        "patrullajes": []
    }

    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)

    sectores = stats["gruas_top_sectores"]
    assert sectores[0]["sector"] == "PEAJE EL CONGOMA"
    assert sectores[0]["cantidad"] == 3
    assert sectores[0]["porcentaje"] == "75.0%"
    assert sectores[0]["texto_completo"] == "PEAJE EL CONGOMA: 3 (75.0%)"

    # Top 1 programático
    assert stats["top_1_sector"]["sector"] == "PEAJE EL CONGOMA"
    assert stats["top_1_sector"]["cantidad"] == 3
    assert stats["top_1_tipologia"]["tipologia"] == "Falla"


def test_prompts_inyectan_tablas_y_rol_estricto():
    """
    Verifica que el System Prompt instruya a Qwen estrictamente a no sumar ni alterar cifras,
    y que el User Prompt contenga las tablas Markdown precalculadas.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 3, 31, 23, 59, 59)

    datos_crudos = {
        "gruas": [
            {"fecha": "2026-01-10", "motivo": "Falla mecánica", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-02-15", "motivo": "Colisión", "sector": "GASOLINERA TERPEL"}
        ],
        "ambulancias": [],
        "patrullajes": []
    }

    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)
    sys_p, usr_p = ai_service._construir_prompts_analisis("informe de enero a marzo 2026", stats, ["gruas"])

    # Verificaciones de System Prompt
    assert "REDACTOR ESTRATÉGICO, NUNCA CALCULADOR" in sys_p
    assert "TERMINANTEMENTE PROHIBIDO calcular sumas, porcentajes" in sys_p
    assert "Sector: Cantidad (XX.X%)" in sys_p
    assert "Recomendaciones operativas basadas estrictamente en datos reales" in sys_p.lower() or "RECOMENDACIONES OPERATIVAS" in sys_p

    # Verificaciones de User Prompt (debe tener las tablas Markdown)
    assert "| Mes | Total | % |" in usr_p
    assert "| Motivo de Asistencia (Grúas) | Cantidad | Incidencia (%) |" in usr_p
    assert "| Sector / Tramo Vial | Cantidad | Incidencia (%) |" in usr_p
    assert "PEAJE EL CONGOMA" in usr_p


def test_generador_respaldo_directo_coherencia_completa():
    """
    Verifica que el generador de respaldo en Python cumpla con todos los requisitos
    cuando el LLM no está disponible: tablas, sectores 'Sector: Cantidad (XX.X%)',
    desglose mensual y recomendaciones basadas en Top 1.
    """
    dt_ini = datetime(2026, 1, 1, 0, 0, 0)
    dt_fin = datetime(2026, 3, 31, 23, 59, 59)

    datos_crudos = {
        "gruas": [
            {"fecha": "2026-01-10", "motivo": "Falla mecánica", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-01-15", "motivo": "Falla mecánica", "sector": "PEAJE EL CONGOMA"},
            {"fecha": "2026-02-15", "motivo": "Neumático", "sector": "GASOLINERA TERPEL"}
        ],
        "ambulancias": [],
        "patrullajes": []
    }

    stats = ai_service._generar_resumen_estadistico(datos_crudos, dt_ini, dt_fin)
    informe = ai_service._generar_respuesta_directa_respaldo("informe enero a marzo", stats, ["gruas"])

    assert "### Informe Ejecutivo de Operaciones Viales" in informe
    assert "| Mes | Total | % |" in informe
    assert "| Motivo de Asistencia (Grúas) | Cantidad | Incidencia (%) |" in informe
    assert "| Sector / Tramo Vial | Cantidad | Incidencia (%) |" in informe
    assert "PEAJE EL CONGOMA" in informe
    assert "Falla mecánica" in informe
    # Formato de sector con cantidad y porcentaje (en prosa con negrita o en tabla)
    assert "**PEAJE EL CONGOMA**: 2 (66.7%)" in informe
    # Recomendaciones basadas en el Top 1
    assert "Posicionamiento Preventivo en Punto Crítico" in informe
    assert "Plan de Mitigación de Causa Principal" in informe
    assert "Refuerzo Operativo Estacional" in informe
