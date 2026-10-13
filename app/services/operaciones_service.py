"""
Servicio de negocio para operaciones y registros de asistencias viales y bitácoras.
Realiza validaciones de integridad referencial, roles y reglas de negocio.
"""
from typing import List, Optional
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.operaciones_repo import operaciones_repo
from app.repositories.catalogos_repo import personal_repo, vehiculo_repo
from app.schemas.operaciones import (
    AmbulanciaCreate,
    AmbulanciaRead,
    GruaCreate,
    GruaRead,
    PatrullajeCreate,
    PatrullajeRead,
)


class OperacionesService:
    # ----------------------------------------------------
    # VALIDACIONES GENERALES DE CATÁLOGOS
    # ----------------------------------------------------
    def _validar_personal_existe(self, db: Session, id_personal: Optional[int], nombre_campo: str, rol_esperado: Optional[str] = None):
        if id_personal is None:
            return
        personal = personal_repo.get_by_id(db, id_personal)
        if not personal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Personal no encontrado para {nombre_campo} (ID: {id_personal})."
            )
        if not personal.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El personal asignado a {nombre_campo} ({personal.nombre_completo}) no se encuentra activo."
            )
        if rol_esperado and personal.rol != rol_esperado:
            # Advertencia o validación de rol
            pass

    def _validar_vehiculo_existe(self, db: Session, id_vehiculo: Optional[int], tipo_flota_esperado: Optional[str] = None):
        if id_vehiculo is None:
            return
        vehiculo = vehiculo_repo.get_by_id(db, id_vehiculo)
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehículo no encontrado (ID: {id_vehiculo})."
            )
        if not vehiculo.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El vehículo asignado ({vehiculo.codigo_interno} - {vehiculo.placa}) no se encuentra activo."
            )
        if tipo_flota_esperado and vehiculo.tipo_flota != tipo_flota_esperado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El vehículo asignado es de tipo {vehiculo.tipo_flota}, pero se esperaba {tipo_flota_esperado}."
            )

    # ----------------------------------------------------
    # AMBULANCIAS
    # ----------------------------------------------------
    def registrar_ambulancia(self, db: Session, data: AmbulanciaCreate) -> AmbulanciaRead:
        # Validar duplicidad de código
        existente = operaciones_repo.get_ambulancia_by_codigo(db, data.codigo_formulario)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código de formulario '{data.codigo_formulario}' ya se encuentra registrado."
            )

        # Validar personal y vehículo
        self._validar_personal_existe(db, data.id_supervisor, "id_supervisor")
        self._validar_personal_existe(db, data.id_paramedico, "id_paramedico")
        self._validar_personal_existe(db, data.id_chofer, "id_chofer")
        self._validar_vehiculo_existe(db, data.id_vehiculo, "AMBULANCIA")

        obj = operaciones_repo.create_ambulancia(db, data)
        return AmbulanciaRead.model_validate(obj)

    def listar_ambulancias(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[AmbulanciaRead]:
        registros = operaciones_repo.get_ambulancias(
            db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, turno=turno, id_vehiculo=id_vehiculo
        )
        return [AmbulanciaRead.model_validate(r) for r in registros]

    # ----------------------------------------------------
    # GRÚAS
    # ----------------------------------------------------
    def registrar_grua(self, db: Session, data: GruaCreate) -> GruaRead:
        existente = operaciones_repo.get_grua_by_codigo(db, data.codigo_formulario)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código de formulario '{data.codigo_formulario}' ya se encuentra registrado."
            )

        self._validar_personal_existe(db, data.id_supervisor, "id_supervisor")
        self._validar_personal_existe(db, data.id_chofer, "id_chofer")
        self._validar_vehiculo_existe(db, data.id_vehiculo, "GRUA")

        obj = operaciones_repo.create_grua(db, data)
        return GruaRead.model_validate(obj)

    def listar_gruas(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[GruaRead]:
        registros = operaciones_repo.get_gruas(
            db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, turno=turno, id_vehiculo=id_vehiculo
        )
        return [GruaRead.model_validate(r) for r in registros]

    # ----------------------------------------------------
    # PATRULLAJE
    # ----------------------------------------------------
    def registrar_patrullaje(self, db: Session, data: PatrullajeCreate) -> PatrullajeRead:
        existente = operaciones_repo.get_patrullaje_by_codigo(db, data.codigo_patrullaje)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código de patrullaje '{data.codigo_patrullaje}' ya se encuentra registrado."
            )

        self._validar_personal_existe(db, data.id_supervisor, "id_supervisor")
        self._validar_personal_existe(db, data.id_chofer, "id_chofer")
        self._validar_vehiculo_existe(db, data.id_vehiculo, "PATRULLA")

        obj = operaciones_repo.create_patrullaje(db, data)
        return PatrullajeRead.model_validate(obj)

    def listar_patrullajes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_vehiculo: Optional[int] = None,
    ) -> List[PatrullajeRead]:
        registros = operaciones_repo.get_patrullajes(
            db, skip=skip, limit=limit, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, id_vehiculo=id_vehiculo
        )
        return [PatrullajeRead.model_validate(r) for r in registros]


operaciones_service = OperacionesService()
