/**
 * Servicio de Analítica, KPIs de Respuesta, Hotspots y Dashboard Ejecutivo
 */
import { apiClient } from "@/lib/api-client";
import {
  DashboardEjecutivoResponse,
  KPITiemposRespuestaResponse,
  PuntosNegrosResponse,
  TramosScoringResponse,
  PatronesTemporalesResponse,
  RecomendacionesDespliegueResponse,
} from "@/types/api";

export interface DashboardEjecutivoQueryParams {
  fecha_inicio?: string;
  fecha_fin?: string;
  servicio?: "AMBULANCIA" | "GRUA" | "PATRULLAJE" | string;
  turno?: 1 | 2 | 3;
  id_vehiculo?: number;
}

export interface KPITiemposQueryParams {
  fecha_inicio?: string;
  fecha_fin?: string;
  servicio?: "AMBULANCIA" | "GRUA" | "PATRULLAJE" | string;
  turno?: 1 | 2 | 3;
  limit?: number;
}

export interface PuntosNegrosQueryParams {
  severidad?: "LEVE" | "GRAVE" | "FATAL" | string;
  causa?: string;
  sentido?: "ASCENDENTE" | "DESCENDENTE" | "BIDIRECCIONAL" | string;
  limit?: number;
}

export interface TramosScoringQueryParams {
  tamano_tramo_km?: number;
  fecha_inicio?: string;
  fecha_fin?: string;
  servicio?: string;
  turno?: 1 | 2 | 3;
  id_vehiculo?: number;
  top_n?: number;
}

export interface PatronesTemporalesQueryParams {
  fecha_inicio?: string;
  fecha_fin?: string;
  servicio?: string;
  turno?: 1 | 2 | 3;
  id_vehiculo?: number;
}

export const analiticaService = {
  /**
   * Obtiene las métricas consolidadas del Dashboard Ejecutivo:
   * totales de asistencias, ambulancias, grúas, patrullajes, tasas, tiempos y recomendación ejecutiva de IA.
   * GET /analitica/dashboard-ejecutivo
   */
  async getDashboardEjecutivo(params?: DashboardEjecutivoQueryParams): Promise<DashboardEjecutivoResponse> {
    return apiClient.get<DashboardEjecutivoResponse>("/analitica/dashboard-ejecutivo", params);
  },

  /**
   * Obtiene KPIs y tiempos de respuesta operativa:
   * promedio_despacho_arribo_min, promedio_sitio_min, promedio_ciclo_total_min, resumen por servicio y detalle.
   * GET /analitica/tiempos-respuesta
   */
  async getTiemposRespuesta(params?: KPITiemposQueryParams): Promise<KPITiemposRespuestaResponse> {
    return apiClient.get<KPITiemposRespuestaResponse>("/analitica/tiempos-respuesta", params);
  },

  /**
   * Obtiene la identificación y priorización de puntos negros de accidentabilidad.
   * GET /analitica/puntos-negros
   */
  async getPuntosNegros(params?: PuntosNegrosQueryParams): Promise<PuntosNegrosResponse> {
    return apiClient.get<PuntosNegrosResponse>("/analitica/puntos-negros", params);
  },

  /**
   * Obtiene el modelo de scoring de peligrosidad vial y hotspots por tramo kilométrico.
   * GET /analitica/tramos-criticos-scoring
   */
  async getTramosScoring(params?: TramosScoringQueryParams): Promise<TramosScoringResponse> {
    return apiClient.get<TramosScoringResponse>("/analitica/tramos-criticos-scoring", params);
  },

  /**
   * Obtiene el análisis de patrones temporales (horas pico, distribución por día y franja horaria).
   * GET /analitica/patrones-temporales
   */
  async getPatronesTemporales(params?: PatronesTemporalesQueryParams): Promise<PatronesTemporalesResponse> {
    return apiClient.get<PatronesTemporalesResponse>("/analitica/patrones-temporales", params);
  },

  /**
   * Obtiene el plan de despliegue estratégico táctico para unidades de grúa, ambulancia y patrulla.
   * GET /analitica/recomendaciones-despliegue
   */
  async getRecomendacionesDespliegue(): Promise<RecomendacionesDespliegueResponse> {
    return apiClient.get<RecomendacionesDespliegueResponse>("/analitica/recomendaciones-despliegue");
  },
};
