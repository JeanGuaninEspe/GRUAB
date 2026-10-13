"""
Pruebas unitarias para la capa de servicios de operaciones y catálogos.
"""
from datetime import datetime, date, time
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from app.services.operaciones_service import OperacionesService
from app.services.catalogos_service import CatalogosService
from app.schemas.operaciones import (
    AmbulanciaCreate,
    GruaCreate,
    PatrullajeCreate,
    TurnoEnum,
    SentidoEnum,
    SeveridadEnum,
    TipoGruaEnum,
    GruaRead,
)


def test_catalogos_service_listar_personal():
    service = CatalogosService()
    mock_db = MagicMock()
    mock_personal = [
        MagicMock(id_personal=1, nombre_completo="Carlos Diaz", rol="SUPERVISOR", activo=True),
        MagicMock(id_personal=2, nombre_completo="Ana Lopez", rol="PARAMEDICO", activo=True),
    ]

    with patch("app.services.catalogos_service.personal_repo.get_personal", return_value=mock_personal):
        res = service.listar_personal(db=mock_db, rol="SUPERVISOR")
        assert len(res) == 2
        assert res[0].nombre_completo == "Carlos Diaz"
        assert res[0].rol == "SUPERVISOR"


def test_catalogos_service_listar_vehiculos():
    service = CatalogosService()
    mock_db = MagicMock()
    mock_vehiculos = [
        MagicMock(id_vehiculo=1, codigo_interno="AMB-01", placa="PBA-1001", tipo_flota="AMBULANCIA", descripcion="Mercedes Sprinter", activo=True)
    ]

    with patch("app.services.catalogos_service.vehiculo_repo.get_vehiculos", return_value=mock_vehiculos):
        res = service.listar_vehiculos(db=mock_db, tipo_flota="AMBULANCIA")
        assert len(res) == 1
        assert res[0].codigo_interno == "AMB-01"


def test_operaciones_service_conflicto_codigo_ambulancia():
    service = OperacionesService()
    mock_db = MagicMock()

    payload = AmbulanciaCreate(
        codigo_formulario="AMB-DUP-01",
        id_supervisor=1,
        id_paramedico=2,
        id_chofer=3,
        id_vehiculo=1,
        turno=TurnoEnum.TURNO_1,
        ts_llamada=datetime(2026, 8, 1, 10, 0),
        ts_arribo=datetime(2026, 8, 1, 10, 15),
        ts_termino=datetime(2026, 8, 1, 10, 45),
        ts_retorno=datetime(2026, 8, 1, 11, 20),
        sector_referencia="Km 10",
        abscisa_km=Decimal("10.0"),
        sentido=SentidoEnum.ASCENDENTE,
        motivo_atencion="Siniestro",
        severidad=SeveridadEnum.GRAVE,
        odometro_salida_km=Decimal("100.0"),
        odometro_llegada_km=Decimal("150.0"),
    )

    with patch("app.services.operaciones_service.operaciones_repo.get_ambulancia_by_codigo", return_value=MagicMock()):
        with pytest.raises(HTTPException) as exc:
            service.registrar_ambulancia(db=mock_db, data=payload)
        assert exc.value.status_code == 409
        assert "ya se encuentra registrado" in exc.value.detail


def test_operaciones_service_personal_inactivo():
    service = OperacionesService()
    mock_db = MagicMock()

    payload = AmbulanciaCreate(
        codigo_formulario="AMB-NEW-01",
        id_supervisor=1,
        id_paramedico=2,
        id_chofer=3,
        id_vehiculo=1,
        turno=TurnoEnum.TURNO_1,
        ts_llamada=datetime(2026, 8, 1, 10, 0),
        ts_arribo=datetime(2026, 8, 1, 10, 15),
        ts_termino=datetime(2026, 8, 1, 10, 45),
        ts_retorno=datetime(2026, 8, 1, 11, 20),
        sector_referencia="Km 10",
        abscisa_km=Decimal("10.0"),
        sentido=SentidoEnum.ASCENDENTE,
        motivo_atencion="Siniestro",
        severidad=SeveridadEnum.LEVE,
        odometro_salida_km=Decimal("100.0"),
        odometro_llegada_km=Decimal("150.0"),
    )

    mock_inactive_user = MagicMock(id_personal=1, nombre_completo="Supervisor Inactivo", activo=False)

    with patch("app.services.operaciones_service.operaciones_repo.get_ambulancia_by_codigo", return_value=None):
        with patch("app.services.operaciones_service.personal_repo.get_by_id", return_value=mock_inactive_user):
            with pytest.raises(HTTPException) as exc:
                service.registrar_ambulancia(db=mock_db, data=payload)
            assert exc.value.status_code == 400
            assert "no se encuentra activo" in exc.value.detail


def test_operaciones_service_listar_gruas_con_campos_nulos():
    service = OperacionesService()
    mock_db = MagicMock()

    mock_grua = MagicMock(
        id_asistencia_grua=1,
        codigo_formulario="GRU-HIST-001",
        id_supervisor=1,
        id_chofer=2,
        id_vehiculo=None,  # Vehículo NULL en BD histórica
        turno=None,
        tipo_grua="PLATAFORMA",
        ts_llamada=datetime(2026, 8, 1, 12, 0),
        ts_arribo=None,
        ts_termino=None,
        ts_retorno=None,
        sector_referencia="Km 30",
        abscisa_km=Decimal("30.0"),
        sentido="ASCENDENTE",
        usuario_reporta=None,
        placa_asistida="ABC-1234",
        tipo_vehiculo_asistido=None,
        usuarios_atendidos=1,
        motivo_atencion="Avería",
        tipo_accidente=None,
        posible_causa=None,
        severidad=None,
        km_origen_traslado=None,
        km_destino_traslado=None,
        odometro_salida_km=None,
        odometro_llegada_km=None,
        km_recorridos=None,
        reportado_mtop=False,
        observaciones="Grúa externa contratada",
    )

    with patch("app.services.operaciones_service.operaciones_repo.get_gruas", return_value=[mock_grua]):
        res = service.listar_gruas(db=mock_db)
        assert len(res) == 1
        assert res[0].id_asistencia_grua == 1
        assert res[0].id_vehiculo is None
        assert res[0].codigo_formulario == "GRU-HIST-001"
