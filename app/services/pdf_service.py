"""
Servicio de generación de reportes institucionales en formato PDF con ReportLab.
Incluye el isotipo/logotipo oficial de la Concesión Vial COSAD 25 (LOGO-COSAD25.webp),
estilos corporativos, gráficos estadísticos de alta resolución (Matplotlib),
tablas con métricas clave, KPIs y foliado automático de páginas.
"""
import io
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable,
)

from app.schemas.reportes import ServicioReporteEnum

# Ruta al logo institucional oficial en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGO_PATH = os.path.join(BASE_DIR, "LOGO-COSAD25.webp")

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


class NumberedCanvas(canvas.Canvas):
    """
    Canvas personalizado para calcular y mostrar 'Página X de Y' y pie institucional sobrio.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Línea divisoria de pie de página
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(36, 32, self._pagesize[0] - 36, 32)

        # Textos de pie limpios (sin jerga técnica de servidores)
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.drawString(36, 20, f"CONCESIÓN VIAL  |  Sistema de Operaciones y Asistencias  |  Emisión: {fecha_str}")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(self._pagesize[0] - 36, 20, page_str)
        self.restoreState()


class PDFReportService:
    def __init__(self):
        self._logo_bytes: Optional[bytes] = None
        self._cargar_logo()

    def _cargar_logo(self):
        """Convierte el archivo LOGO-COSAD25.webp a PNG en memoria para ReportLab."""
        try:
            if os.path.exists(LOGO_PATH):
                with PILImage.open(LOGO_PATH) as img:
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    self._logo_bytes = buf.getvalue()
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el logo ({e})")
            self._logo_bytes = None

    def obtener_imagen_logo(self, width: float = 135, height: float = 46) -> Optional[RLImage]:
        """Retorna el Flowable de imagen del logo institucional si está disponible."""
        if not self._logo_bytes:
            self._cargar_logo()
        if self._logo_bytes:
            buf = io.BytesIO(self._logo_bytes)
            return RLImage(buf, width=width, height=height)
        return None

    def _crear_estilos(self):
        """Genera los estilos tipográficos para los reportes."""
        styles = getSampleStyleSheet()

        c_primary = colors.HexColor("#0f2e5a")    # Azul institucional oscuro
        c_secondary = colors.HexColor("#0284c7")  # Azul vial
        c_text = colors.HexColor("#1e293b")       # Grafito
        c_muted = colors.HexColor("#64748b")      # Gris secundario

        estilos = {
            "title_inst": ParagraphStyle(
                "InstTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=c_primary,
            ),
            "subtitle_inst": ParagraphStyle(
                "InstSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=c_muted,
            ),
            "doc_title": ParagraphStyle(
                "DocTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=12.5,
                leading=15,
                textColor=c_primary,
            ),
            "meta": ParagraphStyle(
                "Meta",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=c_secondary,
            ),
            "h2": ParagraphStyle(
                "SectionH2",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10.5,
                leading=13,
                textColor=c_primary,
                spaceBefore=8,
                spaceAfter=4,
            ),
            "h3": ParagraphStyle(
                "SectionH3",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9.5,
                leading=12,
                textColor=c_secondary,
                spaceBefore=6,
                spaceAfter=3,
            ),
            "body": ParagraphStyle(
                "BodyTextCustom",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=c_text,
                spaceBefore=2,
                spaceAfter=4,
            ),
            "bullet": ParagraphStyle(
                "BulletCustom",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=c_text,
                leftIndent=12,
                spaceBefore=1,
                spaceAfter=2,
            ),
            "table_header": ParagraphStyle(
                "TableHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=colors.white,
                alignment=1,  # Center
            ),
            "table_cell": ParagraphStyle(
                "TableCell",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=c_text,
            ),
            "table_cell_center": ParagraphStyle(
                "TableCellCenter",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=c_text,
                alignment=1,
            ),
            "table_cell_bold": ParagraphStyle(
                "TableCellBold",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=c_text,
            ),
            "kpi_num": ParagraphStyle(
                "KPINum",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=17,
                textColor=c_primary,
                alignment=1,
            ),
            "kpi_label": ParagraphStyle(
                "KPILabel",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9,
                textColor=c_muted,
                alignment=1,
            ),
        }
        return estilos

    def _construir_encabezado_institucional(
        self, titulo_documento: str, subtitulo_meta: str, estilos: Dict[str, ParagraphStyle], ancho_util: float = 540
    ) -> List[Any]:
        """Construye la cabecera estándar sin tecnicismos."""
        elementos = []
        logo = self.obtener_imagen_logo(width=135, height=46)

        textos_header = [
            Paragraph("CONCESIÓN VIAL", estilos["title_inst"]),
            Paragraph("SISTEMA DE GESTIÓN Y ASISTENCIA EN VÍA", estilos["subtitle_inst"]),
            Spacer(1, 4),
            Paragraph(titulo_documento, estilos["doc_title"]),
            Paragraph(subtitulo_meta, estilos["meta"]),
        ]

        if logo:
            tabla_header = Table(
                [[textos_header, logo]],
                colWidths=[ancho_util - 145, 145]
            )
            tabla_header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]))
            elementos.append(tabla_header)
        else:
            elementos.extend(textos_header)

        elementos.append(Spacer(1, 6))
        elementos.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f2e5a"), spaceBefore=2, spaceAfter=8))
        return elementos

    def _generar_grafico_operaciones(self, stats: Dict[str, Any], ancho_util: float = 540) -> Optional[RLImage]:
        """
        Genera gráficos ordenados, estéticos y de alto valor informativo usando matplotlib.
        Produce una imagen compuesta con:
        - Panel 1 (Barras horizontales): Tramos y sectores con mayor demanda vial.
        - Panel 2 (Dona o Barras): Distribución operativa por tipo de servicio o principales motivos.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            top_tramos = stats.get("asistencias_top_tramos") or stats.get("gruas_top_sectores") or stats.get("ambulancias_top_sectores") or []
            total_g = stats.get("gruas_total", 0)
            total_a = stats.get("ambulancias_total", 0)
            total_p = stats.get("patrullajes_total", 0)
            motivos = stats.get("gruas_top_motivos") or stats.get("ambulancias_top_incidentes") or []

            servicios_activos = sum([1 for x in (total_g, total_a, total_p) if x > 0])
            tiene_panel1 = bool(top_tramos)
            tiene_panel2 = (servicios_activos > 1) or bool(motivos)

            if not tiene_panel1 and not tiene_panel2:
                return None

            # Determinar configuración de subplots
            if tiene_panel1 and tiene_panel2:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.3), dpi=180)
            else:
                fig, ax1 = plt.subplots(1, 1, figsize=(7.2, 2.3), dpi=180)
                ax2 = None

            fig.patch.set_facecolor("#ffffff")

            # --- PANEL 1: Barras horizontales de sectores ---
            if tiene_panel1:
                items = top_tramos[:5]
                nombres = [
                    (it.get("sector") or "Sin sector").replace("Sector ", "").strip()
                    for it in items
                ][::-1]
                valores = [
                    it.get("asistencias_totales") or it.get("asistencias") or it.get("atenciones") or 0
                    for it in items
                ][::-1]

                max_val = max(valores) if valores and max(valores) > 0 else 1
                bars = ax1.barh(nombres, valores, color="#0284c7", height=0.52, edgecolor="none")
                ax1.set_title("Tramos con Mayor Demanda Vial", fontsize=8.5, fontweight="bold", color="#0f2e5a", pad=6)
                ax1.tick_params(labelsize=7, colors="#334155")
                ax1.spines["top"].set_visible(False)
                ax1.spines["right"].set_visible(False)
                ax1.spines["left"].set_color("#cbd5e1")
                ax1.spines["bottom"].set_color("#cbd5e1")
                ax1.grid(axis="x", linestyle="--", alpha=0.3, color="#94a3b8")
                ax1.set_xlim(0, max_val * 1.25)

                for bar in bars:
                    w = bar.get_width()
                    ax1.text(
                        w + (max_val * 0.02),
                        bar.get_y() + bar.get_height() / 2,
                        f"{int(w):,}",
                        va="center",
                        ha="left",
                        fontsize=7,
                        fontweight="bold",
                        color="#0f2e5a",
                    )

            # --- PANEL 2: Distribución por Servicio o Causas ---
            if ax2 is not None:
                if servicios_activos > 1:
                    servicios = []
                    cants = []
                    colores_map = []
                    if total_g > 0:
                        servicios.append(f"Grúas ({total_g:,})")
                        cants.append(total_g)
                        colores_map.append("#0284c7")
                    if total_a > 0:
                        servicios.append(f"Ambulancias ({total_a:,})")
                        cants.append(total_a)
                        colores_map.append("#ef4444")
                    if total_p > 0:
                        servicios.append(f"Patrullajes ({total_p:,})")
                        cants.append(total_p)
                        colores_map.append("#10b981")

                    wedges, texts, autotexts = ax2.pie(
                        cants,
                        labels=None,
                        autopct="%1.1f%%",
                        pctdistance=0.72,
                        colors=colores_map,
                        startangle=140,
                        wedgeprops=dict(width=0.46, edgecolor="white", linewidth=2),
                    )
                    for at in autotexts:
                        at.set_fontsize(7)
                        at.set_weight("bold")
                        at.set_color("#ffffff")

                    ax2.set_title("Distribución por Servicio", fontsize=8.5, fontweight="bold", color="#0f2e5a", pad=6)
                    ax2.legend(wedges, servicios, loc="center left", bbox_to_anchor=(0.92, 0.5), fontsize=6.8, frameon=False)

                elif motivos:
                    m_items = motivos[:4]
                    m_nombres = [(m.get("motivo") or m.get("tipo") or "Otro")[:18] for m in m_items][::-1]
                    m_vals = [m.get("cantidad") or 0 for m in m_items][::-1]
                    max_m = max(m_vals) if m_vals and max(m_vals) > 0 else 1

                    color_panel2 = "#ef4444" if total_a > 0 else "#0284c7"
                    bars_m = ax2.barh(m_nombres, m_vals, color=color_panel2, height=0.52, edgecolor="none")
                    titulo_p2 = "Tipología de Emergencias Médicas" if total_a > 0 else "Principales Motivos de Auxilio"
                    ax2.set_title(titulo_p2, fontsize=8.5, fontweight="bold", color="#0f2e5a", pad=6)
                    ax2.tick_params(labelsize=7, colors="#334155")
                    ax2.spines["top"].set_visible(False)
                    ax2.spines["right"].set_visible(False)
                    ax2.spines["left"].set_color("#cbd5e1")
                    ax2.spines["bottom"].set_color("#cbd5e1")
                    ax2.grid(axis="x", linestyle="--", alpha=0.3, color="#94a3b8")
                    ax2.set_xlim(0, max_m * 1.25)

                    for bar in bars_m:
                        w = bar.get_width()
                        ax2.text(
                            w + (max_m * 0.02),
                            bar.get_y() + bar.get_height() / 2,
                            f"{int(w):,}",
                            va="center",
                            ha="left",
                            fontsize=7,
                            fontweight="bold",
                            color="#991b1b" if total_a > 0 else "#0c4a6e",
                        )

            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            chart_width = ancho_util
            chart_height = (2.3 / 7.2) * chart_width
            return RLImage(buf, width=chart_width, height=chart_height)

        except Exception as err:
            print(f"Advertencia al generar gráfico PDF: {err}")
            return None

    def generar_informe_ia_pdf(
        self,
        respuesta_ia: str,
        estadisticas: Optional[Dict[str, Any]] = None,
        datos_crudos: Optional[Dict[str, Any]] = None,
        modulos: Optional[List[str]] = None,
    ) -> Tuple[io.BytesIO, str]:
        """
        Genera el informe oficial de operaciones y asistencias viales en formato PDF,
        con diseño estructurado, métricas clave, gráficos y desglose de tramos.
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=42,
        )

        ancho_util = letter[0] - 72  # 540 pt
        estilos = self._crear_estilos()
        story = []

        stats = estadisticas or {}
        periodo = stats.get("periodo", "Período no especificado")
        emision = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 1. Cabecera Institucional
        subtitulo = f"Periodo evaluado: {periodo}  |  Fecha de emisión: {emision}"
        story.extend(self._construir_encabezado_institucional(
            "INFORME DE OPERACIONES Y ASISTENCIAS VIALES",
            subtitulo,
            estilos,
            ancho_util=ancho_util
        ))

        # 2. Resumen de Métricas (KPI Cards)
        total_comb = stats.get("asistencias_totales_combinadas", 0)
        total_gruas = stats.get("gruas_total", 0)
        total_amb = stats.get("ambulancias_total", 0)
        total_pat = stats.get("patrullajes_total", 0)

        if (total_comb + total_gruas + total_amb + total_pat) > 0:
            c_card_bg = colors.HexColor("#f8fafc")
            c_border = colors.HexColor("#cbd5e1")

            kpi_cols = []
            if total_comb > 0:
                kpi_cols.append([
                    Paragraph(f"{total_comb:,}", estilos["kpi_num"]),
                    Paragraph("TOTAL ASISTENCIAS", estilos["kpi_label"])
                ])
            if total_gruas > 0:
                kpi_cols.append([
                    Paragraph(f"{total_gruas:,}", estilos["kpi_num"]),
                    Paragraph("GRÚAS (AUXILIO)", estilos["kpi_label"])
                ])
            if total_amb > 0:
                kpi_cols.append([
                    Paragraph(f"{total_amb:,}", estilos["kpi_num"]),
                    Paragraph("AMBULANCIAS (SALUD)", estilos["kpi_label"])
                ])
            if total_pat > 0:
                kpi_cols.append([
                    Paragraph(f"{total_pat:,}", estilos["kpi_num"]),
                    Paragraph("PATRULLAJES", estilos["kpi_label"])
                ])

            if kpi_cols:
                ancho_col = ancho_util / len(kpi_cols)
                tabla_kpi = Table([kpi_cols], colWidths=[ancho_col] * len(kpi_cols))
                tabla_kpi.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), c_card_bg),
                    ("BOX", (0, 0), (-1, -1), 1, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                story.append(tabla_kpi)
                story.append(Spacer(1, 8))

        # 3. Gráficos Analíticos de Operaciones
        grafico_flowable = self._generar_grafico_operaciones(stats, ancho_util=ancho_util)
        if grafico_flowable:
            story.append(Paragraph("1. Representación Gráfica de Operaciones", estilos["h2"]))
            story.append(grafico_flowable)
            story.append(Spacer(1, 8))
            num_diagnostico = "2"
            num_tramos = "3"
        else:
            num_diagnostico = "1"
            num_tramos = "2"

        # 4. Diagnóstico y Detalle Operativo
        story.append(Paragraph(f"{num_diagnostico}. Diagnóstico y Detalle Operativo", estilos["h2"]))

        lineas = respuesta_ia.split("\n")
        en_tabla = False
        filas_tabla_md = []

        for l in lineas:
            linea = l.strip()
            if not linea:
                if en_tabla and filas_tabla_md:
                    story.append(self._renderizar_tabla_markdown(filas_tabla_md, estilos, ancho_util))
                    story.append(Spacer(1, 6))
                    en_tabla = False
                    filas_tabla_md = []
                continue

            # Eliminar comillas raras o citas residuales (ej: • "Priorizar..." -> • Priorizar...)
            linea = linea.replace('"', '').replace('“', '').replace('”', '')

            # Omitir viñetas que solo repiten sectores individuales con cantidades (ya van ordenados en la tabla oficial)
            if re.match(r'^[\-\*•]\s*(?:\*\*)?(?:Sector\s+)?.+?:\s*(?:Con un total de\s*)?\d+\s*(?:atenciones|auxilios|asistencias|eventos)', linea, re.IGNORECASE):
                continue
            if re.match(r'^[\-\*•]\s*(?:\*\*)?(?:Sector\s+)?.+?:\s*\d+\s*,\s*[\d\.]+\%', linea, re.IGNORECASE):
                continue
            if re.search(r'(?:en los siguientes sectores|a continuaci[oó]n|los siguientes tramos|sectores detallados)\s*:\s*$', linea, re.IGNORECASE):
                continue

            # Detectar filas de tabla Markdown
            if linea.startswith("|") and linea.endswith("|"):
                if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", linea):
                    continue
                en_tabla = True
                filas_tabla_md.append(linea)
                continue
            else:
                if en_tabla and filas_tabla_md:
                    story.append(self._renderizar_tabla_markdown(filas_tabla_md, estilos, ancho_util))
                    story.append(Spacer(1, 6))
                    en_tabla = False
                    filas_tabla_md = []

            # Encabezados Markdown
            if linea.startswith("### "):
                story.append(Paragraph(self._limpiar_markdown(linea[4:]), estilos["h3"]))
            elif linea.startswith("## "):
                story.append(Paragraph(self._limpiar_markdown(linea[3:]), estilos["h2"]))
            elif linea.startswith("# "):
                story.append(Paragraph(self._limpiar_markdown(linea[2:]), estilos["h2"]))
            elif linea.startswith("- ") or linea.startswith("* "):
                bullet_texto = f"&bull; {self._limpiar_markdown(linea[2:])}"
                story.append(Paragraph(bullet_texto, estilos["bullet"]))
            else:
                story.append(Paragraph(self._limpiar_markdown(linea), estilos["body"]))

        if en_tabla and filas_tabla_md:
            story.append(self._renderizar_tabla_markdown(filas_tabla_md, estilos, ancho_util))
            story.append(Spacer(1, 6))

        # 5. Tablas Estadísticas Complementarias (Top Tramos y Causas)
        top_tramos = stats.get("asistencias_top_tramos") or stats.get("gruas_top_sectores") or stats.get("ambulancias_top_sectores") or []
        if top_tramos:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"{num_tramos}. Concentración por Sector y Demanda Vial", estilos["h2"]))

            encabezados = [
                Paragraph("PUESTO", estilos["table_header"]),
                Paragraph("TRAMO / SECTOR VIAL", estilos["table_header"]),
                Paragraph("EVENTOS", estilos["table_header"]),
                Paragraph("PORCENTAJE", estilos["table_header"]),
            ]
            datos_tabla = [encabezados]

            for idx, item in enumerate(top_tramos[:5], start=1):
                sector = item.get("sector") or "Sin sector"
                cantidad = item.get("asistencias_totales") or item.get("asistencias") or item.get("atenciones") or 0
                pct = item.get("porcentaje") or "0%"
                datos_tabla.append([
                    Paragraph(str(idx), estilos["table_cell_center"]),
                    Paragraph(sector, estilos["table_cell_bold"]),
                    Paragraph(f"{cantidad:,}", estilos["table_cell_center"]),
                    Paragraph(str(pct), estilos["table_cell_center"]),
                ])

            t_tramos = Table(datos_tabla, colWidths=[50, ancho_util - 210, 80, 80])
            t_tramos.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2e5a")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_tramos)

        # Construir y compilar documento con canvas numerado
        doc.build(story, canvasmaker=NumberedCanvas)
        output.seek(0)
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"informe_operaciones_asistencias_viales_{timestamp_slug}.pdf"
        return output, filename

    def generar_reporte_mtop_pdf(
        self,
        df: pd.DataFrame,
        servicio: ServicioReporteEnum,
        mes: int,
        anio: int,
    ) -> Tuple[io.BytesIO, str]:
        """
        Genera el reporte mensual oficial MTOP en formato PDF apaisado (Landscape),
        cabeceras normalizadas y foliado de páginas.
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=42,
        )

        ancho_util = landscape(letter)[0] - 72  # 720 pt
        estilos = self._crear_estilos()
        story = []

        nombre_mes = MESES_ES[mes - 1] if 1 <= mes <= 12 else str(mes)
        emision = datetime.now().strftime("%d/%m/%Y %H:%M")

        servicio_titulos = {
            ServicioReporteEnum.AMBULANCIA: "SERVICIO DE AMBULANCIA Y ATENCIÓN PREHOSPITALARIA",
            ServicioReporteEnum.GRUA: "SERVICIO DE AUXILIO MECÁNICO Y GRÚAS",
            ServicioReporteEnum.PATRULLAJE: "SERVICIO DE PATRULLAJE E INSPECCIÓN VIAL",
        }
        titulo_servicio = servicio_titulos.get(servicio, f"SERVICIO DE {servicio.value.upper()}")

        subtitulo = f"Periodo: {nombre_mes} {anio}  |  Fecha de emisión: {emision}"
        story.extend(self._construir_encabezado_institucional(
            f"REPORTE MENSUAL DE OPERACIONES  —  {titulo_servicio}",
            subtitulo,
            estilos,
            ancho_util=ancho_util
        ))

        # Tarjetas de resumen rápido
        total_filas = len(df)
        c_card_bg = colors.HexColor("#f8fafc")
        c_border = colors.HexColor("#cbd5e1")

        kpi_cols = [
            [Paragraph(f"{total_filas:,}", estilos["kpi_num"]), Paragraph("TOTAL REGISTROS", estilos["kpi_label"])],
            [Paragraph(nombre_mes.upper(), estilos["kpi_num"]), Paragraph("MES AUDITADO", estilos["kpi_label"])],
            [Paragraph(str(anio), estilos["kpi_num"]), Paragraph("AÑO FISCAL", estilos["kpi_label"])],
        ]
        ancho_kpi = ancho_util / len(kpi_cols)
        tabla_kpi = Table([kpi_cols], colWidths=[ancho_kpi] * len(kpi_cols))
        tabla_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_card_bg),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tabla_kpi)
        story.append(Spacer(1, 10))

        # Tabla de Datos MTOP
        if df.empty:
            story.append(Paragraph(
                f"No se registraron operaciones de {servicio.value} para el mes de {nombre_mes} {anio}.",
                estilos["body"]
            ))
        else:
            columnas = list(df.columns)
            cant_cols = len(columnas)
            ancho_col = ancho_util / cant_cols

            encabezados = [Paragraph(str(c).upper(), estilos["table_header"]) for c in columnas]
            datos_tabla = [encabezados]

            for _, row in df.iterrows():
                fila_celdas = []
                for val in row:
                    texto_val = self._formatear_valor_celda(val)
                    fila_celdas.append(Paragraph(texto_val, estilos["table_cell"]))
                datos_tabla.append(fila_celdas)

            tabla_mtop = Table(datos_tabla, colWidths=[ancho_col] * cant_cols, repeatRows=1)
            tabla_mtop.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2e5a")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(tabla_mtop)

        doc.build(story, canvasmaker=NumberedCanvas)
        output.seek(0)
        filename = f"reporte_mtop_{servicio.value}_{anio}_{mes:02d}.pdf"
        return output, filename

    def _renderizar_tabla_markdown(self, filas_md: List[str], estilos: Dict[str, ParagraphStyle], ancho_util: float) -> Table:
        """Convierte una tabla Markdown en un Flowable Table de ReportLab con anchos de columna proporcionales."""
        datos = []
        filas_limpias = []
        for i, fila in enumerate(filas_md):
            celdas_texto = [c.strip() for c in fila.split("|")[1:-1]]
            if not celdas_texto:
                continue
            filas_limpias.append(celdas_texto)
            if i == 0:
                celdas = [Paragraph(self._limpiar_markdown(c), estilos["table_header"]) for c in celdas_texto]
            else:
                celdas = [Paragraph(self._limpiar_markdown(c), estilos["table_cell"]) for c in celdas_texto]
            datos.append(celdas)

        if not datos:
            return Table([[""]])

        num_cols = max(len(r) for r in datos)
        # Normalizar filas
        for r in datos:
            while len(r) < num_cols:
                r.append(Paragraph("", estilos["table_cell"]))

        # Cálculo de anchos proporcionales inteligentes según longitud de contenido
        pesos_cols = []
        for c in range(num_cols):
            max_len = 0
            for fila_c in filas_limpias:
                if c < len(fila_c):
                    max_len = max(max_len, len(fila_c[c]))
            peso = max(max_len, 8)
            if max_len > 25:
                peso = peso * 1.2
            elif max_len <= 12:
                peso = max(peso * 0.7, 6)
            pesos_cols.append(peso)

        total_peso = sum(pesos_cols)
        anchos = [(p / total_peso) * ancho_util for p in pesos_cols]

        # Garantizar ancho mínimo de 45pt por columna para legibilidad
        for idx_col in range(num_cols):
            if anchos[idx_col] < 45:
                anchos[idx_col] = 45

        factor = ancho_util / sum(anchos)
        anchos = [a * factor for a in anchos]

        t = Table(datos, colWidths=anchos)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2e5a")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def _limpiar_markdown(self, texto: str) -> str:
        """Convierte formatos Markdown básicos a etiquetas XML compatibles con ReportLab."""
        if not texto:
            return ""
        # Negritas
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
        # Cursivas
        t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
        # Limpieza de caracteres problemáticos XML
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Restaurar etiquetas permitidas
        t = t.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        t = t.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
        # Remover comillas residuales que parezcan comentarios
        t = t.replace('"', '').replace('“', '').replace('”', '')
        return t

    def _formatear_valor_celda(self, val: Any) -> str:
        """Formatea valores de celdas para su despliegue limpio."""
        if val is None or pd.isna(val):
            return "-"
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.strftime("%d/%m/%Y %H:%M")
        if isinstance(val, (int, float, Decimal)):
            if isinstance(val, float) and val.is_integer():
                return f"{int(val)}"
            if isinstance(val, float):
                return f"{val:.2f}"
            return f"{val:,}"
        return str(val)


pdf_service = PDFReportService()
