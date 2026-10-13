"""
Servicio de negocio para la analítica avanzada de operaciones viales:
- KPIs de Tiempos de Respuesta
- Mapeo de Puntos Negros
- Modelo de Scoring de Peligrosidad e Identificación de Hotspots (Tramos Críticos)
- Análisis de Patrones Temporales y Horas Pico
- Algoritmo de Recomendación de Despliegue Táctico y Operativo
- Resumen Ejecutivo para la Toma de Decisiones
"""
import math
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from app.repositories.analitica_repo import analitica_repo
from app.schemas.analitica import (
    KPITiemposItem,
    KPIServicioResumen,
    KPITiemposRespuestaResponse,
    PuntoNegroItem,
    PuntosNegrosResponse,
    TramoScoringItem,
    TramosScoringResponse,
    NivelRiesgoEnum,
    PatronHoraItem,
    PatronDiaItem,
    PatronesTemporalesResponse,
    RecomendacionDespliegueItem,
    RecomendacionesDespliegueResponse,
    DashboardEjecutivoResponse,
)

DIAS_SEMANA_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}


class AnaliticaService:
    # ----------------------------------------------------
    # 1. TIEMPOS DE RESPUESTA Y KPIS
    # ----------------------------------------------------
    def obtener_kpis_tiempos_respuesta(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        limit: int = 500,
    ) -> KPITiemposRespuestaResponse:
        rows = analitica_repo.get_kpi_tiempos_atencion(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            limit=limit,
        )

        if not rows:
            return KPITiemposRespuestaResponse(
                total_registros=0,
                promedio_despacho_arribo_min=0.0,
                promedio_sitio_min=0.0,
                promedio_ciclo_total_min=0.0,
                total_km_recorridos=0.0,
                resumen_por_servicio=[],
                detalles=[],
            )

        detalles: List[KPITiemposItem] = []
        arribo_vals: List[float] = []
        sitio_vals: List[float] = []
        ciclo_vals: List[float] = []
        total_km = 0.0

        por_servicio: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            tipo_srv = str(row.get("tipo_servicio") or "DESCONOCIDO").upper()
            if tipo_srv not in por_servicio:
                por_servicio[tipo_srv] = {
                    "count": 0,
                    "arribo": [],
                    "sitio": [],
                    "ciclo": [],
                    "km": 0.0,
                }

            t_arribo = float(row["tiempo_despacho_arribo_min"]) if row.get("tiempo_despacho_arribo_min") is not None else None
            t_sitio = float(row["tiempo_en_sitio_min"]) if row.get("tiempo_en_sitio_min") is not None else None
            t_ciclo = float(row["ciclo_total_min"]) if row.get("ciclo_total_min") is not None else None
            km = float(row["km_recorridos"]) if row.get("km_recorridos") is not None else 0.0

            if t_arribo is not None:
                arribo_vals.append(t_arribo)
                por_servicio[tipo_srv]["arribo"].append(t_arribo)

            if t_sitio is not None:
                sitio_vals.append(t_sitio)
                por_servicio[tipo_srv]["sitio"].append(t_sitio)

            if t_ciclo is not None:
                ciclo_vals.append(t_ciclo)
                por_servicio[tipo_srv]["ciclo"].append(t_ciclo)

            total_km += km
            por_servicio[tipo_srv]["km"] += km
            por_servicio[tipo_srv]["count"] += 1

            detalles.append(KPITiemposItem.model_validate(row))

        avg_arribo = round(sum(arribo_vals) / len(arribo_vals), 2) if arribo_vals else 0.0
        avg_sitio = round(sum(sitio_vals) / len(sitio_vals), 2) if sitio_vals else 0.0
        avg_ciclo = round(sum(ciclo_vals) / len(ciclo_vals), 2) if ciclo_vals else 0.0

        resumen_servicios: List[KPIServicioResumen] = []
        for srv_name, data in por_servicio.items():
            srv_avg_arribo = round(sum(data["arribo"]) / len(data["arribo"]), 2) if data["arribo"] else 0.0
            srv_avg_sitio = round(sum(data["sitio"]) / len(data["sitio"]), 2) if data["sitio"] else 0.0
            srv_avg_ciclo = round(sum(data["ciclo"]) / len(data["ciclo"]), 2) if data["ciclo"] else 0.0

            resumen_servicios.append(
                KPIServicioResumen(
                    tipo_servicio=srv_name,
                    total_eventos=data["count"],
                    promedio_despacho_arribo_min=srv_avg_arribo,
                    promedio_sitio_min=srv_avg_sitio,
                    promedio_ciclo_total_min=srv_avg_ciclo,
                    total_km_recorridos=round(data["km"], 2),
                )
            )

        return KPITiemposRespuestaResponse(
            total_registros=len(rows),
            promedio_despacho_arribo_min=avg_arribo,
            promedio_sitio_min=avg_sitio,
            promedio_ciclo_total_min=avg_ciclo,
            total_km_recorridos=round(total_km, 2),
            resumen_por_servicio=resumen_servicios,
            detalles=detalles,
        )

    # ----------------------------------------------------
    # 2. PUNTOS NEGROS DE LA VISTA MTOP
    # ----------------------------------------------------
    def obtener_puntos_negros(
        self,
        db: Session,
        severidad: Optional[str] = None,
        causa: Optional[str] = None,
        sentido: Optional[str] = None,
        limit: int = 100,
    ) -> PuntosNegrosResponse:
        rows = analitica_repo.get_puntos_negros(
            db=db, severidad=severidad, causa=causa, sentido=sentido, limit=limit
        )

        tramos = [PuntoNegroItem.model_validate(r) for r in rows]
        total_eventos = sum(t.total_eventos for t in tramos)

        return PuntosNegrosResponse(
            total_tramos_criticos=len(tramos),
            total_eventos_acumulados=total_eventos,
            tramos=tramos,
        )

    # ----------------------------------------------------
    # 3. MODELO DE SCORING DE PELIGROSIDAD VIAL (HOTSPOTS)
    # ----------------------------------------------------
    def obtener_scoring_tramos_criticos(
        self,
        db: Session,
        tamano_tramo_km: float = 5.0,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
        top_n: int = 15,
    ) -> TramosScoringResponse:
        """
        Agrupa los eventos por intervalos de kilómetros (ej. cada 1km, 2km o 5km)
        y aplica el Modelo Ponderado de Criticidad Vial (ICV):
        ICV = (Fatales * 10) + (Graves * 5) + (Leves * 2) + (Remolques/Mecánicos * 1)
        """
        if tamano_tramo_km <= 0:
            tamano_tramo_km = 5.0

        eventos = analitica_repo.get_eventos_combinados(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            id_vehiculo=id_vehiculo,
        )

        if not eventos:
            return TramosScoringResponse(
                criterio_agrupacion_km=tamano_tramo_km,
                total_tramos_analizados=0,
                total_eventos_evaluados=0,
                resumen_niveles_riesgo={"EXTREMO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0},
                top_tramos_criticos=[],
            )

        # Agrupar eventos por tramo
        bins: Dict[int, List[Dict[str, Any]]] = {}
        for ev in eventos:
            km = ev.get("abscisa_km")
            if km is None:
                continue
            km_float = float(km)
            bin_idx = math.floor(km_float / tamano_tramo_km)
            if bin_idx not in bins:
                bins[bin_idx] = []
            bins[bin_idx].append(ev)

        tramos_scoring: List[TramoScoringItem] = []
        conteo_riesgo = {"EXTREMO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0}

        for bin_idx, ev_list in bins.items():
            km_inicio = round(bin_idx * tamano_tramo_km, 1)
            km_fin = round(km_inicio + tamano_tramo_km, 1)

            total_ev = len(ev_list)
            total_amb = sum(1 for e in ev_list if str(e.get("tipo_servicio")).upper() == "AMBULANCIA")
            total_gru = sum(1 for e in ev_list if str(e.get("tipo_servicio")).upper() == "GRUA")

            fatales = 0
            graves = 0
            leves = 0
            otros = 0

            sentidos: List[str] = []
            tipos_acc: List[str] = []
            causas: List[str] = []
            horas: List[int] = []

            for e in ev_list:
                sev = str(e.get("severidad") or "").upper()
                if "FATAL" in sev:
                    fatales += 1
                elif "GRAVE" in sev:
                    graves += 1
                elif "LEVE" in sev:
                    leves += 1
                else:
                    otros += 1

                if e.get("sentido"):
                    sentidos.append(str(e["sentido"]))
                if e.get("tipo_accidente"):
                    tipos_acc.append(str(e["tipo_accidente"]))
                if e.get("posible_causa"):
                    causas.append(str(e["posible_causa"]))
                elif e.get("motivo_atencion"):
                    causas.append(str(e["motivo_atencion"]))

                ts = e.get("ts_llamada")
                if isinstance(ts, datetime):
                    horas.append(ts.hour)

            # Fórmula ponderada del Índice de Criticidad Vial (ICV)
            icv = round((fatales * 10.0) + (graves * 5.0) + (leves * 2.0) + (otros * 1.0), 2)

            # Clasificación de Nivel de Riesgo
            if icv >= 35 or fatales >= 2:
                nivel = NivelRiesgoEnum.EXTREMO
            elif icv >= 18 or graves >= 3:
                nivel = NivelRiesgoEnum.ALTO
            elif icv >= 8:
                nivel = NivelRiesgoEnum.MEDIO
            else:
                nivel = NivelRiesgoEnum.BAJO

            conteo_riesgo[nivel.value] += 1

            sentido_top = Counter(sentidos).most_common(1)[0][0] if sentidos else "BIDIRECCIONAL"
            tipo_acc_top = Counter(tipos_acc).most_common(1)[0][0] if tipos_acc else "No clasificado"
            causa_top = Counter(causas).most_common(1)[0][0] if causas else "Falla mecánica o no especificada"

            # Determinar franja horaria más frecuente
            franja_top = "Variada"
            if horas:
                franja_counts = {
                    "Madrugada (00:00-06:00)": sum(1 for h in horas if 0 <= h < 6),
                    "Mañana (06:00-12:00)": sum(1 for h in horas if 6 <= h < 12),
                    "Tarde (12:00-18:00)": sum(1 for h in horas if 12 <= h < 18),
                    "Noche (18:00-24:00)": sum(1 for h in horas if 18 <= h < 24),
                }
                franja_top = max(franja_counts, key=franja_counts.get)

            # Generación de recomendación táctica automatizada
            recomendacion = self._generar_recomendacion_tramo(
                km_inicio, km_fin, nivel, fatales, graves, total_amb, total_gru, causa_top, franja_top
            )

            tramos_scoring.append(
                TramoScoringItem(
                    km_inicio=km_inicio,
                    km_fin=km_fin,
                    tramo_label=f"Km {km_inicio:.1f} - Km {km_fin:.1f}",
                    total_eventos=total_ev,
                    total_ambulancias=total_amb,
                    total_gruas=total_gru,
                    total_fatales=fatales,
                    total_graves=graves,
                    total_leves=leves,
                    indice_criticidad=icv,
                    nivel_riesgo=nivel,
                    sentido_predominante=sentido_top,
                    principal_tipo_accidente=tipo_acc_top,
                    principal_motivo_o_causa=causa_top,
                    franja_horaria_mayor_incidencia=franja_top,
                    recomendacion_tactica=recomendacion,
                )
            )

        # Ordenar por índice de criticidad descendente
        tramos_scoring.sort(key=lambda t: t.indice_criticidad, reverse=True)

        return TramosScoringResponse(
            criterio_agrupacion_km=tamano_tramo_km,
            total_tramos_analizados=len(tramos_scoring),
            total_eventos_evaluados=len(eventos),
            resumen_niveles_riesgo=conteo_riesgo,
            top_tramos_criticos=tramos_scoring[:top_n],
        )

    def _generar_recomendacion_tramo(
        self,
        km_ini: float,
        km_fin: float,
        nivel: NivelRiesgoEnum,
        fatales: int,
        graves: int,
        amb: int,
        gru: int,
        causa: str,
        franja: str,
    ) -> str:
        if nivel == NivelRiesgoEnum.EXTREMO:
            return (
                f"🚨 ALERTA CRÍTICA: Ubicar puesto permanente de ambulancia y patrullaje de choque en Km {km_ini:.1f}-{km_fin:.1f} "
                f"durante la franja {franja}. Revisar señalética reflectiva, radar de velocidad y peralte vial."
            )
        elif nivel == NivelRiesgoEnum.ALTO:
            if amb > gru:
                return (
                    f"⚠️ PREVENCIÓN SANITARIA: Reforzar recorrido de ambulancia y señalización luminosa en Km {km_ini:.1f}-{km_fin:.1f} "
                    f"en horario {franja} por incidencia de {causa}."
                )
            else:
                return (
                    f"⚠️ AUXILIO MECÁNICO: Posicionar grúa de retén cercana al Km {km_ini:.1f} en horario {franja} para despeje rápido de calzada."
                )
        elif nivel == NivelRiesgoEnum.MEDIO:
            return f"ℹ️ Monitoreo preventivo ordinario mediante patrulla de inspección en Km {km_ini:.1f}-{km_fin:.1f}."
        else:
            return "✅ Tramo seguro. Mantener inspección rutinaria."

    # ----------------------------------------------------
    # 4. PATRONES TEMPORALES Y HORARIOS PICO
    # ----------------------------------------------------
    def obtener_patrones_temporales(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> PatronesTemporalesResponse:
        eventos = analitica_repo.get_eventos_combinados(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            id_vehiculo=id_vehiculo,
        )

        total_ev = len(eventos)
        if total_ev == 0:
            return PatronesTemporalesResponse(
                total_eventos_analizados=0,
                hora_pico_maxima="N/A",
                dia_pico_maximo="N/A",
                eventos_fin_de_semana=0,
                eventos_entre_semana=0,
                porcentaje_fin_de_semana=0.0,
                distribucion_por_franja={"Madrugada (00-06h)": 0, "Mañana (06-12h)": 0, "Tarde (12-18h)": 0, "Noche (18-24h)": 0},
                distribucion_por_hora=[],
                distribucion_por_dia=[],
            )

        horas_counter: Dict[int, Dict[str, int]] = {
            h: {"total": 0, "amb": 0, "gru": 0, "graves": 0} for h in range(24)
        }
        dias_counter: Dict[int, Dict[str, int]] = {
            d: {"total": 0, "amb": 0, "gru": 0} for d in range(7)
        }

        franja_madrugada = 0
        franja_manana = 0
        franja_tarde = 0
        franja_noche = 0
        fin_semana_count = 0

        for e in eventos:
            ts = e.get("ts_llamada")
            if not isinstance(ts, datetime):
                continue

            h = ts.hour
            d = ts.weekday()  # 0 = Lunes, 6 = Domingo
            srv = str(e.get("tipo_servicio") or "").upper()
            sev = str(e.get("severidad") or "").upper()
            es_grave = "FATAL" in sev or "GRAVE" in sev

            horas_counter[h]["total"] += 1
            if srv == "AMBULANCIA":
                horas_counter[h]["amb"] += 1
            elif srv == "GRUA":
                horas_counter[h]["gru"] += 1
            if es_grave:
                horas_counter[h]["graves"] += 1

            dias_counter[d]["total"] += 1
            if srv == "AMBULANCIA":
                dias_counter[d]["amb"] += 1
            elif srv == "GRUA":
                dias_counter[d]["gru"] += 1

            if d in [4, 5, 6]:  # Viernes, Sábado, Domingo
                fin_semana_count += 1

            if 0 <= h < 6:
                franja_madrugada += 1
            elif 6 <= h < 12:
                franja_manana += 1
            elif 12 <= h < 18:
                franja_tarde += 1
            else:
                franja_noche += 1

        dist_horas: List[PatronHoraItem] = []
        for h in range(24):
            cnt = horas_counter[h]["total"]
            pct = round((cnt / total_ev) * 100, 2) if total_ev else 0.0
            dist_horas.append(
                PatronHoraItem(
                    hora=h,
                    franja_label=f"{h:02d}:00 - {(h+1)%24:02d}:00",
                    total_eventos=cnt,
                    total_ambulancias=horas_counter[h]["amb"],
                    total_gruas=horas_counter[h]["gru"],
                    total_accidentes_graves_o_fatales=horas_counter[h]["graves"],
                    porcentaje=pct,
                )
            )

        dist_dias: List[PatronDiaItem] = []
        for d in range(7):
            cnt = dias_counter[d]["total"]
            pct = round((cnt / total_ev) * 100, 2) if total_ev else 0.0
            dist_dias.append(
                PatronDiaItem(
                    dia_nombre=DIAS_SEMANA_ES[d],
                    total_eventos=cnt,
                    total_ambulancias=dias_counter[d]["amb"],
                    total_gruas=dias_counter[d]["gru"],
                    porcentaje=pct,
                )
            )

        hora_pico_idx = max(horas_counter, key=lambda k: horas_counter[k]["total"])
        dia_pico_idx = max(dias_counter, key=lambda k: dias_counter[k]["total"])

        hora_pico_str = f"{hora_pico_idx:02d}:00 - {hora_pico_idx+1:02d}:00 ({horas_counter[hora_pico_idx]['total']} eventos)"
        dia_pico_str = f"{DIAS_SEMANA_ES[dia_pico_idx]} ({dias_counter[dia_pico_idx]['total']} eventos)"

        entre_semana_count = total_ev - fin_semana_count
        pct_fin_semana = round((fin_semana_count / total_ev) * 100, 2) if total_ev else 0.0

        return PatronesTemporalesResponse(
            total_eventos_analizados=total_ev,
            hora_pico_maxima=hora_pico_str,
            dia_pico_maximo=dia_pico_str,
            eventos_fin_de_semana=fin_semana_count,
            eventos_entre_semana=entre_semana_count,
            porcentaje_fin_de_semana=pct_fin_semana,
            distribucion_por_franja={
                "Madrugada (00-06h)": franja_madrugada,
                "Mañana (06-12h)": franja_manana,
                "Tarde (12-18h)": franja_tarde,
                "Noche (18-24h)": franja_noche,
            },
            distribucion_por_hora=dist_horas,
            distribucion_por_dia=dist_dias,
        )

    # ----------------------------------------------------
    # 5. PLAN DE DESPLIEGUE ESTRATÉGICO
    # ----------------------------------------------------
    def obtener_plan_despliegue_estrategico(self, db: Session) -> RecomendacionesDespliegueResponse:
        scoring = self.obtener_scoring_tramos_criticos(db=db, tamano_tramo_km=5.0, top_n=5)
        patrones = self.obtener_patrones_temporales(db=db)

        recomendaciones: List[RecomendacionDespliegueItem] = []
        prioridad = 1

        for tramo in scoring.top_tramos_criticos:
            if tramo.nivel_riesgo in [NivelRiesgoEnum.EXTREMO, NivelRiesgoEnum.ALTO]:
                recurso = "AMBULANCIA MEDICALIZADA + PATRULLA PREVENTIVA" if tramo.total_ambulancias >= tramo.total_gruas else "GRÚA DE PLATAFORMA PESADA"
                diag = (
                    f"Concentra {tramo.total_eventos} asistencias (ICV {tramo.indice_criticidad}). "
                    f"Causa predominante: '{tramo.principal_motivo_o_causa}' en sentido {tramo.sentido_predominante}."
                )
                accion = (
                    f"Posicionar base móvil en el Km {tramo.km_inicio + 1:.1f} con patrullaje activo en horario {tramo.franja_horaria_mayor_incidencia}."
                )
                impacto = f"Reducir tiempo de despacho-arribo en el tramo a menos de 12 minutos y disuadir siniestros viales."

                recomendaciones.append(
                    RecomendacionDespliegueItem(
                        prioridad=prioridad,
                        recurso_recomendado=recurso,
                        tramo_cobertura=tramo.tramo_label,
                        horario_optimo=f"{tramo.franja_horaria_mayor_incidencia} (Especial énfasis en {patrones.dia_pico_maximo.split()[0]})",
                        diagnostico_problema=diag,
                        accion_preventiva=accion,
                        impacto_esperado=impacto,
                    )
                )
                prioridad += 1

        if not recomendaciones:
            recomendaciones.append(
                RecomendacionDespliegueItem(
                    prioridad=1,
                    recurso_recomendado="PATRULLA DE INSPECCIÓN PERIÓDICA",
                    tramo_cobertura="Corredor Vial Completo",
                    horario_optimo="Turnos rotativos ordinarios",
                    diagnostico_problema="Flujo vial con baja siniestralidad concentrada.",
                    accion_preventiva="Mantener recorridos rutinarios de bitácora.",
                    impacto_esperado="Sostenimiento de tiempos de respuesta estándar.",
                )
            )

        return RecomendacionesDespliegueResponse(
            fecha_generacion=datetime.now(),
            total_recomendaciones=len(recomendaciones),
            estrategia_general=(
                "Optimización de tiempos de respuesta mediante posicionamiento dinámico de flota en tramos de alto índice "
                "de criticidad vial durante las franjas horarias de mayor accidentabilidad histórica."
            ),
            recomendaciones=recomendaciones,
        )

    # ----------------------------------------------------
    # 6. DASHBOARD EJECUTIVO
    # ----------------------------------------------------
    def obtener_dashboard_ejecutivo(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        servicio: Optional[str] = None,
        turno: Optional[int] = None,
        id_vehiculo: Optional[int] = None,
    ) -> DashboardEjecutivoResponse:
        kpis = self.obtener_kpis_tiempos_respuesta(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
        )
        scoring = self.obtener_scoring_tramos_criticos(
            db=db,
            tamano_tramo_km=5.0,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            id_vehiculo=id_vehiculo,
            top_n=1,
        )
        patrones = self.obtener_patrones_temporales(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            id_vehiculo=id_vehiculo,
        )
        total_patrullajes = analitica_repo.get_conteo_patrullajes(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_vehiculo=id_vehiculo,
        )

        eventos = analitica_repo.get_eventos_combinados(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            servicio=servicio,
            turno=turno,
            id_vehiculo=id_vehiculo,
        )

        tot_ev = len(eventos) if (id_vehiculo or turno) else kpis.total_registros
        tot_amb = sum(1 for e in eventos if str(e.get("tipo_servicio")).upper() == "AMBULANCIA") if (id_vehiculo or turno) else sum(s.total_eventos for s in kpis.resumen_por_servicio if s.tipo_servicio == "AMBULANCIA")
        tot_gru = sum(1 for e in eventos if str(e.get("tipo_servicio")).upper() == "GRUA") if (id_vehiculo or turno) else sum(s.total_eventos for s in kpis.resumen_por_servicio if s.tipo_servicio == "GRUA")
        total_km_calc = sum(float(e.get("km_recorridos") or 0.0) for e in eventos) if (id_vehiculo or turno) else (kpis.total_km_recorridos or 0.0)

        pct_acc = round((tot_amb / tot_ev) * 100, 2) if tot_ev else 0.0
        pct_mec = round((tot_gru / tot_ev) * 100, 2) if tot_ev else 0.0

        tramo_top = scoring.top_tramos_criticos[0] if scoring.top_tramos_criticos else None

        rec_ejecutiva = (
            f"Focalizar recursos preventivos en el tramo {tramo_top.tramo_label} (Nivel {tramo_top.nivel_riesgo.value}) "
            f"durante la franja {patrones.hora_pico_maxima.split()[0]} de los {patrones.dia_pico_maximo.split()[0]} "
            f"para optimizar el tiempo medio global de respuesta (actualmente en {kpis.promedio_despacho_arribo_min or 12.5} min)."
            if tramo_top and patrones.hora_pico_maxima != 'N/A' else "Mantener el esquema de patrullaje preventivo y asistencia estándar en todo el corredor vial."
        )

        return DashboardEjecutivoResponse(
            total_asistencias_historicas=tot_ev,
            total_ambulancias=tot_amb,
            total_gruas=tot_gru,
            total_patrullajes=total_patrullajes,
            tasa_accidentabilidad_porcentaje=pct_acc,
            tasa_asistencia_mecanica_porcentaje=pct_mec,
            km_totales_atendidos=round(total_km_calc, 2),
            tiempo_promedio_llegada_min=kpis.promedio_despacho_arribo_min or 0.0,
            tiempo_promedio_sitio_min=kpis.promedio_sitio_min or 0.0,
            tiempo_promedio_ciclo_min=kpis.promedio_ciclo_total_min or 0.0,
            tramo_mas_critico=tramo_top,
            franja_horaria_mas_critica=patrones.hora_pico_maxima,
            dia_mas_critico=patrones.dia_pico_maximo,
            recomendacion_ejecutiva=rec_ejecutiva,
        )


analitica_service = AnaliticaService()
