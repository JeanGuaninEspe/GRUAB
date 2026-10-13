/**
 * Servicio de Reportes Ministeriales MTOP y Análisis Ejecutivo Asistido por IA
 */
import { apiClient } from "@/lib/api-client";
import { ServicioReporte, ReporteEjecutivoIAResponse } from "@/types/api";

export const reportesService = {
  /**
   * Descarga el reporte mensual MTOP en formato Excel (.xlsx)
   * GET /reportes-mtop/exportar-excel
   */
  async exportarReporteExcel(
    servicio: ServicioReporte,
    mes: number,
    anio: number
  ): Promise<{ blob: Blob; filename: string }> {
    return apiClient.downloadBlob("/reportes-mtop/exportar-excel", {
      servicio,
      mes,
      anio,
    });
  },

  /**
   * Descarga el reporte mensual MTOP en formato PDF con Logo Oficial de COSAD 25
   * GET /reportes-mtop/exportar-pdf
   */
  async exportarReportePdf(
    servicio: ServicioReporte,
    mes: number,
    anio: number
  ): Promise<{ blob: Blob; filename: string }> {
    return apiClient.downloadBlob("/reportes-mtop/exportar-pdf", {
      servicio,
      mes,
      anio,
    });
  },

  /**
   * Genera el informe ejecutivo de auditoría y analítica asistido por IA (Qwen 2.5 local)
   * POST /reportes-gruas/ejecutivo-ia
   */
  async generarReporteEjecutivoIA(
    fecha_inicio: string,
    fecha_fin: string
  ): Promise<ReporteEjecutivoIAResponse> {
    return apiClient.post<ReporteEjecutivoIAResponse>("/reportes-gruas/ejecutivo-ia", {
      fecha_inicio,
      fecha_fin,
    });
  },

  /**
   * Utilidad auxiliar en navegador para disparar la descarga directa de un Blob
   */
  triggerBrowserDownload(blob: Blob, filename: string): void {
    if (typeof window === "undefined") return;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
