/**
 * Servicio Frontend para interacción con IA (Qwen 2.5 7B determinista)
 * - Autocompletado estructurado de despacho
 * - Diagnóstico ejecutivo de dashboard
 * - Consultas deterministas en lenguaje natural con grounding SQL
 */
import { apiClient } from "@/lib/api-client";

export interface DespachoParseado {
  tipo_asistencia: "grua" | "ambulancia" | "patrullaje" | null;
  codigo_formulario: string | null;
  turno: "1" | "2" | "3" | null;
  chofer: string | null;
  paramedico: string | null;
  supervisor: string | null;
  tipo_grua: "PEQUEÑA" | "GRANDE" | "PLATAFORMA" | null;
  ubicacion_referencia: string | null;
  tramo_ruta: string | null;
  abscisa_km: number | string | null;
  sentido: "ASCENDENTE" | "DESCENDENTE" | "BIDIRECCIONAL" | null;
  prioridad: "LEVE" | "GRAVE" | "FATAL" | null;
  descripcion_falla_o_motivo: string | null;
  vehiculo_involucrado: string | null;
  placa_vehiculo: string | null;
  nombre_paciente: string | null;
  edad_paciente: string | null;
  usuario_reporta: string | null;
  destino_paciente: string | null;
  odometro_salida_km: number | null;
  odometro_llegada_km: number | null;
}

export interface ConsultaAIResponse {
  respuesta: string;
  accion_ejecutada: string;
  datos_fuente: any;
}

export interface DiagnosticoDashboardResponse {
  resumen: string;
  metricas_base: Record<string, any>;
}

export interface MensajeHistorial {
  role: "user" | "assistant" | "system";
  content: string;
}

export const aiService = {
  /**
   * Consulta determinista en lenguaje natural con grounding estricto a SQL
   * POST /ai/consultar
   */
  async consultarAI(
    pregunta: string,
    historial: MensajeHistorial[] = [],
    sessionId?: string
  ): Promise<ConsultaAIResponse> {
    return apiClient.post<ConsultaAIResponse>("/ai/consultar", {
      pregunta,
      historial,
      session_id: sessionId,
    });
  },

  /**
   * Extracción estructurada de despacho a partir de texto libre / reporte de radio
   * POST /ai/parsear-despacho
   */
  async parsearDespacho(texto: string): Promise<DespachoParseado> {
    return apiClient.post<DespachoParseado>("/ai/parsear-despacho", {
      texto_reporte: texto,
    });
  },

  /**
   * Obtiene un diagnóstico ejecutivo sintetizado en 3 puntos clave sobre métricas del periodo
   * POST /ai/diagnostico-dashboard
   */
  async obtenerDiagnosticoDashboard(
    rangoFechas?: { desde?: string; hasta?: string }
  ): Promise<DiagnosticoDashboardResponse> {
    return apiClient.post<DiagnosticoDashboardResponse>("/ai/diagnostico-dashboard", {
      fecha_inicio: rangoFechas?.desde || null,
      fecha_fin: rangoFechas?.hasta || null,
    });
  },
};
