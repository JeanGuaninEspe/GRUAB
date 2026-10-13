/**
 * Interfaces y tipos de TypeScript para la integración con la API RESTful de FastAPI (VehiculosRC)
 */
import { Severidad, Sentido, TipoGrua, Turno, RolPersonal } from "./asistencias";

// ==========================================
// 1. CATÁLOGOS
// ==========================================

export type TipoFlota = "AMBULANCIA" | "GRUA" | "PATRULLA";

export interface PersonalRead {
  id_personal: number;
  nombre_completo: string;
  rol: RolPersonal | string;
  activo: boolean;
}

export interface VehiculoRead {
  id_vehiculo: number;
  codigo_interno: string;
  placa: string;
  tipo_flota: TipoFlota | string;
  descripcion?: string | null;
  activo: boolean;
}

// ==========================================
// 2. ANALÍTICA Y KPIS
// ==========================================

export type NivelRiesgo = "EXTREMO" | "ALTO" | "MEDIO" | "BAJO";

export interface KPITiemposItem {
  tipo_servicio: string;
  codigo_formulario: string;
  fecha?: string | null;
  turno?: number | null;
  abscisa_km?: number | null;
  sentido?: string | null;
  tiempo_despacho_arribo_min?: number | null;
  tiempo_en_sitio_min?: number | null;
  ciclo_total_min?: number | null;
  km_recorridos?: number | null;
}

export interface KPIServicioResumen {
  tipo_servicio: string;
  total_eventos: number;
  promedio_despacho_arribo_min?: number | null;
  promedio_sitio_min?: number | null;
  promedio_ciclo_total_min?: number | null;
  total_km_recorridos?: number | null;
}

export interface KPITiemposRespuestaResponse {
  total_registros: number;
  promedio_despacho_arribo_min?: number | null;
  promedio_sitio_min?: number | null;
  promedio_ciclo_total_min?: number | null;
  total_km_recorridos?: number | null;
  resumen_por_servicio: KPIServicioResumen[];
  detalles: KPITiemposItem[];
}

export interface PuntoNegroItem {
  km_tramo: number;
  sentido: string;
  tipo_accidente?: string | null;
  posible_causa?: string | null;
  severidad?: Severidad | string | null;
  total_eventos: number;
}

export interface PuntosNegrosResponse {
  total_tramos_criticos: number;
  total_eventos_acumulados: number;
  tramos: PuntoNegroItem[];
}

export interface TramoScoringItem {
  km_inicio: number;
  km_fin: number;
  tramo_label: string;
  total_eventos: number;
  total_ambulancias: number;
  total_gruas: number;
  total_fatales: number;
  total_graves: number;
  total_leves: number;
  indice_criticidad: number;
  nivel_riesgo: NivelRiesgo;
  sentido_predominante?: string | null;
  principal_tipo_accidente?: string | null;
  principal_motivo_o_causa?: string | null;
  franja_horaria_mayor_incidencia?: string | null;
  recomendacion_tactica?: string | null;
}

export interface TramosScoringResponse {
  criterio_agrupacion_km: number;
  total_tramos_analizados: number;
  total_eventos_evaluados: number;
  resumen_niveles_riesgo: Record<string, number>;
  top_tramos_criticos: TramoScoringItem[];
}

export interface PatronHoraItem {
  hora: number;
  franja_label: string;
  total_eventos: number;
  total_ambulancias: number;
  total_gruas: number;
  total_accidentes_graves_o_fatales: number;
  porcentaje: number;
}

export interface PatronDiaItem {
  dia_nombre: string;
  total_eventos: number;
  total_ambulancias: number;
  total_gruas: number;
  porcentaje: number;
}

export interface PatronesTemporalesResponse {
  total_eventos_analizados: number;
  hora_pico_maxima: string;
  dia_pico_maximo: string;
  eventos_fin_de_semana: number;
  eventos_entre_semana: number;
  porcentaje_fin_de_semana: number;
  distribucion_por_franja: Record<string, number>;
  distribucion_por_hora: PatronHoraItem[];
  distribucion_por_dia: PatronDiaItem[];
}

export interface RecomendacionDespliegueItem {
  prioridad: number;
  recurso_recomendado: string;
  tramo_cobertura: string;
  horario_optimo: string;
  diagnostico_problema: string;
  accion_preventiva: string;
  impacto_esperado: string;
}

export interface RecomendacionesDespliegueResponse {
  fecha_generacion: string;
  total_recomendaciones: number;
  estrategia_general: string;
  recomendaciones: RecomendacionDespliegueItem[];
}

export interface DashboardEjecutivoResponse {
  total_asistencias_historicas: number;
  total_ambulancias: number;
  total_gruas: number;
  total_patrullajes: number;
  tasa_accidentabilidad_porcentaje: number;
  tasa_asistencia_mecanica_porcentaje: number;
  km_totales_atendidos: number;
  tiempo_promedio_llegada_min: number;
  tiempo_promedio_sitio_min: number;
  tiempo_promedio_ciclo_min: number;
  tramo_mas_critico?: TramoScoringItem | null;
  franja_horaria_mas_critica: string;
  dia_mas_critico: string;
  recomendacion_ejecutiva: string;
}

// ==========================================
// 3. OPERACIONES
// ==========================================

export interface AmbulanciaApiRead {
  id_asistencia: number;
  codigo_formulario: string;
  id_supervisor?: number | null;
  id_paramedico?: number | null;
  id_chofer?: number | null;
  id_vehiculo?: number | null;
  turno?: Turno | null;
  ts_llamada?: string | null;
  ts_arribo?: string | null;
  ts_termino?: string | null;
  ts_retorno?: string | null;
  sector_referencia?: string | null;
  abscisa_km?: number | null;
  sentido?: Sentido | string | null;
  nombre_paciente?: string | null;
  rango_edad?: string | null;
  motivo_atencion?: string | null;
  tipo_incidente?: string | null;
  tipo_accidente?: string | null;
  severidad?: Severidad | string | null;
  destino_paciente?: string | null;
  usuarios_atendidos?: number | null;
  servicio_comunidad?: boolean | null;
  odometro_salida_km?: number | null;
  odometro_llegada_km?: number | null;
  km_recorridos?: number | null;
  reportado_mtop?: boolean | null;
  observaciones?: string | null;
}

export interface GruaApiRead {
  id_asistencia_grua: number;
  codigo_formulario: string;
  id_supervisor?: number | null;
  id_chofer?: number | null;
  id_vehiculo?: number | null;
  turno?: Turno | null;
  tipo_grua?: TipoGrua | string | null;
  ts_llamada?: string | null;
  ts_arribo?: string | null;
  ts_termino?: string | null;
  ts_retorno?: string | null;
  sector_referencia?: string | null;
  abscisa_km?: number | null;
  sentido?: Sentido | string | null;
  usuario_reporta?: string | null;
  placa_asistida?: string | null;
  tipo_vehiculo_asistido?: string | null;
  usuarios_atendidos?: number | null;
  motivo_atencion?: string | null;
  tipo_accidente?: string | null;
  posible_causa?: string | null;
  severidad?: Severidad | string | null;
  km_origen_traslado?: number | null;
  km_destino_traslado?: number | null;
  odometro_salida_km?: number | null;
  odometro_llegada_km?: number | null;
  km_recorridos?: number | null;
  reportado_mtop?: boolean | null;
  observaciones?: string | null;
}

export interface AsistenciaGruaPaginadaResponse {
  total: number;
  skip: number;
  limit: number;
  items: GruaApiRead[];
}

export interface PatrullajeApiRead {
  id_patrullaje: number;
  codigo_patrullaje: string;
  id_supervisor?: number | null;
  id_chofer?: number | null;
  id_vehiculo?: number | null;
  fecha_recorrido?: string | null;
  hora_salida?: string | null;
  hora_retorno?: string | null;
  ruta_descripcion?: string | null;
  odometro_inicial_km?: number | null;
  odometro_final_km?: number | null;
  km_recorridos?: number | null;
  novedad_en_via?: boolean | null;
  observaciones?: string | null;
}

// ==========================================
// 4. REPORTES E INFORMES IA
// ==========================================

export type ServicioReporte = "ambulancia" | "grua" | "patrullaje";

export interface ReporteEjecutivoIARequest {
  fecha_inicio: string;
  fecha_fin: string;
}

export interface DesgloseMensualItem {
  mes: string;
  total: number;
  porcentaje: string;
  porcentaje_num: number;
}

export interface DesgloseSectorItem {
  sector: string;
  cantidad: number;
  porcentaje: string;
  porcentaje_num: number;
}

export interface DesgloseCruzadoItem {
  mes: string;
  sector: string;
  cantidad: number;
}

export interface ReporteEjecutivoIAResponse {
  periodo: string;
  fecha_inicio: string;
  fecha_fin: string;
  total_auxilios: number;
  kpis: {
    promedio_llegada_min?: number;
    promedio_sitio_min?: number;
    promedio_ciclo_min?: number;
    km_totales?: number;
  };
  desglose_mensual: DesgloseMensualItem[];
  desglose_sectores: DesgloseSectorItem[];
  desglose_cruzado: DesgloseCruzadoItem[];
  tiempos_promedio: Record<string, any>;
  resumen_markdown: string;
}
