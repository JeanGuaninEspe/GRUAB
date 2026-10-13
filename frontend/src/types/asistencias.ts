export type Severidad = 'LEVE' | 'GRAVE' | 'FATAL';
export type Sentido = 'ASCENDENTE' | 'DESCENDENTE' | 'BIDIRECCIONAL';
export type TipoGrua = 'PEQUEÑA' | 'GRANDE' | 'PLATAFORMA';
export type Turno = 1 | 2 | 3;
export type RolPersonal = 'SUPERVISOR' | 'PARAMEDICO' | 'CHOFER_AMBULANCIA' | 'CHOFER_GRUA' | 'PATRULLERO';

export interface AsistenciaAmbulancia {
  id_asistencia: number;
  codigo_formulario: string;
  id_supervisor?: number;
  id_paramedico?: number;
  id_chofer?: number;
  id_vehiculo?: number;
  supervisor_nombre: string;
  paramedico_nombre: string;
  chofer_nombre: string;
  vehiculo_codigo: string;
  placa_unidad: string;
  turno: Turno;
  ts_llamada: string;
  ts_arribo: string;
  ts_termino: string;
  ts_retorno: string;
  sector_referencia: string;
  abscisa_km: number;
  sentido: Sentido;
  nombre_paciente: string;
  rango_edad: string;
  motivo_atencion: string;
  tipo_incidente: string;
  tipo_accidente: string;
  severidad: Severidad;
  destino_paciente: string;
  usuarios_atendidos: number;
  servicio_comunidad: boolean;
  odometro_salida_km: number;
  odometro_llegada_km: number;
  km_recorridos: number;
  reportado_mtop: boolean;
  observaciones?: string;
}

export interface AsistenciaGrua {
  id_asistencia_grua: number;
  codigo_formulario: string;
  turno: Turno;
  tipo_grua: TipoGrua;
  ts_llamada: string;
  ts_arribo: string;
  ts_termino: string;
  ts_retorno: string;
  sector_referencia: string;
  abscisa_km: number;
  sentido: Sentido;
  usuario_reporta: string;
  placa_asistida: string;
  tipo_vehiculo_asistido: string;
  usuarios_atendidos: number;
  motivo_atencion: string;
  tipo_accidente: string;
  posible_causa: string;
  severidad: Severidad;
  km_origen_traslado: number;
  km_destino_traslado: number;
  odometro_salida_km: number;
  odometro_llegada_km: number;
  km_recorridos: number;
  reportado_mtop: boolean;
  observaciones: string;
  chofer_nombre: string;
  vehiculo_codigo: string;
  supervisor_nombre: string;
}

export interface BitacoraPatrullaje {
  id_patrullaje: number;
  codigo_patrullaje: string;
  fecha_recorrido: string;
  hora_salida: string;
  hora_retorno: string;
  ruta_descripcion: string;
  odometro_inicial_km: number;
  odometro_final_km: number;
  km_recorridos: number;
  novedad_en_via: boolean;
  observaciones: string;
  patrullero_nombre: string;
  vehiculo_codigo: string;
  supervisor_nombre: string;
}

export interface DashboardMetrics {
  totalAmbulancias: number;
  totalGruas: number;
  totalPatrullajes: number;
  kmPatrullados: number;
  mtopSincronizadosPercent: number;
  casosCriticos: number;
  tiempoPromedioRespuestaMin: number;
}
