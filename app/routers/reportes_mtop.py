"""
Endpoints para la Exportación de Reportes Oficiales en Excel (.xlsx) y PDF con Logo de COSAD 25
para el Ministerio de Transporte y Obras Públicas (MTOP).
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.reportes_repo import reportes_repo
from app.services.excel_service import excel_service
from app.services.pdf_service import pdf_service
from app.schemas.reportes import ServicioReporteEnum

router = APIRouter(prefix="/reportes-mtop", tags=["Reportes MTOP"])


@router.get(
    "/exportar-excel",
    status_code=status.HTTP_200_OK,
    summary="Exportar reporte mensual MTOP en formato Excel (.xlsx)",
    description=(
        "Consulta las vistas ministeriales (dbo.vw_mtop_ambulancias, dbo.vw_mtop_gruas o dbo.vw_mtop_patrullaje) "
        "para el mes y año indicados, generando un archivo Excel en memoria formateado profesionalmente para su descarga directa."
    ),
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Archivo Excel descargable con los registros ministeriales formateados.",
        }
    },
)
def exportar_reporte_excel(
    servicio: ServicioReporteEnum = Query(..., description="Tipo de servicio a exportar: ambulancia, grua o patrullaje"),
    mes: int = Query(..., ge=1, le=12, description="Mes del reporte (1 = Enero, 12 = Diciembre)"),
    anio: int = Query(..., ge=2000, le=2100, description="Año del reporte (ej. 2026)"),
    db: Session = Depends(get_db),
):
    # Extraer DataFrame con los datos de la vista MTOP correspondiente
    df = reportes_repo.get_datos_mtop_df(db=db, servicio=servicio, mes=mes, anio=anio)

    # Generar el archivo Excel estilizado en memoria
    excel_stream, filename = excel_service.generar_reporte_mtop_excel(
        df=df, servicio=servicio, mes=mes, anio=anio
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/exportar-pdf",
    status_code=status.HTTP_200_OK,
    summary="Exportar reporte mensual MTOP en formato PDF con Logo Oficial de COSAD 25",
    description=(
        "Genera un documento PDF ministerial en formato apaisado (Landscape) con la imagen oficial de COSAD 25, "
        "tablas estilizadas y foliado de páginas oficial para archivo o auditoría."
    ),
    responses={
        200: {
            "content": {
                "application/pdf": {}
            },
            "description": "Documento PDF oficial descargable.",
        }
    },
)
def exportar_reporte_pdf(
    servicio: ServicioReporteEnum = Query(..., description="Tipo de servicio a exportar: ambulancia, grua o patrullaje"),
    mes: int = Query(..., ge=1, le=12, description="Mes del reporte (1 = Enero, 12 = Diciembre)"),
    anio: int = Query(..., ge=2000, le=2100, description="Año del reporte (ej. 2026)"),
    db: Session = Depends(get_db),
):
    # Extraer DataFrame con los datos de la vista MTOP correspondiente
    df = reportes_repo.get_datos_mtop_df(db=db, servicio=servicio, mes=mes, anio=anio)

    # Generar el documento PDF estilizado con el logo institucional de COSAD 25
    pdf_stream, filename = pdf_service.generar_reporte_mtop_pdf(
        df=df, servicio=servicio, mes=mes, anio=anio
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers=headers,
    )
