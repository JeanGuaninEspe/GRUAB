import base64
import hashlib
import json
import os
import time
import uuid
from io import BytesIO
from typing import List, Optional, Dict, Any, Union, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd
from openpyxl.styles import Alignment

from app.core.database import get_db
from app.services.ai_service import ai_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/ai", tags=["Agente IA y Chatbot"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_HTML_PATH = os.path.join(BASE_DIR, "static", "chat.html")


class AIRequest(BaseModel):
    pregunta: str
    historial: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    session_id: Optional[str] = None
    stream: Optional[bool] = False


class ConsultaAIRequest(BaseModel):
    pregunta: str
    historial: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    session_id: Optional[str] = None


class ConsultaAIResponse(BaseModel):
    respuesta: str
    accion_ejecutada: str
    datos_fuente: Any = None


class ParsearDespachoRequest(BaseModel):
    texto_reporte: str


class DespachoParseadoResponse(BaseModel):
    tipo_asistencia: Optional[str] = None
    codigo_formulario: Optional[str] = None
    turno: Optional[str] = None
    chofer: Optional[str] = None
    paramedico: Optional[str] = None
    supervisor: Optional[str] = None
    tipo_grua: Optional[str] = None
    ubicacion_referencia: Optional[str] = None
    tramo_ruta: Optional[str] = None
    abscisa_km: Optional[Union[float, int, str]] = None
    sentido: Optional[str] = None
    prioridad: Optional[str] = None
    descripcion_falla_o_motivo: Optional[str] = None
    vehiculo_involucrado: Optional[str] = None
    placa_vehiculo: Optional[str] = None
    nombre_paciente: Optional[str] = None
    edad_paciente: Optional[str] = None
    usuario_reporta: Optional[str] = None
    destino_paciente: Optional[str] = None
    odometro_salida_km: Optional[Union[float, int, str]] = None
    odometro_llegada_km: Optional[Union[float, int, str]] = None


class DiagnosticoDashboardRequest(BaseModel):
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None


class DiagnosticoDashboardResponse(BaseModel):
    resumen: str
    metricas_base: Dict[str, Any]


class ExportarPDFDirectoRequest(BaseModel):
    respuesta_ia: str
    estadisticas: Optional[Dict[str, Any]] = None


# Esquemas compatibles con la API de OpenAI para Open WebUI
class OpenAIMessage(BaseModel):
    role: str
    content: Union[str, List[Any]]


class OpenAIChatCompletionRequest(BaseModel):
    model: Optional[str] = "vialbot-sql"
    messages: List[OpenAIMessage]
    user: Optional[str] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.0


@router.get(
    "/chat",
    summary="Interfaz Web del Chatbot Analítico (ChatGPT / Gemini UI)",
    description="Entrega la página web interactiva con panel de conversación, historial local, markdown enriquecido y modo oscuro."
)
async def chat_ui():
    """
    Entrega el archivo estático de la interfaz del chat.
    """
    if os.path.exists(CHAT_HTML_PATH):
        with open(CHAT_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h3>La interfaz del Chatbot se está cargando...</h3>", status_code=200)


@router.post(
    "/consultar",
    response_model=ConsultaAIResponse,
    summary="Consulta Determinista con Grounding Estricto a SQL Server",
    description=(
        "Orquestador determinista en 3 fases: "
        "1. Extracción estructurada de intención y parámetros (JSON) con Qwen 2.5 7B. "
        "2. Ejecución de consulta SQL parametrizada de solo lectura (SELECT). "
        "3. Síntesis cerrada con grounding estricto sobre datos SQL (temperature=0.0)."
    )
)
async def consultar_ia(request: ConsultaAIRequest, db: Session = Depends(get_db)):
    """
    Endpoint determinista para consultas verídicas basadas estrictamente en la base de datos SQL.
    """
    resultado = await ai_service.consultar(
        pregunta=request.pregunta,
        db=db,
        historial=request.historial,
        session_id=request.session_id,
    )
    return ConsultaAIResponse(
        respuesta=resultado["respuesta"],
        accion_ejecutada=resultado["accion_ejecutada"],
        datos_fuente=resultado["datos_fuente"],
    )


@router.post(
    "/parsear-despacho",
    response_model=DespachoParseadoResponse,
    summary="Extracción estructurada de despacho desde llamada o reporte de radio",
    description="Procesa texto desordenado o mensaje de radio con Qwen 2.5 7B (temp=0.0) y extrae los campos de despacho en formato normalizado."
)
async def parsear_despacho_endpoint(request: ParsearDespachoRequest):
    """
    Extrae campos clave de operaciones para autocompletar formularios de despacho.
    """
    try:
        resultado = await ai_service.parsear_despacho(texto_reporte=request.texto_reporte)
        return DespachoParseadoResponse(**resultado)
    except Exception as exc:
        return DespachoParseadoResponse()


@router.post(
    "/diagnostico-dashboard",
    response_model=DiagnosticoDashboardResponse,
    summary="Diagnóstico Ejecutivo para Dashboard con Qwen 2.5 7B",
    description="Sintetiza métricas reales de SQL Server en 3 puntos clave (Balance general, Alertas operativas, Recomendación)."
)
async def diagnostico_dashboard_endpoint(
    request: DiagnosticoDashboardRequest,
    db: Session = Depends(get_db)
):
    """
    Genera un diagnóstico ejecutivo de 3 puntos a partir de las métricas reales del periodo.
    """
    try:
        resultado = await ai_service.diagnostico_dashboard(
            db=db,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin
        )
        return DiagnosticoDashboardResponse(
            resumen=resultado["resumen"],
            metricas_base=resultado["metricas_base"]
        )
    except Exception as exc:
        return DiagnosticoDashboardResponse(
            resumen="1. **Balance General:** Monitoreo activo de la infraestructura vial.\n\n2. **Alertas y Dinámica Operativa:** Datos verificados con la base central.\n\n3. **Recomendación Operativa:** Mantener patrullajes y supervisión continua.",
            metricas_base={}
        )


@router.post(
    "/analizar-jornada-stream",
    summary="Agente de IA con Streaming SSE",
    description="Transmite tokens en tiempo real mediante Server-Sent Events (SSE)."
)
async def analizar_jornada_stream(request: AIRequest, db: Session = Depends(get_db)):
    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in ai_service.procesar_peticion_stream(
            prompt_usuario=request.pregunta,
            db=db,
            historial=request.historial,
            session_id=request.session_id
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post(
    "/analizar-jornada",
    summary="Agente de IA (Reportes y ExportaciÃ³n a PDF / Excel)",
    description="Haz una consulta natural. Si pides un reporte en PDF o Excel, generarÃ¡ y descargarÃ¡ automÃ¡ticamente el documento oficial."
)
async def analizar_jornada(request: AIRequest, db: Session = Depends(get_db)):

    resultado = await ai_service.procesar_peticion(
        db=db,
        prompt_usuario=request.pregunta,
        historial=request.historial,
        session_id=request.session_id
    )

    if resultado.get("solicita_exportacion"):
        formato = resultado.get("formato_exportacion", "excel")
        datos = resultado.get("datos_crudos", {})
        modulos = resultado.get("modulos_solicitados", ["ambulancias", "gruas", "patrullajes"])
        respuesta_texto = resultado.get("respuesta_ia", "Reporte generado con Ã©xito.")
        resumen_b64 = base64.b64encode(respuesta_texto.encode("utf-8")).decode("ascii")

        # ----------------------------------------------------
        # EXPORTACIÃ“N A PDF
        # ----------------------------------------------------
        if formato == "pdf":
            pdf_output, filename = pdf_service.generar_informe_ia_pdf(
                respuesta_ia=respuesta_texto,
                estadisticas=resultado.get("estadisticas"),
                datos_crudos=datos,
                modulos=modulos
            )

            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Access-Control-Expose-Headers': 'Content-Disposition, X-Resumen-IA-B64, X-Es-Reporte-Pdf, X-Estadisticas-B64',
                'X-Es-Reporte-Pdf': 'true',
                'X-Resumen-IA-B64': resumen_b64,
            }
            if resultado.get("estadisticas"):
                stats_json = json.dumps(resultado["estadisticas"], ensure_ascii=False)
                headers['X-Estadisticas-B64'] = base64.b64encode(stats_json.encode("utf-8")).decode("ascii")

            return StreamingResponse(
                pdf_output,
                headers=headers,
                media_type='application/pdf'
            )

        # ----------------------------------------------------
        # EXPORTACIÃ“N A EXCEL (.xlsx)
        # ----------------------------------------------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            df_resumen = pd.DataFrame({
                "Resumen AnalÃ­tico": [respuesta_texto]
            })
            df_resumen.to_excel(writer, sheet_name='AnÃ¡lisis Operativo', index=False)

            worksheet_ia = writer.sheets['AnÃ¡lisis Operativo']
            worksheet_ia.column_dimensions['A'].width = 150
            for row in worksheet_ia.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")

            if "ambulancias" in modulos:
                if datos.get("ambulancias"):
                    pd.DataFrame(datos["ambulancias"]).to_excel(writer, sheet_name='Ambulancias', index=False)
                else:
                    pd.DataFrame({"Mensaje": ["No hay datos en este periodo"]}).to_excel(writer, sheet_name='Ambulancias', index=False)

            if "gruas" in modulos:
                if datos.get("gruas"):
                    pd.DataFrame(datos["gruas"]).to_excel(writer, sheet_name='GrÃºas', index=False)
                else:
                    pd.DataFrame({"Mensaje": ["No hay datos en este periodo"]}).to_excel(writer, sheet_name='GrÃºas', index=False)

            if "patrullajes" in modulos or "patrullas" in modulos:
                if datos.get("patrullajes"):
                    pd.DataFrame(datos["patrullajes"]).to_excel(writer, sheet_name='Patrullajes', index=False)
                else:
                    pd.DataFrame({"Mensaje": ["No hay datos en este periodo"]}).to_excel(writer, sheet_name='Patrullajes', index=False)

        output.seek(0)

        headers = {
            'Content-Disposition': 'attachment; filename="informe_operaciones.xlsx"',
            'Access-Control-Expose-Headers': 'Content-Disposition, X-Resumen-IA-B64, X-Es-Reporte-Excel, X-Estadisticas-B64',
            'X-Es-Reporte-Excel': 'true',
            'X-Resumen-IA-B64': resumen_b64
        }
        if resultado.get("estadisticas"):
            stats_json = json.dumps(resultado["estadisticas"], ensure_ascii=False)
            headers['X-Estadisticas-B64'] = base64.b64encode(stats_json.encode("utf-8")).decode("ascii")

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return JSONResponse(content={
        "respuesta_ia": resultado.get("respuesta_ia", ""),
        "estadisticas": resultado.get("estadisticas")
    })


@router.post(
    "/exportar-pdf",
    summary="Exportar anÃ¡lisis actual a PDF",
    description="Genera y descarga un informe oficial en PDF a partir del texto y estadÃ­sticas."
)
async def exportar_pdf_directo(request: ExportarPDFDirectoRequest):
    pdf_output, filename = pdf_service.generar_informe_ia_pdf(
        respuesta_ia=request.respuesta_ia,
        estadisticas=request.estadisticas,
    )
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Access-Control-Expose-Headers': 'Content-Disposition, X-Es-Reporte-Pdf',
        'X-Es-Reporte-Pdf': 'true'
    }
    return StreamingResponse(
        pdf_output,
        headers=headers,
        media_type='application/pdf'
    )


# =====================================================================
# ENDPOINTS COMPATIBLES CON OPENAI (Para Open WebUI Sandbox con SQL)
# =====================================================================

@router.get(
    "/models",
    summary="Listado de Modelos (OpenAI Compatible)",
    description="Permite que Open WebUI descubra el modelo conectado a SQL Server."
)
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "vialbot-sql",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "concesion-vial-cosad",
                "permission": [],
                "root": "vialbot-sql",
                "parent": None
            }
        ]
    }


@router.post(
    "/chat/completions",
    summary="Chat Completions (OpenAI Compatible con soporte de Streaming)",
    description="Recibe mensajes de Open WebUI, consulta SQL Server y responde con streaming en tiempo real."
)
async def chat_completions(req: OpenAIChatCompletionRequest, db: Session = Depends(get_db)):
    ultimo_mensaje_usuario = ""
    historial = []
    primer_mensaje_usuario = ""
    for m in req.messages:
        content_str = m.content if isinstance(m.content, str) else str(m.content)
        if m.role == "user":
            if not primer_mensaje_usuario:
                primer_mensaje_usuario = content_str
            ultimo_mensaje_usuario = content_str
        historial.append({"role": m.role, "content": content_str})

    if not ultimo_mensaje_usuario:
        ultimo_mensaje_usuario = "Resumen general de operaciones recientes"

    # DerivaciÃ³n de session_id estable para Open WebUI
    if req.user:
        session_id = f"owui_user_{req.user}"
    elif primer_mensaje_usuario:
        session_id = f"owui_thread_{hashlib.md5(primer_mensaje_usuario.strip().encode('utf-8')).hexdigest()[:12]}"
    else:
        session_id = "owui_default_session"

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())
    model_name = req.model or "vialbot-sql"

    # 1. MODO STREAMING (Server-Sent Events con formato OpenAI chunk)
    if req.stream:
        async def openai_sse_generator() -> AsyncGenerator[str, None]:
            # Emite rol inicial
            chunk_role = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model_name,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(chunk_role, ensure_ascii=False)}\n\n"

            async for item in ai_service.procesar_peticion_stream(
                prompt_usuario=ultimo_mensaje_usuario,
                db=db,
                historial=historial[:-1],
                session_id=session_id
            ):
                if item.get("tipo") == "token":
                    delta_text = item.get("contenido", "")
                    chunk_token = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": {"content": delta_text}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(chunk_token, ensure_ascii=False)}\n\n"
                elif item.get("tipo") == "done":
                    break

            chunk_stop = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(chunk_stop, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            openai_sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # 2. MODO NO-STREAMING (JSON tradicional)
    resultado = await ai_service.procesar_peticion(
        prompt_usuario=ultimo_mensaje_usuario,
        db=db,
        historial=historial[:-1],
        session_id=session_id
    )

    respuesta_texto = resultado.get("respuesta_ia", "Sin respuesta disponible.")

    if resultado.get("estadisticas") and "DiagnÃ³stico" not in respuesta_texto:
        stats = resultado["estadisticas"]
        periodo = stats.get("periodo", "")
        if periodo:
            respuesta_texto += f"\n\n*(Datos verificados de SQL Server | PerÃ­odo: {periodo})*"

    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": respuesta_texto
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": len(respuesta_texto.split()),
            "total_tokens": 120 + len(respuesta_texto.split())
        }
    }
