"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Ambulance,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  FileSpreadsheet,
  Gauge,
  HeartPulse,
  Info,
  Lock,
  MapPin,
  RefreshCw,
  Route,
  Save,
  Shield,
  Sparkles,
  Truck,
  User,
  Users,
  Wrench,
  Zap,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { catalogosService } from "@/services/catalogos.service";
import { operacionesService } from "@/services/operaciones.service";
import { aiService } from "@/services/ai.service";
import { PersonalRead, VehiculoRead } from "@/types/api";

type ServiceType = "ambulancia" | "grua";
type SeveridadType = "LEVE" | "GRAVE" | "FATAL";
type SentidoType = "ASCENDENTE" | "DESCENDENTE" | "BIDIRECCIONAL";
type TipoGruaType = "PEQUEÑA" | "GRANDE" | "PLATAFORMA";

interface FormDataState {
  // Servicio
  servicio: ServiceType;
  
  // Bloque 1: Asignación Operativa
  codigo_formulario: string;
  id_supervisor: string;
  id_chofer: string;
  id_paramedico: string; // Ambulancia only
  id_vehiculo: string;
  turno: "1" | "2" | "3";

  // Bloque 2: Georreferenciación
  sector_referencia: string;
  abscisa_km: string;
  sentido: SentidoType;

  // Bloque 3: Cronología
  ts_llamada: string;
  ts_arribo: string;
  ts_termino: string;
  ts_retorno: string;

  // Bloque 4: Específico Ambulancia
  nombre_paciente: string;
  rango_edad: string;
  severidad: SeveridadType;
  tipo_incidente: string;
  tipo_accidente: string;
  motivo_atencion: string;
  destino_paciente: string;
  usuarios_atendidos: string;
  servicio_comunidad: boolean;

  // Bloque 4: Específico Grúa
  tipo_grua: TipoGruaType;
  placa_asistida: string;
  usuario_reporta: string;
  tipo_vehiculo_asistido: string;
  posible_causa: string;
  km_origen_traslado: string;
  km_destino_traslado: string;

  // Bloque 5: Odometría y Cierre
  odometro_salida_km: string;
  odometro_llegada_km: string;
  reportado_mtop: boolean;
  observaciones: string;
}

const SECTORES_SUGERIDOS = [
  "Peaje El Congoma (Km 12+000)",
  "Peaje Los Ángeles (Km 54+200)",
  "Km 08+500 - Entrada Santo Domingo",
  "Km 14+300 - El Paraíso",
  "Km 18+200 - Luz de América",
  "Km 25+600 - Puente Río Toachi",
  "Km 32+800 - Patricia Pilar",
  "Km 41+100 - San Carlos",
  "Km 48+500 - Entrada Buena Fe",
  "Bypass Quito - Quevedo",
];

const RANGOS_EDAD = [
  "Pediátrico (0-12 años)",
  "Adolescente (13-17 años)",
  "Adulto Joven (18-35 años)",
  "Adulto (36-64 años)",
  "Adulto Mayor (65+ años)",
  "No especificado / Sin datos",
];

const TIPOS_INCIDENTE_AMB = [
  "Colisión / Choque por alcance",
  "Volcamiento lateral / Pérdida de pista",
  "Atropello a peatón o ciclista",
  "Rozamiento con vehículo pesado",
  "Emergencia médica en vía (Enfermedad común)",
  "Caída de ocupante / motocicleta",
];

const DESTINOS_PACIENTE = [
  "Hospital General Santo Domingo Dr. Gustavo Domínguez",
  "Hospital IESS Santo Domingo",
  "Centro de Salud Tipo C Los Rosales",
  "Centro de Salud Luz de América",
  "Centro de Salud Patricia Pilar",
  "Alta en el sitio / No amerita traslado",
  "Rechaza atención / Traslado por medios propios",
];

const TIPOS_VEHICULO_GRUA = [
  "Automóvil / Sedán",
  "Camioneta 4x4 / Pick-up",
  "SUV / Todo terreno",
  "Bus Interprovincial",
  "Camión Mediano (2 ejes)",
  "Camión Pesado / Tráiler (3+ ejes)",
  "Motocicleta",
  "Furgoneta / Van",
];

const CAUSAS_GRUA = [
  "Falla mecánica - Rotura de banda / motor",
  "Neumático averiado sin repuesto",
  "Recalentamiento de motor / Radiador",
  "Falla del sistema eléctrico / Batería agotada",
  "Siniestro vial / Inmovilización por impacto",
  "Falta de combustible / Despiste",
  "Problemas en sistema de frenos",
];

function RegistroOperacionesFormContent({ fixedService }: { fixedService?: ServiceType }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const servicioParam = searchParams.get("servicio");

  // Estados de catálogo
  const [personal, setPersonal] = React.useState<PersonalRead[]>([]);
  const [vehiculos, setVehiculos] = React.useState<VehiculoRead[]>([]);
  const [loadingCatalogos, setLoadingCatalogos] = React.useState(true);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Determinar servicio inicial según URL o default
  const initialService: ServiceType = fixedService || (servicioParam === "grua" ? "grua" : "ambulancia");

  // Form State
  const [formData, setFormData] = React.useState<FormDataState>({
    servicio: initialService,
    codigo_formulario: "",
    id_supervisor: "",
    id_chofer: "",
    id_paramedico: "",
    id_vehiculo: "",
    turno: "1",
    sector_referencia: "",
    abscisa_km: "",
    sentido: "ASCENDENTE",
    ts_llamada: "",
    ts_arribo: "",
    ts_termino: "",
    ts_retorno: "",
    nombre_paciente: "",
    rango_edad: "Adulto Joven (18-35 años)",
    severidad: "LEVE",
    tipo_incidente: "Colisión / Choque por alcance",
    tipo_accidente: "Choque frontal-lateral",
    motivo_atencion: "",
    destino_paciente: "Hospital General Santo Domingo Dr. Gustavo Domínguez",
    usuarios_atendidos: "1",
    servicio_comunidad: false,
    tipo_grua: "PEQUEÑA",
    placa_asistida: "",
    usuario_reporta: "",
    tipo_vehiculo_asistido: "Automóvil / Sedán",
    posible_causa: "Falla mecánica - Rotura de banda / motor",
    km_origen_traslado: "",
    km_destino_traslado: "",
    odometro_salida_km: "",
    odometro_llegada_km: "",
    reportado_mtop: false,
    observaciones: "",
  });

  // Estados de IA para autocompletado de despacho
  const [aiAccordionOpen, setAiAccordionOpen] = React.useState(false);
  const [textoReporteAi, setTextoReporteAi] = React.useState("");
  const [procesandoAi, setProcesandoAi] = React.useState(false);

  const handleProcesarAi = async () => {
    if (!textoReporteAi.trim()) {
      toast.error("Ingrese el texto del reporte de radio o llamada");
      return;
    }
    setProcesandoAi(true);
    try {
      const parsed = await aiService.parsearDespacho(textoReporteAi);

      setFormData((prev) => {
        const next = { ...prev };

        // 1. Tipo de servicio
        if (parsed.tipo_asistencia === "ambulancia" || parsed.tipo_asistencia === "grua") {
          next.servicio = parsed.tipo_asistencia;
        }

        // 2. Código de formulario / Número de hoja
        if (parsed.codigo_formulario) {
          next.codigo_formulario = parsed.codigo_formulario;
        }

        // 3. Turno
        if (parsed.turno && ["1", "2", "3"].includes(parsed.turno)) {
          next.turno = parsed.turno as "1" | "2" | "3";
        }

        // 4. Tipo de grúa
        if (parsed.tipo_grua && ["PEQUEÑA", "GRANDE", "PLATAFORMA"].includes(parsed.tipo_grua)) {
          next.tipo_grua = parsed.tipo_grua as TipoGruaType;
        }

        // 5. Georreferenciación
        if (parsed.abscisa_km !== null && parsed.abscisa_km !== undefined) {
          next.abscisa_km = String(parsed.abscisa_km);
          if (next.servicio === "grua" && (!prev.km_origen_traslado || prev.km_origen_traslado === prev.abscisa_km)) {
            next.km_origen_traslado = String(parsed.abscisa_km);
          }
        }
        if (parsed.ubicacion_referencia) {
          next.sector_referencia = parsed.ubicacion_referencia;
        }
        if (parsed.sentido && ["ASCENDENTE", "DESCENDENTE", "BIDIRECCIONAL"].includes(parsed.sentido)) {
          next.sentido = parsed.sentido;
        }

        // 6. Severidad / Prioridad
        if (parsed.prioridad && ["LEVE", "GRAVE", "FATAL"].includes(parsed.prioridad)) {
          next.severidad = parsed.prioridad;
        }

        // 7. Personal (Búsqueda por coincidencia de nombre / tokens)
        if (parsed.chofer) {
          const chClean = parsed.chofer.toLowerCase().replace(/^(sr\.|sr|don|conductor|operador)\s*/i, "").trim();
          const words = chClean.split(/\s+/).filter((w) => w.length > 2);
          const foundChofer = personal.find((p) => {
            const name = p.nombre_completo.toLowerCase();
            return name.includes(chClean) || chClean.includes(name) || (words.length > 0 && words.some((w) => name.includes(w)));
          });
          if (foundChofer) {
            next.id_chofer = foundChofer.id_personal.toString();
          }
        }
        if (parsed.supervisor) {
          const supClean = parsed.supervisor.toLowerCase().replace(/^(ing\.|ing|lic\.|lic|sr\.|sr)\s*/i, "").trim();
          const words = supClean.split(/\s+/).filter((w) => w.length > 2);
          const foundSup = supervisores.find((p) => {
            const name = p.nombre_completo.toLowerCase();
            return name.includes(supClean) || supClean.includes(name) || (words.length > 0 && words.some((w) => name.includes(w)));
          });
          if (foundSup) {
            next.id_supervisor = foundSup.id_personal.toString();
          }
        }
        if (parsed.paramedico) {
          const parClean = parsed.paramedico.toLowerCase().replace(/^(lcda\.|lcda|lic\.|lic|dra\.|dra|dr\.|dr)\s*/i, "").trim();
          const words = parClean.split(/\s+/).filter((w) => w.length > 2);
          const foundPar = paramedicos.find((p) => {
            const name = p.nombre_completo.toLowerCase();
            return name.includes(parClean) || parClean.includes(name) || (words.length > 0 && words.some((w) => name.includes(w)));
          });
          if (foundPar) {
            next.id_paramedico = foundPar.id_personal.toString();
          }
        }

        // 8. Datos Médicos / Ambulancia
        if (parsed.nombre_paciente) {
          next.nombre_paciente = parsed.nombre_paciente;
        }
        if (parsed.destino_paciente) {
          next.destino_paciente = parsed.destino_paciente;
        }
        if (parsed.descripcion_falla_o_motivo) {
          if (next.servicio === "ambulancia") {
            next.motivo_atencion = parsed.descripcion_falla_o_motivo;
          } else {
            // En grúa verificar si coincide con causas conocidas
            const causaMatch = CAUSAS_GRUA.find((c) =>
              c.toLowerCase().includes(parsed.descripcion_falla_o_motivo!.toLowerCase()) ||
              parsed.descripcion_falla_o_motivo!.toLowerCase().includes("mecánic") ||
              parsed.descripcion_falla_o_motivo!.toLowerCase().includes("mecanic")
            );
            if (causaMatch) {
              next.posible_causa = causaMatch;
            }
            next.observaciones = prev.observaciones
              ? `${prev.observaciones} | ${parsed.descripcion_falla_o_motivo}`
              : parsed.descripcion_falla_o_motivo;
          }
        }

        // 9. Datos de Grúa y Vehículo
        if (parsed.placa_vehiculo) {
          next.placa_asistida = parsed.placa_vehiculo;
        }
        if (parsed.usuario_reporta) {
          next.usuario_reporta = parsed.usuario_reporta;
        }
        if (parsed.vehiculo_involucrado) {
          const matchVeh = TIPOS_VEHICULO_GRUA.find((t) =>
            t.toLowerCase().includes(parsed.vehiculo_involucrado!.toLowerCase()) ||
            parsed.vehiculo_involucrado!.toLowerCase().includes("volqueta") ||
            parsed.vehiculo_involucrado!.toLowerCase().includes("camión") ||
            parsed.vehiculo_involucrado!.toLowerCase().includes("camion")
          );
          if (matchVeh) {
            next.tipo_vehiculo_asistido = matchVeh;
          } else {
            next.tipo_vehiculo_asistido = parsed.vehiculo_involucrado;
          }
        }

        // 10. Odómetros
        if (parsed.odometro_salida_km !== null && parsed.odometro_salida_km !== undefined) {
          next.odometro_salida_km = String(parsed.odometro_salida_km);
        }
        if (parsed.odometro_llegada_km !== null && parsed.odometro_llegada_km !== undefined) {
          next.odometro_llegada_km = String(parsed.odometro_llegada_km);
        }

        return next;
      });

      toast.success("Campos autocompletados", {
        description: "Se procesó el reporte con éxito. Puedes revisar o ajustar cualquier dato.",
      });
    } catch (err: any) {
      console.error("Error al autocompletar despacho:", err);
      toast.error("No se pudo procesar el reporte", {
        description: err?.message || "Ocurrió un error al analizar el texto.",
      });
    } finally {
      setProcesandoAi(false);
    }
  };

  // Si cambia el parámetro de URL, sincronizar el servicio
  React.useEffect(() => {
    if (servicioParam === "grua" || servicioParam === "ambulancia") {
      setFormData((prev) => ({ ...prev, servicio: servicioParam }));
    }
  }, [servicioParam]);

  // Cargar catálogos al montar
  React.useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoadingCatalogos(true);
        const [pers, vehs] = await Promise.all([
          catalogosService.getPersonal(),
          catalogosService.getVehiculos(),
        ]);
        if (isMounted) {
          setPersonal(pers);
          setVehiculos(vehs);
        }
      } catch (err) {
        console.error("Error al cargar catálogos:", err);
        toast.error("Error al cargar catálogos operativos", {
          description: "Verifique que el backend FastAPI esté en ejecución.",
        });
      } finally {
        if (isMounted) setLoadingCatalogos(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filtros de personal por rol estricto
  const supervisores = React.useMemo(() => {
    return personal.filter(
      (p) => p.rol === "SUPERVISOR" || p.rol.toUpperCase().includes("SUPERVISOR")
    );
  }, [personal]);

  // Choferes filtrados por tipo de servicio
  const choferes = React.useMemo(() => {
    if (formData.servicio === "ambulancia") {
      return personal.filter((p) => p.rol === "CHOFER_AMBULANCIA");
    } else {
      return personal.filter((p) => p.rol === "CHOFER_GRUA" || p.rol === "PATRULLERO");
    }
  }, [personal, formData.servicio]);

  const paramedicos = React.useMemo(() => {
    return personal.filter(
      (p) => p.rol === "PARAMEDICO" || p.rol.toUpperCase().includes("PARAMEDICO")
    );
  }, [personal]);

  const vehiculosFiltrados = React.useMemo(() => {
    if (formData.servicio === "ambulancia") {
      return vehiculos.filter((v) => v.tipo_flota === "AMBULANCIA");
    } else {
      return vehiculos.filter((v) => v.tipo_flota === "GRUA");
    }
  }, [vehiculos, formData.servicio]);

  // Vehículo seleccionado actualmente
  const selectedVehicleObj = React.useMemo(() => {
    return vehiculos.find((v) => v.id_vehiculo.toString() === formData.id_vehiculo);
  }, [vehiculos, formData.id_vehiculo]);

  // Actualizador genérico de campo
  const updateField = (field: keyof FormDataState, value: any) => {
    setFormData((prev) => {
      const next = { ...prev, [field]: value };

      // Si cambia el vehículo asignado en Grúas, inferir y sincronizar automáticamente el tipo de grúa
      if (field === "id_vehiculo" && prev.servicio === "grua") {
        const v = vehiculos.find((item) => item.id_vehiculo.toString() === value);
        if (v) {
          const desc = (v.descripcion || "").toLowerCase();
          const code = (v.codigo_interno || "").toLowerCase();
          if (desc.includes("plataforma") || code === "grua-01" || desc.includes("pesada")) {
            next.tipo_grua = "PLATAFORMA";
          } else if (desc.includes("grande")) {
            next.tipo_grua = "GRANDE";
          } else {
            next.tipo_grua = "PEQUEÑA";
          }
        }
      }

      // Si cambia el servicio, resetear chofer y unidad móvil incompatibles
      if (field === "servicio" && prev.servicio !== value) {
        next.id_chofer = "";
        next.id_vehiculo = "";
      }

      // Si se ingresa la abscisa y el tramo origen de grúa está vacío, auto-completar origen
      if (field === "abscisa_km" && (!prev.km_origen_traslado || prev.km_origen_traslado === prev.abscisa_km)) {
        next.km_origen_traslado = value;
      }

      return next;
    });
  };

  // ==========================================
  // CÁLCULOS REACTIVOS (Métricas Operativas)
  // ==========================================

  // 1. Tiempos cronológicos en minutos
  const metricasTiempo = React.useMemo(() => {
    const tLlamada = formData.ts_llamada ? new Date(formData.ts_llamada).getTime() : null;
    const tArribo = formData.ts_arribo ? new Date(formData.ts_arribo).getTime() : null;
    const tTermino = formData.ts_termino ? new Date(formData.ts_termino).getTime() : null;
    const tRetorno = formData.ts_retorno ? new Date(formData.ts_retorno).getTime() : null;

    let tiempoRespuestaMin: number | null = null;
    let tiempoSitioMin: number | null = null;
    let tiempoCicloMin: number | null = null;
    let cronologiaValida = true;
    let errorCronologia = "";

    if (tLlamada && tArribo) {
      const diffMs = tArribo - tLlamada;
      tiempoRespuestaMin = Math.round(diffMs / 60000);
      if (tiempoRespuestaMin < 0) {
        cronologiaValida = false;
        errorCronologia = "Arribo no puede ser anterior a Llamada";
      }
    }

    if (tArribo && tTermino) {
      const diffMs = tTermino - tArribo;
      tiempoSitioMin = Math.round(diffMs / 60000);
      if (tiempoSitioMin < 0) {
        cronologiaValida = false;
        errorCronologia = "Término no puede ser anterior a Arribo";
      }
    }

    if (tTermino && tRetorno) {
      const diffMs = tRetorno - tTermino;
      if (diffMs < 0) {
        cronologiaValida = false;
        errorCronologia = "Retorno no puede ser anterior a Término";
      }
    }

    if (tLlamada && tRetorno) {
      tiempoCicloMin = Math.round((tRetorno - tLlamada) / 60000);
    }

    return {
      tiempoRespuestaMin,
      tiempoSitioMin,
      tiempoCicloMin,
      cronologiaValida,
      errorCronologia,
    };
  }, [formData.ts_llamada, formData.ts_arribo, formData.ts_termino, formData.ts_retorno]);

  // 2. Odometría (Km recorridos)
  const metricasOdometria = React.useMemo(() => {
    const salida = parseFloat(formData.odometro_salida_km);
    const llegada = parseFloat(formData.odometro_llegada_km);

    if (!isNaN(salida) && !isNaN(llegada)) {
      const diff = Number((llegada - salida).toFixed(2));
      const esValido = diff >= 0;
      return {
        kmRecorridos: diff,
        esValido,
        error: esValido ? null : "El odómetro de llegada no puede ser menor al de salida",
      };
    }
    return { kmRecorridos: null, esValido: true, error: null };
  }, [formData.odometro_salida_km, formData.odometro_llegada_km]);

  // 3. Arrastre de Grúa (Km)
  const kmArrastre = React.useMemo(() => {
    const origen = parseFloat(formData.km_origen_traslado);
    const destino = parseFloat(formData.km_destino_traslado);
    if (!isNaN(origen) && !isNaN(destino)) {
      return Math.abs(Number((destino - origen).toFixed(2)));
    }
    return null;
  }, [formData.km_origen_traslado, formData.km_destino_traslado]);

  // ==========================================
  // SUBMIT DEL FORMULARIO
  // ==========================================
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validaciones preliminares
    if (!formData.codigo_formulario.trim()) {
      toast.error("Campo requerido", { description: "Debe ingresar el código del formulario." });
      return;
    }
    if (!formData.id_supervisor) {
      toast.error("Campo requerido", { description: "Debe seleccionar un supervisor de operaciones." });
      return;
    }
    if (!formData.id_chofer) {
      toast.error("Campo requerido", { description: "Debe seleccionar un conductor / operador." });
      return;
    }
    if (formData.servicio === "ambulancia" && !formData.id_paramedico) {
      toast.error("Campo requerido", { description: "Debe seleccionar un paramédico para la ambulancia." });
      return;
    }
    if (!formData.id_vehiculo) {
      toast.error("Campo requerido", { description: "Debe seleccionar la unidad vehicular asignada." });
      return;
    }
    if (!formData.sector_referencia.trim() || !formData.abscisa_km) {
      toast.error("Ubicación incompleta", { description: "Debe ingresar el sector y la abscisa kilométrica." });
      return;
    }
    if (!formData.ts_llamada || !formData.ts_arribo || !formData.ts_termino || !formData.ts_retorno) {
      toast.error("Cronología incompleta", { description: "Debe completar las 4 marcas de tiempo obligatorias." });
      return;
    }
    if (!metricasTiempo.cronologiaValida) {
      toast.error("Error de cronología", { description: metricasTiempo.errorCronologia });
      return;
    }
    if (!formData.odometro_salida_km || !formData.odometro_llegada_km) {
      toast.error("Odometría requerida", { description: "Debe ingresar los valores del odómetro de salida y llegada." });
      return;
    }
    if (!metricasOdometria.esValido) {
      toast.error("Inconsistencia en odómetro", { description: metricasOdometria.error || "" });
      return;
    }

    try {
      setIsSubmitting(true);

      const toIsoString = (val: string) => {
        if (!val) return null;
        const d = new Date(val);
        return d.toISOString();
      };

      if (formData.servicio === "ambulancia") {
        const payload = {
          codigo_formulario: formData.codigo_formulario.trim(),
          id_supervisor: parseInt(formData.id_supervisor, 10),
          id_paramedico: parseInt(formData.id_paramedico, 10),
          id_chofer: parseInt(formData.id_chofer, 10),
          id_vehiculo: parseInt(formData.id_vehiculo, 10),
          turno: parseInt(formData.turno, 10),
          ts_llamada: toIsoString(formData.ts_llamada),
          ts_arribo: toIsoString(formData.ts_arribo),
          ts_termino: toIsoString(formData.ts_termino),
          ts_retorno: toIsoString(formData.ts_retorno),
          sector_referencia: formData.sector_referencia.trim(),
          abscisa_km: parseFloat(formData.abscisa_km),
          sentido: formData.sentido,
          nombre_paciente: formData.nombre_paciente.trim() || null,
          rango_edad: formData.rango_edad || null,
          motivo_atencion: formData.motivo_atencion.trim(),
          tipo_incidente: formData.tipo_incidente || null,
          tipo_accidente: formData.tipo_accidente || null,
          severidad: formData.severidad,
          destino_paciente: formData.destino_paciente || null,
          usuarios_atendidos: parseInt(formData.usuarios_atendidos, 10) || 1,
          servicio_comunidad: formData.servicio_comunidad,
          odometro_salida_km: parseFloat(formData.odometro_salida_km),
          odometro_llegada_km: parseFloat(formData.odometro_llegada_km),
          reportado_mtop: formData.reportado_mtop,
        };

        await operacionesService.crearAsistenciaAmbulancia(payload);

        toast.success("Registro de Ambulancia Guardado", {
          description: `Código: ${formData.codigo_formulario} registrado exitosamente.`,
        });

        setTimeout(() => {
          router.push("/?tab=ambulancias");
        }, 1400);
      } else {
        const payload = {
          codigo_formulario: formData.codigo_formulario.trim(),
          id_supervisor: parseInt(formData.id_supervisor, 10),
          id_chofer: parseInt(formData.id_chofer, 10),
          id_vehiculo: formData.id_vehiculo ? parseInt(formData.id_vehiculo, 10) : null,
          turno: parseInt(formData.turno, 10),
          tipo_grua: formData.tipo_grua,
          ts_llamada: toIsoString(formData.ts_llamada),
          ts_arribo: toIsoString(formData.ts_arribo),
          ts_termino: toIsoString(formData.ts_termino),
          ts_retorno: toIsoString(formData.ts_retorno),
          sector_referencia: formData.sector_referencia.trim(),
          abscisa_km: parseFloat(formData.abscisa_km),
          sentido: formData.sentido,
          usuario_reporta: formData.usuario_reporta.trim() || null,
          placa_asistida: formData.placa_asistida.trim().toUpperCase() || null,
          tipo_vehiculo_asistido: formData.tipo_vehiculo_asistido || null,
          usuarios_atendidos: parseInt(formData.usuarios_atendidos, 10) || 1,
          motivo_atencion: formData.motivo_atencion.trim() || "Auxilio y remolque vehicular en vía",
          posible_causa: formData.posible_causa || null,
          severidad: formData.severidad || "LEVE",
          km_origen_traslado: formData.km_origen_traslado ? parseFloat(formData.km_origen_traslado) : null,
          km_destino_traslado: formData.km_destino_traslado ? parseFloat(formData.km_destino_traslado) : null,
          odometro_salida_km: parseFloat(formData.odometro_salida_km),
          odometro_llegada_km: parseFloat(formData.odometro_llegada_km),
          reportado_mtop: formData.reportado_mtop,
          observaciones: formData.observaciones.trim() || null,
        };

        await operacionesService.crearAsistenciaGrua(payload);

        toast.success("Orden de Grúa Guardada", {
          description: `Código: ${formData.codigo_formulario} registrado exitosamente.`,
        });

        setTimeout(() => {
          router.push("/?tab=gruas");
        }, 1400);
      }
    } catch (err: any) {
      console.error("Error al guardar registro:", err);
      toast.error("Error al procesar el registro", {
        description: err?.message || "Ocurrió un error inesperado al conectar con el servidor.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadingCatalogos) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-6 pb-16">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-24 rounded-md" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="space-y-6 mt-8">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="border border-zinc-200/80 dark:border-zinc-800">
              <CardHeader className="p-4 border-b border-zinc-100 dark:border-zinc-800/80">
                <Skeleton className="h-5 w-48" />
              </CardHeader>
              <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <div key={j} className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-9 w-full" />
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 pb-16">
      {/* ========================================================================= */}
      {/* Top Header con Selector de Servicio Deslizable */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(formData.servicio === "ambulancia" ? "/?tab=ambulancias" : "/?tab=gruas")}
            className="h-8 gap-1.5 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            <ArrowLeft className="size-3.5" />
            <span>Volver a {formData.servicio === "ambulancia" ? "Ambulancias" : "Grúas"}</span>
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <span>Registro de Asistencia Operativa</span>
              <Badge variant="outline" className="text-[10px] font-mono tracking-normal py-0">
                {formData.servicio === "ambulancia" ? "Ambulancia" : "Grúa"}
              </Badge>
            </h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Captura de atenciones viales con validación cronológica y cálculo métrico en tiempo real.
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* Selector de Servicio tipo Pastilla Deslizable con Motion */}
      {/* ========================================================================= */}
      {!fixedService && (
        <div className="flex justify-center">
          <div className="inline-flex p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs">
            <button
              type="button"
              onClick={() => updateField("servicio", "ambulancia")}
              data-testid="tab-servicio-ambulancia"
              className={`relative flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold transition-colors z-10 ${
                formData.servicio === "ambulancia"
                  ? "text-emerald-950 dark:text-emerald-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200"
              }`}
            >
              {formData.servicio === "ambulancia" && (
                <motion.div
                  layoutId="service-pill-active"
                  className="absolute inset-0 bg-white dark:bg-zinc-800 rounded-lg shadow-sm border border-emerald-500/30 dark:border-emerald-500/40 -z-10"
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                />
              )}
              <Ambulance className={`size-4 ${formData.servicio === "ambulancia" ? "text-emerald-600 dark:text-emerald-400" : ""}`} />
              <span>Asistencia de Ambulancia</span>
            </button>

            <button
              type="button"
              onClick={() => updateField("servicio", "grua")}
              data-testid="tab-servicio-grua"
              className={`relative flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold transition-colors z-10 ${
                formData.servicio === "grua"
                  ? "text-blue-950 dark:text-blue-100"
                  : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200"
              }`}
            >
              {formData.servicio === "grua" && (
                <motion.div
                  layoutId="service-pill-active"
                  className="absolute inset-0 bg-white dark:bg-zinc-800 rounded-lg shadow-sm border border-blue-500/30 dark:border-blue-500/40 -z-10"
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                />
              )}
              <Truck className={`size-4 ${formData.servicio === "grua" ? "text-blue-600 dark:text-blue-400" : ""}`} />
              <span>Auxilio de Grúa</span>
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ========================================================================= */}
        {/* Autocompletar desde reporte de radio / WhatsApp */}
        {/* ========================================================================= */}
        <Card className="border border-indigo-200/70 dark:border-indigo-900/40 bg-gradient-to-r from-indigo-50/50 via-white to-sky-50/30 dark:from-indigo-950/20 dark:via-zinc-900/90 dark:to-sky-950/10 shadow-xs overflow-hidden">
          <button
            type="button"
            onClick={() => setAiAccordionOpen((prev) => !prev)}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-indigo-50/40 dark:hover:bg-indigo-950/30 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400">
                <Zap className="size-4" />
              </div>
              <div>
                <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  ⚡ Autocompletar desde reporte de radio / llamada
                </span>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Pega el reporte de WhatsApp o radio para completar los campos automáticamente.
                </p>
              </div>
            </div>
            <div className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200">
              {aiAccordionOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
            </div>
          </button>

          <AnimatePresence>
            {aiAccordionOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="p-4 pt-1 border-t border-indigo-100 dark:border-indigo-900/30 space-y-3">
                  <Textarea
                    rows={4}
                    placeholder={"Pega aquí el reporte de WhatsApp o radio...\nEj:\nASISTENCIAS DE GRÚAS PEAJE LOS ÁNGELES\nConductor: Yasmani Maldonado\nPLACAS: GSF-7761\nKm 184 Gasolinera Génesis"}
                    value={textoReporteAi}
                    onChange={(e) => setTextoReporteAi(e.target.value)}
                    className="bg-white/80 dark:bg-zinc-950/70 text-xs border-indigo-200/80 dark:border-indigo-900/60 focus-visible:ring-indigo-500 resize-none font-normal"
                  />
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
                      Los campos se rellenan automáticamente y podrás editarlos antes de guardar.
                    </span>
                    <div className="flex items-center gap-2">
                      {textoReporteAi && (
                        <motion.div
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.97 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setTextoReporteAi("")}
                            disabled={procesandoAi}
                            className="h-8 text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 cursor-pointer"
                          >
                            Limpiar
                          </Button>
                        </motion.div>
                      )}
                      <motion.div
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.97 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      >
                        <Button
                          type="button"
                          size="sm"
                          onClick={handleProcesarAi}
                          disabled={procesandoAi || !textoReporteAi.trim()}
                          className="h-8 gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs cursor-pointer"
                        >
                          {procesandoAi ? (
                            <>
                              <Loader2 className="size-3.5 animate-spin" />
                              <span>Procesando reporte...</span>
                            </>
                          ) : (
                            <>
                              <Zap className="size-3.5" />
                              <span>Completar formulario</span>
                            </>
                          )}
                        </Button>
                      </motion.div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>

        {/* ========================================================================= */}
        {/* BLOQUE 1: Asignación Operativa y Turno */}
        {/* ========================================================================= */}
        <Card className="border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/90 shadow-xs">
          <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                <Shield className="size-4" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  Bloque 1: Asignación Operativa y Turno
                </CardTitle>
                <CardDescription className="text-xs">
                  Personal de guardia, unidad vehicular y código de control.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Código de Formulario */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Código de Formulario</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Input
                placeholder={formData.servicio === "ambulancia" ? "AMB-2026-089" : "GRU-2026-142"}
                value={formData.codigo_formulario}
                onChange={(e) => updateField("codigo_formulario", e.target.value)}
                data-testid="input-codigo-formulario"
                className="h-9 text-xs font-mono font-medium"
                required
              />
            </div>

            {/* Turno */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Turno Operativo</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Select
                value={formData.turno}
                onValueChange={(val) => updateField("turno", val as "1" | "2" | "3")}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="Seleccionar turno">
                    {(val) => `Turno ${val} (${val === "1" ? "06:00 - 14:00" : val === "2" ? "14:00 - 22:00" : "22:00 - 06:00"})`}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Turno 1 (06:00 - 14:00)</SelectItem>
                  <SelectItem value="2">Turno 2 (14:00 - 22:00)</SelectItem>
                  <SelectItem value="3">Turno 3 (22:00 - 06:00)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Supervisor */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Supervisor de Guardia</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Select
                value={formData.id_supervisor}
                onValueChange={(val) => updateField("id_supervisor", val)}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="Seleccionar supervisor">
                    {(val) => {
                      const found = supervisores.find((s) => s.id_personal.toString() === val);
                      return found ? found.nombre_completo : val ? `Supervisor #${val}` : "Seleccionar supervisor";
                    }}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {supervisores.map((s) => (
                    <SelectItem key={s.id_personal} value={s.id_personal.toString()}>
                      {s.nombre_completo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Chofer / Operador (Filtrado estricto por rol) */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>{formData.servicio === "ambulancia" ? "Chofer de Ambulancia" : "Operador de Grúa"}</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Select
                value={formData.id_chofer}
                onValueChange={(val) => updateField("id_chofer", val)}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder={formData.servicio === "ambulancia" ? "Seleccionar chofer ambulancia" : "Seleccionar operador de grúa"}>
                    {(val) => {
                      const found = choferes.find((c) => c.id_personal.toString() === val);
                      return found ? found.nombre_completo : val ? `Conductor #${val}` : "Seleccionar personal";
                    }}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {choferes.map((c) => (
                    <SelectItem key={c.id_personal} value={c.id_personal.toString()}>
                      {c.nombre_completo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Paramédico (Solo Ambulancia) */}
            {formData.servicio === "ambulancia" && (
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span>Paramédico Actuante</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Select
                  value={formData.id_paramedico}
                  onValueChange={(val) => updateField("id_paramedico", val)}
                >
                  <SelectTrigger className="h-9 text-xs">
                    <SelectValue placeholder="Seleccionar paramédico">
                      {(val) => {
                        const found = paramedicos.find((p) => p.id_personal.toString() === val);
                        return found ? found.nombre_completo : val ? `Paramédico #${val}` : "Seleccionar paramédico";
                      }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {paramedicos.map((p) => (
                      <SelectItem key={p.id_personal} value={p.id_personal.toString()}>
                        {p.nombre_completo}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Unidad Móvil */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Unidad Móvil Asignada</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Select
                value={formData.id_vehiculo}
                onValueChange={(val) => updateField("id_vehiculo", val)}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="Seleccionar vehículo">
                    {(val) => {
                      const found = vehiculosFiltrados.find((v) => v.id_vehiculo.toString() === val);
                      return found ? `${found.codigo_interno} (${found.placa})` : val ? `Unidad #${val}` : "Seleccionar vehículo";
                    }}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {vehiculosFiltrados.map((v) => (
                    <SelectItem key={v.id_vehiculo} value={v.id_vehiculo.toString()}>
                      {v.codigo_interno} - {v.placa} ({v.descripcion || v.tipo_flota})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* ========================================================================= */}
        {/* BLOQUE 2: Georreferenciación y Ubicación */}
        {/* ========================================================================= */}
        <Card className="border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/90 shadow-xs">
          <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                <MapPin className="size-4" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  Bloque 2: Georreferenciación y Ubicación Vial
                </CardTitle>
                <CardDescription className="text-xs">
                  Sector, abscisa kilométrica y sentido de circulación en la vía.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Sector de Referencia con Sugerencias */}
            <div className="space-y-1.5 sm:col-span-1">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Sector de Referencia</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Input
                list="sectores-list"
                placeholder="ej. Km 18+200 - Luz de América"
                value={formData.sector_referencia}
                onChange={(e) => updateField("sector_referencia", e.target.value)}
                data-testid="input-sector-referencia"
                className="h-9 text-xs"
                required
              />
              <datalist id="sectores-list">
                {SECTORES_SUGERIDOS.map((s, idx) => (
                  <option key={idx} value={s} />
                ))}
              </datalist>
            </div>

            {/* Abscisa Km */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Abscisa Km (Precisión Decimal)</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Input
                type="number"
                step="0.001"
                min="0"
                placeholder="18.200"
                value={formData.abscisa_km}
                onChange={(e) => updateField("abscisa_km", e.target.value)}
                data-testid="input-abscisa-km"
                className="h-9 text-xs font-mono"
                required
              />
            </div>

            {/* Sentido */}
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                <span>Sentido de Calzada</span>
                <span className="text-rose-500">*</span>
              </Label>
              <Select
                value={formData.sentido}
                onValueChange={(val) => updateField("sentido", val as SentidoType)}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="Seleccionar sentido">
                    {(val) => val}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ASCENDENTE">ASCENDENTE (Sto. Domingo → Quevedo)</SelectItem>
                  <SelectItem value="DESCENDENTE">DESCENDENTE (Quevedo → Sto. Domingo)</SelectItem>
                  <SelectItem value="BIDIRECCIONAL">BIDIRECCIONAL (Ambos sentidos / Eje)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* ========================================================================= */}
        {/* BLOQUE 3: Cronología Temporal y Métricas Reactivas */}
        {/* ========================================================================= */}
        <Card className="border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/90 shadow-xs">
          <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                  <Clock className="size-4" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Bloque 3: Cronología Temporal de Operaciones
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Cadena secuencial de marcas de tiempo y métricas de desempeño calculadas en tiempo real.
                  </CardDescription>
                </div>
              </div>

              {/* Badges Reactivos de Métricas */}
              <div className="flex flex-wrap items-center gap-2">
                {metricasTiempo.tiempoRespuestaMin !== null && (
                  <Badge
                    data-testid="badge-tiempo-respuesta"
                    variant="outline"
                    className={`text-[11px] font-medium px-2.5 py-1 ${
                      metricasTiempo.tiempoRespuestaMin < 0
                        ? "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border-rose-300"
                        : metricasTiempo.tiempoRespuestaMin <= 15
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800"
                        : metricasTiempo.tiempoRespuestaMin <= 30
                        ? "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border-amber-300 dark:border-amber-800"
                        : "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border-rose-300 dark:border-rose-800"
                    }`}
                  >
                    Δt Respuesta: {metricasTiempo.tiempoRespuestaMin} min
                  </Badge>
                )}

                {metricasTiempo.tiempoSitioMin !== null && (
                  <Badge
                    data-testid="badge-tiempo-sitio"
                    variant="outline"
                    className="bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border-blue-300 dark:border-blue-800 text-[11px] font-medium px-2.5 py-1"
                  >
                    Δt En Sitio: {metricasTiempo.tiempoSitioMin} min
                  </Badge>
                )}

                {metricasTiempo.tiempoCicloMin !== null && (
                  <Badge
                    variant="outline"
                    className="bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700 text-[11px] font-medium px-2.5 py-1"
                  >
                    Ciclo Total: {metricasTiempo.tiempoCicloMin} min
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* 1. Llamada */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span className="size-2 rounded-full bg-blue-500 shrink-0" />
                  <span>1. Recepción Llamada</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="datetime-local"
                  value={formData.ts_llamada}
                  onChange={(e) => updateField("ts_llamada", e.target.value)}
                  data-testid="input-ts-llamada"
                  className="h-9 text-xs"
                  required
                />
              </div>

              {/* 2. Arribo */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span className="size-2 rounded-full bg-amber-500 shrink-0" />
                  <span>2. Arribo al Sitio</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="datetime-local"
                  value={formData.ts_arribo}
                  onChange={(e) => updateField("ts_arribo", e.target.value)}
                  data-testid="input-ts-arribo"
                  className="h-9 text-xs"
                  required
                />
              </div>

              {/* 3. Término */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span className="size-2 rounded-full bg-purple-500 shrink-0" />
                  <span>3. Fin de Atención</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="datetime-local"
                  value={formData.ts_termino}
                  onChange={(e) => updateField("ts_termino", e.target.value)}
                  data-testid="input-ts-termino"
                  className="h-9 text-xs"
                  required
                />
              </div>

              {/* 4. Retorno */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span className="size-2 rounded-full bg-emerald-500 shrink-0" />
                  <span>4. Retorno a Base</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="datetime-local"
                  value={formData.ts_retorno}
                  onChange={(e) => updateField("ts_retorno", e.target.value)}
                  data-testid="input-ts-retorno"
                  className="h-9 text-xs"
                  required
                />
              </div>
            </div>

            {/* Alerta de Error Cronológico */}
            {!metricasTiempo.cronologiaValida && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs"
              >
                <AlertCircle className="size-4 shrink-0 text-rose-600 dark:text-rose-400" />
                <span>
                  <strong>Inconsistencia en Cronología:</strong> {metricasTiempo.errorCronologia}. Los eventos deben guardar el orden: Llamada ≤ Arribo ≤ Término ≤ Retorno.
                </span>
              </motion.div>
            )}
          </CardContent>
        </Card>

        {/* ========================================================================= */}
        {/* BLOQUE 4: Campos Específicos según Servicio (AnimatePresence) */}
        {/* ========================================================================= */}
        <AnimatePresence mode="wait">
          {formData.servicio === "ambulancia" ? (
            <motion.div
              key="bloque-ambulancia"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Card className="border border-emerald-200/80 dark:border-emerald-950/80 bg-white dark:bg-zinc-900/90 shadow-xs">
                <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80 bg-emerald-50/30 dark:bg-emerald-950/20">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-md bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300">
                      <HeartPulse className="size-4" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
                        Bloque 4: Datos Clínicos y Atención de Ambulancia
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Triaje de severidad, signos y destino del paciente asistido.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {/* Nombre del Paciente */}
                    <div className="space-y-1.5 sm:col-span-2">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Nombre Completo del Paciente
                      </Label>
                      <Input
                        placeholder="ej. Carlos Eduardo Mendoza"
                        value={formData.nombre_paciente}
                        onChange={(e) => updateField("nombre_paciente", e.target.value)}
                        data-testid="input-nombre-paciente"
                        className="h-9 text-xs"
                      />
                    </div>

                    {/* Rango de Edad */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Rango de Edad
                      </Label>
                      <Select
                        value={formData.rango_edad}
                        onValueChange={(val) => updateField("rango_edad", val)}
                      >
                        <SelectTrigger className="h-9 text-xs">
                          <SelectValue placeholder="Seleccionar rango">
                            {(val) => val}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {RANGOS_EDAD.map((r, idx) => (
                            <SelectItem key={idx} value={r}>
                              {r}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Severidad: Radio Badges Interactivos */}
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                      <span>Triaje / Severidad del Paciente</span>
                      <span className="text-rose-500">*</span>
                    </Label>
                    <div className="flex flex-wrap gap-3">
                      {(["LEVE", "GRAVE", "FATAL"] as SeveridadType[]).map((sev) => {
                        const isSelected = formData.severidad === sev;
                        return (
                          <button
                            key={sev}
                            type="button"
                            onClick={() => updateField("severidad", sev)}
                            data-testid={`btn-severidad-${sev.toLowerCase()}`}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                              isSelected
                                ? sev === "LEVE"
                                  ? "bg-emerald-50 border-emerald-500 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-600 ring-2 ring-emerald-500/20"
                                  : sev === "GRAVE"
                                  ? "bg-amber-50 border-amber-500 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-600 ring-2 ring-amber-500/20"
                                  : "bg-rose-50 border-rose-500 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-600 ring-2 ring-rose-500/20"
                                : "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300"
                            }`}
                          >
                            <span
                              className={`size-2.5 rounded-full ${
                                sev === "LEVE"
                                  ? "bg-emerald-500"
                                  : sev === "GRAVE"
                                  ? "bg-amber-500"
                                  : "bg-rose-500"
                              }`}
                            />
                            <span>{sev}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Tipo de Incidente */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Tipo de Incidente Vial
                      </Label>
                      <Select
                        value={formData.tipo_incidente}
                        onValueChange={(val) => updateField("tipo_incidente", val)}
                      >
                        <SelectTrigger className="h-9 text-xs">
                          <SelectValue placeholder="Seleccionar incidente">
                            {(val) => val}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {TIPOS_INCIDENTE_AMB.map((t, idx) => (
                            <SelectItem key={idx} value={t}>
                              {t}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Destino del Paciente */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Destino o Casa de Salud
                      </Label>
                      <Select
                        value={formData.destino_paciente}
                        onValueChange={(val) => updateField("destino_paciente", val)}
                      >
                        <SelectTrigger className="h-9 text-xs">
                          <SelectValue placeholder="Seleccionar destino">
                            {(val) => val}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {DESTINOS_PACIENTE.map((d, idx) => (
                            <SelectItem key={idx} value={d}>
                              {d}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Motivo de Atención */}
                  <div className="space-y-1.5">
                    <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                      <span>Motivo de Atención Médica (Síntomas / Signos Vitales)</span>
                      <span className="text-rose-500">*</span>
                    </Label>
                    <Textarea
                      placeholder="Describa el estado clínico, signos vitales, traumatismos y procedimientos efectuados..."
                      value={formData.motivo_atencion}
                      onChange={(e) => updateField("motivo_atencion", e.target.value)}
                      data-testid="input-motivo-atencion"
                      className="min-h-[75px] text-xs"
                      required
                    />
                  </div>

                  {/* Checkboxes de Comunidad y Usuarios */}
                  <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                    <div className="flex items-center gap-2">
                      <Switch
                        id="servicio-comunidad"
                        checked={formData.servicio_comunidad}
                        onCheckedChange={(val) => updateField("servicio_comunidad", val)}
                      />
                      <Label htmlFor="servicio-comunidad" className="text-xs cursor-pointer text-zinc-700 dark:text-zinc-300">
                        Servicio a la Comunidad (Apoyo fuera de franja concesionada)
                      </Label>
                    </div>

                    <div className="flex items-center gap-2">
                      <Label className="text-xs text-zinc-700 dark:text-zinc-300">
                        Usuarios Atendidos:
                      </Label>
                      <Input
                        type="number"
                        min="1"
                        value={formData.usuarios_atendidos}
                        onChange={(e) => updateField("usuarios_atendidos", e.target.value)}
                        className="w-20 h-8 text-xs font-mono text-center"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ) : (
            <motion.div
              key="bloque-grua"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Card className="border border-blue-200/80 dark:border-blue-950/80 bg-white dark:bg-zinc-900/90 shadow-xs">
                <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80 bg-blue-50/30 dark:bg-blue-950/20">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-md bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                      <Wrench className="size-4" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-semibold text-blue-950 dark:text-blue-100">
                        Bloque 4: Datos del Auxilio Mecánico y Remolque de Grúa
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Vehículo asistido, causas de inmovilización y tramo de arrastre.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {/* Tipo de Grúa: Bloqueado/Derivado si hay unidad móvil seleccionada para evitar redundancia */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                        <span>Tipo de Grúa Operada</span>
                        <span className="text-rose-500">*</span>
                      </Label>

                      {selectedVehicleObj ? (
                        <div className="h-9 px-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/60 flex items-center justify-between text-xs">
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {formData.tipo_grua === "PEQUEÑA"
                              ? "PEQUEÑA (Pluma Liviana)"
                              : formData.tipo_grua === "GRANDE"
                              ? "GRANDE (Pesada)"
                              : "PLATAFORMA (Autotransportador)"}
                          </span>
                          <Badge variant="secondary" className="text-[10px] text-blue-700 dark:text-blue-300 font-mono py-0 flex items-center gap-1">
                            <Lock className="size-2.5" />
                            {selectedVehicleObj.codigo_interno}
                          </Badge>
                        </div>
                      ) : (
                        <Select
                          value={formData.tipo_grua}
                          onValueChange={(val) => updateField("tipo_grua", val as TipoGruaType)}
                        >
                          <SelectTrigger className="h-9 text-xs">
                            <SelectValue placeholder="Seleccionar tipo">
                              {(val) => val}
                            </SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="PEQUEÑA">PEQUEÑA (Pluma Liviana)</SelectItem>
                            <SelectItem value="GRANDE">GRANDE (Pesada / Wincha Industrial)</SelectItem>
                            <SelectItem value="PLATAFORMA">PLATAFORMA (Autotransportador)</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>

                    {/* Placa Asistida */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Placa del Vehículo Asistido
                      </Label>
                      <Input
                        placeholder="ej. PBA-8942"
                        value={formData.placa_asistida}
                        onChange={(e) => updateField("placa_asistida", e.target.value.toUpperCase())}
                        data-testid="input-placa-asistida"
                        className="h-9 text-xs font-mono uppercase"
                      />
                    </div>

                    {/* Usuario que Reporta */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Usuario / Conductor que Reporta
                      </Label>
                      <Input
                        placeholder="ej. Roberto Alarcón"
                        value={formData.usuario_reporta}
                        onChange={(e) => updateField("usuario_reporta", e.target.value)}
                        data-testid="input-usuario-reporta"
                        className="h-9 text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Tipo de Vehículo Asistido */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Tipo de Vehículo Asistido
                      </Label>
                      <Select
                        value={formData.tipo_vehiculo_asistido}
                        onValueChange={(val) => updateField("tipo_vehiculo_asistido", val)}
                      >
                        <SelectTrigger className="h-9 text-xs">
                          <SelectValue placeholder="Seleccionar tipo vehículo">
                            {(val) => val}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {TIPOS_VEHICULO_GRUA.map((t, idx) => (
                            <SelectItem key={idx} value={t}>
                              {t}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Posible Causa */}
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                        Causa Principal de la Inmovilización
                      </Label>
                      <Select
                        value={formData.posible_causa}
                        onValueChange={(val) => updateField("posible_causa", val)}
                      >
                        <SelectTrigger className="h-9 text-xs">
                          <SelectValue placeholder="Seleccionar causa">
                            {(val) => val}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {CAUSAS_GRUA.map((c, idx) => (
                            <SelectItem key={idx} value={c}>
                              {c}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Tramo de Remolque con Cálculo Automático de Arrastre */}
                  <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200/80 dark:border-zinc-700/60 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200 flex items-center gap-1.5">
                        <Route className="size-3.5 text-blue-600 dark:text-blue-400" />
                        Tramo de Remolque y Arrastre
                      </span>
                      {kmArrastre !== null && (
                        <Badge
                          data-testid="badge-km-arrastre"
                          variant="outline"
                          className="bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300 border-blue-300 font-mono text-[11px]"
                        >
                          Arrastre Total: {kmArrastre} km
                        </Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <Label className="text-xs text-zinc-600 dark:text-zinc-400">
                          Km Origen Traslado
                        </Label>
                        <Input
                          type="number"
                          step="0.001"
                          placeholder="ej. 32.800"
                          value={formData.km_origen_traslado}
                          onChange={(e) => updateField("km_origen_traslado", e.target.value)}
                          data-testid="input-km-origen"
                          className="h-8 text-xs font-mono"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-xs text-zinc-600 dark:text-zinc-400">
                          Km Destino Traslado
                        </Label>
                        <Input
                          type="number"
                          step="0.001"
                          placeholder="ej. 54.200"
                          value={formData.km_destino_traslado}
                          onChange={(e) => updateField("km_destino_traslado", e.target.value)}
                          data-testid="input-km-destino"
                          className="h-8 text-xs font-mono"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Motivo de Atención Grúa */}
                  <div className="space-y-1.5">
                    <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                      <span>Motivo del Servicio y Maniobra Efectuada</span>
                      <span className="text-rose-500">*</span>
                    </Label>
                    <Textarea
                      placeholder="Describa el trabajo realizado, maniobras especiales, uso de dolly, despeje de calzada..."
                      value={formData.motivo_atencion}
                      onChange={(e) => updateField("motivo_atencion", e.target.value)}
                      className="min-h-[70px] text-xs"
                      required
                    />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ========================================================================= */}
        {/* BLOQUE 5: Odometría, Cierre y Auditoría */}
        {/* ========================================================================= */}
        <Card className="border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/90 shadow-xs">
          <CardHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                  <Gauge className="size-4" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Bloque 5: Odometría, Cierre y Certificación MTOP
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Lecturas de kilometraje vehicular y bandera para sincronización ministerial.
                  </CardDescription>
                </div>
              </div>

              {/* Badge de Km Recorridos Reactivo */}
              {metricasOdometria.kmRecorridos !== null && (
                <Badge
                  data-testid="badge-km-recorridos"
                  variant="outline"
                  className={`text-[11px] font-mono font-medium px-2.5 py-1 ${
                    metricasOdometria.esValido
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800"
                      : "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border-rose-300 dark:border-rose-800"
                  }`}
                >
                  {metricasOdometria.esValido
                    ? `Total Recorrido: ${metricasOdometria.kmRecorridos} km`
                    : "⚠️ Odómetro Inválido"}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Odómetro Salida */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span>Odómetro Salida (Km)</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="ej. 14250.0"
                  value={formData.odometro_salida_km}
                  onChange={(e) => updateField("odometro_salida_km", e.target.value)}
                  data-testid="input-odometro-salida"
                  className="h-9 text-xs font-mono"
                  required
                />
              </div>

              {/* Odómetro Llegada */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                  <span>Odómetro Llegada (Km)</span>
                  <span className="text-rose-500">*</span>
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="ej. 14286.5"
                  value={formData.odometro_llegada_km}
                  onChange={(e) => updateField("odometro_llegada_km", e.target.value)}
                  data-testid="input-odometro-llegada"
                  className="h-9 text-xs font-mono"
                  required
                />
              </div>

              {/* Km Calculados (Deshabilitado) */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  Km Recorridos (Calculado)
                </Label>
                <Input
                  disabled
                  value={
                    metricasOdometria.kmRecorridos !== null
                      ? `${metricasOdometria.kmRecorridos} km`
                      : "—"
                  }
                  className="h-9 text-xs font-mono bg-zinc-100 dark:bg-zinc-800/60 font-semibold text-zinc-800 dark:text-zinc-200"
                />
              </div>
            </div>

            {/* Error Odometría */}
            {!metricasOdometria.esValido && (
              <p className="text-xs font-medium text-rose-500 dark:text-rose-400">
                {metricasOdometria.error}
              </p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-zinc-100 dark:border-zinc-800">
              {/* Switch MTOP */}
              <div className="sm:col-span-1 flex items-center gap-3 p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800">
                <Switch
                  id="switch-mtop"
                  checked={formData.reportado_mtop}
                  onCheckedChange={(val) => updateField("reportado_mtop", val)}
                  data-testid="switch-reportado-mtop"
                />
                <div className="space-y-0.5">
                  <Label htmlFor="switch-mtop" className="text-xs font-semibold cursor-pointer text-zinc-900 dark:text-zinc-100">
                    Certificación MTOP
                  </Label>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    Habilitar para sincronización ministerial.
                  </p>
                </div>
              </div>

              {/* Observaciones */}
              <div className="sm:col-span-2 space-y-1.5">
                <Label className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Observaciones de Campo Adicionales
                </Label>
                <Textarea
                  placeholder="Detalles complementarios, condiciones climáticas o requerimientos especiales..."
                  value={formData.observaciones}
                  onChange={(e) => updateField("observaciones", e.target.value)}
                  className="min-h-[60px] text-xs"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ========================================================================= */}
        {/* Acciones Finales (Submit & Cancel) */}
        {/* ========================================================================= */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push(formData.servicio === "ambulancia" ? "/?tab=ambulancias" : "/?tab=gruas")}
            disabled={isSubmitting}
            className="h-10 px-5 text-xs text-zinc-600 dark:text-zinc-300"
          >
            Cancelar
          </Button>

          <Button
            type="submit"
            disabled={isSubmitting || !metricasTiempo.cronologiaValida || !metricasOdometria.esValido}
            data-testid="btn-guardar-registro"
            className="h-10 px-6 text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 gap-2 shadow-sm"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="size-4 animate-spin" />
                <span>Guardando en Servidor...</span>
              </>
            ) : (
              <>
                <Save className="size-4" />
                <span>Guardar Asistencia Operativa</span>
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

export function RegistroOperacionesForm(props: { fixedService?: ServiceType }) {
  return (
    <React.Suspense
      fallback={
        <div className="w-full max-w-5xl mx-auto p-12 text-center text-xs text-zinc-500 flex flex-col items-center justify-center gap-2">
          <Loader2 className="size-5 text-indigo-600 animate-spin" />
          <span>Cargando formulario de operaciones...</span>
        </div>
      }
    >
      <RegistroOperacionesFormContent {...props} />
    </React.Suspense>
  );
}
