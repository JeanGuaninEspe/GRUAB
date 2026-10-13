/**
 * Servicio de Operaciones (Ambulancias, Grúas y Patrullaje)
 */
import { apiClient } from "@/lib/api-client";
import {
  AmbulanciaApiRead,
  GruaApiRead,
  PatrullajeApiRead,
  AsistenciaGruaPaginadaResponse,
} from "@/types/api";

export interface OperacionesQueryParams {
  fecha_inicio?: string;
  fecha_fin?: string;
  turno?: 1 | 2 | 3;
  id_vehiculo?: number;
  skip?: number;
  limit?: number;
}

export const operacionesService = {
  /**
   * Obtiene la lista de asistencias de ambulancias
   * GET /operaciones/ambulancias
   */
  async getAsistenciasAmbulancia(params?: OperacionesQueryParams): Promise<AmbulanciaApiRead[]> {
    return apiClient.get<AmbulanciaApiRead[]>("/operaciones/ambulancias", params);
  },

  /**
   * Registra una nueva asistencia médica de ambulancia
   * POST /operaciones/ambulancias
   */
  async crearAsistenciaAmbulancia(payload: any): Promise<any> {
    return apiClient.post<any>("/operaciones/ambulancias", payload);
  },

  /**
   * Obtiene la lista de asistencias de grúa (paginadas o completas)
   * GET /operaciones/gruas o /asistencias-grua/
   */
  async getAsistenciasGrua(params?: OperacionesQueryParams): Promise<AsistenciaGruaPaginadaResponse> {
    try {
      const list = await apiClient.get<GruaApiRead[]>("/operaciones/gruas", params);
      return {
        total: list.length,
        skip: params?.skip || 0,
        limit: params?.limit || list.length,
        items: list,
      };
    } catch {
      return await apiClient.get<AsistenciaGruaPaginadaResponse>("/asistencias-grua/", params);
    }
  },

  /**
   * Registra una nueva orden de servicio y remolque de grúa
   * POST /asistencias-grua/
   */
  async crearAsistenciaGrua(payload: any): Promise<any> {
    return apiClient.post<any>("/asistencias-grua/", payload);
  },

  /**
   * Obtiene las bitácoras diarias de patrullaje vial
   * GET /operaciones/patrullaje
   */
  async getBitacoraPatrullaje(params?: OperacionesQueryParams): Promise<PatrullajeApiRead[]> {
    return apiClient.get<PatrullajeApiRead[]>("/operaciones/patrullaje", params);
  },

  /**
   * Registra un nuevo recorrido de patrullaje e inspección vial
   * POST /operaciones/patrullaje
   */
  async crearPatrullaje(payload: any): Promise<any> {
    return apiClient.post<any>("/operaciones/patrullaje", payload);
  },
};
