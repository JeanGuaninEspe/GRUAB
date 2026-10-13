/**
 * Servicio de Catálogos (Personal y Flota Vehicular)
 */
import { apiClient } from "@/lib/api-client";
import { PersonalRead, VehiculoRead } from "@/types/api";

export const catalogosService = {
  /**
   * Obtiene la lista completa de personal de la concesión
   * GET /catalogos/personal
   */
  async getPersonal(): Promise<PersonalRead[]> {
    return apiClient.get<PersonalRead[]>("/catalogos/personal");
  },

  /**
   * Obtiene la flota vehicular activa de la concesión
   * GET /catalogos/vehiculos
   */
  async getVehiculos(): Promise<VehiculoRead[]> {
    return apiClient.get<VehiculoRead[]>("/catalogos/vehiculos");
  },

  /**
   * Obtiene choferes y operadores de grúa activos
   * GET /catalogos/choferes-grua
   */
  async getChoferesGrua(): Promise<PersonalRead[]> {
    return apiClient.get<PersonalRead[]>("/catalogos/choferes-grua");
  },

  /**
   * Obtiene supervisores de operaciones activos
   * GET /catalogos/supervisores
   */
  async getSupervisores(): Promise<PersonalRead[]> {
    return apiClient.get<PersonalRead[]>("/catalogos/supervisores");
  },

  /**
   * Obtiene unidades vehiculares de grúa activas
   * GET /catalogos/vehiculos-grua
   */
  async getVehiculosGrua(): Promise<VehiculoRead[]> {
    return apiClient.get<VehiculoRead[]>("/catalogos/vehiculos-grua");
  },
};
