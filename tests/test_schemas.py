"""
Pruebas unitarias para esquemas y validaciones de Pydantic v2.
"""
from datetime import datetime, date, time
from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas.operaciones import (
    AmbulanciaCreate,
    GruaCreate,
    PatrullajeCreate,
    TurnoEnum,
    SentidoEnum,
    SeveridadEnum,
    TipoGruaEnum,
)


def test_ambulancia_create_valido():
    payload = {
        "codigo_formulario": "AMB-2026-001",
        "id_supervisor": 1,
        "id_paramedico": 2,
        "id_chofer": 3,
        "id_vehiculo": 1,
        "turno": TurnoEnum.TURNO_1,
        "ts_llamada": datetime(2026, 8, 1, 10, 0, 0),
        "ts_arribo": datetime(2026, 8, 1, 10, 15, 0),
        "ts_termino": datetime(2026, 8, 1, 10, 45, 0),
        "ts_retorno": datetime(2026, 8, 1, 11, 20, 0),
        "sector_referencia": "Km 25 Tramo Norte",
        "abscisa_km": Decimal("25.500"),
        "sentido": SentidoEnum.ASCENDENTE,
        "motivo_atencion": "Colisión lateral",
        "severidad": SeveridadEnum.LEVE,
        "odometro_salida_km": Decimal("15000.00"),
        "odometro_llegada_km": Decimal("15045.50"),
    }
    schema = AmbulanciaCreate(**payload)
    assert schema.codigo_formulario == "AMB-2026-001"
    assert schema.odometro_llegada_km > schema.odometro_salida_km


def test_ambulancia_error_cronologia_timestamps():
    payload = {
        "codigo_formulario": "AMB-2026-002",
        "id_supervisor": 1,
        "id_paramedico": 2,
        "id_chofer": 3,
        "id_vehiculo": 1,
        "turno": TurnoEnum.TURNO_1,
        "ts_llamada": datetime(2026, 8, 1, 10, 30, 0),
        "ts_arribo": datetime(2026, 8, 1, 10, 15, 0),  # Arribo anterior a llamada
        "ts_termino": datetime(2026, 8, 1, 10, 45, 0),
        "ts_retorno": datetime(2026, 8, 1, 11, 20, 0),
        "sector_referencia": "Km 25",
        "abscisa_km": Decimal("25.500"),
        "sentido": SentidoEnum.ASCENDENTE,
        "motivo_atencion": "Colisión",
        "severidad": SeveridadEnum.LEVE,
        "odometro_salida_km": Decimal("15000.00"),
        "odometro_llegada_km": Decimal("15045.50"),
    }
    with pytest.raises(ValidationError) as exc:
        AmbulanciaCreate(**payload)
    assert "ts_arribo" in str(exc.value)


def test_ambulancia_error_odometro_invalido():
    payload = {
        "codigo_formulario": "AMB-2026-003",
        "id_supervisor": 1,
        "id_paramedico": 2,
        "id_chofer": 3,
        "id_vehiculo": 1,
        "turno": TurnoEnum.TURNO_1,
        "ts_llamada": datetime(2026, 8, 1, 10, 0, 0),
        "ts_arribo": datetime(2026, 8, 1, 10, 15, 0),
        "ts_termino": datetime(2026, 8, 1, 10, 45, 0),
        "ts_retorno": datetime(2026, 8, 1, 11, 20, 0),
        "sector_referencia": "Km 25",
        "abscisa_km": Decimal("25.500"),
        "sentido": SentidoEnum.ASCENDENTE,
        "motivo_atencion": "Colisión",
        "severidad": SeveridadEnum.LEVE,
        "odometro_salida_km": Decimal("15000.00"),
        "odometro_llegada_km": Decimal("14900.00"),  # Menor que salida
    }
    with pytest.raises(ValidationError) as exc:
        AmbulanciaCreate(**payload)
    assert "odómetro de llegada" in str(exc.value)


def test_grua_create_valido():
    payload = {
        "codigo_formulario": "GRU-2026-001",
        "id_supervisor": 1,
        "id_chofer": 4,
        "id_vehiculo": 2,
        "turno": TurnoEnum.TURNO_2,
        "tipo_grua": TipoGruaEnum.PLATAFORMA,
        "ts_llamada": datetime(2026, 8, 1, 14, 0, 0),
        "ts_arribo": datetime(2026, 8, 1, 14, 20, 0),
        "ts_termino": datetime(2026, 8, 1, 15, 0, 0),
        "ts_retorno": datetime(2026, 8, 1, 15, 45, 0),
        "sector_referencia": "Km 40 Peaje",
        "abscisa_km": Decimal("40.000"),
        "sentido": SentidoEnum.DESCENDENTE,
        "placa_asistida": "PBC-1234",
        "motivo_atencion": "Avería de embrague",
        "odometro_salida_km": Decimal("50000.00"),
        "odometro_llegada_km": Decimal("50060.00"),
    }
    schema = GruaCreate(**payload)
    assert schema.codigo_formulario == "GRU-2026-001"


def test_patrullaje_create_valido():
    payload = {
        "codigo_patrullaje": "PAT-2026-001",
        "id_supervisor": 1,
        "id_chofer": 5,
        "id_vehiculo": 3,
        "fecha_recorrido": date(2026, 8, 1),
        "hora_salida": time(8, 0, 0),
        "hora_retorno": time(16, 0, 0),
        "ruta_descripcion": "Recorrido integral tramo central Km 0 al Km 80",
        "odometro_inicial_km": Decimal("80000.00"),
        "odometro_final_km": Decimal("80160.00"),
        "novedad_en_via": True,
        "observaciones": "Presencia de derrumbe menor en Km 32. Vía señalizada.",
    }
    schema = PatrullajeCreate(**payload)
    assert schema.codigo_patrullaje == "PAT-2026-001"
