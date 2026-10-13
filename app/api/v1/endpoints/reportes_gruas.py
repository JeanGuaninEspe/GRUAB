"""
Endpoint de Analítica e Informe Ejecutivo con IA para Asistencias de Grúas.
- POST /api/v1/reportes-gruas/ejecutivo-ia
CERO matemáticas delegadas al LLM: Las agregaciones se calculan en SQL y Pandas,
y se inyectan en un prompt rígido a Qwen 2.5 local (Ollama) para redacción ejecutiva.
"""
import calendar
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaccionales import AsistenciaGrua

logger = logging.getLogger(__name__)

router = APIRouter()

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELO_OLLAMA = "qwen2.5:3b"

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


class ReporteEjecutivoIARequest(BaseModel):
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio del periodo a auditar")
    fecha_fin: datetime = Field(..., description="Fecha y hora de fin del periodo a auditar")


class DesgloseMensualItem(BaseModel):
    mes: str
    total: int
    porcentaje: str
    porcentaje_num: float


class DesgloseSectorItem(BaseModel):
    sector: str
    cantidad: int
    porcentaje: str
    porcentaje_num: float


class DesgloseCruzadoItem(BaseModel):
    motivo: str
    pequena: int
    grande: int
    plataforma: int
    otros: int
    total: int
    porcentaje: str
    porcentaje_num: float


class TiemposPromedio(BaseModel):
    respuesta_min: float = Field(..., description="Tiempo promedio de respuesta (arribo - llamada) en minutos")
    despeje_min: float = Field(..., description="Tiempo promedio de maniobra/despeje (término - arribo) en minutos")


class KpisReporte(BaseModel):
    total_eventos: int
    tpa_respuesta_min: float
    tpa_despeje_min: float
    tramo_critico: str
    tramo_critico_cantidad: int
    tramo_critico_pct: str
    porcentaje_mecanicos: str
    motivo_principal: str
    motivo_principal_pct: str
    tipo_grua_principal: str


class ReporteEjecutivoIAResponse(BaseModel):
    periodo: str
    fecha_inicio: str
    fecha_fin: str
    total_auxilios: int
    kpis: KpisReporte
    desglose_mensual: List[DesgloseMensualItem]
    desglose_sectores: List[DesgloseSectorItem]
    desglose_cruzado: List[DesgloseCruzadoItem]
    tiempos_promedio: TiemposPromedio
    resumen_markdown: str


def ajustar_porcentajes_a_100(
    items: List[Dict[str, Any]],
    clave_cant: str = "cantidad",
    clave_pct_str: str = "porcentaje",
    clave_pct_num: str = "porcentaje_num",
    total: Optional[int] = None,
) -> None:
    """Garantiza que la suma de porcentajes numéricos y strings sea exactamente 100.0%."""
    if not items:
        return
    tot = total if (total is not None and total > 0) else sum(it.get(clave_cant, 0) for it in items)
    if tot <= 0:
        for it in items:
            it[clave_pct_str] = "0.0%"
            it[clave_pct_num] = 0.0
        return

    pcts = [round((it.get(clave_cant, 0) / tot) * 100.0, 1) for it in items]
    diff = round(100.0 - sum(pcts), 1)

    if abs(diff) > 0 and abs(diff) <= 1.0:
        idx_max = max(range(len(items)), key=lambda i: items[i].get(clave_cant, 0))
        pcts[idx_max] = round(pcts[idx_max] + diff, 1)

    for i, it in enumerate(items):
        it[clave_pct_num] = pcts[i]
        it[clave_pct_str] = f"{pcts[i]:.1f}%"


def redaccion_fallback(
    periodo_str: str,
    total: int,
    kpis: Dict[str, Any],
    top_sectores: List[Dict[str, Any]],
    top_cruzado: List[Dict[str, Any]],
    tiempos: Dict[str, Any],
) -> str:
    """Generador determinista de informe ejecutivo estructurado en caso de no disponibilidad de Ollama."""
    sector_1 = top_sectores[0] if top_sectores else {"sector": "N/D", "cantidad": 0, "porcentaje": "0.0%"}
    sector_2 = top_sectores[1] if len(top_sectores) > 1 else {"sector": "N/D", "cantidad": 0, "porcentaje": "0.0%"}
    motivo_1 = top_cruzado[0] if top_cruzado else {"motivo": "N/D", "total": 0, "porcentaje": "0.0%"}

    return f"""# INFORME EJECUTIVO DE OPERACIONES DE GRÚAS
**Concesión Vial COSAD 25 | Auditoría Operativa y Análisis de Siniestralidad**

**Período Evaluado:** {periodo_str}  
**Total de Auxilios Mecánicos y Remolques:** {total} eventos asistidos

---

### 1. Resumen Ejecutivo de la Operación
Durante el período analizado comprendido entre el **{periodo_str}**, el servicio de grúas de la concesión atendió un total de **{total} auxilios viales**. 
El desempeño de la flota reflejó un **Tiempo Promedio de Respuesta (TPA)** de **{tiempos['respuesta_min']:.1f} minutos** desde la recepción de la llamada hasta el arribo en sitio, y un **Tiempo Promedio de Despeje** de **{tiempos['despeje_min']:.1f} minutos** para la maniobra y liberación de la calzada.
El **{kpis['porcentaje_mecanicos']}** de los incidentes asistidos correspondieron a fallas mecánicas de diversa índole, consolidándose como la causa preponderante de requerimiento de grúa.

---

### 2. Análisis del Tramo Crítico (Foco Prioritario en Sector #1)
El análisis geoespacial identifica a **{sector_1['sector']}** como el punto crítico con mayor siniestralidad y concentración de demanda, registrando **{sector_1['cantidad']} auxilios**, lo que representa el **{sector_1['porcentaje']}** de la carga operativa total del corredor.
En segundo término se sitúa el tramo **{sector_2['sector']}** con **{sector_2['cantidad']} auxilios ({sector_2['porcentaje']})**.
La alta incidencia en **{sector_1['sector']}** evidencia una necesidad imperativa de refuerzo de patrullaje preventivo y pre-posicionamiento estratégico en dicho sector.

---

### 3. Tipología de Auxilios y Despliegue de Unidades
La tipología con mayor recurrencia fue **{motivo_1['motivo']}**, totalizando **{motivo_1['total']} eventos ({motivo_1['porcentaje']})**. 
La unidad operativa con mayor tasa de asignación fue la grúa tipo **{kpis['tipo_grua_principal']}**, atendiendo principalmente vehículos livianos y transporte comercial mediano.

---

### 4. Recomendaciones Operativas Estratégicas
1. **Puesto de Avanzada en {sector_1['sector']}:** Implementar una base de espera estratégica de grúa de plataforma / pluma en el tramo **{sector_1['sector']}** para recortar los {tiempos['respuesta_min']:.1f} min actuales a un objetivo inferior a 15 minutos en horas pico.
2. **Campaña Preventiva sobre '{motivo_1['motivo']}':** Coordinar con la brigada de patrullaje inspecciones de detenciones indebidas en berma y puntos de control de temperatura de neumáticos y recalentamiento antes de las pendientes pronunciadas del sector crítico.
3. **Mantenimiento Preventivo de Flota:** Garantizar disponibilidad permanente de repuestos y mantenimiento en grúas tipo **{kpis['tipo_grua_principal']}**, garantizando disponibilidad > 95% ante la alta rotación registrada.
"""


@router.post(
    "/ejecutivo-ia",
    response_model=ReporteEjecutivoIAResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar informe ejecutivo de grúas asistido por IA",
    description=(
        "Ejecuta agregaciones deterministas en SQL y Pandas sobre dbo.asistencias_grua, "
        "calculando desglose mensual, sectores críticos, matriz cruzada (motivo vs grúa) "
        "y tiempos de respuesta/despeje. Inyecta los datos matemáticos cerrados en Qwen 2.5 "
        "para una redacción analítica de alto nivel con foco en el Sector #1 y la Tipología #1."
    ),
)
async def generar_reporte_ejecutivo_ia(
    req: ReporteEjecutivoIARequest,
    db: Session = Depends(get_db),
) -> ReporteEjecutivoIAResponse:
    f_ini = req.fecha_inicio
    f_fin = req.fecha_fin

    if f_fin < f_ini:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha_fin no puede ser anterior a la fecha_inicio.",
        )

    # 1. Extracción de registros de la base de datos SQL Server
    query = (
        db.query(AsistenciaGrua)
        .filter(AsistenciaGrua.ts_llamada >= f_ini, AsistenciaGrua.ts_llamada <= f_fin)
        .order_by(AsistenciaGrua.ts_llamada.asc())
    )
    df = pd.read_sql(query.statement, db.bind)

    periodo_str = f"Del {f_ini.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')}"
    total_auxilios = len(df)

    if total_auxilios == 0:
        kpis_vacio = KpisReporte(
            total_eventos=0,
            tpa_respuesta_min=0.0,
            tpa_despeje_min=0.0,
            tramo_critico="Sin registros",
            tramo_critico_cantidad=0,
            tramo_critico_pct="0.0%",
            porcentaje_mecanicos="0.0%",
            motivo_principal="Sin registros",
            motivo_principal_pct="0.0%",
            tipo_grua_principal="N/A",
        )
        return ReporteEjecutivoIAResponse(
            periodo=periodo_str,
            fecha_inicio=f_ini.strftime("%Y-%m-%d %H:%M:%S"),
            fecha_fin=f_fin.strftime("%Y-%m-%d %H:%M:%S"),
            total_auxilios=0,
            kpis=kpis_vacio,
            desglose_mensual=[],
            desglose_sectores=[],
            desglose_cruzado=[],
            tiempos_promedio=TiemposPromedio(respuesta_min=0.0, despeje_min=0.0),
            resumen_markdown=f"### Sin Datos Registrados\nNo se encontraron asistencias de grúas en el período {periodo_str}.",
        )

    # Normalización de textos para consistencia
    df["sector_limpio"] = df["sector_referencia"].fillna("").astype(str).str.strip()
    df["sector_limpio"] = df["sector_limpio"].replace("", "Otros / No clasificado")

    df["motivo_limpio"] = df["motivo_atencion"].fillna("").astype(str).str.strip()
    df["motivo_limpio"] = df["motivo_limpio"].replace("", "Otros / No clasificado")

    df["tipo_grua_limpio"] = df["tipo_grua"].fillna("").astype(str).str.strip().str.upper()
    df["tipo_grua_limpio"] = df["tipo_grua_limpio"].replace("", "OTROS")

    # 2. Desglose Mensual (Mes | Total | %)
    df["ts_dt"] = pd.to_datetime(df["ts_llamada"])
    df["anio_mes"] = df["ts_dt"].dt.to_period("M")

    mensual_dict: List[Dict[str, Any]] = []
    conteo_mensual = df.groupby("anio_mes").size().reset_index(name="cantidad")
    conteo_mensual = conteo_mensual.sort_values(by="anio_mes")

    for _, row in conteo_mensual.iterrows():
        periodo_m = row["anio_mes"]
        nombre_mes = f"{MESES_NOMBRES[periodo_m.month]} {periodo_m.year}"
        cant = int(row["cantidad"])
        mensual_dict.append({
            "mes": nombre_mes,
            "cantidad": cant,
            "total": cant,
        })

    ajustar_porcentajes_a_100(
        mensual_dict,
        clave_cant="cantidad",
        clave_pct_str="porcentaje",
        clave_pct_num="porcentaje_num",
        total=total_auxilios,
    )
    desglose_mensual = [DesgloseMensualItem(**it) for it in mensual_dict]

    # 3. Desglose por Sector de Referencia (con cantidad absoluta y %)
    sectores_dict: List[Dict[str, Any]] = []
    conteo_sectores = df["sector_limpio"].value_counts()

    # Tomamos los principales y agrupamos el resto en 'Otros' si son más de 7
    top_sectores_n = conteo_sectores.head(7)
    otros_sectores_cant = conteo_sectores.iloc[7:].sum() if len(conteo_sectores) > 7 else 0

    for sector_nom, cant in top_sectores_n.items():
        if sector_nom != "Otros / No clasificado":
            sectores_dict.append({
                "sector": sector_nom,
                "cantidad": int(cant),
            })
    if otros_sectores_cant > 0 or "Otros / No clasificado" in top_sectores_n:
        otros_total = otros_sectores_cant + int(top_sectores_n.get("Otros / No clasificado", 0))
        sectores_dict.append({
            "sector": "Otros / No clasificado",
            "cantidad": otros_total,
        })

    ajustar_porcentajes_a_100(
        sectores_dict,
        clave_cant="cantidad",
        clave_pct_str="porcentaje",
        clave_pct_num="porcentaje_num",
        total=total_auxilios,
    )
    desglose_sectores = [DesgloseSectorItem(**it) for it in sectores_dict]

    # 4. Desglose Cruzado: Motivo de Atención vs Tipo de Grúa
    # Clasificación de tipo de grúa: PEQUEÑA, GRANDE, PLATAFORMA, OTROS
    cruzado_dict: List[Dict[str, Any]] = []
    conteo_motivos = df["motivo_limpio"].value_counts()
    top_motivos_n = conteo_motivos.head(6)
    resto_motivos_cant = conteo_motivos.iloc[6:].sum() if len(conteo_motivos) > 6 else 0

    motivos_a_procesar = [m for m in top_motivos_n.index if m != "Otros / No clasificado"]

    for m in motivos_a_procesar:
        sub_df = df[df["motivo_limpio"] == m]
        peq = int(sub_df[sub_df["tipo_grua_limpio"].str.contains("PEQUE|PEQ", na=False)].shape[0])
        gra = int(sub_df[sub_df["tipo_grua_limpio"].str.contains("GRANDE", na=False)].shape[0])
        plat = int(sub_df[sub_df["tipo_grua_limpio"].str.contains("PLATAFORMA", na=False)].shape[0])
        otros = int(sub_df.shape[0] - (peq + gra + plat))
        if otros < 0:
            otros = 0
        tot_m = int(sub_df.shape[0])
        cruzado_dict.append({
            "motivo": m,
            "pequena": peq,
            "grande": gra,
            "plataforma": plat,
            "otros": otros,
            "cantidad": tot_m,
            "total": tot_m,
        })

    # Fila consolidada de 'Otros / No clasificado'
    df_otros = df[~df["motivo_limpio"].isin(motivos_a_procesar)]
    if not df_otros.empty:
        peq_o = int(df_otros[df_otros["tipo_grua_limpio"].str.contains("PEQUE|PEQ", na=False)].shape[0])
        gra_o = int(df_otros[df_otros["tipo_grua_limpio"].str.contains("GRANDE", na=False)].shape[0])
        plat_o = int(df_otros[df_otros["tipo_grua_limpio"].str.contains("PLATAFORMA", na=False)].shape[0])
        otr_o = int(df_otros.shape[0] - (peq_o + gra_o + plat_o))
        if otr_o < 0:
            otr_o = 0
        tot_o = int(df_otros.shape[0])
        cruzado_dict.append({
            "motivo": "Otros / No clasificado",
            "pequena": peq_o,
            "grande": gra_o,
            "plataforma": plat_o,
            "otros": otr_o,
            "cantidad": tot_o,
            "total": tot_o,
        })

    ajustar_porcentajes_a_100(
        cruzado_dict,
        clave_cant="cantidad",
        clave_pct_str="porcentaje",
        clave_pct_num="porcentaje_num",
        total=total_auxilios,
    )
    desglose_cruzado = [DesgloseCruzadoItem(**it) for it in cruzado_dict]

    # 5. Tiempos Promedio: Respuesta (arribo - llamada) y Despeje (termino - arribo)
    df["ts_arribo_dt"] = pd.to_datetime(df["ts_arribo"])
    df["ts_termino_dt"] = pd.to_datetime(df["ts_termino"])

    df["minutos_respuesta"] = (df["ts_arribo_dt"] - df["ts_dt"]).dt.total_seconds() / 60.0
    df["minutos_despeje"] = (df["ts_termino_dt"] - df["ts_arribo_dt"]).dt.total_seconds() / 60.0

    # Filtramos valores válidos no anómalos (0 a 300 minutos)
    valid_resp = df["minutos_respuesta"].dropna()
    valid_resp = valid_resp[(valid_resp >= 0) & (valid_resp <= 300)]
    tpa_respuesta = round(float(valid_resp.mean()), 1) if not valid_resp.empty else 0.0

    valid_desp = df["minutos_despeje"].dropna()
    valid_desp = valid_desp[(valid_desp >= 0) & (valid_desp <= 600)]
    tpa_despeje = round(float(valid_desp.mean()), 1) if not valid_desp.empty else 0.0

    tiempos_promedio = TiemposPromedio(
        respuesta_min=tpa_respuesta,
        despeje_min=tpa_despeje,
    )

    # 6. Identificación de KPIs Principales
    sector_top_1 = desglose_sectores[0] if desglose_sectores else None
    motivo_top_1 = desglose_cruzado[0] if desglose_cruzado else None

    # Porcentaje de mecánicos (daños mecánicos vs accidentes/otros)
    df_mecanicos = df[df["motivo_limpio"].str.contains("MECANIC|MECÁNICO|MECANICO|AVERIA|AVARÍA", case=False, na=False)]
    cant_mecanicos = len(df_mecanicos)
    pct_mecanicos = f"{(cant_mecanicos / total_auxilios * 100.0):.1f}%" if total_auxilios > 0 else "0.0%"

    tipo_grua_top = df["tipo_grua_limpio"].mode()
    tipo_grua_principal = str(tipo_grua_top.iloc[0]) if not tipo_grua_top.empty else "PEQUEÑA"

    kpis = KpisReporte(
        total_eventos=total_auxilios,
        tpa_respuesta_min=tpa_respuesta,
        tpa_despeje_min=tpa_despeje,
        tramo_critico=sector_top_1.sector if sector_top_1 else "N/D",
        tramo_critico_cantidad=sector_top_1.cantidad if sector_top_1 else 0,
        tramo_critico_pct=sector_top_1.porcentaje if sector_top_1 else "0.0%",
        porcentaje_mecanicos=pct_mecanicos,
        motivo_principal=motivo_top_1.motivo if motivo_top_1 else "N/D",
        motivo_principal_pct=motivo_top_1.porcentaje if motivo_top_1 else "0.0%",
        tipo_grua_principal=tipo_grua_principal,
    )

    # 7. Formateo de Tablas en Markdown para el Prompt Rígido del LLM
    tabla_mensual_md = "| Mes | Total Auxilios | % del Período |\n|---|---:|---:|\n"
    for m in desglose_mensual:
        tabla_mensual_md += f"| {m.mes} | {m.total} | {m.porcentaje} |\n"

    tabla_sectores_md = "| Sector Vial | Auxilios | % |\n|---|---:|---:|\n"
    for s in desglose_sectores:
        tabla_sectores_md += f"| {s.sector} | {s.cantidad} | {s.porcentaje} |\n"

    tabla_cruzada_md = "| Motivo de Atención | Grúa Pequeña | Grúa Grande | Plataforma | Otros | Total | % |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for c in desglose_cruzado:
        tabla_cruzada_md += f"| {c.motivo} | {c.pequena} | {c.grande} | {c.plataforma} | {c.otros} | {c.total} | {c.porcentaje} |\n"

    prompt_sistema_rigido = f"""Eres un Consultor Senior en Operaciones y Seguridad Vial para la Concesión Vial COSAD 25.
Tu misión es redactar un INFORME EJECUTIVO OFICIAL Y ESTRATÉGICO sobre las operaciones de asistencia con grúas en el corredor vial.

REGLAS MATEMÁTICAS ESTRICTAS (CERO INVENCIONES):
1. Las tablas numéricas de abajo fueron calculadas de forma determinista mediante SQL Server y Pandas.
2. NO calcules, NO modifiques, NO redondees ni inventes NINGÚN número o porcentaje.
3. El total de auxilios es EXACTAMENTE {total_auxilios}.
4. El Sector #1 más crítico es EXACTAMENTE '{kpis.tramo_critico}' con {kpis.tramo_critico_cantidad} auxilios ({kpis.tramo_critico_pct}).
5. La Tipología #1 más recurrente es EXACTAMENTE '{kpis.motivo_principal}' con {kpis.motivo_principal_pct}.
6. El TPA Respuesta promedio es {tpa_respuesta} minutos y el TPA Despeje promedio es {tpa_despeje} minutos.
7. El {pct_mecanicos} de las atenciones correspondió a fallas mecánicas.

TABLAS PRE-CALCULADAS OFICIALES:
**Período:** {periodo_str}
**Total de Auxilios:** {total_auxilios}

DESGLOSE MENSUAL (100% CERRADO):
{tabla_mensual_md}

TOP SECTORES VIALES CRÍTICOS (100% CERRADO):
{tabla_sectores_md}

DESGLOSE CRUZADO: MOTIVO DE ATENCIÓN VS TIPO DE GRÚA (100% CERRADO):
{tabla_cruzada_md}

TIEMPOS OPERATIVOS PROMEDIO:
- Tiempo Promedio de Respuesta (arribo - llamada): {tpa_respuesta} minutos.
- Tiempo Promedio de Maniobra y Despeje (término - arribo): {tpa_despeje} minutos.

ESTRUCTURA DEL INFORME REQUERIDA (En Markdown elegante y profesional):
# INFORME EJECUTIVO DE OPERACIONES DE GRÚAS
**Concesión Vial COSAD 25**

### 1. Resumen Ejecutivo
(Diagnóstico global del período, volumen total de asistencias y tiempos de respuesta).

### 2. Análisis del Tramo Crítico (Foco Prioritario en Sector #1: {kpis.tramo_critico})
(Explicación detallada de por qué {kpis.tramo_critico} encabeza la siniestralidad con {kpis.tramo_critico_pct} del total).

### 3. Tipología de Auxilios y Despliegue de Unidades
(Análisis de la tipología dominante '{kpis.motivo_principal}' y el uso de grúas {kpis.tipo_grua_principal}).

### 4. Recomendaciones Operativas Estratégicas
(3 a 4 acciones concretas y viables de mitigación vial, ubicación de patrullas y pre-posicionamiento de grúas en {kpis.tramo_critico}).
"""

    resumen_markdown = ""
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODELO_OLLAMA,
                    "messages": [
                        {"role": "system", "content": "Eres un redactor técnico de informes ejecutivos de concesiones viales."},
                        {"role": "user", "content": prompt_sistema_rigido},
                    ],
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1024,
                    },
                },
            )
            if res.status_code == 200:
                contenido = res.json().get("message", {}).get("content", "")
                if contenido and len(contenido.strip()) > 100:
                    resumen_markdown = contenido.strip()
            else:
                logger.warning(f"Ollama retornó status {res.status_code}. Se activará fallback determinista.")
    except Exception as e:
        logger.warning(f"No fue posible conectar con Ollama ({e}). Se generará informe determinista de alta fidelidad.")

    if not resumen_markdown:
        resumen_markdown = redaccion_fallback(
            periodo_str=periodo_str,
            total=total_auxilios,
            kpis=kpis.model_dump(),
            top_sectores=[s.model_dump() for s in desglose_sectores],
            top_cruzado=[c.model_dump() for c in desglose_cruzado],
            tiempos=tiempos_promedio.model_dump(),
        )

    return ReporteEjecutivoIAResponse(
        periodo=periodo_str,
        fecha_inicio=f_ini.strftime("%Y-%m-%d %H:%M:%S"),
        fecha_fin=f_fin.strftime("%Y-%m-%d %H:%M:%S"),
        total_auxilios=total_auxilios,
        kpis=kpis,
        desglose_mensual=desglose_mensual,
        desglose_sectores=desglose_sectores,
        desglose_cruzado=desglose_cruzado,
        tiempos_promedio=tiempos_promedio,
        resumen_markdown=resumen_markdown,
    )
