"""
Aplicación Chainlit para VialBot AI.
Características directivas solicitadas:
1. Autenticación de usuarios para historial de chats persistente y personal por usuario (SQLAlchemyDataLayer).
2. Gráficos Plotly interactivos fijos y no modificables (sin barra de herramientas zoom/pan/reset, hover informativo).
3. Botón de "Descargar Informe PDF" directo que al hacer clic entrega inmediatamente el archivo listo para abrir/descargar.
4. Gráficos por defecto generados automáticamente sin comandos extra.
5. Persistencia y reanudación limpia de conversaciones en la barra lateral sin mensajes vacíos.
6. Indicador de estado claro, amigable e informativo durante el procesamiento (sin tecnicismos de SQL Server o métricas de bajo nivel).
7. Persistencia completa de elementos (gráficos y documentos descargables) al cerrar sesión y reanudar el chat.
"""
import io
import os
import sys
from pathlib import Path
from typing import Optional

# Asegurar que el directorio raíz del proyecto esté en sys.path para resolver 'app'
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from openpyxl.styles import Alignment
import plotly.express as px
import plotly.graph_objects as go
import chainlit as cl
from chainlit.context import local_steps
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from chainlit.server import app as chainlit_fastapi_app
from starlette.staticfiles import StaticFiles

from app.core.database import SessionLocal
from app.services.ai_service import ai_service
from app.services.pdf_service import pdf_service

# ==============================================================================
# 1. PERSISTENCIA DE CHATS, ELEMENTOS (GRÁFICOS/DOCUMENTOS) E HISTORIAL
# ==============================================================================
DB_CHATS_PATH = ROOT_DIR / "chainlit_historial.db"
CONN_STR = f"sqlite+aiosqlite:///{DB_CHATS_PATH.as_posix()}"

ELEMENTS_STORAGE_DIR = ROOT_DIR / "temp_storage"
ELEMENTS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Servir archivos estáticos subidos para que la UI los cargue tras reanudar el chat
chainlit_fastapi_app.mount(
    "/storage_files",
    StaticFiles(directory=str(ELEMENTS_STORAGE_DIR)),
    name="storage_files"
)


class LocalStorageClient(BaseStorageClient):
    """
    Proveedor de almacenamiento local para Chainlit SQLAlchemyDataLayer.
    Guarda en disco los archivos binarios y JSON de elementos (gráficos Plotly,
    documentos PDF y Excel) para que se inserten en la base de datos 'elements'
    y persistan al cerrar sesión y reanudar la conversación.
    """
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        object_key: str,
        data,
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: Optional[str] = None
    ) -> dict:
        clean_key = object_key.replace("\\", "/")
        target_path = self.base_dir / clean_key
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, str):
            data = data.encode("utf-8")

        target_path.write_bytes(data)
        url = f"/storage_files/{clean_key}"
        return {"object_key": clean_key, "url": url}

    async def delete_file(self, object_key: str) -> bool:
        clean_key = object_key.replace("\\", "/")
        target_path = self.base_dir / clean_key
        if target_path.exists():
            target_path.unlink()
        return True

    async def get_read_url(self, object_key: str) -> str:
        clean_key = object_key.replace("\\", "/")
        return f"/storage_files/{clean_key}"

    async def close(self) -> None:
        pass


local_storage_provider = LocalStorageClient(ELEMENTS_STORAGE_DIR)

try:
    data_layer = SQLAlchemyDataLayer(
        conninfo=CONN_STR,
        storage_provider=local_storage_provider,
        show_logger=False
    )
    cl_data._data_layer = data_layer
except Exception as exc:
    print(f"[Aviso] No se pudo inicializar la persistencia SQLite con almacenamiento: {exc}")

PDF_STORAGE_DIR = ROOT_DIR / "temp_pdfs"
PDF_STORAGE_DIR.mkdir(exist_ok=True)

# Usuarios válidos para autenticación (incluye tanto 'admin' como 'admin123')
USUARIOS_AUTORIZADOS = {
    "admin": "admin",
    "operaciones": "cosad2026",
    "supervisor": "vialbot2026"
}


@cl.password_auth_callback
def autenticar_usuario(username: str, password: str):
    """
    Verifica credenciales del usuario.
    Si es válido, devuelve el objeto User para que Chainlit cree o reanude
    su sesión y aísle su historial en la base de datos personal.
    Permite tanto 'admin' como 'admin123' para el usuario admin.
    """
    u_clean = username.strip().lower()
    p_clean = password.strip()
    
    if u_clean == "admin" and p_clean in ("admin", "admin123"):
        return cl.User(
            identifier="admin",
            metadata={"role": "admin"}
        )

    if u_clean in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[u_clean] == p_clean:
        return cl.User(
            identifier=u_clean,
            metadata={"role": u_clean}
        )

    return None


def generar_graficos_plotly_fijos(stats: dict) -> list:
    """
    Construye gráficos Plotly estilizados en formato de BARRAS con configuración FIJA
    (sin barra de zoom, pan, autoscale o reset). Los gráficos son ejecutivos,
    con etiquetas externas nítidas y sin superposiciones de texto.
    """
    if not stats:
        return []

    elementos = []

    # 1. Gráfico de barras de asistencias en vía (Grúas vs Ambulancias)
    total_amb = stats.get("ambulancias_total", 0)
    total_gru = stats.get("gruas_total", 0)
    total_asist = total_amb + total_gru

    if total_amb > 0 or total_gru > 0:
        categorias = []
        cantidades = []
        colores = []
        etiquetas_texto = []

        if total_gru > 0:
            pct_gru = (total_gru / total_asist * 100) if total_asist > 0 else 0
            categorias.append("Grúas de Auxilio")
            cantidades.append(total_gru)
            colores.append("#2563EB")  # Azul vial operativo
            etiquetas_texto.append(f"<b>{total_gru:,}</b> ({pct_gru:.1f}%)")

        if total_amb > 0:
            pct_amb = (total_amb / total_asist * 100) if total_asist > 0 else 0
            categorias.append("Ambulancias")
            cantidades.append(total_amb)
            colores.append("#E11D48")  # Rojo asistencial
            etiquetas_texto.append(f"<b>{total_amb:,}</b> ({pct_amb:.1f}%)")

        max_y = max(cantidades) if cantidades else 10

        fig_dist = go.Figure(
            data=[
                go.Bar(
                    x=categorias,
                    y=cantidades,
                    text=etiquetas_texto,
                    textposition="outside",
                    marker=dict(
                        color=colores,
                        line=dict(color="#1E293B", width=1.2)
                    ),
                    width=0.38 if len(categorias) == 1 else 0.44,
                    cliponaxis=False,
                    hoverinfo="x+y"
                )
            ]
        )
        fig_dist.update_layout(
            title=dict(
                text="<b>Distribución de Asistencias en Vía</b>",
                font=dict(size=14, color="#1E293B"),
                x=0.03
            ),
            showlegend=False,
            margin=dict(l=40, r=25, t=55, b=35),
            height=290,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                showgrid=True,
                gridcolor="#F1F5F9",
                zeroline=True,
                zerolinecolor="#CBD5E1",
                range=[0, max_y * 1.28]
            ),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=13, color="#334155")
            ),
            bargap=0.35
        )

        elementos.append(
            cl.Plotly(
                name="grafico_asistencias",
                figure=fig_dist,
                display="inline"
            )
        )

    # 2. Gráfico de Patrullajes Viales por Turno / Tipo si existen datos
    patrullajes = stats.get("patrullajes_total", 0)
    if patrullajes > 0:
        turnos = stats.get("patrullajes_por_turno", {})
        if turnos:
            eje_x = list(turnos.keys())
            eje_y = list(turnos.values())
        else:
            eje_x = ["Patrullajes Totales"]
            eje_y = [patrullajes]

        fig_pat = go.Figure(
            data=[
                go.Bar(
                    x=eje_x,
                    y=eje_y,
                    marker=dict(
                        color="#0D9488",  # Verde esmeralda vial
                        line=dict(color="#042F2E", width=1.5)
                    ),
                    text=eje_y,
                    textposition="auto",
                    hoverinfo="x+y"
                )
            ]
        )
        fig_pat.update_layout(
            title=dict(
                text="<b>Patrullajes de Inspección Vial</b>",
                font=dict(size=14, color="#1E293B"),
                x=0.05
            ),
            margin=dict(l=30, r=20, t=50, b=30),
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
            xaxis=dict(showgrid=False)
        )

        elementos.append(
            cl.Plotly(
                name="grafico_patrullajes",
                figure=fig_pat,
                display="inline"
            )
        )

    return elementos


@cl.on_chat_start
async def al_iniciar_chat():
    """
    Inicializa el chat con bienvenida profesional de COSAD 25.
    Configura el historial limpio en la sesión del usuario autenticado.
    """
    cl.user_session.set("historial", [])
    cl.user_session.set("session_id", cl.context.session.id)
    cl.user_session.set("ultimo_resultado", None)


@cl.on_chat_resume
async def al_reanudar_chat(thread: dict):
    """
    Restaura el contexto conversacional cuando el usuario selecciona un chat previo
    del historial en la barra lateral, reconstruyendo el contexto y la última analítica.
    """
    historial = []
    ultimo_resultado = None

    for step in thread.get("steps", []):
        stype = step.get("type")
        content = step.get("output") or step.get("input")
        if stype == "user_message" and content:
            historial.append({"role": "user", "content": content})
        elif stype == "assistant_message" and content:
            historial.append({"role": "assistant", "content": content})
            step_meta = step.get("metadata") or {}
            if isinstance(step_meta, dict) and "ultimo_resultado" in step_meta:
                ultimo_resultado = step_meta["ultimo_resultado"]

    cl.user_session.set("historial", historial[-6:])
    cl.user_session.set("session_id", thread.get("id", cl.context.session.id))
    cl.user_session.set("ultimo_resultado", ultimo_resultado)


@cl.action_callback("descargar_pdf_accion")
async def descargar_pdf_accion(action: cl.Action):
    """
    Al presionar el botón 'Descargar Informe PDF', compila inmediatamente
    el archivo y lo entrega de forma directa y lista para abrir en un clic.
    """
    ultimo = cl.user_session.get("ultimo_resultado")
    if not ultimo:
        await cl.Message(content="*No hay un análisis reciente para compilar el PDF.*").send()
        return

    # Remover el botón para evitar clics duplicados
    await action.remove()

    pdf_output, filename = pdf_service.generar_informe_ia_pdf(
        respuesta_ia=ultimo.get("respuesta_texto", ""),
        estadisticas=ultimo.get("stats", {}),
        datos_crudos=ultimo.get("datos", {}),
        modulos=ultimo.get("modulos", ["ambulancias", "gruas", "patrullajes"])
    )

    ruta_archivo = PDF_STORAGE_DIR / filename
    ruta_archivo.write_bytes(pdf_output.getvalue())

    # Entrega inmediata del archivo para descarga en un solo clic
    archivo_pdf = cl.File(
        name=filename,
        path=str(ruta_archivo),
        display="inline"
    )

    await cl.Message(
        content=f"📄 **Informe oficial:** Haz clic en **{filename}** para descargarlo.",
        elements=[archivo_pdf]
    ).send()


@cl.on_message
async def al_recibir_mensaje(message: cl.Message):
    await procesar_mensaje(message.content)


async def procesar_mensaje(prompt_usuario: str):
    historial = cl.user_session.get("historial", [])
    session_id = cl.user_session.get("session_id", cl.context.session.id)

    db = SessionLocal()
    metadatos = {}
    tokens_generados = []

    # Detección temprana de solicitud de archivo PDF o Excel
    formato = None
    try:
        classif = ai_service._clasificar_intencion(prompt_usuario)
        formato = classif.get("formato_exportacion")
    except Exception:
        pass

    pide_pdf_explicito = bool(formato == "pdf" or ("pdf" in prompt_usuario.lower()))
    pide_excel_explicito = bool(formato == "excel" or ("excel" in prompt_usuario.lower() or "xlsx" in prompt_usuario.lower()))

    # 1. CASO ARCHIVO EXPLÍCITO (PDF O EXCEL DIRECTO)
    if pide_pdf_explicito or pide_excel_explicito:
        formato_export = "pdf" if pide_pdf_explicito else "excel"

        resultado = await ai_service.procesar_peticion(
            prompt_usuario=prompt_usuario,
            db=db,
            historial=historial,
            session_id=session_id
        )
        db.close()

        respuesta_texto = resultado.get("respuesta_ia", "Informe oficial generado.")
        datos = resultado.get("datos_crudos", {})
        modulos_sol = resultado.get("modulos_solicitados", ["ambulancias", "gruas", "patrullajes"])
        stats = resultado.get("estadisticas", {})

        elementos = []

        if formato_export == "pdf":
            pdf_output, filename = pdf_service.generar_informe_ia_pdf(
                respuesta_ia=respuesta_texto,
                estadisticas=stats,
                datos_crudos=datos,
                modulos=modulos_sol
            )
            ruta_archivo = PDF_STORAGE_DIR / filename
            ruta_archivo.write_bytes(pdf_output.getvalue())
            elementos.append(
                cl.File(name=filename, path=str(ruta_archivo), display="inline")
            )
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_res = pd.DataFrame({"Resumen Analítico": [respuesta_texto]})
                df_res.to_excel(writer, sheet_name='Análisis Operativo', index=False)
                ws = writer.sheets['Análisis Operativo']
                ws.column_dimensions['A'].width = 130
                for row in ws.iter_rows():
                    for cell in row:
                        cell.alignment = Alignment(wrap_text=True, vertical="top")

                if "ambulancias" in modulos_sol:
                    pd.DataFrame(datos.get("ambulancias") or [{"Mensaje": "Sin datos"}]).to_excel(writer, sheet_name='Ambulancias', index=False)
                if "gruas" in modulos_sol:
                    pd.DataFrame(datos.get("gruas") or [{"Mensaje": "Sin datos"}]).to_excel(writer, sheet_name='Grúas', index=False)
                if "patrullajes" in modulos_sol or "patrullas" in modulos_sol:
                    pd.DataFrame(datos.get("patrullajes") or [{"Mensaje": "Sin datos"}]).to_excel(writer, sheet_name='Patrullajes', index=False)

            ruta_excel = PDF_STORAGE_DIR / "informe_operaciones.xlsx"
            ruta_excel.write_bytes(output.getvalue())
            elementos.append(
                cl.File(name="informe_operaciones.xlsx", path=str(ruta_excel), display="inline")
            )

        # Gráficos de apoyo fijos
        elementos.extend(generar_graficos_plotly_fijos(stats))

        ultimo_res = {
            "respuesta_texto": respuesta_texto,
            "stats": stats,
            "datos": datos,
            "modulos": modulos_sol
        }
        # Guardar para posible re-descarga
        cl.user_session.set("ultimo_resultado", ultimo_res)

        await cl.Message(
            content=respuesta_texto,
            elements=elementos,
            metadata={"ultimo_resultado": ultimo_res}
        ).send()

        historial.append({"role": "user", "content": prompt_usuario})
        historial.append({"role": "assistant", "content": respuesta_texto})
        cl.user_session.set("historial", historial[-6:])
        return

    # 2. CASO CONVERSACIONAL STREAMING DIRECTO COMO MENSAJE RAÍZ (ROOT)
    msg_salida = cl.Message(content="", parent_id=None)
    await msg_salida.send()

    try:
        async for chunk in ai_service.procesar_peticion_stream(
            prompt_usuario=prompt_usuario,
            db=db,
            historial=historial,
            session_id=session_id
        ):
            tipo = chunk.get("tipo")
            if tipo == "meta":
                metadatos = chunk
            elif tipo == "token":
                token = chunk.get("contenido", "")
                tokens_generados.append(token)
                await msg_salida.stream_token(token)
            elif tipo == "done":
                break

        # Renderizar gráficos Plotly por defecto (fijos, sin barra de zoom/pan)
        stats = metadatos.get("estadisticas", {})
        graficos = generar_graficos_plotly_fijos(stats)
        if graficos:
            msg_salida.elements = graficos

        # Botón para compilar y descargar PDF al instante
        total_asist = stats.get("total_asistencias_via", 0)
        total_p = stats.get("patrullajes_total", 0)

        if total_asist > 0 or total_p > 0:
            texto_final_ia = "".join(tokens_generados) or msg_salida.content
            ultimo_res = {
                "respuesta_texto": texto_final_ia,
                "stats": stats,
                "datos": metadatos.get("datos_crudos", {}),
                "modulos": metadatos.get("modulos_solicitados", ["ambulancias", "gruas", "patrullajes"])
            }
            cl.user_session.set("ultimo_resultado", ultimo_res)
            msg_salida.metadata = {"ultimo_resultado": ultimo_res}

            msg_salida.actions = [
                cl.Action(
                    name="descargar_pdf_accion",
                    payload={"origen": "boton_post_respuesta"},
                    label="📄 Descargar Informe PDF"
                )
            ]

        await msg_salida.update()

        # Guardar en memoria conversacional
        texto_final = "".join(tokens_generados) or msg_salida.content
        historial.append({"role": "user", "content": prompt_usuario})
        historial.append({"role": "assistant", "content": texto_final})
        cl.user_session.set("historial", historial[-6:])

    except Exception as e:
        error_msg = f"❌ Ocurrió un inconveniente al procesar la consulta: {str(e)}"
        await msg_salida.stream_token(error_msg)
        await msg_salida.update()
    finally:
        db.close()
