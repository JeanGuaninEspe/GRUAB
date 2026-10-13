import json
import logging
import re
import calendar
from datetime import date, datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from collections import Counter

import httpx
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.services.operaciones_service import operaciones_service

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELO_OLLAMA = "qwen2.5:3b"
OLLAMA_KEEP_ALIVE = -1  # Mantiene el modelo en RAM permanentemente evitando cold starts
NUM_THREADS = 18        # Núcleos físicos de CPU para óptimo aprovechamiento AVX2 sin contención L3

MESES_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

MESES_NOMBRES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def ajustar_porcentajes_a_100(
    items: List[Dict[str, Any]],
    clave_cant: str = "cantidad",
    clave_pct: str = "porcentaje",
    total: Optional[int] = None
) -> None:
    """
    Asegura que los porcentajes redondeados a 1 decimal sumen exactamente 100.0%.
    Si hay una ligera discrepancia por redondeo (ej. 99.9% o 100.1%), ajusta el residuo
    en el elemento con mayor cantidad o en el último elemento.
    """
    if not items:
        return
    tot = total if (total is not None and total > 0) else sum(it.get(clave_cant, 0) for it in items)
    if tot <= 0:
        for it in items:
            it[clave_pct] = "0.0%"
        return

    pcts = [round((it.get(clave_cant, 0) / tot) * 100, 1) for it in items]
    diff = round(100.0 - sum(pcts), 1)

    if abs(diff) > 0 and abs(diff) <= 0.8:
        # Encontrar el elemento con mayor valor para absorber el redondeo mínimo
        idx_max = max(range(len(items)), key=lambda i: items[i].get(clave_cant, 0))
        pcts[idx_max] = round(pcts[idx_max] + diff, 1)

    for i, it in enumerate(items):
        it[clave_pct] = f"{pcts[i]:.1f}%"


class AIService:

    def __init__(self):
        # Memoria de sesión (Slot Filling) para herencia de filtros y contexto temporal
        self.estado_sesiones: Dict[str, Dict[str, Any]] = {}

    def resolver_rango_fechas_python(self, filtro: Dict[str, Any]) -> Tuple[datetime, datetime]:
        """
        Calcula con precisión matemática estricta (usando dateutil.relativedelta y calendar)
        las marcas de tiempo exactas para SQL Server basadas en la intención clasificada.
        Maneja meses completos, rangos de meses (ej. enero a julio), trimestres, semestres,
        años bisiestos y rangos explícitos con cobertura de microsegundos.
        """
        ahora = datetime.now()
        hoy_inicio = datetime.combine(ahora.date(), time.min)
        hoy_fin = datetime.combine(ahora.date(), time.max)

        tipo = (filtro.get("tipo_filtro") or "HOY").upper()

        if tipo == "HOY":
            return hoy_inicio, hoy_fin

        elif tipo == "AYER":
            ayer = ahora - relativedelta(days=1)
            return datetime.combine(ayer.date(), time.min), datetime.combine(ayer.date(), time.max)

        elif tipo == "RANGO_MESES":
            mes_ini = int(filtro.get("mes_inicio") or 1)
            mes_fin = int(filtro.get("mes_fin") or 12)
            anio_ini = int(filtro.get("anio_inicio") or filtro.get("anio") or ahora.year)
            anio_fin = int(filtro.get("anio_fin") or filtro.get("anio") or anio_ini)

            if anio_ini == anio_fin and mes_ini > mes_fin:
                anio_ini = anio_fin - 1

            ultimo_dia = calendar.monthrange(anio_fin, mes_fin)[1]
            inicio = datetime(anio_ini, mes_ini, 1, 0, 0, 0, 0)
            fin = datetime(anio_fin, mes_fin, ultimo_dia, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "MES_ESPECIFICO":
            mes = int(filtro.get("mes") or ahora.month)
            anio = int(filtro.get("anio") or ahora.year)
            ultimo_dia = calendar.monthrange(anio, mes)[1]
            inicio = datetime(anio, mes, 1, 0, 0, 0, 0)
            fin = datetime(anio, mes, ultimo_dia, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "ESTE_MES":
            inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ultimo_dia = calendar.monthrange(ahora.year, ahora.month)[1]
            fin = datetime(ahora.year, ahora.month, ultimo_dia, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "MES_PASADO":
            inicio_mes_pasado = (ahora - relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin_mes_pasado = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(microseconds=1)
            return inicio_mes_pasado, fin_mes_pasado

        elif tipo == "ULTIMOS_DIAS":
            dias = int(filtro.get("dias_atras") or 7)
            inicio = (ahora - relativedelta(days=dias)).replace(hour=0, minute=0, second=0, microsecond=0)
            return inicio, hoy_fin

        elif tipo == "ULTIMOS_MESES":
            num_meses = int(filtro.get("meses_atras") or 3)
            inicio = (ahora - relativedelta(months=num_meses)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ultimo_dia = calendar.monthrange(ahora.year, ahora.month)[1]
            fin = datetime(ahora.year, ahora.month, ultimo_dia, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "ANIO_ESPECIFICO":
            anio = int(filtro.get("anio_especifico") or filtro.get("anio") or ahora.year)
            inicio = datetime(anio, 1, 1, 0, 0, 0, 0)
            fin = datetime(anio, 12, 31, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "ESTE_ANIO":
            inicio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            fin = ahora.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return inicio, fin

        elif tipo == "ANIO_PASADO":
            anio = ahora.year - 1
            inicio = datetime(anio, 1, 1, 0, 0, 0, 0)
            fin = datetime(anio, 12, 31, 23, 59, 59, 999999)
            return inicio, fin

        elif tipo == "ULTIMOS_ANIOS":
            num_anios = int(filtro.get("anios_atras") or 1)
            inicio = (ahora - relativedelta(years=num_anios)).replace(hour=0, minute=0, second=0, microsecond=0)
            return inicio, hoy_fin

        elif tipo == "HISTORICO":
            inicio = datetime(2020, 1, 1, 0, 0, 0, 0)
            return inicio, hoy_fin

        elif tipo == "RANGO_EXPLICITO":
            f_ini_str = filtro.get("fecha_inicio")
            f_fin_str = filtro.get("fecha_fin")
            if f_ini_str and f_fin_str:
                try:
                    d_ini = date.fromisoformat(f_ini_str)
                    d_fin = date.fromisoformat(f_fin_str)
                    return datetime.combine(d_ini, time.min), datetime.combine(d_fin, time.max)
                except Exception:
                    pass

        return hoy_inicio, hoy_fin

    def _resolver_intencion_heuristica(
        self, prompt: str
    ) -> Optional[Tuple[datetime, datetime, Optional[str], List[str]]]:
        """
        Fast-Path determinístico sin latencia para intenciones temporales y de formato.
        Soporta de forma prioritaria rangos de meses ("enero a julio"), rangos de fechas,
        semestres, trimestres, meses individuales, años y expresiones relativas.
        """
        p = prompt.lower().strip()
        formato = None
        modulos = []

        # 1. Detección de formato solicitado
        if any(w in p for w in ("excel", "xlsx", "hoja de calculo", "hoja de cálculo", "descargar excel")):
            formato = "excel"
        elif any(w in p for w in ("pdf", "informe pdf", "reporte pdf", "descargar pdf", "exportar pdf")):
            formato = "pdf"

        # 2. Detección de módulos solicitados
        if any(w in p for w in ("ambulancia", "ambulancias", "salud", "medica", "médica", "herido", "heridos", "accidente", "paciente")):
            modulos.append("ambulancias")
        if any(w in p for w in ("grua", "grúa", "gruas", "grúas", "remolque", "auxilio mecanico", "auxilio mecánico", "averia", "avería")):
            modulos.append("gruas")
        if any(w in p for w in ("patrullaje", "patrullajes", "patrulla", "patrullas", "bitacora", "bitácora", "inspeccion", "inspección", "novedad")):
            modulos.append("patrullajes")

        if not modulos:
            modulos = ["ambulancias", "gruas", "patrullajes"]

        filtro = None
        meses_re = "|".join(MESES_MAP.keys())

        # =========================================================================
        # 3. EXTRACCIÓN TEMPORAL CON PRIORIDAD ESTRICTA
        # =========================================================================

        # A. Rangos explícitos ISO (ej: "2026-01-01 a 2026-07-31" o "desde 2026-01-01 hasta 2026-07-31")
        m_iso = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:a|al|hasta|-)\s*(\d{4}-\d{2}-\d{2})", p)
        if m_iso:
            filtro = {
                "tipo_filtro": "RANGO_EXPLICITO",
                "fecha_inicio": m_iso.group(1),
                "fecha_fin": m_iso.group(2)
            }

        # B. Rangos explícitos DD/MM/AAAA o DD-MM-AAAA (ej: "01/01/2026 al 31/07/2026")
        if not filtro:
            m_slash = re.search(
                r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\s*(?:a|al|hasta|-)\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})",
                p
            )
            if m_slash:
                d1, m1, y1 = int(m_slash.group(1)), int(m_slash.group(2)), int(m_slash.group(3))
                d2, m2, y2 = int(m_slash.group(4)), int(m_slash.group(5)), int(m_slash.group(6))
                filtro = {
                    "tipo_filtro": "RANGO_EXPLICITO",
                    "fecha_inicio": f"{y1:04d}-{m1:02d}-{d1:02d}",
                    "fecha_fin": f"{y2:04d}-{m2:02d}-{d2:02d}"
                }

        # C. Rangos de meses por nombre (ej: "enero a julio", "de enero a julio 2026", "desde enero hasta julio")
        if not filtro:
            patron_rango_meses = (
                rf"(?:de|desde|entre)?\s*\b({meses_re})\b"
                rf"(?:\s+(?:de|del)?\s*(20\d\d))?"
                rf"\s*(?:a|al|hasta|y|-)\s*(?:el\s*|mes\s*de\s*)?\b({meses_re})\b"
                rf"(?:\s+(?:de|del|en|del\s+a[ñn]o)?\s*(20\d\d))?"
            )
            m_rm = re.search(patron_rango_meses, p)
            if m_rm:
                nom_m1 = m_rm.group(1)
                nom_m2 = m_rm.group(3)
                num_m1 = MESES_MAP[nom_m1]
                num_m2 = MESES_MAP[nom_m2]

                y1_str = m_rm.group(2)
                y2_str = m_rm.group(4)

                anio_actual = datetime.now().year
                m_anio_general = re.search(r"\b(20\d\d)\b", p)
                anio_detectado = int(m_anio_general.group(1)) if m_anio_general else anio_actual

                anio_ini = int(y1_str) if y1_str else (int(y2_str) if y2_str else anio_detectado)
                anio_fin = int(y2_str) if y2_str else anio_ini

                filtro = {
                    "tipo_filtro": "RANGO_MESES",
                    "mes_inicio": num_m1,
                    "mes_fin": num_m2,
                    "anio_inicio": anio_ini,
                    "anio_fin": anio_fin,
                }

        # D. Semestres (ej: "primer semestre 2026", "1er semestre", "segundo semestre")
        if not filtro:
            m_sem = re.search(r"\b(1er|primer|2do|segundo)\s+semestre(?:\s+(?:de|del)?\s*(20\d\d))?\b", p)
            if m_sem:
                sem_str = m_sem.group(1)
                anio_sem = int(m_sem.group(2)) if m_sem.group(2) else datetime.now().year
                if sem_str in ("1er", "primer"):
                    filtro = {"tipo_filtro": "RANGO_MESES", "mes_inicio": 1, "mes_fin": 6, "anio": anio_sem}
                else:
                    filtro = {"tipo_filtro": "RANGO_MESES", "mes_inicio": 7, "mes_fin": 12, "anio": anio_sem}

        # E. Trimestres (ej: "primer trimestre", "1er trimestre", "q1", etc.)
        if not filtro:
            m_tri = re.search(r"\b(1er|primer|2do|segundo|3er|tercer|4to|cuarto)\s+trimestre(?:\s+(?:de|del)?\s*(20\d\d))?\b", p)
            if m_tri:
                tri_str = m_tri.group(1)
                anio_tri = int(m_tri.group(2)) if m_tri.group(2) else datetime.now().year
                tri_map = {
                    "1er": (1, 3), "primer": (1, 3),
                    "2do": (4, 6), "segundo": (4, 6),
                    "3er": (7, 9), "tercer": (7, 9),
                    "4to": (10, 12), "cuarto": (10, 12)
                }
                m_ini, m_fin = tri_map[tri_str]
                filtro = {"tipo_filtro": "RANGO_MESES", "mes_inicio": m_ini, "mes_fin": m_fin, "anio": anio_tri}

        # F. Mes por nombre individual (ej: "agosto 2026", "mes de agosto", "en julio")
        if not filtro:
            patron_mes = rf"\b({meses_re})\b(?:\s+(?:de|del|en|del\s+a[ñn]o)?\s*(20\d\d))?"
            m_mes = re.search(patron_mes, p)
            if m_mes:
                nombre_mes = m_mes.group(1)
                num_mes = MESES_MAP[nombre_mes]
                anio_val = int(m_mes.group(2)) if m_mes.group(2) else datetime.now().year
                filtro = {"tipo_filtro": "MES_ESPECIFICO", "mes": num_mes, "anio": anio_val}

        # G. Mes pasado / mes anterior
        if not filtro and any(w in p for w in ("mes pasado", "mes anterior", "el mes anterior", "el mes pasado", "del mes pasado")):
            filtro = {"tipo_filtro": "MES_PASADO"}

        # H. Mes actual / este mes
        if not filtro and any(w in p for w in ("este mes", "mes actual", "mes en curso")):
            filtro = {"tipo_filtro": "ESTE_MES"}

        # I. Año calendario específico (ej: 2026, 2025, 2024)
        if not filtro:
            m_anio = re.search(r"\b(?:a[ñn]o|ano|del|en)?\s*(20\d\d)\b", p)
            if m_anio:
                anio = int(m_anio.group(1))
                if 2018 <= anio <= 2035:
                    filtro = {"tipo_filtro": "ANIO_ESPECIFICO", "anio_especifico": anio}

        # J. Rango de N años
        if not filtro:
            m_anios = re.search(r"(\d+)\s*(?:a[ñn]os|anos)", p)
            if m_anios:
                filtro = {"tipo_filtro": "ULTIMOS_ANIOS", "anios_atras": int(m_anios.group(1))}

        # K. Últimos N meses
        if not filtro:
            m_u_meses = re.search(r"(?:ultimos|últimos)\s*(\d+)\s*meses", p)
            if m_u_meses:
                filtro = {"tipo_filtro": "ULTIMOS_MESES", "meses_atras": int(m_u_meses.group(1))}

        # L. Histórico completo
        if not filtro and any(w in p for w in ("historico", "histórico", "todos los años", "todos los anos", "desde siempre", "general", "todos los datos", "todo el historico")):
            filtro = {"tipo_filtro": "HISTORICO"}

        # M. Este año / año actual
        if not filtro and any(w in p for w in ("este año", "este ano", "año actual", "ano actual")):
            filtro = {"tipo_filtro": "ESTE_ANIO"}

        # N. Año pasado / año anterior
        if not filtro and any(w in p for w in ("año pasado", "ano pasado", "el año anterior", "el ano anterior")):
            filtro = {"tipo_filtro": "ANIO_PASADO"}

        # O. Últimos 30 días o último mes móvil
        if not filtro and any(w in p for w in ("ultimo mes", "último mes", "ultimos 30 dias", "últimos 30 días", "30 dias", "30 días")):
            filtro = {"tipo_filtro": "ULTIMOS_DIAS", "dias_atras": 30}

        # P. Últimos N días
        if not filtro:
            m_dias = re.search(r"(\d+)\s*(?:dias|días)", p)
            if m_dias:
                filtro = {"tipo_filtro": "ULTIMOS_DIAS", "dias_atras": int(m_dias.group(1))}

        # Q. Ayer
        if not filtro and "ayer" in p:
            filtro = {"tipo_filtro": "AYER"}

        # R. Hoy
        if not filtro and "hoy" in p:
            filtro = {"tipo_filtro": "HOY"}

        if filtro:
            dt_inicio, dt_fin = self.resolver_rango_fechas_python(filtro)
            return dt_inicio, dt_fin, formato, modulos

        return None

    def _clasificar_intencion(self, prompt: str) -> Dict[str, Any]:
        """
        Clasifica rápidamente la intención (formato, módulos, fechas) de forma síncrona.
        Garantiza compatibilidad con Chainlit y validaciones previas de la API.
        """
        res = self._resolver_intencion_heuristica(prompt)
        p = prompt.lower().strip()
        formato = None
        if any(w in p for w in ("excel", "xlsx", "hoja de calculo", "hoja de cálculo", "descargar excel")):
            formato = "excel"
        elif any(w in p for w in ("pdf", "informe pdf", "reporte pdf", "descargar pdf", "exportar pdf")):
            formato = "pdf"

        if res:
            dt_inicio, dt_fin, fmt, mods = res
            return {
                "tipo_filtro": "HEURISTICO",
                "dt_inicio": dt_inicio,
                "dt_fin": dt_fin,
                "formato_exportacion": fmt or formato,
                "modulos_solicitados": mods
            }
        return {
            "tipo_filtro": "NO_ESPECIFICADO",
            "formato_exportacion": formato,
            "modulos_solicitados": ["ambulancias", "gruas", "patrullajes"]
        }

    def _buscar_filtro_en_historial(self, historial: Optional[List[Dict[str, Any]]]) -> Optional[Tuple[datetime, datetime]]:
        """
        Inspecciona mensajes previos del historial para heredar fechas si la sesión no está en memoria.
        """
        if not historial:
            return None
        for m in reversed(historial):
            contenido = m.get("content", "")
            if isinstance(contenido, str) and contenido.strip():
                res = self._resolver_intencion_heuristica(contenido)
                if res is not None:
                    return res[0], res[1]
        return None

    def _detectar_modulos_de_contexto(self, prompt: str, stats: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Detecta los módulos prioritarios a partir del prompt del usuario o de las estadísticas provistas.
        """
        p = prompt.lower().strip()
        mods = []
        if any(w in p for w in ("ambulancia", "ambulancias", "salud", "medica", "médica", "herido", "heridos", "accidente", "paciente")):
            mods.append("ambulancias")
        if any(w in p for w in ("grua", "grúa", "gruas", "grúas", "remolque", "auxilio mecanico", "auxilio mecánico", "averia", "avería")):
            mods.append("gruas")
        if any(w in p for w in ("patrullaje", "patrullajes", "patrulla", "patrullas", "bitacora", "bitácora", "inspeccion", "inspección")):
            mods.append("patrullajes")

        if mods:
            return mods

        if stats:
            tiene_g = stats.get("gruas_total", 0) > 0
            tiene_a = stats.get("ambulancias_total", 0) > 0
            tiene_p = stats.get("patrullajes_total", 0) > 0
            if tiene_a and not tiene_g:
                return ["ambulancias"]
            if tiene_g and not tiene_a:
                return ["gruas"]
            if tiene_a or tiene_g or tiene_p:
                res = []
                if tiene_a:
                    res.append("ambulancias")
                if tiene_g:
                    res.append("gruas")
                if tiene_p:
                    res.append("patrullajes")
                return res

        return ["ambulancias", "gruas", "patrullajes"]

    async def _interpretar_intencion(
        self,
        prompt: str,
        historial: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> Tuple[datetime, datetime, Optional[str], List[str]]:
        """
        Enfoque Híbrido con Herencia de Estado (Slot Filling):
        1. Fast-Path heurístico inmediato para todas las expresiones conocidas.
        2. Clasificador LLM local en JSON estricto como respaldo si la heurística no coincide.
        3. Slot filling / memoria de sesión para retener fechas en preguntas consecutivas.
        """
        p = prompt.lower().strip()

        # Detección de módulos en el prompt actual
        modulos_detectados = []
        if any(w in p for w in ("ambulancia", "ambulancias", "salud", "medica", "médica", "herido", "heridos", "accidente", "paciente")):
            modulos_detectados.append("ambulancias")
        if any(w in p for w in ("grua", "grúa", "gruas", "grúas", "remolque", "auxilio mecanico", "auxilio mecánico", "averia", "avería")):
            modulos_detectados.append("gruas")
        if any(w in p for w in ("patrullaje", "patrullajes", "patrulla", "patrullas", "bitacora", "bitácora", "inspeccion", "inspección", "novedad")):
            modulos_detectados.append("patrullajes")

        # Detección de formato
        formato = None
        if any(w in p for w in ("excel", "xlsx", "hoja de calculo", "hoja de cálculo", "descargar excel")):
            formato = "excel"
        elif any(w in p for w in ("pdf", "informe pdf", "reporte pdf", "descargar pdf", "exportar pdf")):
            formato = "pdf"

        # 1. Fast-Path heurístico
        res_heuristico = self._resolver_intencion_heuristica(prompt)
        if res_heuristico is not None:
            dt_inicio, dt_fin, fmt, mods = res_heuristico
            if formato:
                fmt = formato
            if session_id:
                self.estado_sesiones[session_id] = {
                    "dt_inicio": dt_inicio,
                    "dt_fin": dt_fin,
                    "modulos": mods
                }
            return dt_inicio, dt_fin, fmt, mods

        # 2. Si no hubo coincidencia temporal heurística, verificar si el LLM extrae intención
        ahora = datetime.now()
        fecha_actual_str = ahora.strftime("%Y-%m-%d")

        prompt_clasificacion = (
            f"Hoy es {fecha_actual_str}.\n"
            "Tu tarea es analizar la solicitud del operador vial y clasificarla en formato JSON estricto.\n"
            "IMPORTANTE: NO calcules fechas por tu cuenta. Solo identifica el 'tipo_filtro' y sus parámetros numéricos:\n"
            "{\n"
            '  "tipo_filtro": "RANGO_MESES" | "MES_ESPECIFICO" | "MES_PASADO" | "ESTE_MES" | "HOY" | "AYER" | "ULTIMOS_DIAS" | "ULTIMOS_ANIOS" | "ANIO_ESPECIFICO" | "HISTORICO" | "RANGO_EXPLICITO" | "NO_ESPECIFICADO",\n'
            '  "mes_inicio": null,\n'
            '  "mes_fin": null,\n'
            '  "mes": null,\n'
            '  "anio": null,\n'
            '  "dias_atras": null,\n'
            '  "anios_atras": null,\n'
            '  "anio_especifico": null,\n'
            '  "fecha_inicio": null,\n'
            '  "fecha_fin": null,\n'
            '  "exportar": null | "excel" | "pdf",\n'
            '  "modulos": ["ambulancias", "gruas", "patrullajes"]\n'
            "}\n\n"
            "Reglas de Clasificación:\n"
            "- Si menciona un rango de meses (ej: 'de enero a julio', 'marzo a mayo 2026') -> tipo_filtro: 'RANGO_MESES', mes_inicio: <1-12>, mes_fin: <1-12>, anio: <año o año actual>\n"
            "- Si menciona un mes específico (ej: 'en agosto', 'marzo 2026', 'mes de mayo') -> tipo_filtro: 'MES_ESPECIFICO', mes: <1-12>, anio: <año o año actual>\n"
            "- Si el usuario no menciona ninguna fecha explícita (ej: 'y cuántas fueron ambulancias?', 'y en qué tramo?', 'muéstrame sólo grúas') -> tipo_filtro: 'NO_ESPECIFICADO'\n"
            "- 'el mes pasado', 'el mes anterior' -> tipo_filtro: 'MES_PASADO'\n"
            "- 'este mes', 'mes actual' -> tipo_filtro: 'ESTE_MES'\n"
            "- 'hoy' -> tipo_filtro: 'HOY'\n"
            "- 'ayer' -> tipo_filtro: 'AYER'\n"
            "- 'hace N dias', 'ultimos N dias' -> tipo_filtro: 'ULTIMOS_DIAS', dias_atras: N\n"
            "- 'en el año 2025', 'en 2026' -> tipo_filtro: 'ANIO_ESPECIFICO', anio_especifico: <numero>\n"
            "- 'ultimos N años' -> tipo_filtro: 'ULTIMOS_ANIOS', anios_atras: N\n"
            "- 'historico', 'todo' -> tipo_filtro: 'HISTORICO'\n"
            "- Si solicita descargar reporte o informe en excel o pdf, asigna 'exportar'.\n"
            "- Devuelve ÚNICAMENTE el bloque JSON válido sin comentarios.\n\n"
            f'Solicitud del Operador: "{prompt}"'
        )

        filtro = {"tipo_filtro": "NO_ESPECIFICADO"}
        modulos = modulos_detectados if modulos_detectados else ["ambulancias", "gruas", "patrullajes"]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODELO_OLLAMA,
                        "messages": [{"role": "user", "content": prompt_clasificacion}],
                        "stream": False,
                        "format": "json",
                        "keep_alive": OLLAMA_KEEP_ALIVE,
                        "options": {
                            "num_thread": NUM_THREADS,
                            "num_ctx": 2048,
                            "num_predict": 256
                        }
                    }
                )
                if res.status_code == 200:
                    data = json.loads(res.json()["message"]["content"])
                    filtro = data
                    if not formato:
                        formato = data.get("exportar")
                    if not modulos_detectados and data.get("modulos") and isinstance(data["modulos"], list):
                        modulos = data["modulos"]
        except Exception as e:
            logger.warning(f"Ollama clasificación no disponible ({e}). Usando clasificación por defecto.")

        tipo_filtro = (filtro.get("tipo_filtro") or "NO_ESPECIFICADO").upper()

        # 3. Herencia de Estado (Slot Filling):
        if tipo_filtro == "NO_ESPECIFICADO":
            if session_id and session_id in self.estado_sesiones:
                ses = self.estado_sesiones[session_id]
                dt_inicio = ses["dt_inicio"]
                dt_fin = ses["dt_fin"]
                if modulos_detectados:
                    ses["modulos"] = modulos_detectados
                    modulos = modulos_detectados
                else:
                    modulos = ses.get("modulos", modulos)
                logger.info(f"Slot Filling: Fechas heredadas de session_id '{session_id}': {dt_inicio} a {dt_fin}")
                return dt_inicio, dt_fin, formato, modulos

            rango_hist = self._buscar_filtro_en_historial(historial)
            if rango_hist:
                dt_inicio, dt_fin = rango_hist
                if session_id:
                    self.estado_sesiones[session_id] = {
                        "dt_inicio": dt_inicio,
                        "dt_fin": dt_fin,
                        "modulos": modulos
                    }
                logger.info(f"Slot Filling: Fechas heredadas de historial: {dt_inicio} a {dt_fin}")
                return dt_inicio, dt_fin, formato, modulos

            dt_inicio, dt_fin = self.resolver_rango_fechas_python({"tipo_filtro": "HOY"})
        else:
            dt_inicio, dt_fin = self.resolver_rango_fechas_python(filtro)

        if session_id:
            self.estado_sesiones[session_id] = {
                "dt_inicio": dt_inicio,
                "dt_fin": dt_fin,
                "modulos": modulos
            }

        return dt_inicio, dt_fin, formato, modulos

    def _formatear_ambulancias(self, registros: List[Any]) -> List[Dict[str, Any]]:
        salida = []
        for r in registros:
            ts = getattr(r, "ts_llamada", None)
            fecha_str = str(ts.date()) if (ts and hasattr(ts, "date")) else str(getattr(r, "fecha_asistencia", "") or "")
            sector = (getattr(r, "sector_referencia", None) or getattr(r, "sector", None) or "Sin sector").strip()
            km_val = getattr(r, "abscisa_km", None) if getattr(r, "abscisa_km", None) is not None else getattr(r, "km", None)
            motivo = (getattr(r, "motivo_atencion", None) or getattr(r, "motivo_llamada", None) or "").strip()
            tipo_inc = (getattr(r, "tipo_incidente", None) or getattr(r, "tipo_accidente", None) or motivo or "Emergencia médica").strip()
            severidad = (getattr(r, "severidad", None) or getattr(r, "estado_paciente", None) or "No especificado").strip()

            salida.append({
                "fecha": fecha_str,
                "ts": ts.isoformat() if hasattr(ts, "isoformat") else str(ts or ""),
                "codigo": getattr(r, "codigo_formulario", None) or getattr(r, "codigo_ambulancia", "") or "",
                "sector": sector,
                "km": float(km_val) if km_val is not None else None,
                "paciente_estado": severidad,
                "severidad": severidad,
                "motivo": motivo,
                "tipo_incidente": tipo_inc,
                "personal": "Paramédico asignado" if getattr(r, "id_paramedico", None) else "No asignado",
                "vehiculo": "Ambulancia de concesión" if getattr(r, "id_vehiculo", None) else "No asignado"
            })
        return salida

    def _formatear_gruas(self, registros: List[Any]) -> List[Dict[str, Any]]:
        salida = []
        for r in registros:
            ts = getattr(r, "ts_llamada", None)
            fecha_str = str(ts.date()) if (ts and hasattr(ts, "date")) else str(getattr(r, "fecha_asistencia", "") or "")
            sector = (getattr(r, "sector_referencia", None) or getattr(r, "sector", None) or "Sin sector").strip()
            km_val = getattr(r, "abscisa_km", None) if getattr(r, "abscisa_km", None) is not None else getattr(r, "km", None)
            motivo = (getattr(r, "motivo_atencion", None) or getattr(r, "motivo_llamada", None) or "").strip()
            tipo_v = (getattr(r, "tipo_vehiculo", None) or getattr(r, "tipo_vehiculo_asistido", None) or "No especificado").strip()

            salida.append({
                "fecha": fecha_str,
                "ts": ts.isoformat() if hasattr(ts, "isoformat") else str(ts or ""),
                "codigo": getattr(r, "codigo_formulario", None) or getattr(r, "codigo_grua", "") or "",
                "sector": sector,
                "km": float(km_val) if km_val is not None else None,
                "tipo_vehiculo": tipo_v,
                "motivo": motivo,
                "personal": "Operador de grúa asignado" if getattr(r, "id_chofer", None) else "No asignado",
                "vehiculo": "Grúa de plataforma" if getattr(r, "id_vehiculo", None) else "No asignado"
            })
        return salida

    def _generar_resumen_estadistico(
        self,
        datos_crudos: Dict[str, Any],
        dt_inicio: datetime,
        dt_fin: datetime
    ) -> Dict[str, Any]:
        """
        Precalcula agregaciones exactas en Python garantizando:
        1. Rango temporal exacto y bandera explícita de disponibilidad.
        2. Cuadre matemático al 100% en tipologías con categoría 'Otros / No especificado'.
        3. Desglose mensual (Mes | Total | %) obligatorio si el rango cubre más de un mes.
        4. Concentración de sectores con cantidad absoluta y porcentaje: Sector: Cantidad (XX.X%).
        5. Identificación programática del Top 1 de sector y Top 1 de tipología.
        """
        periodo_str = f"Del {dt_inicio.strftime('%d/%m/%Y')} al {dt_fin.strftime('%d/%m/%Y')}"
        resumen: Dict[str, Any] = {
            "periodo": periodo_str,
            "fecha_inicio_solicitada": dt_inicio.strftime("%Y-%m-%d"),
            "fecha_fin_solicitada": dt_fin.strftime("%Y-%m-%d"),
        }

        gruas = datos_crudos.get("gruas", [])
        ambulancias = datos_crudos.get("ambulancias", [])
        patrullajes = datos_crudos.get("patrullajes", [])

        tot_gru = len(gruas)
        tot_amb = len(ambulancias)
        tot_pat = len(patrullajes)
        total_asistencias = tot_gru + tot_amb
        total_general = total_asistencias if total_asistencias > 0 else tot_pat

        resumen["gruas_total"] = tot_gru
        resumen["ambulancias_total"] = tot_amb
        resumen["patrullajes_total"] = tot_pat
        resumen["total_asistencias_via"] = total_asistencias
        resumen["asistencias_totales_combinadas"] = total_asistencias
        resumen["total_general"] = total_general

        # =====================================================================
        # 1. VERIFICACIÓN DE DISPONIBILIDAD TEMPORAL
        # =====================================================================
        fechas_reales: List[date] = []
        for g in gruas:
            f_str = g.get("fecha") or (g.get("ts") or "")[:10]
            if f_str:
                try:
                    fechas_reales.append(date.fromisoformat(f_str[:10]))
                except Exception:
                    pass
        for a in ambulancias:
            f_str = a.get("fecha") or (a.get("ts") or "")[:10]
            if f_str:
                try:
                    fechas_reales.append(date.fromisoformat(f_str[:10]))
                except Exception:
                    pass
        for p in patrullajes:
            f_str = p.get("fecha")
            if f_str:
                try:
                    fechas_reales.append(date.fromisoformat(f_str[:10]))
                except Exception:
                    pass

        meses_solicitados: List[Tuple[int, int]] = []
        cur_m = datetime(dt_inicio.year, dt_inicio.month, 1)
        end_m = datetime(dt_fin.year, dt_fin.month, 1)
        while cur_m <= end_m:
            meses_solicitados.append((cur_m.year, cur_m.month))
            if cur_m.month == 12:
                cur_m = datetime(cur_m.year + 1, 1, 1)
            else:
                cur_m = datetime(cur_m.year, cur_m.month + 1, 1)

        aviso_disponibilidad: Optional[str] = None
        if not fechas_reales:
            aviso_disponibilidad = (
                f"Aviso de disponibilidad: No se encontraron datos registrados entre el "
                f"{dt_inicio.strftime('%d/%m/%Y')} y el {dt_fin.strftime('%d/%m/%Y')}."
            )
        else:
            fecha_min = min(fechas_reales)
            fecha_max = max(fechas_reales)
            meses_con_datos = set((f.year, f.month) for f in fechas_reales)
            meses_faltantes = [m for m in meses_solicitados if m not in meses_con_datos]

            if len(meses_solicitados) > 1 and meses_faltantes:
                f_min_str = fecha_min.strftime("%d/%m/%Y")
                f_max_str = fecha_max.strftime("%d/%m/%Y")
                aviso_disponibilidad = f"Aviso de disponibilidad: Solo se encontraron datos entre {f_min_str} y {f_max_str}"

        resumen["aviso_disponibilidad"] = aviso_disponibilidad

        # =====================================================================
        # 2. AGRUPACIÓN MENSUAL (OBLIGATORIA SI EL RANGO ABARCA MÁS DE UN MES)
        # =====================================================================
        desglose_mensual: List[Dict[str, Any]] = []
        if len(meses_solicitados) > 1:
            for y, m in meses_solicitados:
                cant_mes = sum(1 for f in fechas_reales if f.year == y and f.month == m)
                pct_mes = (cant_mes / total_general * 100) if total_general > 0 else 0.0
                desglose_mensual.append({
                    "mes": f"{MESES_NOMBRES[m]} {y}",
                    "total": cant_mes,
                    "porcentaje": f"{pct_mes:.1f}%",
                    "porcentaje_num": pct_mes
                })

            ajustar_porcentajes_a_100(desglose_mensual, clave_cant="total", clave_pct="porcentaje", total=total_general)

        resumen["desglose_mensual"] = desglose_mensual
        resumen["rango_multimes"] = bool(len(meses_solicitados) > 1)

        mes_pico = None
        if desglose_mensual and any(m["total"] > 0 for m in desglose_mensual):
            mes_pico_obj = max(desglose_mensual, key=lambda x: x["total"])
            mes_pico = {
                "mes": mes_pico_obj["mes"],
                "total": mes_pico_obj["total"],
                "porcentaje": mes_pico_obj["porcentaje"]
            }
        resumen["mes_pico"] = mes_pico

        # =====================================================================
        # 3. AGRUPACIÓN POR TIPOLOGÍA (CIERRE MATEMÁTICO 100% Y TOTAL GENERAL)
        # =====================================================================
        gruas_top_motivos: List[Dict[str, Any]] = []
        if tot_gru > 0:
            c_motivos = Counter()
            for g in gruas:
                m = (g.get("motivo") or "").strip()
                if not m or m.lower() in ("sin motivo", "ninguno", "null", "none"):
                    m = "Otros / No especificado"
                c_motivos[m] += 1

            top_m = [item for item in c_motivos.most_common() if item[0] != "Otros / No especificado"]
            principales = top_m[:4]
            otros_cant = sum(c for _, c in top_m[4:]) + c_motivos.get("Otros / No especificado", 0)

            for mot, cnt in principales:
                gruas_top_motivos.append({
                    "motivo": mot,
                    "cantidad": cnt,
                    "porcentaje": f"{(cnt / tot_gru * 100):.1f}%"
                })
            if otros_cant > 0:
                gruas_top_motivos.append({
                    "motivo": "Otros / No especificado",
                    "cantidad": otros_cant,
                    "porcentaje": f"{(otros_cant / tot_gru * 100):.1f}%"
                })
            ajustar_porcentajes_a_100(gruas_top_motivos, total=tot_gru)

        resumen["gruas_top_motivos"] = gruas_top_motivos

        tipos_v = Counter((g.get("tipo_vehiculo") or "No especificado").strip() for g in gruas)
        resumen["gruas_tipos_vehiculo"] = dict(tipos_v.most_common(4))

        amb_top_incidentes: List[Dict[str, Any]] = []
        if tot_amb > 0:
            c_incidentes = Counter()
            for a in ambulancias:
                inc = (a.get("tipo_incidente") or a.get("motivo") or "").strip()
                if not inc or inc.lower() in ("sin novedad", "ninguno", "null", "none"):
                    inc = "Otros / No especificado"
                c_incidentes[inc] += 1

            top_i = [item for item in c_incidentes.most_common() if item[0] != "Otros / No especificado"]
            principales_i = top_i[:4]
            otros_cant_i = sum(c for _, c in top_i[4:]) + c_incidentes.get("Otros / No especificado", 0)

            for inc, cnt in principales_i:
                amb_top_incidentes.append({
                    "tipo": inc,
                    "cantidad": cnt,
                    "atenciones": cnt,
                    "porcentaje": f"{(cnt / tot_amb * 100):.1f}%"
                })
            if otros_cant_i > 0:
                amb_top_incidentes.append({
                    "tipo": "Otros / No especificado",
                    "cantidad": otros_cant_i,
                    "atenciones": otros_cant_i,
                    "porcentaje": f"{(otros_cant_i / tot_amb * 100):.1f}%"
                })
            ajustar_porcentajes_a_100(amb_top_incidentes, total=tot_amb)

        resumen["ambulancias_top_incidentes"] = amb_top_incidentes
        severidad = Counter((a.get("severidad") or "No especificada").strip() for a in ambulancias)
        resumen["ambulancias_severidad"] = dict(severidad.most_common(4))

        # =====================================================================
        # 4. AGRUPACIÓN POR SECTORES (FORMATO "Sector: Cantidad (XX.X%)")
        # =====================================================================
        gruas_sectores = Counter()
        for g in gruas:
            s = (g.get("sector") or "").strip()
            gruas_sectores[s if s else "Otros / No especificado"] += 1

        resumen_gruas_sectores = []
        if tot_gru > 0:
            top_sg = [item for item in gruas_sectores.most_common() if item[0] != "Otros / No especificado"]
            sel_sg = top_sg[:5]
            otros_sg = sum(c for _, c in top_sg[5:]) + gruas_sectores.get("Otros / No especificado", 0)
            for s, c in sel_sg:
                resumen_gruas_sectores.append({
                    "sector": s,
                    "cantidad": c,
                    "porcentaje": f"{(c / tot_gru * 100):.1f}%",
                    "texto_completo": f"{s}: {c} ({(c / tot_gru * 100):.1f}%)"
                })
            if otros_sg > 0:
                resumen_gruas_sectores.append({
                    "sector": "Otros / No especificado",
                    "cantidad": otros_sg,
                    "porcentaje": f"{(otros_sg / tot_gru * 100):.1f}%",
                    "texto_completo": f"Otros / No especificado: {otros_sg} ({(otros_sg / tot_gru * 100):.1f}%)"
                })
            ajustar_porcentajes_a_100(resumen_gruas_sectores, total=tot_gru)
            for it in resumen_gruas_sectores:
                it["texto_completo"] = f"{it['sector']}: {it['cantidad']} ({it['porcentaje']})"

        resumen["gruas_top_sectores"] = resumen_gruas_sectores

        amb_sectores = Counter()
        for a in ambulancias:
            s = (a.get("sector") or "").strip()
            amb_sectores[s if s else "Otros / No especificado"] += 1

        resumen_amb_sectores = []
        if tot_amb > 0:
            top_sa = [item for item in amb_sectores.most_common() if item[0] != "Otros / No especificado"]
            sel_sa = top_sa[:5]
            otros_sa = sum(c for _, c in top_sa[5:]) + amb_sectores.get("Otros / No especificado", 0)
            for s, c in sel_sa:
                resumen_amb_sectores.append({
                    "sector": s,
                    "cantidad": c,
                    "atenciones": c,
                    "porcentaje": f"{(c / tot_amb * 100):.1f}%",
                    "texto_completo": f"{s}: {c} ({(c / tot_amb * 100):.1f}%)"
                })
            if otros_sa > 0:
                resumen_amb_sectores.append({
                    "sector": "Otros / No especificado",
                    "cantidad": otros_sa,
                    "atenciones": otros_sa,
                    "porcentaje": f"{(otros_sa / tot_amb * 100):.1f}%",
                    "texto_completo": f"Otros / No especificado: {otros_sa} ({(otros_sa / tot_amb * 100):.1f}%)"
                })
            ajustar_porcentajes_a_100(resumen_amb_sectores, total=tot_amb)
            for it in resumen_amb_sectores:
                it["texto_completo"] = f"{it['sector']}: {it['cantidad']} ({it['porcentaje']})"

        resumen["ambulancias_top_sectores"] = resumen_amb_sectores

        sectores_combinados = Counter()
        for g in gruas:
            s = (g.get("sector") or "").strip()
            sectores_combinados[s if s else "Otros / No especificado"] += 1
        for a in ambulancias:
            s = (a.get("sector") or "").strip()
            sectores_combinados[s if s else "Otros / No especificado"] += 1

        asistencias_top_tramos = []
        if total_asistencias > 0:
            top_sc = [item for item in sectores_combinados.most_common() if item[0] != "Otros / No especificado"]
            sel_sc = top_sc[:5]
            otros_sc = sum(c for _, c in top_sc[5:]) + sectores_combinados.get("Otros / No especificado", 0)
            for s, c in sel_sc:
                asistencias_top_tramos.append({
                    "sector": s,
                    "cantidad": c,
                    "asistencias_totales": c,
                    "atenciones": c,
                    "porcentaje": f"{(c / total_asistencias * 100):.1f}%",
                    "texto_completo": f"{s}: {c} ({(c / total_asistencias * 100):.1f}%)"
                })
            if otros_sc > 0:
                asistencias_top_tramos.append({
                    "sector": "Otros / No especificado",
                    "cantidad": otros_sc,
                    "asistencias_totales": otros_sc,
                    "atenciones": otros_sc,
                    "porcentaje": f"{(otros_sc / total_asistencias * 100):.1f}%",
                    "texto_completo": f"Otros / No especificado: {otros_sc} ({(otros_sc / total_asistencias * 100):.1f}%)"
                })
            ajustar_porcentajes_a_100(asistencias_top_tramos, total=total_asistencias)
            for it in asistencias_top_tramos:
                it["texto_completo"] = f"{it['sector']}: {it['cantidad']} ({it['porcentaje']})"

        resumen["asistencias_top_tramos"] = asistencias_top_tramos

        # =====================================================================
        # 5. PATRULLAJES
        # =====================================================================
        if patrullajes:
            con_novedad = sum(1 for p in patrullajes if p.get("hubo_novedad"))
            resumen["patrullajes_con_novedad"] = con_novedad
            resumen["patrullajes_normales"] = tot_pat - con_novedad

        # =====================================================================
        # 6. IDENTIFICACIÓN PROGRAMÁTICA DEL TOP 1 DE SECTOR Y TIPOLOGÍA
        # =====================================================================
        top_1_s = None
        if asistencias_top_tramos:
            s_cand = [s for s in asistencias_top_tramos if s["sector"] != "Otros / No especificado"]
            top_1_s = s_cand[0] if s_cand else asistencias_top_tramos[0]
        elif resumen_amb_sectores:
            s_cand = [s for s in resumen_amb_sectores if s["sector"] != "Otros / No especificado"]
            top_1_s = s_cand[0] if s_cand else resumen_amb_sectores[0]
        elif resumen_gruas_sectores:
            s_cand = [s for s in resumen_gruas_sectores if s["sector"] != "Otros / No especificado"]
            top_1_s = s_cand[0] if s_cand else resumen_gruas_sectores[0]

        resumen["top_1_sector"] = {
            "sector": top_1_s["sector"],
            "cantidad": top_1_s["cantidad"],
            "porcentaje": top_1_s["porcentaje"],
            "texto": f"{top_1_s['sector']}: {top_1_s['cantidad']} ({top_1_s['porcentaje']})"
        } if top_1_s else None

        top_1_t = None
        if tot_gru >= tot_amb and gruas_top_motivos:
            m_cand = [m for m in gruas_top_motivos if m["motivo"] != "Otros / No especificado"]
            if m_cand:
                m_top = m_cand[0]
                top_1_t = {
                    "tipologia": m_top["motivo"],
                    "servicio": "Grúas (Auxilio Mecánico)",
                    "cantidad": m_top["cantidad"],
                    "porcentaje": m_top["porcentaje"]
                }
        elif amb_top_incidentes:
            i_cand = [i for i in amb_top_incidentes if i["tipo"] != "Otros / No especificado"]
            if i_cand:
                i_top = i_cand[0]
                top_1_t = {
                    "tipologia": i_top["tipo"],
                    "servicio": "Ambulancias (Atención Médica)",
                    "cantidad": i_top["cantidad"],
                    "porcentaje": i_top["porcentaje"]
                }

        resumen["top_1_tipologia"] = top_1_t

        return resumen

    def _generar_tablas_markdown(
        self,
        stats: Dict[str, Any],
        modulos: List[str]
    ) -> Dict[str, str]:
        """
        Construye determinísticamente las tablas Markdown limpias para inyectar a Qwen
        y para el respaldo directo, evitando que el LLM tenga que calcular sumas o porcentajes.
        """
        tablas: Dict[str, str] = {}
        solo_gruas = ("gruas" in modulos) and ("ambulancias" not in modulos)
        solo_amb = ("ambulancias" in modulos) and ("gruas" not in modulos)

        # 1. Tabla Mensual (si abarca más de un mes)
        desglose_m = stats.get("desglose_mensual", [])
        if desglose_m:
            lineas_m = [
                "| Mes | Total | % |",
                "|:---|:---:|:---:|"
            ]
            for m in desglose_m:
                lineas_m.append(f"| {m['mes']} | {m['total']:,} | {m['porcentaje']} |")
            tot_gen = stats.get("total_general", 0)
            lineas_m.append(f"| **Total** | **{tot_gen:,}** | **100.0%** |")
            tablas["tabla_mensual"] = "\n".join(lineas_m)

        # 2. Tabla de Tipologías
        if solo_gruas or ("gruas" in modulos and not solo_amb):
            mots = stats.get("gruas_top_motivos", [])
            tot_g = stats.get("gruas_total", 0)
            if mots and tot_g > 0:
                lineas_g = [
                    "| Motivo de Asistencia (Grúas) | Cantidad | Incidencia (%) |",
                    "|:---|:---:|:---:|"
                ]
                for mot in mots:
                    cant_m = mot.get("cantidad") if mot.get("cantidad") is not None else mot.get("asistencias", 0)
                    lineas_g.append(f"| {mot['motivo']} | {cant_m:,} | {mot['porcentaje']} |")
                lineas_g.append(f"| **Total** | **{tot_g:,}** | **100.0%** |")
                tablas["tabla_gruas_motivos"] = "\n".join(lineas_g)

        if solo_amb or ("ambulancias" in modulos and not solo_gruas):
            incs = stats.get("ambulancias_top_incidentes", [])
            tot_a = stats.get("ambulancias_total", 0)
            if incs and tot_a > 0:
                lineas_a = [
                    "| Tipo de Incidente Médico (Ambulancias) | Atenciones | Incidencia (%) |",
                    "|:---|:---:|:---:|"
                ]
                for inc in incs:
                    cant_i = inc.get("cantidad") if inc.get("cantidad") is not None else inc.get("atenciones", 0)
                    lineas_a.append(f"| {inc['tipo']} | {cant_i:,} | {inc['porcentaje']} |")
                lineas_a.append(f"| **Total** | **{tot_a:,}** | **100.0%** |")
                tablas["tabla_ambulancias_incidentes"] = "\n".join(lineas_a)

        # 3. Tabla de Sectores
        if solo_gruas:
            secs = stats.get("gruas_top_sectores", [])
            tot_sec = stats.get("gruas_total", 0)
        elif solo_amb:
            secs = stats.get("ambulancias_top_sectores", [])
            tot_sec = stats.get("ambulancias_total", 0)
        else:
            secs = stats.get("asistencias_top_tramos", []) or stats.get("ambulancias_top_sectores", []) or stats.get("gruas_top_sectores", [])
            tot_sec = stats.get("total_asistencias_via", 0) or stats.get("ambulancias_total", 0) or stats.get("gruas_total", 0)

        if secs and tot_sec > 0:
            lineas_s = [
                "| Sector / Tramo Vial | Cantidad | Incidencia (%) |",
                "|:---|:---:|:---:|"
            ]
            for sec in secs:
                cant_s = sec.get("cantidad") if sec.get("cantidad") is not None else (sec.get("atenciones") if sec.get("atenciones") is not None else sec.get("asistencias_totales", 0))
                lineas_s.append(f"| {sec['sector']} | {cant_s:,} | {sec['porcentaje']} |")
            lineas_s.append(f"| **Total** | **{tot_sec:,}** | **100.0%** |")
            tablas["tabla_sectores"] = "\n".join(lineas_s)

        return tablas

    def _generar_respuesta_directa_respaldo(
        self,
        prompt: str,
        stats: Dict[str, Any],
        modulos_solicitados: Optional[List[str]] = None
    ) -> str:
        """
        Genera el informe ejecutivo oficial y estructurado de forma 100% determinística
        en Python cuando el LLM está fuera de línea o ante excepciones de red.
        Aplica rigurosamente: tablas Markdown cuadradas al 100%, sectores en formato
        'Sector: Cantidad (XX.X%)', desglose mensual si aplica y recomendaciones
        conectadas directamente al Top 1 de sector y tipología.
        """
        mods = modulos_solicitados or self._detectar_modulos_de_contexto(prompt, stats)
        solo_gruas = ("gruas" in mods) and ("ambulancias" not in mods)
        solo_amb = ("ambulancias" in mods) and ("gruas" not in mods)

        periodo = stats.get("periodo", "Período no especificado")
        aviso_disp = stats.get("aviso_disponibilidad")
        tot_amb = stats.get("ambulancias_total", 0)
        tot_gru = stats.get("gruas_total", 0)
        tot_p = stats.get("patrullajes_total", 0)
        tot_asist = stats.get("total_asistencias_via") if stats.get("total_asistencias_via") is not None else (tot_amb + tot_gru)

        # Regla de cero registros
        if tot_asist == 0 and tot_p == 0:
            partes = [
                "### Informe de Operaciones y Asistencias Viales\n",
                f"**Período Evaluado:** {periodo}  \n"
            ]
            if aviso_disp:
                partes.append(f"> **{aviso_disp}**\n")
            partes.append(
                "No se registraron asistencias ni recorridos operativos para el periodo seleccionado.\n\n"
                "- Verificación de base de datos completada: 0 atenciones para los servicios consultados.\n"
                "- La infraestructura vial operó con normalidad durante este rango temporal sin intervenciones solicitadas."
            )
            return "\n".join(partes)

        tablas = self._generar_tablas_markdown(stats, mods)
        partes = [
            "### Informe Ejecutivo de Operaciones Viales\n",
            f"**Período Evaluado:** {periodo}  "
        ]

        if aviso_disp:
            partes.append(f"> **{aviso_disp}**\n")

        # 1. Total General y Desglose por Servicio
        if solo_gruas:
            partes.append(f"**Total de Auxilios de Grúas en Vía:** **{tot_gru:,}** eventos registrados  \n")
        elif solo_amb:
            partes.append(f"**Total de Atenciones de Ambulancias en Vía:** **{tot_amb:,}** atenciones médicas registradas  \n")
        else:
            partes.append(f"**Total de Asistencias en Vía:** **{tot_asist:,}** eventos registrados  \n")
            partes.append("#### 1. Desglose Operativo por Servicio")
            if tot_gru > 0:
                pct_g = (tot_gru / tot_asist * 100) if tot_asist > 0 else 0.0
                partes.append(f"- **Grúas de Auxilio:** **{tot_gru:,}** asistencias ({pct_g:.1f}% del volumen total)")
            if tot_amb > 0:
                pct_a = (tot_amb / tot_asist * 100) if tot_asist > 0 else 0.0
                partes.append(f"- **Ambulancias:** **{tot_amb:,}** atenciones de salud ({pct_a:.1f}% del volumen total)\n")

        # 2. Evolución Temporal Mensual (si abarca más de un mes)
        if "tabla_mensual" in tablas:
            partes.append("#### Distribución y Evolución Mensual")
            partes.append(tablas["tabla_mensual"])
            mes_pico = stats.get("mes_pico")
            if mes_pico:
                partes.append(
                    f"\n*Evolución Temporal:* La mayor actividad operativa se concentró en el mes de **{mes_pico['mes']}** "
                    f"con **{mes_pico['total']:,} eventos ({mes_pico['porcentaje']})**, requiriendo el mayor despliegue de recursos en dicho período.\n"
                )
            else:
                partes.append("")

        # 3. Concentración Territorial por Sectores Viales
        partes.append("#### Concentración Territorial por Sectores Viales")
        if solo_gruas:
            top_secs = stats.get("gruas_top_sectores", [])
        elif solo_amb:
            top_secs = stats.get("ambulancias_top_sectores", [])
        else:
            top_secs = stats.get("asistencias_top_tramos", []) or stats.get("ambulancias_top_sectores", []) or stats.get("gruas_top_sectores", [])

        if top_secs:
            items_en_prosa = []
            for s in top_secs[:3]:
                if s.get("sector") != "Otros / No especificado":
                    c_val = s.get("cantidad") if s.get("cantidad") is not None else (s.get("atenciones") if s.get("atenciones") is not None else s.get("asistencias_totales", 0))
                    items_en_prosa.append(f"**{s.get('sector')}**: {c_val:,} ({s.get('porcentaje', '0%')})")
            if items_en_prosa:
                partes.append(f"La demanda de operaciones se concentró de forma preponderante en los sectores: {', '.join(items_en_prosa)}.\n")

        if "tabla_sectores" in tablas:
            partes.append(tablas["tabla_sectores"])
            partes.append("")

        # 4. Tipología de Auxilios / Incidentes
        if solo_gruas and "tabla_gruas_motivos" in tablas:
            partes.append("#### Tipología de Auxilios Mecánicos (Grúas)")
            partes.append(tablas["tabla_gruas_motivos"])
            partes.append("")
        elif solo_amb and "tabla_ambulancias_incidentes" in tablas:
            partes.append("#### Tipología de Emergencias Médicas (Ambulancias)")
            partes.append(tablas["tabla_ambulancias_incidentes"])
            sev_items = [f"**{k}**: {v}" for k, v in stats.get("ambulancias_severidad", {}).items()]
            if sev_items:
                partes.append(f"\n*Severidad de Pacientes:* {', '.join(sev_items)}.\\n")
        else:
            if "tabla_gruas_motivos" in tablas:
                partes.append("#### Tipología de Auxilios Mecánicos (Grúas)")
                partes.append(tablas["tabla_gruas_motivos"])
                partes.append("")
            if "tabla_ambulancias_incidentes" in tablas:
                partes.append("#### Tipología de Emergencias Médicas (Ambulancias)")
                partes.append(tablas["tabla_ambulancias_incidentes"])
                sev_items = [f"**{k}**: {v}" for k, v in stats.get("ambulancias_severidad", {}).items()]
                if sev_items:
                    partes.append(f"\n*Severidad de Pacientes:* {', '.join(sev_items)}.\\n")

        # 5. Patrullajes
        if tot_p > 0 and ("patrullajes" in mods or "patrullas" in mods):
            nov_p = stats.get("patrullajes_con_novedad", 0)
            norm_p = stats.get("patrullajes_normales", 0)
            partes.append("#### Control de Recorridos de Patrullaje")
            partes.append(
                f"Las unidades de patrullaje vial realizaron **{tot_p:,} recorridos de inspección**, registrando **{norm_p:,} patrullajes sin novedad** "
                f"y **{nov_p:,} intervenciones por novedades en vía**.\n"
            )

        # 6. Conclusiones y Recomendaciones Estratégicas Basadas en Puntos Críticos Reales
        partes.append("#### Recomendaciones de Operación")
        top_s = stats.get("top_1_sector")
        if not top_s and top_secs:
            s0 = top_secs[0]
            c0 = s0.get("cantidad") if s0.get("cantidad") is not None else (s0.get("atenciones") if s0.get("atenciones") is not None else s0.get("asistencias_totales", 0))
            top_s = {
                "sector": s0.get("sector"),
                "cantidad": c0,
                "porcentaje": s0.get("porcentaje", "0%")
            }

        top_t = stats.get("top_1_tipologia")
        if not top_t:
            if solo_amb and stats.get("ambulancias_top_incidentes"):
                i0 = stats["ambulancias_top_incidentes"][0]
                ci = i0.get("cantidad") if i0.get("cantidad") is not None else i0.get("atenciones", 0)
                top_t = {
                    "tipologia": i0.get("tipo"),
                    "cantidad": ci,
                    "porcentaje": i0.get("porcentaje", "0%")
                }
            elif solo_gruas and stats.get("gruas_top_motivos"):
                m0 = stats["gruas_top_motivos"][0]
                cm = m0.get("cantidad") if m0.get("cantidad") is not None else m0.get("asistencias", 0)
                top_t = {
                    "tipologia": m0.get("motivo"),
                    "cantidad": cm,
                    "porcentaje": m0.get("porcentaje", "0%")
                }
            elif stats.get("ambulancias_top_incidentes"):
                i0 = stats["ambulancias_top_incidentes"][0]
                ci = i0.get("cantidad") if i0.get("cantidad") is not None else i0.get("atenciones", 0)
                top_t = {
                    "tipologia": i0.get("tipo"),
                    "cantidad": ci,
                    "porcentaje": i0.get("porcentaje", "0%")
                }
            elif stats.get("gruas_top_motivos"):
                m0 = stats["gruas_top_motivos"][0]
                cm = m0.get("cantidad") if m0.get("cantidad") is not None else m0.get("asistencias", 0)
                top_t = {
                    "tipologia": m0.get("motivo"),
                    "cantidad": cm,
                    "porcentaje": m0.get("porcentaje", "0%")
                }

        mes_p = stats.get("mes_pico")

        rec_num = 1
        if top_s:
            partes.append(
                f"{rec_num}. **Posicionamiento Preventivo en Punto Crítico:** Desplegar una base de avanzada prioritaria "
                f"en **{top_s['sector']}**, sector que registró la mayor siniestralidad con **{top_s['cantidad']:,} eventos ({top_s['porcentaje']})**, "
                f"para optimizar tiempos de respuesta y despeje de calzada."
            )
            rec_num += 1
        else:
            partes.append(f"{rec_num}. Posicionar unidades en los tramos con mayor recurrencia identificada para reducir tiempos de atención.")
            rec_num += 1

        if top_t:
            partes.append(
                f"{rec_num}. **Plan de Mitigación de Causa Principal:** Implementar protocolos técnicos enfocados en la atención ágil de "
                f"**{top_t['tipologia']}** (principal factor con **{top_t['cantidad']:,} asistencias, {top_t['porcentaje']}**), dotando a las unidades "
                f"con herramental especializado para resolver averías sin requerir remolques innecesarios."
            )
            rec_num += 1
        else:
            partes.append(f"{rec_num}. Priorizar el despeje ágil de la calzada para evitar incidentes colaterales.")
            rec_num += 1

        if mes_p and stats.get("rango_multimes"):
            partes.append(
                f"{rec_num}. **Refuerzo Operativo Estacional:** Reforzar turnos de guardia y disponibilidad mecánica en meses de máxima demanda "
                f"como **{mes_p['mes']}** (**{mes_p['total']:,} eventos**), asegurando cobertura continua ante picos de tráfico."
            )
        else:
            partes.append(f"{rec_num}. Mantener el registro continuo de datos de campo para optimizar la toma de decisiones operativas.")

        return "\n".join(partes)

    def _sanitizar_texto_ia(self, texto: str) -> str:
        """
        Limpia la respuesta generada por el LLM preservando tablas Markdown,
        viñetas estructuradas y encabezados ejecutivos.
        """
        if not texto:
            return ""

        texto_limpio = texto.replace('“', '"').replace('”', '"')
        texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_limpio).strip()
        return texto_limpio

    def _construir_prompts_analisis(
        self,
        prompt_usuario: str,
        estadisticas: Dict[str, Any],
        modulos_solicitados: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Construye el System Prompt y User Prompt inyectando directamente las tablas Markdown
        precalculadas, asignando a Qwen el rol estricto de Redactor Ejecutivo y Estratega Operativo,
        e instruyéndolo terminantemente a NO recalcular cifras ni alterar la matemática.
        """
        mods = modulos_solicitados or self._detectar_modulos_de_contexto(prompt_usuario, estadisticas)
        solo_gruas = ("gruas" in mods) and ("ambulancias" not in mods)
        solo_amb = ("ambulancias" in mods) and ("gruas" not in mods)

        tablas = self._generar_tablas_markdown(estadisticas, mods)
        periodo = estadisticas.get("periodo", "")
        aviso_disp = estadisticas.get("aviso_disponibilidad")
        tot_gen = estadisticas.get("total_general", 0)
        tot_asist = estadisticas.get("total_asistencias_via", 0)
        
        top_s = estadisticas.get("top_1_sector")
        if not top_s:
            s_cand = estadisticas.get("asistencias_top_tramos") or estadisticas.get("ambulancias_top_sectores") or estadisticas.get("gruas_top_sectores")
            if s_cand:
                s0 = s_cand[0]
                c0 = s0.get("cantidad") if s0.get("cantidad") is not None else (s0.get("atenciones") if s0.get("atenciones") is not None else s0.get("asistencias_totales", 0))
                top_s = {
                    "sector": s0.get("sector"),
                    "cantidad": c0,
                    "porcentaje": s0.get("porcentaje", "0%"),
                    "texto": f"{s0.get('sector')}: {c0} ({s0.get('porcentaje', '0%')})"
                }

        top_t = estadisticas.get("top_1_tipologia")
        if not top_t:
            if solo_amb and estadisticas.get("ambulancias_top_incidentes"):
                i0 = estadisticas["ambulancias_top_incidentes"][0]
                ci = i0.get("cantidad") if i0.get("cantidad") is not None else i0.get("atenciones", 0)
                top_t = {
                    "tipologia": i0.get("tipo"),
                    "cantidad": ci,
                    "porcentaje": i0.get("porcentaje", "0%")
                }
            elif solo_gruas and estadisticas.get("gruas_top_motivos"):
                m0 = estadisticas["gruas_top_motivos"][0]
                cm = m0.get("cantidad") if m0.get("cantidad") is not None else m0.get("asistencias", 0)
                top_t = {
                    "tipologia": m0.get("motivo"),
                    "cantidad": cm,
                    "porcentaje": m0.get("porcentaje", "0%")
                }
            elif estadisticas.get("ambulancias_top_incidentes"):
                i0 = estadisticas["ambulancias_top_incidentes"][0]
                ci = i0.get("cantidad") if i0.get("cantidad") is not None else i0.get("atenciones", 0)
                top_t = {
                    "tipologia": i0.get("tipo"),
                    "cantidad": ci,
                    "porcentaje": i0.get("porcentaje", "0%")
                }
            elif estadisticas.get("gruas_top_motivos"):
                m0 = estadisticas["gruas_top_motivos"][0]
                cm = m0.get("cantidad") if m0.get("cantidad") is not None else m0.get("asistencias", 0)
                top_t = {
                    "tipologia": m0.get("motivo"),
                    "cantidad": cm,
                    "porcentaje": m0.get("porcentaje", "0%")
                }

        mes_pico = estadisticas.get("mes_pico")

        system_prompt = (
            "Eres el Director de Operaciones Viales y Asistencias de la Concesión ('VialBot AI').\n"
            "Tu misión es redactar un Informe Ejecutivo de Operaciones Viales de alto nivel, profesional, analítico y conciso.\n\n"
            "REGLAS OBLIGATORIAS Y MATEMÁTICA ESTRICTA:\n"
            "1. ROL DE REDACTOR ESTRATÉGICO, NUNCA CALCULADOR:\n"
            "   - Tienes TERMINANTEMENTE PROHIBIDO calcular sumas, porcentajes o alterar los conteos provistos.\n"
            "   - Todas las tablas y métricas han sido calculadas con precisión matemática en el backend de SQL Server.\n"
            "   - Transcribe e incorpora las tablas Markdown provistas EXACTAMENTE como se te entregan, sin modificar números ni porcentajes.\n"
            "2. FIDELIDAD TEMPORAL Y AVISO DE DISPONIBILIDAD:\n"
            "   - Cita siempre el período evaluado exacto indicado en los datos.\n"
            "   - Si se incluye un 'Aviso de disponibilidad', DEBES colocarlo obligatoriamente al inicio del informe como una alerta destacada en negrita (ej: > **Aviso de disponibilidad:** ...).\n"
            "3. DESGLOSE TERRITORIAL (SECTORES):\n"
            "   - En párrafos y menciones territoriales en prosa, indica SIEMPRE tanto la cantidad absoluta como el porcentaje relativo con el formato estricto: 'Sector: Cantidad (XX.X%)' (ejemplo: 'PEAJE EL CONGOMA: 73 (35.8%)'). PROHIBIDO omitir la cantidad o mostrar solo el porcentaje.\n"
            "4. ANÁLISIS DE EVOLUCIÓN MENSUAL:\n"
            "   - Si se presenta la tabla de distribución mensual, incluye una sección de 'Evolución Temporal y Tendencia' describiendo el comportamiento mes a mes: cuál fue el mes con mayor demanda (pico), cómo varió la tendencia y la estabilidad operativa, basándote exclusivamente en la tabla provista.\n"
            "5. RECOMENDACIONES OPERATIVAS BASADAS ESTRICTAMENTE EN DATOS REALES:\n"
            "   - Prohibido emitir recomendaciones genéricas o de relleno.\n"
            "   - Vincula las recomendaciones directamente con los datos duros provistos:\n"
            "     * Ubicación estratégica de unidades y bases prioritarias en el Sector Crítico #1 identificado (citando nombre, cantidad y %).\n"
            "     * Protocolos técnicos específicos orientados a mitigar la Tipología Principal #1 identificada (citando causa, cantidad y %).\n"
            "     * Si hay desglose mensual, refuerzo operativo para el mes pico identificado.\n"
            "6. ENFOQUE EXCLUSIVO EN EL SERVICIO SOLICITADO:\n"
            "   - Si la consulta es de Grúas, responde sobre Grúas. Prohibido decir que hubo 0 ambulancias.\n"
            "   - Si la consulta es de Ambulancias, responde sobre Ambulancias. Prohibido decir que hubo 0 grúas.\n"
            "7. CERO ESPECULACIÓN: No inventes lluvia, niebla, pendientes ni curvas no presentes en los datos.\n"
            "8. NO menciones aspectos técnicos internos (SQL Server, backend, JSON, bases de datos).\n"
            "9. Mantén un tono formal, ejecutivo y directivo (máximo 400 palabras)."
        )

        bloque_datos = []
        bloque_datos.append(f"**Período Evaluado:** {periodo}")
        if aviso_disp:
            bloque_datos.append(f"> **{aviso_disp}**")

        if solo_gruas:
            bloque_datos.append(f"**Total Auxilios de Grúas:** {estadisticas.get('gruas_total', 0):,} eventos")
        elif solo_amb:
            bloque_datos.append(f"**Total Atenciones de Ambulancias:** {estadisticas.get('ambulancias_total', 0):,} atenciones")
        else:
            bloque_datos.append(f"**Total General Asistencias:** {tot_asist:,} eventos")
            bloque_datos.append(f"- Grúas: {estadisticas.get('gruas_total', 0):,} | Ambulancias: {estadisticas.get('ambulancias_total', 0):,}")

        if top_s:
            texto_s = top_s.get("texto") or f"{top_s.get('sector')}: {top_s.get('cantidad')} ({top_s.get('porcentaje')})"
            bloque_datos.append(f"**Sector Crítico #1:** {texto_s}")
        if top_t:
            bloque_datos.append(f"**Tipología Principal #1:** {top_t['tipologia']} con {top_t['cantidad']:,} casos ({top_t['porcentaje']})")
        if mes_pico:
            bloque_datos.append(f"**Mes Pico con Mayor Demanda:** {mes_pico['mes']} con {mes_pico['total']:,} eventos ({mes_pico['porcentaje']})")

        bloque_datos.append("\n### TABLAS OFICIALES PRECALCULADAS:")
        if "tabla_mensual" in tablas:
            bloque_datos.append("#### Evolución Mensual\n" + tablas["tabla_mensual"])
        if "tabla_sectores" in tablas:
            bloque_datos.append("#### Concentración por Sectores Viales\n" + tablas["tabla_sectores"])
        if "tabla_gruas_motivos" in tablas:
            bloque_datos.append("#### Tipología de Auxilios Mecánicos (Grúas)\n" + tablas["tabla_gruas_motivos"])
        if "tabla_ambulancias_incidentes" in tablas:
            bloque_datos.append("#### Tipología de Emergencias Médicas (Ambulancias)\n" + tablas["tabla_ambulancias_incidentes"])

        texto_datos_markdown = "\n\n".join(bloque_datos)

        user_content = (
            f"Consulta del Operador: {prompt_usuario}\n\n"
            f"DATOS Y TABLAS OPERATIVAS VALIDADAS:\n"
            f"{texto_datos_markdown}\n\n"
            "INSTRUCCIONES DE REDACCIÓN:\n"
            "Redacta el informe ejecutivo incorporando las tablas anteriores sin modificar cifras. "
            "Incluye el análisis de tendencia mensual (si aplica), describe la concentración territorial en formato 'Sector: Cantidad (XX.X%)', "
            "y formula recomendaciones operativas concretas basadas explícitamente en el Sector Crítico #1 y la Tipología Principal #1 identificados."
        )

        return system_prompt, user_content

    async def procesar_peticion(
        self,
        prompt_usuario: str,
        db: Session,
        historial: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa la consulta y devuelve el resultado completo (modo síncrono).
        """
        dt_inicio, dt_fin, formato, modulos = await self._interpretar_intencion(
            prompt=prompt_usuario,
            historial=historial,
            session_id=session_id
        )

        f_ini_date = dt_inicio.date() if isinstance(dt_inicio, datetime) else dt_inicio
        f_fin_date = dt_fin.date() if isinstance(dt_fin, datetime) else dt_fin

        contexto = {
            "rango_busqueda": f"Desde {f_ini_date} hasta {f_fin_date}"
        }

        limite_extraccion = 50000

        if "ambulancias" in modulos:
            ambulancias = operaciones_service.listar_ambulancias(db=db, fecha_inicio=dt_inicio, fecha_fin=dt_fin, limit=limite_extraccion)
            contexto["ambulancias"] = self._formatear_ambulancias(ambulancias)

        if "gruas" in modulos:
            gruas = operaciones_service.listar_gruas(db=db, fecha_inicio=dt_inicio, fecha_fin=dt_fin, limit=limite_extraccion)
            contexto["gruas"] = self._formatear_gruas(gruas)

        if "patrullajes" in modulos or "patrullas" in modulos:
            patrullajes = operaciones_service.listar_patrullajes(db=db, fecha_inicio=f_ini_date, fecha_fin=f_fin_date, limit=limite_extraccion)
            patrullajes_procesados = []
            for p in patrullajes:
                hubo_novedad = p.novedad_en_via
                obs_baja = (p.observaciones or "").lower()
                es_normal = (not hubo_novedad) or ("sin novedad" in obs_baja)
                clasificacion = "RECORRIDO NORMAL" if es_normal else "INCIDENTE"

                patrullajes_procesados.append({
                    "fecha": str(p.fecha_recorrido),
                    "codigo": p.codigo_patrullaje,
                    "ruta": p.ruta_descripcion,
                    "hubo_novedad": hubo_novedad,
                    "observaciones": p.observaciones,
                    "CLASIFICACION": clasificacion
                })
            contexto["patrullajes"] = patrullajes_procesados

        estadisticas = self._generar_resumen_estadistico(contexto, dt_inicio, dt_fin)
        system_prompt, user_content = self._construir_prompts_analisis(prompt_usuario, estadisticas, modulos)

        payload = {
            "model": MODELO_OLLAMA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "temperature": 0.1,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {
                "num_thread": NUM_THREADS,
                "num_ctx": 2048,
                "num_predict": 750
            }
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(OLLAMA_URL, json=payload)
                res.raise_for_status()
                respuesta_ia = self._sanitizar_texto_ia(res.json()["message"]["content"])

                return {
                    "solicita_exportacion": bool(formato in ("excel", "pdf")),
                    "formato_exportacion": formato,
                    "respuesta_ia": respuesta_ia,
                    "datos_crudos": contexto,
                    "modulos_solicitados": modulos,
                    "estadisticas": estadisticas
                }

        except Exception as e:
            logger.warning(f"Ollama no respondió o error ({e}). Activando respaldo analítico directo.")
            respuesta_directa = self._generar_respuesta_directa_respaldo(prompt_usuario, estadisticas, modulos)
            return {
                "solicita_exportacion": bool(formato in ("excel", "pdf")),
                "formato_exportacion": formato,
                "respuesta_ia": respuesta_directa,
                "datos_crudos": contexto,
                "modulos_solicitados": modulos,
                "estadisticas": estadisticas
            }

    async def procesar_peticion_stream(
        self,
        prompt_usuario: str,
        db: Session,
        historial: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generador asíncrono para streaming (SSE / OpenAI Chunking).
        Emite el evento inicial con estadísticas de SQL y luego los tokens del LLM en tiempo real.
        """
        dt_inicio, dt_fin, formato, modulos = await self._interpretar_intencion(
            prompt=prompt_usuario,
            historial=historial,
            session_id=session_id
        )

        f_ini_date = dt_inicio.date() if isinstance(dt_inicio, datetime) else dt_inicio
        f_fin_date = dt_fin.date() if isinstance(dt_fin, datetime) else dt_fin

        contexto = {
            "rango_busqueda": f"Desde {f_ini_date} hasta {f_fin_date}"
        }

        limite_extraccion = 50000

        if "ambulancias" in modulos:
            ambulancias = operaciones_service.listar_ambulancias(db=db, fecha_inicio=dt_inicio, fecha_fin=dt_fin, limit=limite_extraccion)
            contexto["ambulancias"] = self._formatear_ambulancias(ambulancias)

        if "gruas" in modulos:
            gruas = operaciones_service.listar_gruas(db=db, fecha_inicio=dt_inicio, fecha_fin=dt_fin, limit=limite_extraccion)
            contexto["gruas"] = self._formatear_gruas(gruas)

        if "patrullajes" in modulos or "patrullas" in modulos:
            patrullajes = operaciones_service.listar_patrullajes(db=db, fecha_inicio=f_ini_date, fecha_fin=f_fin_date, limit=limite_extraccion)
            patrullajes_procesados = []
            for p in patrullajes:
                hubo_novedad = p.novedad_en_via
                obs_baja = (p.observaciones or "").lower()
                es_normal = (not hubo_novedad) or ("sin novedad" in obs_baja)
                clasificacion = "RECORRIDO NORMAL" if es_normal else "INCIDENTE"

                patrullajes_procesados.append({
                    "fecha": str(p.fecha_recorrido),
                    "codigo": p.codigo_patrullaje,
                    "ruta": p.ruta_descripcion,
                    "hubo_novedad": hubo_novedad,
                    "observaciones": p.observaciones,
                    "CLASIFICACION": clasificacion
                })
            contexto["patrullajes"] = patrullajes_procesados

        estadisticas = self._generar_resumen_estadistico(contexto, dt_inicio, dt_fin)

        # Emite primer chunk de metadatos (estadísticas y formato de exportación)
        yield {
            "tipo": "meta",
            "solicita_exportacion": bool(formato in ("excel", "pdf")),
            "formato_exportacion": formato,
            "estadisticas": estadisticas,
            "datos_crudos": contexto,
            "modulos_solicitados": modulos
        }

        # Si solicita exportar archivo, no hacemos streaming de texto hacia la vista
        if formato in ("excel", "pdf"):
            return

        system_prompt, user_content = self._construir_prompts_analisis(prompt_usuario, estadisticas, modulos)

        payload = {
            "model": MODELO_OLLAMA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "stream": True,
            "temperature": 0.1,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {
                "num_thread": NUM_THREADS,
                "num_ctx": 2048,
                "num_predict": 750
            }
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            yield {
                                "tipo": "token",
                                "contenido": token
                            }
                            if data.get("done", False):
                                yield {"tipo": "done"}
                                break

        except Exception as e:
            logger.warning(f"Streaming Ollama interrumpido ({e}). Emitiendo análisis estructurado directo.")
            respuesta_directa = self._generar_respuesta_directa_respaldo(prompt_usuario, estadisticas, modulos)
            yield {
                "tipo": "token",
                "contenido": respuesta_directa
            }
            yield {"tipo": "done"}


ai_service = AIService()
