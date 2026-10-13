# Endpoints del Backend (`VehiculosRC`)
A continuación se detallan los endpoints disponibles, sus métodos, y la estructura esperada para request/response. Esto servirá de contexto para integrar el frontend con Gemini.

### GET `/api/v1/catalogos/personal`
**Propósito:** Listar personal de la concesión
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ PersonalRead { nombre_completo*: string, rol*: any, activo: boolean, id_personal*: integer }} ]`

### GET `/api/v1/catalogos/vehiculos`
**Propósito:** Listar flota de vehículos de la concesión
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ VehiculoRead { codigo_interno*: string, placa*: string, tipo_flota*: any, descripcion: any, activo: boolean, id_vehiculo*: integer }} ]`

### POST `/api/v1/operaciones/ambulancias`
**Propósito:** Registrar asistencia médica de ambulancia
- **Payload (Body) que se envía:** `AmbulanciaCreate { codigo_formulario*: string, id_supervisor*: integer, id_paramedico*: integer, id_chofer*: integer, id_vehiculo*: integer, turno*: any, ts_llamada*: string (date-time), ts_arribo*: string (date-time), ts_termino*: string (date-time), ts_retorno*: string (date-time), sector_referencia*: string, abscisa_km*: any, sentido*: any, nombre_paciente: any, rango_edad: any, motivo_atencion*: string, tipo_incidente: any, tipo_accidente: any, severidad*: any, destino_paciente: any, usuarios_atendidos: integer, servicio_comunidad: boolean, odometro_salida_km*: any, odometro_llegada_km*: any, reportado_mtop: boolean }}`
- **Respuesta (Response) que se recibe:** `None`

### GET `/api/v1/operaciones/ambulancias`
**Propósito:** Listar asistencias de ambulancias
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ AmbulanciaRead { codigo_formulario*: string, id_supervisor: any, id_paramedico: any, id_chofer: any, id_vehiculo: any, turno: any, ts_llamada: any, ts_arribo: any, ts_termino: any, ts_retorno: any, sector_referencia: any, abscisa_km: any, sentido: any, nombre_paciente: any, rango_edad: any, motivo_atencion: any, tipo_incidente: any, tipo_accidente: any, severidad: any, destino_paciente: any, usuarios_atendidos: any, servicio_comunidad: any, odometro_salida_km: any, odometro_llegada_km: any, reportado_mtop: any, id_asistencia*: integer, km_recorridos: any }} ]`

### POST `/api/v1/operaciones/gruas`
**Propósito:** Registrar asistencia y remolque de grúa
- **Payload (Body) que se envía:** `GruaCreate { codigo_formulario*: string, id_supervisor*: integer, id_chofer*: integer, id_vehiculo: any, turno*: any, tipo_grua*: any, ts_llamada*: string (date-time), ts_arribo*: string (date-time), ts_termino*: string (date-time), ts_retorno*: string (date-time), sector_referencia*: string, abscisa_km*: any, sentido*: any, usuario_reporta: any, placa_asistida: any, tipo_vehiculo_asistido: any, usuarios_atendidos: integer, motivo_atencion*: string, tipo_accidente: any, posible_causa: any, severidad: any, km_origen_traslado: any, km_destino_traslado: any, odometro_salida_km*: any, odometro_llegada_km*: any, reportado_mtop: boolean, observaciones: any }}`
- **Respuesta (Response) que se recibe:** `None`

### GET `/api/v1/operaciones/gruas`
**Propósito:** Listar asistencias de grúas
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ GruaRead { codigo_formulario*: string, id_supervisor: any, id_chofer: any, id_vehiculo: any, turno: any, tipo_grua: any, ts_llamada: any, ts_arribo: any, ts_termino: any, ts_retorno: any, sector_referencia: any, abscisa_km: any, sentido: any, usuario_reporta: any, placa_asistida: any, tipo_vehiculo_asistido: any, usuarios_atendidos: any, motivo_atencion: any, tipo_accidente: any, posible_causa: any, severidad: any, km_origen_traslado: any, km_destino_traslado: any, odometro_salida_km: any, odometro_llegada_km: any, reportado_mtop: any, observaciones: any, id_asistencia_grua*: integer, km_recorridos: any }} ]`

### POST `/api/v1/operaciones/patrullaje`
**Propósito:** Registrar bitácora diaria de patrullaje e inspección
- **Payload (Body) que se envía:** `PatrullajeCreate { codigo_patrullaje*: string, id_supervisor*: integer, id_chofer*: integer, id_vehiculo*: integer, fecha_recorrido*: string (date), hora_salida*: string (time), hora_retorno*: string (time), ruta_descripcion*: string, odometro_inicial_km*: any, odometro_final_km*: any, novedad_en_via: boolean, observaciones: any }}`
- **Respuesta (Response) que se recibe:** `None`

### GET `/api/v1/operaciones/patrullaje`
**Propósito:** Listar bitácoras de patrullaje vial
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ PatrullajeRead { codigo_patrullaje*: string, id_supervisor: any, id_chofer: any, id_vehiculo: any, fecha_recorrido: any, hora_salida: any, hora_retorno: any, ruta_descripcion: any, odometro_inicial_km: any, odometro_final_km: any, novedad_en_via: any, observaciones: any, id_patrullaje*: integer, km_recorridos: any }} ]`

### GET `/api/v1/analitica/tiempos-respuesta`
**Propósito:** Consultar KPIs y tiempos de respuesta operativa
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `KPITiemposRespuestaResponse { total_registros*: integer, promedio_despacho_arribo_min: any, promedio_sitio_min: any, promedio_ciclo_total_min: any, total_km_recorridos: any, resumen_por_servicio: array, detalles: array }}`

### GET `/api/v1/analitica/puntos-negros`
**Propósito:** Identificar y priorizar puntos negros de accidentabilidad
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `PuntosNegrosResponse { total_tramos_criticos*: integer, total_eventos_acumulados*: integer, tramos: array }}`

### GET `/api/v1/analitica/tramos-criticos-scoring`
**Propósito:** Modelo de Scoring de Peligrosidad Vial y Hotspots por Tramo Kilométrico
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `TramosScoringResponse { criterio_agrupacion_km*: number, total_tramos_analizados*: integer, total_eventos_evaluados*: integer, resumen_niveles_riesgo*: object, top_tramos_criticos: array }}`

### GET `/api/v1/analitica/patrones-temporales`
**Propósito:** Análisis de patrones temporales, horas pico y días de mayor accidentabilidad
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `PatronesTemporalesResponse { total_eventos_analizados*: integer, hora_pico_maxima*: string, dia_pico_maximo*: string, eventos_fin_de_semana*: integer, eventos_entre_semana*: integer, porcentaje_fin_de_semana*: number, distribucion_por_franja*: object, distribucion_por_hora*: array, distribucion_por_dia*: array }}`

### GET `/api/v1/analitica/recomendaciones-despliegue`
**Propósito:** Plan de despliegue estratégico de ambulancias, grúas y patrullas
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `RecomendacionesDespliegueResponse { fecha_generacion*: string (date-time), total_recomendaciones*: integer, estrategia_general*: string, recomendaciones*: array }}`

### GET `/api/v1/analitica/dashboard-ejecutivo`
**Propósito:** Dashboard analítico consolidado para toma de decisiones ejecutivas
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `DashboardEjecutivoResponse { total_asistencias_historicas*: integer, total_ambulancias*: integer, total_gruas*: integer, total_patrullajes*: integer, tasa_accidentabilidad_porcentaje*: number, tasa_asistencia_mecanica_porcentaje*: number, km_totales_atendidos*: number, tiempo_promedio_llegada_min*: number, tiempo_promedio_sitio_min*: number, tiempo_promedio_ciclo_min*: number, tramo_mas_critico*: any, franja_horaria_mas_critica*: string, dia_mas_critico*: string, recomendacion_ejecutiva*: string }}`

### GET `/api/v1/reportes-mtop/exportar-excel`
**Propósito:** Exportar reporte mensual MTOP en formato Excel (.xlsx)
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `any`

### GET `/api/v1/reportes-mtop/exportar-pdf`
**Propósito:** Exportar reporte mensual MTOP en formato PDF con Logo Oficial de COSAD 25
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `any`

### GET `/api/v1/ai/chat`
**Propósito:** Interfaz Web del Chatbot AnalÃ­tico (ChatGPT / Gemini UI)
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `any`

### POST `/api/v1/ai/analizar-jornada-stream`
**Propósito:** Agente de IA con Streaming SSE
- **Payload (Body) que se envía:** `AIRequest { pregunta*: string, historial: any, session_id: any, stream: any }}`
- **Respuesta (Response) que se recibe:** `any`

### POST `/api/v1/ai/analizar-jornada`
**Propósito:** Agente de IA (Reportes y ExportaciÃ³n a PDF / Excel)
- **Payload (Body) que se envía:** `AIRequest { pregunta*: string, historial: any, session_id: any, stream: any }}`
- **Respuesta (Response) que se recibe:** `any`

### POST `/api/v1/ai/exportar-pdf`
**Propósito:** Exportar anÃ¡lisis actual a PDF
- **Payload (Body) que se envía:** `ExportarPDFDirectoRequest { respuesta_ia*: string, estadisticas: any }}`
- **Respuesta (Response) que se recibe:** `any`

### GET `/api/v1/ai/models`
**Propósito:** Listado de Modelos (OpenAI Compatible)
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `any`

### POST `/api/v1/ai/chat/completions`
**Propósito:** Chat Completions (OpenAI Compatible con soporte de Streaming)
- **Payload (Body) que se envía:** `OpenAIChatCompletionRequest { model: any, messages*: array, user: any, stream: any, temperature: any }}`
- **Respuesta (Response) que se recibe:** `any`

### GET `/api/v1/catalogos/choferes-grua`
**Propósito:** Listar choferes y operadores de grúa activos
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ PersonalRead { nombre_completo*: string, rol*: any, activo: boolean, id_personal*: integer }} ]`

### GET `/api/v1/catalogos/supervisores`
**Propósito:** Listar supervisores de operaciones activos
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ PersonalRead { nombre_completo*: string, rol*: any, activo: boolean, id_personal*: integer }} ]`

### GET `/api/v1/catalogos/vehiculos-grua`
**Propósito:** Listar unidades vehiculares de grúa activas
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `List[ VehiculoRead { codigo_interno*: string, placa*: string, tipo_flota*: any, descripcion: any, activo: boolean, id_vehiculo*: integer }} ]`

### POST `/api/v1/asistencias-grua/`
**Propósito:** Registrar una nueva asistencia de grúa
- **Payload (Body) que se envía:** `GruaCreate { codigo_formulario*: string, id_supervisor*: integer, id_chofer*: integer, id_vehiculo: any, turno*: any, tipo_grua*: any, ts_llamada*: string (date-time), ts_arribo*: string (date-time), ts_termino*: string (date-time), ts_retorno*: string (date-time), sector_referencia*: string, abscisa_km*: any, sentido*: any, usuario_reporta: any, placa_asistida: any, tipo_vehiculo_asistido: any, usuarios_atendidos: integer, motivo_atencion*: string, tipo_accidente: any, posible_causa: any, severidad: any, km_origen_traslado: any, km_destino_traslado: any, odometro_salida_km*: any, odometro_llegada_km*: any, reportado_mtop: boolean, observaciones: any }}`
- **Respuesta (Response) que se recibe:** `None`

### GET `/api/v1/asistencias-grua/`
**Propósito:** Listar asistencias de grúa con filtros y paginación
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `AsistenciaGruaPaginadaResponse { total*: integer, skip*: integer, limit*: integer, items*: array }}`

### POST `/api/v1/reportes-gruas/ejecutivo-ia`
**Propósito:** Generar informe ejecutivo de grúas asistido por IA
- **Payload (Body) que se envía:** `ReporteEjecutivoIARequest { fecha_inicio*: string (date-time), fecha_fin*: string (date-time) }}`
- **Respuesta (Response) que se recibe:** `ReporteEjecutivoIAResponse { periodo*: string, fecha_inicio*: string, fecha_fin*: string, total_auxilios*: integer, kpis*: any, desglose_mensual*: array, desglose_sectores*: array, desglose_cruzado*: array, tiempos_promedio*: any, resumen_markdown*: string }}`

### GET `/`
**Propósito:** Información y bienvenida al microservicio
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `any`

### GET `/health`
**Propósito:** Estado de salud del microservicio y base de datos
- **Payload (Body) que se envía:** `None`
- **Respuesta (Response) que se recibe:** `object`

