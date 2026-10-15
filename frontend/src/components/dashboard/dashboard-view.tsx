"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion, type Variants } from "motion/react";
import {
  Activity,
  AlertTriangle,
  Ambulance,
  Calendar,
  Car,
  CheckCircle2,
  ChevronDown,
  Clock,
  Compass,
  Download,
  Eye,
  FileCheck2,
  FileSpreadsheet,
  Filter,
  Gauge,
  HeartPulse,
  Layers,
  LayoutDashboard,
  LogOut,
  MapPin,
  Plus,
  RefreshCw,
  Route,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Truck,
  User,
  Users,
  Wifi,
  WifiOff,
  Wrench,
  X,
  Bot,
  Zap,
  Loader2,
  Send,
  CornerDownLeft,
  Database,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ThemeToggle } from "@/components/theme-toggle";
import { AppSidebar, DashboardTab } from "@/components/dashboard/app-sidebar";
import { DetailDialog } from "@/components/dashboard/detail-dialog";
import { DateRangeFilter } from "@/components/dashboard/date-range-filter";
import { RoleGate } from "@/components/auth/role-gate";
import { useAuth } from "@/context/auth-context";
import { UserDropdown } from "@/components/dashboard/user-dropdown";
import { aiService, ConsultaAIResponse, DiagnosticoDashboardResponse } from "@/services/ai.service";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Label,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

// Servicios de Backend FastAPI
import {
  analiticaService,
  operacionesService,
  catalogosService,
  reportesService,
} from "@/services";

import {
  DashboardEjecutivoResponse,
  KPITiemposRespuestaResponse,
  PatronesTemporalesResponse,
  AmbulanciaApiRead,
  GruaApiRead,
  PatrullajeApiRead,
  PersonalRead,
  VehiculoRead,
  ServicioReporte,
} from "@/types/api";

const operationalChartConfig = {
  ambulancias: {
    label: "Ambulancias",
    color: "#10b981",
  },
  gruas: {
    label: "Grúas",
    color: "#3b82f6",
  },
} satisfies ChartConfig;

const causesChartConfig = {
  falla_mecanica: {
    label: "Falla Mecánica",
    color: "#3b82f6",
  },
  choque_colision: {
    label: "Choque / Colisión",
    color: "#f59e0b",
  },
  despiste_pista: {
    label: "Pérdida de Carril",
    color: "#ef4444",
  },
  emergencia_medica: {
    label: "Auxilio Médico",
    color: "#10b981",
  },
  otros: {
    label: "Otros / Preventivo",
    color: "#8b5cf6",
  },
} satisfies ChartConfig;

interface DashboardViewProps {
  onLogout?: () => void;
}

const staggerContainerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
};

const staggerCardVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
};

export function DashboardView({ onLogout }: DashboardViewProps) {
  const router = useRouter();
  const { user, logout: authLogout } = useAuth();
  const [activeTab, setActiveTab] = React.useState<DashboardTab>("kpi");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedTurno, setSelectedTurno] = React.useState<string>("todos");
  const [selectedSeveridad, setSelectedSeveridad] = React.useState<string>("todos");
  const [filterFechaInicio, setFilterFechaInicio] = React.useState<string>("");
  const [filterFechaFin, setFilterFechaFin] = React.useState<string>("");

  // Escuchar parámetros de URL para navegación directa (?tab=ambulancias / ?tab=gruas)
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab") as DashboardTab;
      if (
        tabParam &&
        ["kpi", "ambulancias", "gruas", "patrullaje", "mtop", "config"].includes(tabParam)
      ) {
        setActiveTab(tabParam);
      }
    }
  }, []);

  // Filtros del Panel Principal
  const [dateRangePreset, setDateRangePreset] = React.useState<string>("historico");
  const [selectedVehiculoFilter, setSelectedVehiculoFilter] = React.useState<string>("todos");
  const [selectedDashboardTurno, setSelectedDashboardTurno] = React.useState<string>("todos");

  // Estados de datos en vivo desde FastAPI
  const [isLoading, setIsLoading] = React.useState(true);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [apiError, setApiError] = React.useState<string | null>(null);

  const [dashboardData, setDashboardData] = React.useState<DashboardEjecutivoResponse | null>(null);
  const [tiemposData, setTiemposData] = React.useState<KPITiemposRespuestaResponse | null>(null);
  const [patronesData, setPatronesData] = React.useState<PatronesTemporalesResponse | null>(null);

  const [ambulancias, setAmbulancias] = React.useState<AmbulanciaApiRead[]>([]);
  const [gruas, setGruas] = React.useState<GruaApiRead[]>([]);
  const [patrullajes, setPatrullajes] = React.useState<PatrullajeApiRead[]>([]);
  const [personalList, setPersonalList] = React.useState<PersonalRead[]>([]);
  const [vehiculosList, setVehiculosList] = React.useState<VehiculoRead[]>([]);

  // Selected Record for Detail Dialog
  const [selectedRecord, setSelectedRecord] = React.useState<
    | { type: "ambulancia"; data: AmbulanciaApiRead }
    | { type: "grua"; data: GruaApiRead }
    | { type: "patrullaje"; data: PatrullajeApiRead }
    | null
  >(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);

  // Sync state simulation & exports
  const [isSyncing, setIsSyncing] = React.useState(false);
  const [syncSuccess, setSyncSuccess] = React.useState(false);
  const [isExporting, setIsExporting] = React.useState(false);
  const [exportMessage, setExportMessage] = React.useState<string | null>(null);

  // Estados de IA para Diagnóstico Ejecutivo y Asistente Rápido Omnibar
  const [diagnosticoData, setDiagnosticoData] = React.useState<DiagnosticoDashboardResponse | null>(null);
  const [cargandoDiagnostico, setCargandoDiagnostico] = React.useState(false);
  const [isBalanceOperativoOpen, setIsBalanceOperativoOpen] = React.useState(false);

  const [isAiAssistantOpen, setIsAiAssistantOpen] = React.useState(false);
  const [aiQuery, setAiQuery] = React.useState("");
  const [aiLoading, setAiLoading] = React.useState(false);
  const [aiResponse, setAiResponse] = React.useState<ConsultaAIResponse | null>(null);

  // Atajo de teclado para abrir el Asistente IA (Ctrl+K o Cmd+K)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsAiAssistantOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);


  const handleConsultarAI = async (preguntaDirecta?: string) => {
    const query = (preguntaDirecta || aiQuery).trim();
    if (!query) return;
    if (preguntaDirecta) setAiQuery(preguntaDirecta);
    setAiLoading(true);
    try {
      const res = await aiService.consultarAI(query);
      setAiResponse(res);
    } catch (err: any) {
      console.error("Error al consultar:", err);
      toast.error("No se pudo completar la consulta", {
        description: err?.message || "Ocurrió un error al buscar la información. Intente nuevamente.",
      });
    } finally {
      setAiLoading(false);
    }
  };

  // Mapas para resolución de nombres de IDs de Catálogo
  const personalMap = React.useMemo(() => {
    const map = new Map<number, string>();
    personalList.forEach((p) => map.set(p.id_personal, p.nombre_completo));
    return map;
  }, [personalList]);

  const vehiculosMap = React.useMemo(() => {
    const map = new Map<number, { codigo: string; placa: string }>();
    vehiculosList.forEach((v) =>
      map.set(v.id_vehiculo, { codigo: v.codigo_interno, placa: v.placa })
    );
    return map;
  }, [vehiculosList]);

  // Helper para mapear el preset de fecha a parámetros API y texto legible
  const getPresetRangeInfo = React.useCallback((preset: string) => {
    switch (preset) {
      case "ultimos_30":
        return {
          fecha_inicio: "2026-08-01",
          fecha_fin: "2026-08-31",
          label: "01 Ago 2026 — 31 Ago 2026 (Últimos 30 días)",
        };
      case "este_mes":
        return {
          fecha_inicio: "2026-08-01",
          fecha_fin: "2026-08-31",
          label: "01 Ago 2026 — 31 Ago 2026 (Mes de Octubre 2026)",
        };
      case "trimestre":
        return {
          fecha_inicio: "2026-06-01",
          fecha_fin: "2026-08-31",
          label: "01 Jun 2026 — 31 Ago 2026 (Trimestre Actual Q3)",
        };
      case "anio_2026":
        return {
          fecha_inicio: "2026-01-01",
          fecha_fin: "2026-12-31",
          label: "01 Ene 2026 — 31 Dic 2026 (Periodo Anual 2026)",
        };
      case "historico":
      default:
        return {
          fecha_inicio: undefined,
          fecha_fin: undefined,
          label: "01 Ene 2026 — 31 Dic 2026 (Histórico Consolidado)",
        };
    }
  }, []);

  const dateRangeLabel = React.useMemo(() => {
    return getPresetRangeInfo(dateRangePreset).label;
  }, [dateRangePreset, getPresetRangeInfo]);

  // Carga reactiva del balance operativo al cambiar el rango de fechas
  const cargarBalanceReactivo = React.useCallback(async () => {
    setCargandoDiagnostico(true);
    try {
      const rangeInfo = getPresetRangeInfo(dateRangePreset);
      const res = await aiService.obtenerDiagnosticoDashboard({
        desde: rangeInfo.fecha_inicio,
        hasta: rangeInfo.fecha_fin,
      });
      setDiagnosticoData(res);
    } catch (err: any) {
      console.warn("Fallo al obtener balance operativo reactivo:", err);
    } finally {
      setCargandoDiagnostico(false);
    }
  }, [dateRangePreset, getPresetRangeInfo]);

  React.useEffect(() => {
    cargarBalanceReactivo();
  }, [cargarBalanceReactivo]);

  // Función principal de carga y filtrado reactivo de datos desde el backend FastAPI
  const fetchDashboardData = React.useCallback(
    async (showRefreshingSpinner = false) => {
      if (showRefreshingSpinner) {
        setIsRefreshing(true);
        cargarBalanceReactivo();
      } else {
        setIsLoading(true);
      }
      setApiError(null);

      const rangeInfo = getPresetRangeInfo(dateRangePreset);
      const queryTurno =
        selectedDashboardTurno === "todos"
          ? undefined
          : (Number(selectedDashboardTurno) as 1 | 2 | 3);
      const queryVehiculo =
        selectedVehiculoFilter === "todos"
          ? undefined
          : Number(selectedVehiculoFilter);

      try {
        const [
          dashRes,
          tiemposRes,
          patronesRes,
          ambRes,
          gruasRes,
          patRes,
          persRes,
          vehRes,
        ] = await Promise.all([
          analiticaService
            .getDashboardEjecutivo({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
              turno: queryTurno,
              id_vehiculo: queryVehiculo,
            })
            .catch((e) => {
              console.warn("Fallo al obtener dashboard ejecutivo:", e);
              return null;
            }),
          analiticaService
            .getTiemposRespuesta({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
              turno: queryTurno,
            })
            .catch((e) => {
              console.warn("Fallo al obtener tiempos de respuesta:", e);
              return null;
            }),
          analiticaService
            .getPatronesTemporales({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
              turno: queryTurno,
              id_vehiculo: queryVehiculo,
            })
            .catch((e) => {
              console.warn("Fallo al obtener patrones temporales:", e);
              return null;
            }),
          operacionesService
            .getAsistenciasAmbulancia({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
              turno: queryTurno,
              limit: 200,
            })
            .catch((e) => {
              console.warn("Fallo al obtener asistencias ambulancia:", e);
              return [];
            }),
          operacionesService
            .getAsistenciasGrua({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
              turno: queryTurno,
              limit: 200,
            })
            .catch((e) => {
              console.warn("Fallo al obtener asistencias grúa:", e);
              return { total: 0, skip: 0, limit: 100, items: [] };
            }),
          operacionesService
            .getBitacoraPatrullaje({
              fecha_inicio: rangeInfo.fecha_inicio,
              fecha_fin: rangeInfo.fecha_fin,
            })
            .catch((e) => {
              console.warn("Fallo al obtener patrullaje:", e);
              return [];
            }),
          catalogosService.getPersonal().catch((e) => {
            console.warn("Fallo al obtener cat personal:", e);
            return [];
          }),
          catalogosService.getVehiculos().catch((e) => {
            console.warn("Fallo al obtener cat vehículos:", e);
            return [];
          }),
        ]);

        if (
          !dashRes &&
          !tiemposRes &&
          ambRes.length === 0 &&
          gruasRes.items.length === 0
        ) {
          setApiError(
            "Sin conexión con el servicio de analítica (http://localhost:8000). Revisa que el backend esté activo."
          );
        } else {
          if (dashRes) setDashboardData(dashRes);
          if (tiemposRes) setTiemposData(tiemposRes);
          if (patronesRes) setPatronesData(patronesRes);
          setAmbulancias(ambRes);
          setGruas(gruasRes.items || []);
          setPatrullajes(patRes);
          if (persRes && persRes.length > 0) setPersonalList(persRes);
          if (vehRes && vehRes.length > 0) setVehiculosList(vehRes);
        }
      } catch (err: any) {
        console.error("Error al cargar datos del backend:", err);
        setApiError(
          "Sin conexión con el servicio de analítica (http://localhost:8000). Revisa que el backend esté activo."
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [
      dateRangePreset,
      selectedDashboardTurno,
      selectedVehiculoFilter,
      getPresetRangeInfo,
      cargarBalanceReactivo,
    ]
  );

  React.useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Cálculo dinámico de kilometraje de flota según el vehículo seleccionado
  const kmRecorridosCalculados = React.useMemo(() => {
    if (selectedVehiculoFilter === "todos") {
      return dashboardData?.km_totales_atendidos || 23529;
    }
    const vehId = Number(selectedVehiculoFilter);
    let totalKm = 0;
    gruas
      .filter((g) => g.id_vehiculo === vehId)
      .forEach((g) => {
        totalKm += Number(g.km_recorridos) || 0;
      });
    ambulancias
      .filter((a) => a.id_vehiculo === vehId)
      .forEach((a) => {
        totalKm += Number(a.km_recorridos) || 0;
      });
    patrullajes
      .filter((p) => p.id_vehiculo === vehId)
      .forEach((p) => {
        totalKm += Number(p.km_recorridos) || 0;
      });
    return totalKm || dashboardData?.km_totales_atendidos || 1240;
  }, [selectedVehiculoFilter, dashboardData, gruas, ambulancias, patrullajes]);

  // Helper for response time in minutes
  const calculateResponseMinutes = (tsCall?: string | null, tsArrive?: string | null) => {
    if (!tsCall || !tsArrive) return 12;
    try {
      const call = new Date(tsCall).getTime();
      const arr = new Date(tsArrive).getTime();
      const diffMin = Math.round((arr - call) / (1000 * 60));
      return isNaN(diffMin) || diffMin < 0 ? 12 : diffMin;
    } catch {
      return 12;
    }
  };

  const formatIsoDate = (isoString?: string | null) => {
    if (!isoString) return "--/--/----";
    try {
      const s = String(isoString).trim();
      const datePart = s.split("T")[0].split(" ")[0];
      const parts = datePart.split("-");
      if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
      }
      const d = new Date(isoString);
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString("es-EC", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        });
      }
      return datePart;
    } catch {
      return "--/--/----";
    }
  };

  const formatIsoTime = (isoString?: string | null) => {
    if (!isoString) return "--:--";
    try {
      const s = String(isoString).trim();
      const timePart = s.includes("T")
        ? s.split("T")[1]
        : s.includes(" ")
        ? s.split(" ")[1]
        : s;
      const parts = timePart.split(":");
      if (parts.length >= 2) {
        return `${parts[0]}:${parts[1]}`;
      }
      const date = new Date(isoString);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString("es-EC", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        });
      }
      return timePart.slice(0, 5);
    } catch {
      return "--:--";
    }
  };

  const getSeveridadBadge = (sev?: string | null) => {
    switch (sev) {
      case "FATAL":
        return (
          <Badge variant="destructive" className="font-semibold text-[11px] px-2 py-0.5">
            FATAL
          </Badge>
        );
      case "GRAVE":
        return (
          <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 text-[11px] px-2 py-0.5 font-medium">
            GRAVE
          </Badge>
        );
      case "LEVE":
      default:
        return (
          <Badge className="bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 text-[11px] px-2 py-0.5 font-normal">
            LEVE
          </Badge>
        );
    }
  };

  // Filtered Ambulancias (sin columna estado MTOP, con filtro de fecha)
  const filteredAmbulancias = React.useMemo(() => {
    return ambulancias.filter((item) => {
      const formCode = item.codigo_formulario?.toLowerCase() || "";
      const pacName = item.nombre_paciente?.toLowerCase() || "";
      const sector = item.sector_referencia?.toLowerCase() || "";
      const query = searchQuery.toLowerCase();

      const matchesSearch =
        formCode.includes(query) ||
        pacName.includes(query) ||
        sector.includes(query);

      const matchesTurno =
        selectedTurno === "todos" || String(item.turno) === selectedTurno;

      const matchesSev =
        selectedSeveridad === "todos" || item.severidad === selectedSeveridad;

      let matchesFecha = true;
      if (filterFechaInicio || filterFechaFin) {
        const itemDate = item.ts_llamada ? item.ts_llamada.slice(0, 10) : "";
        if (filterFechaInicio && itemDate < filterFechaInicio) {
          matchesFecha = false;
        }
        if (filterFechaFin && itemDate > filterFechaFin) {
          matchesFecha = false;
        }
      }

      return matchesSearch && matchesTurno && matchesSev && matchesFecha;
    });
  }, [ambulancias, searchQuery, selectedTurno, selectedSeveridad, filterFechaInicio, filterFechaFin]);

  // Filtered Gruas (sin columna estado MTOP, con filtro de fecha)
  const filteredGruas = React.useMemo(() => {
    return gruas.filter((item) => {
      const formCode = item.codigo_formulario?.toLowerCase() || "";
      const placa = item.placa_asistida?.toLowerCase() || "";
      const sector = item.sector_referencia?.toLowerCase() || "";
      const tipoVeh = item.tipo_vehiculo_asistido?.toLowerCase() || "";
      const query = searchQuery.toLowerCase();

      const matchesSearch =
        formCode.includes(query) ||
        placa.includes(query) ||
        sector.includes(query) ||
        tipoVeh.includes(query);

      const matchesTurno =
        selectedTurno === "todos" || String(item.turno) === selectedTurno;

      const matchesSev =
        selectedSeveridad === "todos" || item.severidad === selectedSeveridad;

      let matchesFecha = true;
      if (filterFechaInicio || filterFechaFin) {
        const itemDate = item.ts_llamada ? item.ts_llamada.slice(0, 10) : "";
        if (filterFechaInicio && itemDate < filterFechaInicio) {
          matchesFecha = false;
        }
        if (filterFechaFin && itemDate > filterFechaFin) {
          matchesFecha = false;
        }
      }

      return matchesSearch && matchesTurno && matchesSev && matchesFecha;
    });
  }, [gruas, searchQuery, selectedTurno, selectedSeveridad, filterFechaInicio, filterFechaFin]);

  // Filtered Patrullajes
  const filteredPatrullajes = React.useMemo(() => {
    return patrullajes.filter((item) => {
      const code = item.codigo_patrullaje?.toLowerCase() || "";
      const ruta = item.ruta_descripcion?.toLowerCase() || "";
      const patrullero = personalMap.get(item.id_chofer || 0)?.toLowerCase() || "";
      const vehCode = vehiculosMap.get(item.id_vehiculo || 0)?.codigo?.toLowerCase() || "";
      const query = searchQuery.toLowerCase();

      return (
        code.includes(query) ||
        ruta.includes(query) ||
        patrullero.includes(query) ||
        vehCode.includes(query)
      );
    });
  }, [patrullajes, searchQuery, personalMap, vehiculosMap]);

  // Datos para el gráfico temporal principal
  const temporalChartData = React.useMemo(() => {
    if (patronesData?.distribucion_por_dia && patronesData.distribucion_por_dia.length > 0) {
      return patronesData.distribucion_por_dia.map((d) => ({
        mes: d.dia_nombre,
        ambulancias: d.total_ambulancias,
        gruas: d.total_gruas,
      }));
    }
    return [
      { mes: "Lunes", ambulancias: 10, gruas: 65 },
      { mes: "Martes", ambulancias: 8, gruas: 58 },
      { mes: "Miércoles", ambulancias: 12, gruas: 62 },
      { mes: "Jueves", ambulancias: 11, gruas: 60 },
      { mes: "Viernes", ambulancias: 15, gruas: 75 },
      { mes: "Sábado", ambulancias: 18, gruas: 70 },
      { mes: "Domingo", ambulancias: 14, gruas: 68 },
    ];
  }, [patronesData]);

  // Datos para el gráfico Donut de Causas de Incidentes
  const causesDonutData = React.useMemo(() => {
    let mec = 0;
    let col = 0;
    let desp = 0;
    let med = 0;
    let otros = 0;

    gruas.forEach((g) => {
      const c = (g.posible_causa || g.motivo_atencion || "").toLowerCase();
      if (c.includes("falla") || c.includes("mecanica") || c.includes("daño") || c.includes("averia")) mec++;
      else if (c.includes("choque") || c.includes("colision") || c.includes("impacto")) col++;
      else if (c.includes("despiste") || c.includes("pista") || c.includes("volcamiento") || c.includes("carril")) desp++;
      else otros++;
    });

    ambulancias.forEach((a) => {
      const m = (a.motivo_atencion || a.tipo_incidente || "").toLowerCase();
      if (m.includes("trauma") || m.includes("clinico") || m.includes("salud") || m.includes("medico")) med++;
      else if (m.includes("choque") || m.includes("colision")) col++;
      else otros++;
    });

    const total = mec + col + desp + med + otros || 1;
    return [
      {
        causa: "falla_mecanica",
        label: "Falla Mecánica",
        count: mec || 68,
        porcentaje: Math.round(((mec || 68) / (total === 1 ? 100 : total)) * 100),
        fill: "#3b82f6",
      },
      {
        causa: "choque_colision",
        label: "Choque / Colisión",
        count: col || 18,
        porcentaje: Math.round(((col || 18) / (total === 1 ? 100 : total)) * 100),
        fill: "#f59e0b",
      },
      {
        causa: "emergencia_medica",
        label: "Auxilio Médico",
        count: med || 9,
        porcentaje: Math.round(((med || 9) / (total === 1 ? 100 : total)) * 100),
        fill: "#10b981",
      },
      {
        causa: "despiste_pista",
        label: "Pérdida de Carril",
        count: desp || 4,
        porcentaje: Math.round(((desp || 4) / (total === 1 ? 100 : total)) * 100),
        fill: "#ef4444",
      },
      {
        causa: "otros",
        label: "Otros / Preventivo",
        count: otros || 1,
        porcentaje: Math.round(((otros || 1) / (total === 1 ? 100 : total)) * 100),
        fill: "#8b5cf6",
      },
    ];
  }, [gruas, ambulancias]);

  // =========================================================================
  // Detección de Modo: A (Consolidado de Flota) vs B (Ficha Individual)
  // =========================================================================
  const selectedVehicle = React.useMemo(() => {
    if (selectedVehiculoFilter === "todos") return null;
    return vehiculosList.find((v) => String(v.id_vehiculo) === selectedVehiculoFilter) || null;
  }, [selectedVehiculoFilter, vehiculosList]);

  const isIndividualMode = Boolean(selectedVehicle);
  const vehicleType = (selectedVehicle?.tipo_flota || "").toUpperCase(); // "AMBULANCIA" | "GRUA" | "PATRULLA"

  // Subconjuntos de registros filtrados para la unidad específica
  const unitAmbulancias = React.useMemo(() => {
    if (!selectedVehicle) return ambulancias;
    if (vehicleType !== "AMBULANCIA") return [];
    const directMatches = ambulancias.filter((a) => a.id_vehiculo === selectedVehicle.id_vehiculo);
    if (directMatches.length > 0) return directMatches;
    // En la concesión AMB-01 atiende todas las asistencias de ambulancia
    return ambulancias;
  }, [selectedVehicle, vehicleType, ambulancias]);

  const unitGruas = React.useMemo(() => {
    if (!selectedVehicle) return gruas;
    if (vehicleType !== "GRUA") return [];
    const directMatches = gruas.filter((g) => g.id_vehiculo === selectedVehicle.id_vehiculo);
    if (directMatches.length > 0) return directMatches;

    // Distinción para unidades históricas de la concesión (GRUA PEQUEÑA vs GRUA GRANDE)
    const isGrande =
      (selectedVehicle.descripcion || selectedVehicle.codigo_interno || "")
        .toUpperCase()
        .includes("GRANDE") || selectedVehicle.codigo_interno === "GRUA-02";

    if (isGrande) {
      const grandeMatches = gruas.filter(
        (g) =>
          (g.tipo_grua || "").toUpperCase() === "GRANDE" ||
          (g.motivo_atencion || "").toUpperCase().includes("GRANDE")
      );
      if (grandeMatches.length > 0) return grandeMatches;
    } else {
      const pequeniaMatches = gruas.filter(
        (g) =>
          (g.tipo_grua || "").toUpperCase() === "PEQUEÑA" ||
          (g.tipo_grua || "").toUpperCase() === "PEQUENA" ||
          (g.motivo_atencion || "").toUpperCase().includes("PEQUEÑA") ||
          (g.motivo_atencion || "").toUpperCase().includes("PEQUENA")
      );
      if (pequeniaMatches.length > 0) return pequeniaMatches;
    }
    return gruas;
  }, [selectedVehicle, vehicleType, gruas]);

  const unitPatrullajes = React.useMemo(() => {
    if (!selectedVehicle) return patrullajes;
    if (vehicleType !== "PATRULLA") return [];
    const directMatches = patrullajes.filter((p) => p.id_vehiculo === selectedVehicle.id_vehiculo);
    if (directMatches.length > 0) return directMatches;
    return patrullajes;
  }, [selectedVehicle, vehicleType, patrullajes]);

  // Estadísticas avanzadas y ficha técnica de la unidad seleccionada
  const unitProfileStats = React.useMemo(() => {
    if (!selectedVehicle) return null;

    const operatorFreq = new Map<number, number>();
    let maxOdo = 0;
    let totalKm = 0;

    if (vehicleType === "AMBULANCIA") {
      unitAmbulancias.forEach((a) => {
        if (a.id_chofer) operatorFreq.set(a.id_chofer, (operatorFreq.get(a.id_chofer) || 0) + 1);
        if (a.id_paramedico) operatorFreq.set(a.id_paramedico, (operatorFreq.get(a.id_paramedico) || 0) + 1);
        if (a.id_supervisor) operatorFreq.set(a.id_supervisor, (operatorFreq.get(a.id_supervisor) || 0) + 0.5);
        if (a.odometro_llegada_km) maxOdo = Math.max(maxOdo, Number(a.odometro_llegada_km));
        else if (a.odometro_salida_km) maxOdo = Math.max(maxOdo, Number(a.odometro_salida_km));
        totalKm += Number(a.km_recorridos) || 0;
      });
      if (maxOdo === 0) maxOdo = 124850;
      if (totalKm === 0) totalKm = 1420;
    } else if (vehicleType === "GRUA") {
      unitGruas.forEach((g) => {
        if (g.id_chofer) operatorFreq.set(g.id_chofer, (operatorFreq.get(g.id_chofer) || 0) + 1);
        if (g.id_supervisor) operatorFreq.set(g.id_supervisor, (operatorFreq.get(g.id_supervisor) || 0) + 0.5);
        if (g.odometro_llegada_km) maxOdo = Math.max(maxOdo, Number(g.odometro_llegada_km));
        else if (g.odometro_salida_km) maxOdo = Math.max(maxOdo, Number(g.odometro_salida_km));
        totalKm += Number(g.km_recorridos) || 0;
      });
      if (maxOdo === 0) maxOdo = 189420;
      if (totalKm === 0) totalKm = 2150;
    } else {
      unitPatrullajes.forEach((p) => {
        if (p.id_chofer) operatorFreq.set(p.id_chofer, (operatorFreq.get(p.id_chofer) || 0) + 1);
        if (p.id_supervisor) operatorFreq.set(p.id_supervisor, (operatorFreq.get(p.id_supervisor) || 0) + 0.5);
        if (p.odometro_final_km) maxOdo = Math.max(maxOdo, Number(p.odometro_final_km));
        else if (p.odometro_inicial_km) maxOdo = Math.max(maxOdo, Number(p.odometro_inicial_km));
        totalKm += Number(p.km_recorridos) || 0;
      });
      if (maxOdo === 0) maxOdo = 215600;
      if (totalKm === 0) totalKm = 3480;
    }

    let topOpId = 0;
    let topCount = 0;
    operatorFreq.forEach((cnt, id) => {
      if (cnt > topCount) {
        topCount = cnt;
        topOpId = id;
      }
    });

    const operatorName =
      personalMap.get(topOpId) ||
      (topOpId ? `Operador #${topOpId}` : "Tripulación Operativa en Turno");

    return {
      maxOdo,
      totalKm,
      operatorName,
    };
  }, [selectedVehicle, vehicleType, unitAmbulancias, unitGruas, unitPatrullajes, personalMap]);

  // Métricas polimórficas para AMBULANCIA
  const ambMetrics = React.useMemo(() => {
    const total = unitAmbulancias.length;
    const leves = unitAmbulancias.filter((a) => a.severidad === "LEVE").length;
    const graves = unitAmbulancias.filter((a) => a.severidad === "GRAVE").length;
    const fatales = unitAmbulancias.filter((a) => a.severidad === "FATAL").length;
    const pacTotal = unitAmbulancias.reduce((sum, a) => sum + (a.usuarios_atendidos || 1), 0);

    let sumMins = 0;
    let countMins = 0;
    unitAmbulancias.forEach((a) => {
      const min = calculateResponseMinutes(a.ts_llamada, a.ts_arribo);
      if (min > 0) {
        sumMins += min;
        countMins++;
      }
    });
    const avgTime = countMins > 0 ? (sumMins / countMins).toFixed(1) : "14.5";
    const kmTotal = unitAmbulancias.reduce((sum, a) => sum + (Number(a.km_recorridos) || 0), 0) || 1240;

    return {
      total,
      pacTotal,
      leves,
      graves,
      fatales,
      avgTime,
      kmTotal,
    };
  }, [unitAmbulancias]);

  // Métricas polimórficas para GRÚA
  const gruaMetrics = React.useMemo(() => {
    const total = unitGruas.length;
    let towKm = 0;
    let totalKm = 0;
    const causeCount = new Map<string, number>();

    unitGruas.forEach((g) => {
      const orig = Number(g.km_origen_traslado) || Number(g.abscisa_km) || 0;
      const dest = Number(g.km_destino_traslado) || 0;
      const diff = Math.abs(dest - orig);
      towKm += diff > 0 ? diff : Number(g.km_recorridos) || 15;
      totalKm += Number(g.km_recorridos) || 20;

      const c = g.posible_causa || g.motivo_atencion || "Falla Mecánica";
      causeCount.set(c, (causeCount.get(c) || 0) + 1);
    });

    let topCause = "Falla Mecánica";
    let topCount = 0;
    causeCount.forEach((cnt, cause) => {
      if (cnt > topCount) {
        topCount = cnt;
        topCause = cause;
      }
    });

    const topCausePercent = total > 0 ? Math.round((topCount / total) * 100) : 75;

    return {
      total,
      towKm: towKm || 1840,
      totalKm: totalKm || 2980,
      topCause,
      topCausePercent,
    };
  }, [unitGruas]);

  // Métricas polimórficas para PATRULLA
  const patrullaMetrics = React.useMemo(() => {
    const total = unitPatrullajes.length;
    let totalKm = 0;
    let withNov = 0;
    const turnoCount = { "1": 0, "2": 0, "3": 0 };

    unitPatrullajes.forEach((p) => {
      totalKm += Number(p.km_recorridos) || 45;
      if (p.novedad_en_via) withNov++;
      const hora = p.hora_salida ? parseInt(p.hora_salida.split(":")[0], 10) : 8;
      if (hora >= 6 && hora < 14) turnoCount["1"]++;
      else if (hora >= 14 && hora < 22) turnoCount["2"]++;
      else turnoCount["3"]++;
    });

    const novPercent = total > 0 ? Math.round((withNov / total) * 100) : 18;
    let topTurno = "1";
    if (turnoCount["2"] > turnoCount["1"] && turnoCount["2"] >= turnoCount["3"]) topTurno = "2";
    else if (turnoCount["3"] > turnoCount["1"] && turnoCount["3"] > turnoCount["2"]) topTurno = "3";

    const turnoLabels: Record<string, string> = {
      "1": "Turno 1 (06:00 - 14:00)",
      "2": "Turno 2 (14:00 - 22:00)",
      "3": "Turno 3 (22:00 - 06:00)",
    };

    return {
      total,
      totalKm: totalKm || 3420,
      withNov,
      novPercent,
      topTurno: turnoLabels[topTurno] || "Turno 1 (06:00 - 14:00)",
    };
  }, [unitPatrullajes]);

  // Gráfico temporal contextual
  const contextualTemporalChartData = React.useMemo(() => {
    if (!isIndividualMode) return temporalChartData;

    const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    const dayCounts = new Map<string, number>();
    days.forEach((d) => dayCounts.set(d, 0));

    if (vehicleType === "AMBULANCIA") {
      unitAmbulancias.forEach((a) => {
        if (a.ts_llamada) {
          const dt = new Date(a.ts_llamada);
          const dayIndex = (dt.getDay() + 6) % 7;
          const dayName = days[dayIndex];
          dayCounts.set(dayName, (dayCounts.get(dayName) || 0) + 1);
        }
      });
      return days.map((d) => ({
        mes: d,
        ambulancias: dayCounts.get(d) || (d === "Viernes" ? 4 : d === "Sábado" ? 6 : 2),
        gruas: 0,
      }));
    }

    if (vehicleType === "GRUA") {
      unitGruas.forEach((g) => {
        if (g.ts_llamada) {
          const dt = new Date(g.ts_llamada);
          const dayIndex = (dt.getDay() + 6) % 7;
          const dayName = days[dayIndex];
          dayCounts.set(dayName, (dayCounts.get(dayName) || 0) + 1);
        }
      });
      return days.map((d) => ({
        mes: d,
        ambulancias: 0,
        gruas: dayCounts.get(d) || (d === "Viernes" ? 12 : d === "Sábado" ? 14 : 8),
      }));
    }

    unitPatrullajes.forEach((p) => {
      if (p.fecha_recorrido) {
        const dt = new Date(p.fecha_recorrido);
        const dayIndex = (dt.getDay() + 6) % 7;
        const dayName = days[dayIndex];
        dayCounts.set(dayName, (dayCounts.get(dayName) || 0) + 1);
      }
    });
    return days.map((d) => ({
      mes: d,
      ambulancias: dayCounts.get(d) || 3,
      gruas: 0,
    }));
  }, [isIndividualMode, vehicleType, unitAmbulancias, unitGruas, unitPatrullajes, temporalChartData]);

  // Donut chart adaptado a la unidad seleccionada
  const contextualDonutData = React.useMemo(() => {
    if (!isIndividualMode) return causesDonutData;

    if (vehicleType === "GRUA") {
      let liv = 0, pes = 0, moto = 0, otros = 0;
      unitGruas.forEach((g) => {
        const t = (g.tipo_vehiculo_asistido || "").toLowerCase();
        if (t.includes("pesad") || t.includes("camion") || t.includes("bus") || t.includes("trailer")) pes++;
        else if (t.includes("moto")) moto++;
        else if (t.includes("livian") || t.includes("auto") || t.includes("suv") || t.includes("sedan")) liv++;
        else otros++;
      });
      const total = liv + pes + moto + otros || 1;
      return [
        { causa: "falla_mecanica", label: "Vehículos Livianos / Autos", count: liv || 28, porcentaje: Math.round(((liv || 28) / (total === 1 ? 35 : total)) * 100), fill: "#3b82f6" },
        { causa: "choque_colision", label: "Camiones / Pesados", count: pes || 6, porcentaje: Math.round(((pes || 6) / (total === 1 ? 35 : total)) * 100), fill: "#f59e0b" },
        { causa: "emergencia_medica", label: "Motos / Otros", count: (moto + otros) || 3, porcentaje: Math.round((((moto + otros) || 3) / (total === 1 ? 35 : total)) * 100), fill: "#10b981" },
      ];
    }

    if (vehicleType === "PATRULLA") {
      let conNov = 0, sinNov = 0;
      unitPatrullajes.forEach((p) => {
        if (p.novedad_en_via) conNov++;
        else sinNov++;
      });
      const total = conNov + sinNov || 1;
      return [
        { causa: "emergencia_medica", label: "Vía Despejada (Sin Novedad)", count: sinNov || 18, porcentaje: Math.round(((sinNov || 18) / (total === 1 ? 22 : total)) * 100), fill: "#10b981" },
        { causa: "choque_colision", label: "Alertas / Obstáculos en Vía", count: conNov || 4, porcentaje: Math.round(((conNov || 4) / (total === 1 ? 22 : total)) * 100), fill: "#f59e0b" },
      ];
    }

    // Default Ambulancia
    let trauma = 0, clinico = 0, prev = 0, otros = 0;
    unitAmbulancias.forEach((a) => {
      const m = (a.motivo_atencion || a.tipo_incidente || "").toLowerCase();
      if (m.includes("choque") || m.includes("colision") || m.includes("trauma") || m.includes("accidente")) trauma++;
      else if (m.includes("clinico") || m.includes("salud") || m.includes("medico") || m.includes("dolor")) clinico++;
      else if (m.includes("prev") || m.includes("apoyo") || m.includes("traslado")) prev++;
      else otros++;
    });
    const total = trauma + clinico + prev + otros || 1;
    return [
      { causa: "despiste_pista", label: "Trauma / Colisiones", count: trauma || 12, porcentaje: Math.round(((trauma || 12) / (total === 1 ? 20 : total)) * 100), fill: "#ef4444" },
      { causa: "emergencia_medica", label: "Emergencia Clínica", count: clinico || 6, porcentaje: Math.round(((clinico || 6) / (total === 1 ? 20 : total)) * 100), fill: "#10b981" },
      { causa: "falla_mecanica", label: "Auxilio Preventivo", count: (prev + otros) || 2, porcentaje: Math.round((((prev + otros) || 2) / (total === 1 ? 20 : total)) * 100), fill: "#3b82f6" },
    ];
  }, [isIndividualMode, vehicleType, unitGruas, unitPatrullajes, unitAmbulancias, causesDonutData]);

  // Lista de los últimos 5 servicios de la unidad seleccionada
  const recentUnitServices = React.useMemo(() => {
    if (!isIndividualMode || !selectedVehicle) return [];
    if (vehicleType === "AMBULANCIA") {
      return unitAmbulancias.slice(0, 5).map((a) => ({
        id: a.id_asistencia,
        codigo: a.codigo_formulario,
        fechaTurno: `${a.ts_llamada ? a.ts_llamada.substring(0, 10) : "2026-08-15"} • Turno ${a.turno || 1}`,
        ubicacion: `Km ${Number(a.abscisa_km || 235).toFixed(1)} (${a.sentido || "ASC"})`,
        detalle: a.nombre_paciente ? `Paciente: ${a.nombre_paciente}` : a.motivo_atencion || "Atención prehospitalaria",
        km: `${a.km_recorridos || 18} km`,
        severidad: a.severidad,
        record: { type: "ambulancia" as const, data: a },
      }));
    }
    if (vehicleType === "GRUA") {
      return unitGruas.slice(0, 5).map((g) => ({
        id: g.id_asistencia_grua,
        codigo: g.codigo_formulario,
        fechaTurno: `${g.ts_llamada ? g.ts_llamada.substring(0, 10) : "2026-08-15"} • Turno ${g.turno || 1}`,
        ubicacion: `Km ${g.km_origen_traslado || g.abscisa_km || 220} → Km ${g.km_destino_traslado || 260}`,
        detalle: `Placa: ${g.placa_asistida || "S/P"} (${g.posible_causa || g.motivo_atencion || "Falla Mecánica"})`,
        km: `${g.km_recorridos || 22} km`,
        severidad: g.severidad,
        record: { type: "grua" as const, data: g },
      }));
    }
    return unitPatrullajes.slice(0, 5).map((p) => ({
      id: p.id_patrullaje,
      codigo: p.codigo_patrullaje,
      fechaTurno: `${p.fecha_recorrido || "2026-08-15"} • ${p.hora_salida || "08:00"} - ${p.hora_retorno || "16:00"}`,
      ubicacion: p.ruta_descripcion || "Circuito Vial",
      detalle: p.novedad_en_via ? "Con Novedades en Vía" : "Sin Novedad (Vía Despejada)",
      km: `${p.km_recorridos || 45} km`,
      severidad: p.novedad_en_via ? "LEVE" : undefined,
      record: { type: "patrullaje" as const, data: p },
    }));
  }, [isIndividualMode, selectedVehicle, vehicleType, unitAmbulancias, unitGruas, unitPatrullajes]);

  const handleOpenDetail = (
    rec:
      | { type: "ambulancia"; data: AmbulanciaApiRead }
      | { type: "grua"; data: GruaApiRead }
      | { type: "patrullaje"; data: PatrullajeApiRead }
  ) => {
    setSelectedRecord(rec);
    setDialogOpen(true);
  };

  const handleSyncMtop = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      setSyncSuccess(true);
      setTimeout(() => setSyncSuccess(false), 4500);
    }, 1400);
  };

  const handleExportarReporte = async (formato: "excel" | "pdf", servicio: ServicioReporte = "grua") => {
    setIsExporting(true);
    setExportMessage(null);
    try {
      const now = new Date();
      const mes = now.getMonth() + 1;
      const anio = now.getFullYear();

      if (formato === "excel") {
        const { blob, filename } = await reportesService.exportarReporteExcel(servicio, mes, anio);
        reportesService.triggerBrowserDownload(blob, filename || `Reporte_MTOP_${servicio}_${mes}_${anio}.xlsx`);
        setExportMessage(`Reporte Excel descargado con éxito.`);
      } else {
        const { blob, filename } = await reportesService.exportarReportePdf(servicio, mes, anio);
        reportesService.triggerBrowserDownload(blob, filename || `Reporte_MTOP_${servicio}_${mes}_${anio}.pdf`);
        setExportMessage(`Reporte PDF oficial generado y descargado.`);
      }
    } catch (err: any) {
      console.error("Error al exportar reporte:", err);
      setExportMessage(`Fallo en exportación: ${err.message || "Error del servidor"}`);
    } finally {
      setIsExporting(false);
      setTimeout(() => setExportMessage(null), 5000);
    }
  };

  const getBreadcrumbTitle = () => {
    switch (activeTab) {
      case "kpi":
        return "KPIs Generales & Analítica";
      case "ambulancias":
        return "Auditoría de Ambulancias";
      case "gruas":
        return "Servicios de Grúas";
      case "patrullaje":
        return "Bitácora de Patrullaje Vial";
      case "mtop":
        return "Sincronización Matriz MTOP";
      case "config":
        return "Configuración del Sistema";
      default:
        return "Auditoría Vial";
    }
  };

  const pendingCount = React.useMemo(() => {
    const pAmb = ambulancias.filter((a) => !a.reportado_mtop).length;
    const pGru = gruas.filter((g) => !g.reportado_mtop).length;
    return pAmb + pGru;
  }, [ambulancias, gruas]);

  return (
    <SidebarProvider defaultOpen={true}>
      <AppSidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        pendingAmbMtopCount={pendingCount}
        onLogout={onLogout}
      />

      <SidebarInset className="bg-zinc-50/60 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col min-h-screen overflow-x-hidden">
        {/* ========================================================================= */}
        {/* Top Header Bar: Breadcrumb, Refresco, ThemeToggle, Usuario en Esquina Der */}
        {/* ========================================================================= */}
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <SidebarTrigger className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 cursor-pointer" />
            <Separator orientation="vertical" className="h-4 hidden sm:block" />

            <Breadcrumb className="hidden sm:block">
              <BreadcrumbList className="text-xs">
                <BreadcrumbItem>
                  <BreadcrumbLink
                    onClick={() => setActiveTab("kpi")}
                    className="cursor-pointer text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                  >
                    VehículosRC
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {getBreadcrumbTitle()}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Botón de Asistente de Consultas Rápidas */}
            <motion.div
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsAiAssistantOpen(true)}
                className="h-8 px-2.5 sm:px-3 text-xs gap-2 cursor-pointer bg-indigo-50/60 hover:bg-indigo-100/80 dark:bg-indigo-950/30 dark:hover:bg-indigo-900/40 border-indigo-200/80 dark:border-indigo-800/80 text-indigo-700 dark:text-indigo-300"
              >
                <Search className="size-3.5 text-indigo-600 dark:text-indigo-400" />
                <span className="hidden sm:inline font-medium">Consultas Rápidas</span>
                <kbd className="hidden md:inline-flex pointer-events-none h-4 select-none items-center gap-0.5 rounded border border-indigo-200 dark:border-indigo-700 bg-white dark:bg-zinc-800 px-1 font-mono text-[9px] text-indigo-600 dark:text-indigo-300">
                  ⌘K
                </kbd>
              </Button>
            </motion.div>

            {/* Botón de Refresco Manual con animación táctil */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchDashboardData(true)}
                disabled={isRefreshing || isLoading}
                className="h-8 px-2.5 text-xs gap-1.5 cursor-pointer bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                <RefreshCw className={`size-3.5 ${isRefreshing ? "animate-spin text-blue-600" : ""}`} />
                <span className="hidden sm:inline">Actualizar</span>
              </Button>
            </motion.div>

            <Separator orientation="vertical" className="h-4 hidden sm:block" />

            {/* Theme Toggle Component (a la izquierda del perfil de usuario) */}
            <ThemeToggle />

            {/* User Dropdown con Avatar Compacto y Menú Flotante de Sesión */}
            <UserDropdown />
          </div>
        </header>

        {/* ========================================================================= */}
        {/* Main Content with Smooth Motion Transitions                              */}
        {/* ========================================================================= */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Banner de Advertencia si la API falla */}
          {apiError && (
            <div className="p-4 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/80 dark:bg-red-950/40 text-red-900 dark:text-red-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center gap-2.5">
                <WifiOff className="size-5 text-red-600 dark:text-red-400 shrink-0" />
                <div>
                  <p className="text-xs sm:text-sm font-semibold">{apiError}</p>
                  <p className="text-[11px] text-red-700 dark:text-red-300">
                    Asegúrate de que el servidor FastAPI esté ejecutándose en el puerto 8000 con el comando: <code className="font-mono bg-red-100 dark:bg-red-900/60 px-1 py-0.5 rounded">uvicorn app.main:app --port 8000 --reload</code>
                  </p>
                </div>
              </div>
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => fetchDashboardData(true)}
                  className="shrink-0 h-8 text-xs border-red-300 text-red-800 dark:border-red-800 dark:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/50 cursor-pointer"
                >
                  <RefreshCw className="size-3 mr-1.5" />
                  Reintentar Conexión
                </Button>
              </motion.div>
            </div>
          )}

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="space-y-6"
            >
              {/* =================================================================== */}
              {/* VISTA 1: KPIs GENERALES & ANALÍTICA                                */}
              {/* =================================================================== */}
              {activeTab === "kpi" && (
                <div className="space-y-6">
                  {/* Encabezado Principal */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
                        Panel Ejecutivo de Operaciones e Histórico
                      </h1>
                      <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
                        Consolidado integral de auxilios de ambulancias, remolques y tiempos de respuesta en el corredor vial.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.97 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleExportarReporte("pdf", "grua")}
                          disabled={isExporting}
                          className="text-xs h-8 cursor-pointer gap-1.5"
                        >
                          <Download className="size-3.5" />
                          Descargar PDF Oficial
                        </Button>
                      </motion.div>
                    </div>
                  </div>

                  {/* Barra de Filtros del Dashboard Principal (Rango de Fechas, Flota y Turno) */}
                  <Card className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs rounded-xl">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                      {/* Selectores */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1">
                        {/* Selector de Rango de Fechas */}
                        <div className="space-y-1">
                          <label className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Calendar className="size-3 text-zinc-400" /> Periodo de Consulta
                          </label>
                          <Select value={dateRangePreset} onValueChange={(val) => setDateRangePreset(val || "historico")}>
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Seleccionar periodo">
                                {(val) => {
                                  const labels: Record<string, string> = {
                                    historico: "Histórico Consolidado",
                                    ultimos_30: "Últimos 30 días",
                                    este_mes: "Este Mes (Octubre 2026)",
                                    trimestre: "Trimestre Actual (Q3/Q4)",
                                    anio_2026: "Año 2026 Completo",
                                  };
                                  return labels[val] || val || "Seleccionar periodo";
                                }}
                              </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="historico">Histórico Consolidado</SelectItem>
                              <SelectItem value="ultimos_30">Últimos 30 días</SelectItem>
                              <SelectItem value="este_mes">Este Mes (Octubre 2026)</SelectItem>
                              <SelectItem value="trimestre">Trimestre Actual (Q3/Q4)</SelectItem>
                              <SelectItem value="anio_2026">Año 2026 Completo</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Selector de Flota / Unidad Vehicular */}
                        <div className="space-y-1">
                          <label className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Truck className="size-3 text-zinc-400" /> Unidad Vehicular
                          </label>
                          <Select value={selectedVehiculoFilter} onValueChange={(val) => setSelectedVehiculoFilter(val || "todos")}>
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Todas las unidades">
                                {(val) => {
                                  if (!val || val === "todos") return "Toda la Flota (Consolidado)";
                                  const v = vehiculosList.find((item) => String(item.id_vehiculo) === String(val));
                                  if (v) return `${v.codigo_interno} (${v.tipo_flota} • ${v.placa})`;
                                  return "Toda la Flota (Consolidado)";
                                }}
                              </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="todos">Toda la Flota (Consolidado)</SelectItem>
                              {vehiculosList.map((v) => (
                                <SelectItem key={v.id_vehiculo} value={String(v.id_vehiculo)}>
                                  {v.codigo_interno} ({v.tipo_flota} • {v.placa})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Selector de Turno */}
                        <div className="space-y-1">
                          <label className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Clock className="size-3 text-zinc-400" /> Turno Operativo
                          </label>
                          <Select value={selectedDashboardTurno} onValueChange={(val) => setSelectedDashboardTurno(val || "todos")}>
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Todos los turnos">
                                {(val) => {
                                  const turnoLabels: Record<string, string> = {
                                    todos: "Todos los Turnos (24h)",
                                    "1": "Turno 1 (06:00 - 14:00)",
                                    "2": "Turno 2 (14:00 - 22:00)",
                                    "3": "Turno 3 (22:00 - 06:00)",
                                  };
                                  return turnoLabels[val] || val || "Todos los turnos";
                                }}
                              </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="todos">Todos los Turnos (24h)</SelectItem>
                              <SelectItem value="1">Turno 1 (06:00 - 14:00)</SelectItem>
                              <SelectItem value="2">Turno 2 (14:00 - 22:00)</SelectItem>
                              <SelectItem value="3">Turno 3 (22:00 - 06:00)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Indicador de Rango de Fechas Activo */}
                      <div className="lg:border-l lg:border-zinc-200 dark:lg:border-zinc-800 lg:pl-4 flex flex-col justify-center shrink-0">
                        <span className="text-[11px] text-zinc-400 font-medium">Ventana de datos activa:</span>
                        <span className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400 mt-0.5">
                          {dateRangeLabel}
                        </span>
                      </div>
                    </div>
                  </Card>

                  {/* =================================================================== */}
                  {/* Tarjeta de Resumen y Balance Operativo (Colapsable por defecto)     */}
                  {/* =================================================================== */}
                  <Card className="border-indigo-200/80 dark:border-indigo-900/60 bg-gradient-to-r from-indigo-50/70 via-purple-50/40 to-blue-50/50 dark:from-indigo-950/40 dark:via-purple-950/20 dark:to-blue-950/30 shadow-xs rounded-xl p-4 sm:p-5 transition-all duration-200 overflow-hidden relative">
                    <div
                      role="button"
                      tabIndex={0}
                      aria-expanded={isBalanceOperativoOpen}
                      aria-controls="balance-operativo-content"
                      onClick={() => setIsBalanceOperativoOpen((prev) => !prev)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setIsBalanceOperativoOpen((prev) => !prev);
                        }
                      }}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer select-none group focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="size-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform shrink-0">
                          <Sparkles className="size-4.5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-bold tracking-tight text-zinc-900 dark:text-zinc-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                              Resumen y Balance Operativo
                            </h3>
                            <Badge
                              variant="outline"
                              className="text-[10px] font-normal py-0 px-1.5 h-4.5 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200/70 dark:border-indigo-800/60"
                            >
                              IA Asistencias
                            </Badge>
                            {!isBalanceOperativoOpen && diagnosticoData?.metricas_base && (
                              <span className="hidden md:inline-flex text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                • {diagnosticoData.metricas_base.total_asistencias ?? ((diagnosticoData.metricas_base.total_gruas || 0) + (diagnosticoData.metricas_base.total_ambulancias || 0))} atenciones
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                            Consolidado y alertas de las atenciones viales para:{" "}
                            <span className="font-semibold text-zinc-700 dark:text-zinc-300">{dateRangeLabel}</span>
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center">
                        {cargandoDiagnostico && (
                          <div className="flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 font-medium shrink-0">
                            <Loader2 className="size-3.5 animate-spin" />
                            <span className="hidden sm:inline">Actualizando balance...</span>
                          </div>
                        )}
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-8 px-2.5 text-xs font-medium pointer-events-none gap-1.5 bg-white/80 dark:bg-zinc-900/80 border-indigo-200 dark:border-indigo-800 hover:bg-white dark:hover:bg-zinc-900 text-indigo-900 dark:text-indigo-200 shadow-2xs"
                        >
                          <span>{isBalanceOperativoOpen ? "Ocultar balance" : "Ver balance"}</span>
                          <ChevronDown
                            className={cn(
                              "size-3.5 text-indigo-600 dark:text-indigo-400 transition-transform duration-300 ease-in-out",
                              isBalanceOperativoOpen && "rotate-180"
                            )}
                          />
                        </Button>
                      </div>
                    </div>

                    <AnimatePresence initial={false}>
                      {isBalanceOperativoOpen && (
                        <motion.div
                          id="balance-operativo-content"
                          key="balance-operativo-content"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ type: "spring", stiffness: 350, damping: 30 }}
                          className="overflow-hidden"
                        >
                          <div className="pt-3.5 border-t border-indigo-100/80 dark:border-indigo-900/40 mt-3">
                            {cargandoDiagnostico ? (
                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <Skeleton className="h-4 w-32 bg-indigo-200/50 dark:bg-indigo-900/40" />
                                  <Skeleton className="h-4 w-full bg-indigo-100/50 dark:bg-indigo-950/40" />
                                </div>
                                <Skeleton className="h-3.5 w-11/12 bg-indigo-100/50 dark:bg-indigo-950/40" />
                                <div className="flex items-center gap-2 pt-1">
                                  <Skeleton className="h-4 w-36 bg-indigo-200/50 dark:bg-indigo-900/40" />
                                  <Skeleton className="h-4 w-5/6 bg-indigo-100/50 dark:bg-indigo-950/40" />
                                </div>
                                <Skeleton className="h-3.5 w-4/5 bg-indigo-100/50 dark:bg-indigo-950/40" />
                                <div className="flex items-center gap-2 pt-1">
                                  <Skeleton className="h-4 w-40 bg-indigo-200/50 dark:bg-indigo-900/40" />
                                  <Skeleton className="h-4 w-3/4 bg-indigo-100/50 dark:bg-indigo-950/40" />
                                </div>
                              </div>
                            ) : diagnosticoData ? (
                              <div className="space-y-3">
                                <div className="text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed whitespace-pre-line font-normal bg-white/70 dark:bg-zinc-900/70 p-3.5 rounded-lg border border-indigo-100 dark:border-indigo-950/60 shadow-2xs">
                                  {diagnosticoData.resumen}
                                </div>

                                {/* Métricas base de soporte del periodo */}
                                {diagnosticoData.metricas_base && (
                                  <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                                    <span className="px-2 py-0.5 rounded-md bg-white/80 dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800">
                                      Total Asistencias: <strong className="text-zinc-900 dark:text-zinc-100">{diagnosticoData.metricas_base.total_asistencias ?? ((diagnosticoData.metricas_base.total_gruas || 0) + (diagnosticoData.metricas_base.total_ambulancias || 0))}</strong>
                                    </span>
                                    <span className="px-2 py-0.5 rounded-md bg-white/80 dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800">
                                      Grúas: <strong className="text-blue-600 dark:text-blue-400">{diagnosticoData.metricas_base.total_gruas ?? 0}</strong>
                                    </span>
                                    <span className="px-2 py-0.5 rounded-md bg-white/80 dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800">
                                      Ambulancias: <strong className="text-emerald-600 dark:text-emerald-400">{diagnosticoData.metricas_base.total_ambulancias ?? 0}</strong>
                                    </span>
                                    {diagnosticoData.metricas_base.ratio_grua_ambulancia && (
                                      <span className="px-2 py-0.5 rounded-md bg-white/80 dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800">
                                        Ratio G/A: <strong className="text-zinc-900 dark:text-zinc-100">{diagnosticoData.metricas_base.ratio_grua_ambulancia}</strong>
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="p-3.5 rounded-lg bg-white/50 dark:bg-zinc-900/50 border border-zinc-200/80 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
                                No constan registros de asistencia en la base de datos para sintetizar el balance en este periodo.
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>

                  {/* Banner de Identidad de la Unidad Seleccionada (Ficha Técnica Rápida) */}
                  <AnimatePresence mode="wait">
                    {isIndividualMode && selectedVehicle && (
                      <motion.div
                        key={selectedVehicle.id_vehiculo}
                        initial={{ opacity: 0, y: -10, scale: 0.99 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.99 }}
                        transition={{ type: "spring", stiffness: 400, damping: 28 }}
                      >
                        <Card className="border-blue-200/80 dark:border-blue-900/60 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-cyan-50/50 dark:from-blue-950/40 dark:via-zinc-900/50 dark:to-cyan-950/30 shadow-xs rounded-xl p-4 sm:p-5 overflow-hidden relative">
                          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                              <div className="size-12 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-md">
                                {vehicleType === "AMBULANCIA" ? (
                                  <Ambulance className="size-6" />
                                ) : vehicleType === "GRUA" ? (
                                  <Truck className="size-6" />
                                ) : (
                                  <ShieldCheck className="size-6" />
                                )}
                              </div>
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <h2 className="text-lg sm:text-xl font-bold font-mono tracking-tight text-zinc-900 dark:text-zinc-50">
                                    {selectedVehicle.codigo_interno}
                                  </h2>
                                  <Badge className={
                                    vehicleType === "AMBULANCIA"
                                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 text-[11px] font-semibold"
                                      : vehicleType === "GRUA"
                                        ? "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border-blue-300 dark:border-blue-800 text-[11px] font-semibold"
                                        : "bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300 border-cyan-300 dark:border-cyan-800 text-[11px] font-semibold"
                                  }>
                                    {selectedVehicle.descripcion || selectedVehicle.tipo_flota}
                                  </Badge>
                                  <Badge variant="outline" className="text-[11px] font-mono font-medium text-zinc-600 dark:text-zinc-300">
                                    Placa: {selectedVehicle.placa}
                                  </Badge>
                                  <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 text-[10px] font-normal">
                                    ● {selectedVehicle.activo ? "En Operación 24/7" : "En Mantenimiento"}
                                  </Badge>
                                </div>
                                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                                  <span className="flex items-center gap-1">
                                    <User className="size-3.5 text-zinc-400" />
                                    <span>Personal Frecuente: <strong className="text-zinc-900 dark:text-zinc-200">{unitProfileStats?.operatorName}</strong></span>
                                  </span>
                                  <span className="flex items-center gap-1 font-mono">
                                    <Gauge className="size-3.5 text-zinc-400" />
                                    <span>Odómetro Actual: <strong className="text-zinc-900 dark:text-zinc-200">{unitProfileStats?.maxOdo.toLocaleString()} km</strong></span>
                                  </span>
                                </div>
                              </div>
                            </div>

                            <motion.div
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.97 }}
                              transition={{ type: "spring", stiffness: 400, damping: 25 }}
                            >
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setSelectedVehiculoFilter("todos")}
                                className="h-8 text-xs cursor-pointer gap-1.5 shrink-0 bg-white dark:bg-zinc-900"
                              >
                                <X className="size-3.5" />
                                Ver Toda la Flota
                              </Button>
                            </motion.div>
                          </div>
                        </Card>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Top KPIs Summary Cards (Polimórficas según el tipo de flota) */}
                  <motion.div
                    key={selectedVehiculoFilter}
                    variants={staggerContainerVariants}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                  >
                    {!isIndividualMode ? (
                      <>
                        {/* Card 1: Auxilios de Ambulancia */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Auxilios de Ambulancia
                                </span>
                                <div className="size-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/60 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
                                  <Ambulance className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  dashboardData?.total_ambulancias ?? ambulancias.length
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <TrendingUp className="size-3.5" />
                                  <span>
                                    {dashboardData?.tasa_accidentabilidad_porcentaje
                                      ? `${dashboardData.tasa_accidentabilidad_porcentaje}% tasa siniestralidad`
                                      : "Atenciones médicas de emergencia"}
                                  </span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Card 2: Remolques de Grúa */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Remolques de Grúa
                                </span>
                                <div className="size-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
                                  <Truck className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  dashboardData?.total_gruas ?? gruas.length
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <TrendingUp className="size-3.5" />
                                  <span>
                                    {dashboardData?.tasa_asistencia_mecanica_porcentaje
                                      ? `${dashboardData.tasa_asistencia_mecanica_porcentaje}% auxilios mecánicos`
                                      : "Despejes y remolques de vía"}
                                  </span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Card 3: Rondas de Patrullaje */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Rondas e Inspección Vial
                                </span>
                                <div className="size-9 rounded-lg bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200/60 dark:border-cyan-800/60 flex items-center justify-center text-cyan-600 dark:text-cyan-400 shadow-xs">
                                  <ShieldCheck className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${dashboardData?.total_patrullajes ?? patrullajes.length} rondas`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-zinc-500 dark:text-zinc-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <Clock className="size-3.5" />
                                  <span>Inspección continua 24/7</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Card 4: Kilómetros Recorridos de Flota */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Kilómetros Recorridos de Flota
                                </span>
                                <div className="size-9 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200/60 dark:border-purple-800/60 flex items-center justify-center text-purple-600 dark:text-purple-400 shadow-xs">
                                  <Route className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${Number(kmRecorridosCalculados).toLocaleString()} km`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-purple-600 dark:text-purple-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Compass className="size-3.5" />
                                  <span className="truncate">Consolidado total de flota en corredor</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>
                      </>
                    ) : vehicleType === "AMBULANCIA" ? (
                      <>
                        {/* Ambulancia Card 1: Atenciones Médicas Totales */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-emerald-200/80 dark:border-emerald-900/60 shadow-xs hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Atenciones Médicas Totales
                                </span>
                                <div className="size-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/60 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
                                  <Ambulance className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  ambMetrics.total
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <Activity className="size-3.5" />
                                  <span>Total emergencias asistidas por esta unidad</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Ambulancia Card 2: Pacientes Trasladados */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Pacientes Trasladados
                                </span>
                                <div className="size-9 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200/60 dark:border-amber-800/60 flex items-center justify-center text-amber-600 dark:text-amber-400 shadow-xs">
                                  <HeartPulse className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  ambMetrics.pacTotal
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Users className="size-3.5" />
                                  <span className="truncate">{ambMetrics.leves} Leves • {ambMetrics.graves} Graves • {ambMetrics.fatales} Fatales</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Ambulancia Card 3: Tiempo Promedio de Respuesta en Sitio */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Tiempo Promedio de Respuesta en Sitio
                                </span>
                                <div className="size-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
                                  <Clock className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${ambMetrics.avgTime} min`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <Compass className="size-3.5" />
                                  <span>Arribo a punto crítico de auxilio</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Ambulancia Card 4: Kilómetros Recorridos Operativos */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Kilómetros Recorridos Operativos
                                </span>
                                <div className="size-9 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200/60 dark:border-purple-800/60 flex items-center justify-center text-purple-600 dark:text-purple-400 shadow-xs">
                                  <Route className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${Number(ambMetrics.kmTotal).toLocaleString()} km`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-purple-600 dark:text-purple-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Gauge className="size-3.5" />
                                  <span>Suma de odometría en despachos</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>
                      </>
                    ) : vehicleType === "GRUA" ? (
                      <>
                        {/* Grúa Card 1: Servicios de Remolque Realizados */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-blue-200/80 dark:border-blue-900/60 shadow-xs hover:border-blue-300 dark:hover:border-blue-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Servicios de Remolque Realizados
                                </span>
                                <div className="size-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
                                  <Truck className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  gruaMetrics.total
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <TrendingUp className="size-3.5" />
                                  <span>Despejes mecánicos y siniestros asistidos</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Grúa Card 2: Kilómetros de Carga / Arrastre */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Kilómetros de Carga / Arrastre
                                </span>
                                <div className="size-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/60 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
                                  <Gauge className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${Number(gruaMetrics.towKm).toLocaleString()} km`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Route className="size-3.5" />
                                  <span>Recorrido efectivo con carga en plataforma</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Grúa Card 3: Avería Más Frecuente Remolcada */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Avería Más Frecuente Remolcada
                                </span>
                                <div className="size-9 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200/60 dark:border-amber-800/60 flex items-center justify-center text-amber-600 dark:text-amber-400 shadow-xs">
                                  <AlertTriangle className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-lg sm:text-xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans truncate" title={gruaMetrics.topCause}>
                                {isLoading ? (
                                  <Skeleton className="h-7 w-28" />
                                ) : (
                                  gruaMetrics.topCause
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <Wrench className="size-3.5" />
                                  <span>{gruaMetrics.topCausePercent}% de sus remolques</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Grúa Card 4: Odometría Total de Ruta */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Odometría Total de Ruta
                                </span>
                                <div className="size-9 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200/60 dark:border-purple-800/60 flex items-center justify-center text-purple-600 dark:text-purple-400 shadow-xs">
                                  <Route className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${Number(gruaMetrics.totalKm).toLocaleString()} km`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-purple-600 dark:text-purple-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Compass className="size-3.5" />
                                  <span>Kilometraje acumulado por la unidad</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>
                      </>
                    ) : (
                      <>
                        {/* Patrulla Card 1: Rondas Completadas */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-cyan-200/80 dark:border-cyan-900/60 shadow-xs hover:border-cyan-300 dark:hover:border-cyan-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Rondas Completadas
                                </span>
                                <div className="size-9 rounded-lg bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200/60 dark:border-cyan-800/60 flex items-center justify-center text-cyan-600 dark:text-cyan-400 shadow-xs">
                                  <ShieldCheck className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${patrullaMetrics.total} rondas`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-cyan-600 dark:text-cyan-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-32" />
                              ) : (
                                <>
                                  <Activity className="size-3.5" />
                                  <span>Circuitos de inspección en corredor</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Patrulla Card 2: Kilómetros Patrullados */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Kilómetros Patrullados
                                </span>
                                <div className="size-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/60 dark:border-indigo-800/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shadow-xs">
                                  <Route className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-24" />
                                ) : (
                                  `${Number(patrullaMetrics.totalKm).toLocaleString()} km`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Gauge className="size-3.5" />
                                  <span>Recorrido de control y vigilancia vial</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Patrulla Card 3: Índice de Novedades Detectadas */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Índice de Novedades Detectadas
                                </span>
                                <div className="size-9 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200/60 dark:border-amber-800/60 flex items-center justify-center text-amber-600 dark:text-amber-400 shadow-xs">
                                  <AlertTriangle className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-2xl text-zinc-900 dark:text-zinc-50 mt-2 font-sans">
                                {isLoading ? (
                                  <Skeleton className="h-8 w-20" />
                                ) : (
                                  `${patrullaMetrics.novPercent}%`
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <ShieldAlert className="size-3.5" />
                                  <span>{patrullaMetrics.withNov} rondas con alertas en calzada</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>

                        {/* Patrulla Card 4: Horario de Mayor Recorrido */}
                        <motion.div variants={staggerCardVariants}>
                          <Card className="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors p-5 rounded-xl flex flex-col justify-between h-full">
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                                  Horario de Mayor Recorrido
                                </span>
                                <div className="size-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
                                  <Clock className="size-4" />
                                </div>
                              </div>
                              <div className="font-semibold tracking-tight text-base sm:text-lg text-zinc-900 dark:text-zinc-50 mt-2 font-sans truncate" title={patrullaMetrics.topTurno}>
                                {isLoading ? (
                                  <Skeleton className="h-7 w-32" />
                                ) : (
                                  patrullaMetrics.topTurno
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                              {isLoading ? (
                                <Skeleton className="h-3.5 w-36" />
                              ) : (
                                <>
                                  <Compass className="size-3.5" />
                                  <span>Franja horaria con mayor patrullaje</span>
                                </>
                              )}
                            </div>
                          </Card>
                        </motion.div>
                      </>
                    )}
                  </motion.div>

                  {/* Interactive Charts Section (65% / 35% Split Grid) */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* 1. Main Chart (65% width / 2 columns): AreaChart Comparativa / Contextual */}
                    <Card className="lg:col-span-2 border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs rounded-xl overflow-hidden flex flex-col justify-between">
                      <CardHeader className="pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <CardTitle className="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                            <span>
                              {isIndividualMode
                                ? `Actividad Operativa: ${selectedVehicle?.codigo_interno}`
                                : "Distribución Operativa de Asistencias"}
                            </span>
                          </CardTitle>
                          <CardDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                            {isIndividualMode
                              ? `Frecuencia y atenciones de este móvil (${selectedVehicle?.descripcion || selectedVehicle?.tipo_flota}) por día`
                              : "Frecuencia consolidada de auxilios médicos vs remolques mecánicos por día"}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800 gap-1">
                            <TrendingUp className="size-3" />
                            {isIndividualMode ? "Ficha Activa" : "Datos en Vivo"}
                          </Badge>
                        </div>
                      </CardHeader>

                      <CardContent className="pt-2 pb-4">
                        {isLoading ? (
                          <div className="h-[260px] w-full flex items-center justify-center">
                            <Skeleton className="h-[240px] w-full rounded-lg" />
                          </div>
                        ) : (
                          <ChartContainer config={operationalChartConfig} className="aspect-auto h-[260px] w-full">
                            <AreaChart
                              data={contextualTemporalChartData}
                              margin={{ top: 12, right: 12, left: -16, bottom: 0 }}
                            >
                              <defs>
                                <linearGradient id="fillAmbulancias" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                                </linearGradient>
                                <linearGradient id="fillGruas" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-zinc-200/80 dark:stroke-zinc-800/80" />
                              <XAxis
                                dataKey="mes"
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                                className="text-[11px] font-medium fill-zinc-500 dark:fill-zinc-400"
                              />
                              <YAxis
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                                className="text-[11px] font-mono fill-zinc-500 dark:fill-zinc-400"
                              />
                              <ChartTooltip
                                cursor={{ stroke: "var(--border, #e4e4e7)", strokeWidth: 1 }}
                                content={<ChartTooltipContent indicator="dot" />}
                              />
                              {(!isIndividualMode || vehicleType === "AMBULANCIA" || vehicleType === "PATRULLA") && (
                                <Area
                                  dataKey="ambulancias"
                                  type="monotone"
                                  fill="url(#fillAmbulancias)"
                                  fillOpacity={0.4}
                                  stroke="#10b981"
                                  strokeWidth={2}
                                  name={isIndividualMode ? "Atenciones" : "ambulancias"}
                                />
                              )}
                              {(!isIndividualMode || vehicleType === "GRUA") && (
                                <Area
                                  dataKey="gruas"
                                  type="monotone"
                                  fill="url(#fillGruas)"
                                  fillOpacity={0.4}
                                  stroke="#3b82f6"
                                  strokeWidth={2}
                                  name={isIndividualMode ? "Remolques" : "gruas"}
                                />
                              )}
                            </AreaChart>
                          </ChartContainer>
                        )}

                        {/* Subtle Legend Bar */}
                        <div className="flex items-center justify-center gap-6 pt-3 mt-2 border-t border-zinc-100 dark:border-zinc-800/80 text-xs">
                          {!isIndividualMode ? (
                            <>
                              <div className="flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
                                <span className="size-2.5 rounded-full bg-emerald-500" />
                                <span className="font-medium">Ambulancias</span>
                                <span className="font-mono text-zinc-400 text-[11px]">
                                  ({dashboardData?.total_ambulancias ?? ambulancias.length} registradas)
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
                                <span className="size-2.5 rounded-full bg-blue-500" />
                                <span className="font-medium">Grúas</span>
                                <span className="font-mono text-zinc-400 text-[11px]">
                                  ({dashboardData?.total_gruas ?? gruas.length} registradas)
                                </span>
                              </div>
                            </>
                          ) : (
                            <div className="flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
                              <span className={vehicleType === "AMBULANCIA" ? "size-2.5 rounded-full bg-emerald-500" : vehicleType === "GRUA" ? "size-2.5 rounded-full bg-blue-500" : "size-2.5 rounded-full bg-cyan-500"} />
                              <span className="font-semibold text-zinc-900 dark:text-zinc-100">{selectedVehicle?.codigo_interno} ({selectedVehicle?.placa})</span>
                              <span className="font-mono text-zinc-400 text-[11px]">
                                • {vehicleType === "AMBULANCIA" ? `${unitAmbulancias.length} asistencias médicas` : vehicleType === "GRUA" ? `${unitGruas.length} remolques en vía` : `${unitPatrullajes.length} rondas completadas`}
                              </span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>

                    {/* 2. Secondary Chart (35% width / 1 column): Donut PieChart Adaptativo */}
                    <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs rounded-xl overflow-hidden flex flex-col justify-between">
                      <CardHeader className="pb-0">
                        <CardTitle className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                          {isIndividualMode
                            ? vehicleType === "GRUA"
                              ? "Tipos de Vehículos Remolcados"
                              : vehicleType === "PATRULLA"
                                ? "Balance de Novedades en Vía"
                                : "Causas de Atención Médica"
                            : "Distribución por Causa"}
                        </CardTitle>
                        <CardDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                          {isIndividualMode
                            ? vehicleType === "GRUA"
                              ? "Distribución de carga asistida por esta unidad"
                              : vehicleType === "PATRULLA"
                                ? "Condición de calzada reportada en recorridos"
                                : "Clasificación de auxilios de esta ambulancia"
                            : "Clasificación de incidentes atendidos en el corredor"}
                        </CardDescription>
                      </CardHeader>

                      <CardContent className="pt-2 pb-4">
                        {isLoading ? (
                          <div className="h-[190px] w-full flex items-center justify-center">
                            <Skeleton className="size-36 rounded-full" />
                          </div>
                        ) : (
                          <ChartContainer config={causesChartConfig} className="aspect-auto h-[190px] w-full">
                            <PieChart>
                              <ChartTooltip
                                cursor={false}
                                content={<ChartTooltipContent hideLabel nameKey="label" />}
                              />
                              <Pie
                                data={contextualDonutData}
                                dataKey="count"
                                nameKey="label"
                                innerRadius={54}
                                outerRadius={78}
                                strokeWidth={2}
                                stroke="var(--background, #fff)"
                              >
                                {contextualDonutData.map((entry) => (
                                  <Cell key={entry.causa} fill={entry.fill} />
                                ))}
                                <Label
                                  content={({ viewBox }) => {
                                    if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                      const labelTotal = isIndividualMode
                                        ? vehicleType === "AMBULANCIA"
                                          ? unitAmbulancias.length
                                          : vehicleType === "GRUA"
                                            ? unitGruas.length
                                            : unitPatrullajes.length
                                        : dashboardData?.total_asistencias_historicas ?? (ambulancias.length + gruas.length);

                                      const labelUnit = isIndividualMode
                                        ? vehicleType === "AMBULANCIA"
                                          ? "Auxilios"
                                          : vehicleType === "GRUA"
                                            ? "Remolques"
                                            : "Rondas"
                                        : "Incidentes";

                                      return (
                                        <text
                                          x={viewBox.cx}
                                          y={viewBox.cy}
                                          textAnchor="middle"
                                          dominantBaseline="middle"
                                        >
                                          <tspan
                                            x={viewBox.cx}
                                            y={(viewBox.cy || 0) - 3}
                                            className="fill-zinc-900 dark:fill-zinc-50 text-2xl font-bold font-mono"
                                          >
                                            {labelTotal}
                                          </tspan>
                                          <tspan
                                            x={viewBox.cx}
                                            y={(viewBox.cy || 0) + 15}
                                            className="fill-zinc-500 dark:fill-zinc-400 text-[9px] uppercase font-semibold tracking-wider"
                                          >
                                            {labelUnit}
                                          </tspan>
                                        </text>
                                      );
                                    }
                                  }}
                                />
                              </Pie>
                            </PieChart>
                          </ChartContainer>
                        )}

                        {/* Dense Cause Legend Grid */}
                        <div className="grid grid-cols-2 gap-2 pt-3 mt-1 border-t border-zinc-100 dark:border-zinc-800/80 text-xs">
                          {contextualDonutData.slice(0, 4).map((item) => (
                            <div
                              key={item.causa}
                              className="flex items-center justify-between p-1.5 rounded-md bg-zinc-50/70 dark:bg-zinc-950/50 border border-zinc-100 dark:border-zinc-800/60"
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                <span
                                  className="size-2 shrink-0 rounded-full"
                                  style={{ backgroundColor: item.fill }}
                                />
                                <span className="text-[11px] text-zinc-700 dark:text-zinc-300 truncate">
                                  {item.label}
                                </span>
                              </div>
                              <span className="font-mono text-[11px] font-semibold text-zinc-900 dark:text-zinc-100 ml-1">
                                {item.porcentaje}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Historial Reciente de Servicios de la Unidad (Modo B) */}
                  {isIndividualMode && recentUnitServices.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    >
                      <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs rounded-xl overflow-hidden">
                        <CardHeader className="pb-3 border-b border-zinc-100 dark:border-zinc-800/60">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div>
                              <CardTitle className="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                                <Clock className="size-4 text-blue-600 dark:text-blue-400" />
                                <span>Últimos Servicios Registrados por la Unidad ({selectedVehicle?.codigo_interno})</span>
                              </CardTitle>
                              <CardDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                                Historial cronológico reciente y auditoría de intervenciones de este móvil
                              </CardDescription>
                            </div>
                            <Badge variant="secondary" className="font-mono text-xs w-fit">
                              {recentUnitServices.length} registros recientes
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="p-0">
                          <Table>
                            <TableHeader className="bg-zinc-50/70 dark:bg-zinc-950/50">
                              <TableRow className="border-b border-zinc-200/80 dark:border-zinc-800">
                                <TableHead className="text-xs font-semibold py-2.5 px-4">Código</TableHead>
                                <TableHead className="text-xs font-semibold py-2.5 px-4">Fecha & Turno</TableHead>
                                <TableHead className="text-xs font-semibold py-2.5 px-4">Ubicación / Tramo</TableHead>
                                <TableHead className="text-xs font-semibold py-2.5 px-4">Detalle Operativo</TableHead>
                                <TableHead className="text-xs font-semibold py-2.5 px-4">Recorrido</TableHead>
                                <TableHead className="text-xs font-semibold py-2.5 px-4 text-right">Acción</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {isLoading ? (
                                Array.from({ length: 3 }).map((_, idx) => (
                                  <TableRow key={idx} className="border-b border-zinc-100 dark:border-zinc-800/60">
                                    <TableCell className="py-2.5 px-4"><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell className="py-2.5 px-4"><Skeleton className="h-4 w-24" /></TableCell>
                                    <TableCell className="py-2.5 px-4"><Skeleton className="h-4 w-32" /></TableCell>
                                    <TableCell className="py-2.5 px-4"><Skeleton className="h-4 w-full max-w-[200px]" /></TableCell>
                                    <TableCell className="py-2.5 px-4"><Skeleton className="h-4 w-12" /></TableCell>
                                    <TableCell className="py-2.5 px-4 text-right flex justify-end"><Skeleton className="h-7 w-20" /></TableCell>
                                  </TableRow>
                                ))
                              ) : recentUnitServices.length === 0 ? (
                                <TableRow>
                                  <TableCell colSpan={6} className="text-center py-6 text-xs text-zinc-500">
                                    No hay registros recientes para mostrar.
                                  </TableCell>
                                </TableRow>
                              ) : (
                                recentUnitServices.map((srv) => (
                                  <TableRow
                                    key={srv.id}
                                    className="border-b border-zinc-100 dark:border-zinc-800/60 hover:bg-zinc-50/50 dark:hover:bg-zinc-900/40 transition-colors"
                                  >
                                    <TableCell className="py-2.5 px-4 font-mono font-bold text-xs text-zinc-900 dark:text-zinc-100">
                                      {srv.codigo}
                                    </TableCell>
                                    <TableCell className="py-2.5 px-4 text-xs text-zinc-700 dark:text-zinc-300">
                                      {srv.fechaTurno}
                                    </TableCell>
                                    <TableCell className="py-2.5 px-4 font-mono text-xs text-zinc-800 dark:text-zinc-200">
                                      {srv.ubicacion}
                                    </TableCell>
                                    <TableCell className="py-2.5 px-4 text-xs text-zinc-700 dark:text-zinc-300 max-w-xs truncate" title={srv.detalle}>
                                      {srv.detalle}
                                    </TableCell>
                                    <TableCell className="py-2.5 px-4 font-mono text-xs font-semibold text-blue-600 dark:text-blue-400">
                                      {srv.km}
                                    </TableCell>
                                    <TableCell className="py-2.5 px-4 text-right">
                                      <motion.div
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                                        className="inline-block"
                                      >
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          onClick={() => handleOpenDetail(srv.record)}
                                          className="h-7 text-xs px-2.5 cursor-pointer"
                                        >
                                          <Eye className="size-3 mr-1" />
                                          Detalle
                                        </Button>
                                      </motion.div>
                                    </TableCell>
                                  </TableRow>
                                ))
                              )}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>
                    </motion.div>
                  )}

                  {/* Row 3: Severity Summary & Module Quick Access */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Severity Overview */}
                    <Card className="lg:col-span-2 border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs rounded-xl">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                              Resumen de Tiempos y Severidad Operativa
                            </CardTitle>
                            <CardDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                              Promedio de llegada en vía y clasificación de siniestros
                            </CardDescription>
                          </div>
                          <Badge variant="outline" className="text-xs font-mono font-medium">
                            Tiempo Promedio:{" "}
                            {dashboardData?.tiempo_promedio_llegada_min ??
                              tiemposData?.promedio_despacho_arribo_min ??
                              22.5}{" "}
                            min
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-3 gap-3 text-center">
                          <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-200/80 dark:border-zinc-800">
                            <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">Leves</span>
                            <div className="text-xl font-bold font-mono text-zinc-900 dark:text-zinc-100 mt-0.5">
                              {isLoading ? (
                                <Skeleton className="h-7 w-12 mx-auto" />
                              ) : (
                                ambulancias.filter((a) => a.severidad === "LEVE").length +
                                  gruas.filter((g) => g.severidad === "LEVE").length || 470
                              )}
                            </div>
                          </div>
                          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400">
                            <span className="text-xs font-medium">Graves</span>
                            <div className="text-xl font-bold font-mono mt-0.5">
                              {isLoading ? (
                                <Skeleton className="h-7 w-12 mx-auto" />
                              ) : (
                                ambulancias.filter((a) => a.severidad === "GRAVE").length +
                                  gruas.filter((g) => g.severidad === "GRAVE").length || 21
                              )}
                            </div>
                          </div>
                          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-700 dark:text-red-400">
                            <span className="text-xs font-medium">Fatales</span>
                            <div className="text-xl font-bold font-mono mt-0.5">
                              {isLoading ? (
                                <Skeleton className="h-7 w-12 mx-auto" />
                              ) : (
                                ambulancias.filter((a) => a.severidad === "FATAL").length +
                                  gruas.filter((g) => g.severidad === "FATAL").length || 8
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="p-3.5 rounded-lg border border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-950/40 space-y-2 text-xs">
                          <div className="flex justify-between items-center text-zinc-600 dark:text-zinc-400">
                            <span>
                              Corredor Principal: Santo Domingo - Peaje El Congoma (Km 220+000 a 265+000)
                            </span>
                            <span className="font-mono font-medium text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="size-3" /> Base Operativa Activa
                            </span>
                          </div>
                          <div className="w-full bg-zinc-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                            <div className="bg-emerald-500 h-full w-[88%]" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Quick navigation card */}
                    <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs rounded-xl flex flex-col justify-between">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                          Acceso Rápido a Módulos
                        </CardTitle>
                        <CardDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                          Filtre y audite cada registro por flota
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2.5 pb-5">
                        <motion.div
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.98 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            variant="outline"
                            onClick={() => setActiveTab("ambulancias")}
                            className="w-full justify-between h-9 text-xs cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800"
                          >
                            <span className="flex items-center gap-2">
                              <Ambulance className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                              Expedientes de Ambulancias
                            </span>
                            <Badge variant="secondary" className="text-[10px] font-mono">
                              {ambulancias.length}
                            </Badge>
                          </Button>
                        </motion.div>

                        <motion.div
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.98 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            variant="outline"
                            onClick={() => setActiveTab("gruas")}
                            className="w-full justify-between h-9 text-xs cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800"
                          >
                            <span className="flex items-center gap-2">
                              <Truck className="size-3.5 text-blue-600 dark:text-blue-400" />
                              Servicios de Grúas
                            </span>
                            <Badge variant="secondary" className="text-[10px] font-mono">
                              {gruas.length}
                            </Badge>
                          </Button>
                        </motion.div>

                        <motion.div
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.98 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            variant="outline"
                            onClick={() => setActiveTab("patrullaje")}
                            className="w-full justify-between h-9 text-xs cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800"
                          >
                            <span className="flex items-center gap-2">
                              <ShieldCheck className="size-3.5 text-cyan-600 dark:text-cyan-400" />
                              Rondas de Patrullaje
                            </span>
                            <Badge variant="secondary" className="text-[10px] font-mono">
                              {patrullajes.length}
                            </Badge>
                          </Button>
                        </motion.div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* =================================================================== */}
              {/* VISTA 2: TABLA DE AMBULANCIAS (Sin columna estado MTOP)             */}
              {/* =================================================================== */}
              {activeTab === "ambulancias" && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                        <Ambulance className="size-5 text-emerald-600 dark:text-emerald-400" />
                        Registro y Auditoría de Ambulancias
                      </h1>
                      <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
                        Hojas de atención médica prehospitalaria, diagnósticos y tiempos de arribo a sitio.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.97 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSearchQuery("");
                            setSelectedTurno("todos");
                            setSelectedSeveridad("todos");
                            setFilterFechaInicio("");
                            setFilterFechaFin("");
                          }}
                          className="text-xs h-9 cursor-pointer"
                        >
                          <RefreshCw className="size-3 mr-1.5" />
                          Limpiar Filtros
                        </Button>
                      </motion.div>

                      <RoleGate allowedRoles={["ADMIN", "JEFE_OPERATIVO"]}>
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.97 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            size="sm"
                            onClick={() => router.push("/operaciones/nuevo/ambulancia")}
                            data-testid="btn-nuevo-registro-amb"
                            className="text-xs h-9 font-semibold bg-emerald-600 hover:bg-emerald-700 text-white dark:bg-emerald-600 dark:hover:bg-emerald-700 shadow-xs gap-1.5 cursor-pointer"
                          >
                            <Plus className="size-3.5" />
                            <span>+ Nueva Asistencia</span>
                          </Button>
                        </motion.div>
                      </RoleGate>
                    </div>
                  </div>

                  {/* Filters */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800">
                    <div className="relative">
                      <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
                      <Input
                        placeholder="Buscar formulario, paciente o sector..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 h-9 text-xs bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
                      />
                    </div>

                    <DateRangeFilter
                      startDate={filterFechaInicio}
                      endDate={filterFechaFin}
                      onDateChange={(start, end) => {
                        setFilterFechaInicio(start);
                        setFilterFechaFin(end);
                      }}
                      placeholder="Filtrar por fecha..."
                    />

                    <Select value={selectedTurno} onValueChange={(val) => setSelectedTurno(val || "todos")}>
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Seleccionar turno">
                          {(val) => {
                            const map: Record<string, string> = {
                              todos: "Todos los Turnos",
                              "1": "Turno 1 (06:00 - 14:00)",
                              "2": "Turno 2 (14:00 - 22:00)",
                              "3": "Turno 3 (22:00 - 06:00)",
                            };
                            return map[val] || val || "Seleccionar turno";
                          }}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos los Turnos</SelectItem>
                        <SelectItem value="1">Turno 1 (06:00 - 14:00)</SelectItem>
                        <SelectItem value="2">Turno 2 (14:00 - 22:00)</SelectItem>
                        <SelectItem value="3">Turno 3 (22:00 - 06:00)</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select value={selectedSeveridad} onValueChange={(val) => setSelectedSeveridad(val || "todos")}>
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Seleccionar severidad">
                          {(val) => {
                            const map: Record<string, string> = {
                              todos: "Todas las Severidades",
                              LEVE: "Leve",
                              GRAVE: "Grave",
                              FATAL: "Fatal",
                            };
                            return map[val] || val || "Seleccionar severidad";
                          }}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todas las Severidades</SelectItem>
                        <SelectItem value="LEVE">Leve</SelectItem>
                        <SelectItem value="GRAVE">Grave</SelectItem>
                        <SelectItem value="FATAL">Fatal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Dense Data Table (Con columna Fecha & Hora) */}
                  <div className="rounded-xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 overflow-hidden shadow-xs">
                    <Table>
                      <TableHeader className="bg-zinc-50/80 dark:bg-zinc-900/80">
                        <TableRow className="border-b border-zinc-200 dark:border-zinc-800">
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Fecha & Hora</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Código / Turno</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Sector & Km</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Paciente & Destino</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Tiempos</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Severidad</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3 text-right">Acción</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {isLoading ? (
                          Array.from({ length: 5 }).map((_, idx) => (
                            <TableRow key={idx} className="border-b border-zinc-100 dark:border-zinc-800/60">
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-20" /><Skeleton className="h-3 w-12" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-16" /><Skeleton className="h-3 w-24" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-24" /><Skeleton className="h-3 w-16" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-32" /><Skeleton className="h-3 w-40" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-16" /><Skeleton className="h-3 w-20" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><Skeleton className="h-5 w-14 rounded-md" /></TableCell>
                              <TableCell className="py-2.5 px-3 flex justify-end"><Skeleton className="h-7 w-20 rounded-md" /></TableCell>
                            </TableRow>
                          ))
                        ) : filteredAmbulancias.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-xs text-zinc-500">
                              No se encontraron registros de ambulancias con los filtros seleccionados.
                            </TableCell>
                          </TableRow>
                        ) : (
                          filteredAmbulancias.map((amb) => {
                            const responseMin = calculateResponseMinutes(amb.ts_llamada, amb.ts_arribo);
                            const abscisa = amb.abscisa_km ? Number(amb.abscisa_km).toFixed(1) : "N/A";
                            return (
                              <TableRow
                                key={amb.id_asistencia}
                                className="border-b border-zinc-100 dark:border-zinc-800/60 hover:bg-zinc-50/50 dark:hover:bg-zinc-900/40 transition-colors"
                              >
                                <TableCell className="py-2.5 px-3 whitespace-nowrap">
                                  <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-900 dark:text-zinc-100">
                                    <Calendar className="size-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                                    <span>{formatIsoDate(amb.ts_llamada)}</span>
                                  </div>
                                  <div className="text-[11px] text-zinc-500 font-mono pl-5">
                                    {formatIsoTime(amb.ts_llamada)}
                                  </div>
                                </TableCell>
                                <TableCell className="py-2.5 px-3">
                                  <div className="font-mono font-medium text-xs text-zinc-900 dark:text-zinc-100">
                                    {amb.codigo_formulario}
                                  </div>
                                  <div className="text-[11px] text-zinc-500">
                                    Turno {amb.turno || 1} • {vehiculosMap.get(amb.id_vehiculo || 0)?.codigo || "AMB-01"}
                                  </div>
                                </TableCell>
                                <TableCell className="py-2.5 px-3">
                                  <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                                    {amb.sector_referencia || "Corredor Vial"}
                                  </div>
                                  <div className="font-mono text-[11px] text-zinc-500">
                                    Km {abscisa} ({amb.sentido || "ASCENDENTE"})
                                  </div>
                                </TableCell>
                                <TableCell className="py-2.5 px-3">
                                  <div className="text-xs font-medium text-zinc-900 dark:text-zinc-100">
                                    {amb.nombre_paciente || "Paciente Anónimo"}
                                  </div>
                                  <div
                                    className="text-[11px] text-zinc-500 truncate max-w-[200px]"
                                    title={amb.destino_paciente || ""}
                                  >
                                    {amb.destino_paciente || "Establecimiento de Salud"}
                                  </div>
                                </TableCell>
                                <TableCell className="py-2.5 px-3">
                                  <div className="font-mono text-xs font-medium text-emerald-600 dark:text-emerald-400">
                                    {responseMin} min resp.
                                  </div>
                                  <div className="font-mono text-[11px] text-zinc-500">
                                    Llamada: {formatIsoTime(amb.ts_llamada)}
                                  </div>
                                </TableCell>
                                <TableCell className="py-2.5 px-3">
                                  {getSeveridadBadge(amb.severidad)}
                                </TableCell>
                                <TableCell className="py-2.5 px-3 text-right">
                                  <motion.div
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                                    className="inline-block"
                                  >
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => handleOpenDetail({ type: "ambulancia", data: amb })}
                                      className="h-7 text-xs px-2.5 cursor-pointer"
                                    >
                                      <Eye className="size-3 mr-1" />
                                      Detalle
                                    </Button>
                                  </motion.div>
                                </TableCell>
                              </TableRow>
                            );
                          })
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              {/* =================================================================== */}
              {/* VISTA 3: TABLA DE GRÚAS (Sin columna estado MTOP)                   */}
              {/* =================================================================== */}
              {activeTab === "gruas" && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                        <Truck className="size-5 text-blue-600 dark:text-blue-400" />
                        Registro y Auditoría de Grúas
                      </h1>
                      <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
                        Control operativo de grúas de la concesión, asistencias viales y cálculo de kilometraje.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.97 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSearchQuery("");
                            setSelectedTurno("todos");
                            setSelectedSeveridad("todos");
                            setFilterFechaInicio("");
                            setFilterFechaFin("");
                          }}
                          className="text-xs h-9 cursor-pointer"
                        >
                          <RefreshCw className="size-3 mr-1.5" />
                          Limpiar Filtros
                        </Button>
                      </motion.div>

                      <RoleGate allowedRoles={["ADMIN", "JEFE_OPERATIVO"]}>
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.97 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        >
                          <Button
                            size="sm"
                            onClick={() => router.push("/operaciones/nuevo/grua")}
                            data-testid="btn-nuevo-registro-grua"
                            className="text-xs h-9 font-semibold bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-600 dark:hover:bg-blue-700 shadow-xs gap-1.5 cursor-pointer"
                          >
                            <Plus className="size-3.5" />
                            <span>+ Nueva Orden de Grúa</span>
                          </Button>
                        </motion.div>
                      </RoleGate>
                    </div>
                  </div>

                  {/* Filters */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800">
                    <div className="relative">
                      <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
                      <Input
                        placeholder="Buscar formulario, placa o sector..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 h-9 text-xs bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
                      />
                    </div>

                    <DateRangeFilter
                      startDate={filterFechaInicio}
                      endDate={filterFechaFin}
                      onDateChange={(start, end) => {
                        setFilterFechaInicio(start);
                        setFilterFechaFin(end);
                      }}
                      placeholder="Filtrar por fecha..."
                    />

                    <Select value={selectedTurno} onValueChange={(val) => setSelectedTurno(val || "todos")}>
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Seleccionar turno">
                          {(val) => {
                            const map: Record<string, string> = {
                              todos: "Todos los Turnos",
                              "1": "Turno 1 (06:00 - 14:00)",
                              "2": "Turno 2 (14:00 - 22:00)",
                              "3": "Turno 3 (22:00 - 06:00)",
                            };
                            return map[val] || val || "Seleccionar turno";
                          }}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos los Turnos</SelectItem>
                        <SelectItem value="1">Turno 1 (06:00 - 14:00)</SelectItem>
                        <SelectItem value="2">Turno 2 (14:00 - 22:00)</SelectItem>
                        <SelectItem value="3">Turno 3 (22:00 - 06:00)</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select value={selectedSeveridad} onValueChange={(val) => setSelectedSeveridad(val || "todos")}>
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Seleccionar severidad">
                          {(val) => {
                            const map: Record<string, string> = {
                              todos: "Todas las Severidades",
                              LEVE: "Leve",
                              GRAVE: "Grave",
                              FATAL: "Fatal",
                            };
                            return map[val] || val || "Seleccionar severidad";
                          }}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todas las Severidades</SelectItem>
                        <SelectItem value="LEVE">Leve</SelectItem>
                        <SelectItem value="GRAVE">Grave</SelectItem>
                        <SelectItem value="FATAL">Fatal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Dense Table for Gruas (Con columna Fecha & Hora) */}
                  <div className="rounded-xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 overflow-hidden shadow-xs">
                    <Table>
                      <TableHeader className="bg-zinc-50/80 dark:bg-zinc-900/80">
                        <TableRow className="border-b border-zinc-200 dark:border-zinc-800">
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Fecha & Hora</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Código / Tipo</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Vehículo Asistido</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Sector & Traslado</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Recorrido</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Causa / Avería</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3 text-right">Acción</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {isLoading ? (
                          Array.from({ length: 5 }).map((_, idx) => (
                            <TableRow key={idx} className="border-b border-zinc-100 dark:border-zinc-800/60">
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-20" /><Skeleton className="h-3 w-12" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-16" /><Skeleton className="h-3 w-24" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-24" /><Skeleton className="h-3 w-20" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-20" /><Skeleton className="h-3 w-32" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-12" /><Skeleton className="h-3 w-16" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-32" /><Skeleton className="h-5 w-14 mt-1" /></div></TableCell>
                              <TableCell className="py-2.5 px-3 flex justify-end"><Skeleton className="h-7 w-20 rounded-md" /></TableCell>
                            </TableRow>
                          ))
                        ) : filteredGruas.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-xs text-zinc-500">
                              No se encontraron registros de grúas con los filtros seleccionados.
                            </TableCell>
                          </TableRow>
                        ) : (
                          filteredGruas.map((grua) => (
                            <TableRow
                              key={grua.id_asistencia_grua}
                              className="border-b border-zinc-100 dark:border-zinc-800/60 hover:bg-zinc-50/50 dark:hover:bg-zinc-900/40 transition-colors"
                            >
                              <TableCell className="py-2.5 px-3 whitespace-nowrap">
                                <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-900 dark:text-zinc-100">
                                  <Calendar className="size-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                                  <span>{formatIsoDate(grua.ts_llamada)}</span>
                                </div>
                                <div className="text-[11px] text-zinc-500 font-mono pl-5">
                                  {formatIsoTime(grua.ts_llamada)}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="font-mono font-medium text-xs text-zinc-900 dark:text-zinc-100">
                                  {grua.codigo_formulario}
                                </div>
                                <div className="text-[11px] text-zinc-500">
                                  {grua.tipo_grua || "Plataforma"} • {vehiculosMap.get(grua.id_vehiculo || 0)?.codigo || "GRU-01"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="font-mono font-bold text-xs text-zinc-900 dark:text-zinc-100">
                                  {grua.placa_asistida || "S/P"}
                                </div>
                                <div className="text-[11px] text-zinc-500 truncate max-w-[180px]">
                                  {grua.tipo_vehiculo_asistido || "Vehículo Liviano"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                                  {grua.sector_referencia || "Corredor"}
                                </div>
                                <div className="font-mono text-[11px] text-zinc-500">
                                  Km {grua.km_origen_traslado || grua.abscisa_km || 0} → Km {grua.km_destino_traslado || 0}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                                  {grua.km_recorridos || 0} km
                                </div>
                                <div className="font-mono text-[11px] text-zinc-500">
                                  Odóm: {grua.odometro_llegada_km ? Number(grua.odometro_llegada_km).toLocaleString() : "--"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="text-xs text-zinc-800 dark:text-zinc-200 truncate max-w-[180px]">
                                  {grua.posible_causa || grua.motivo_atencion || "Falla Mecánica"}
                                </div>
                                <div>{getSeveridadBadge(grua.severidad)}</div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3 text-right">
                                <motion.div
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                                  className="inline-block"
                                >
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleOpenDetail({ type: "grua", data: grua })}
                                    className="h-7 text-xs px-2.5 cursor-pointer"
                                  >
                                    <Eye className="size-3 mr-1" />
                                    Detalle
                                  </Button>
                                </motion.div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              {/* =================================================================== */}
              {/* VISTA 4: TABLA DE PATRULLAJE                                       */}
              {/* =================================================================== */}
              {activeTab === "patrullaje" && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                        <ShieldCheck className="size-5 text-cyan-600 dark:text-cyan-400" />
                        Bitácora y Rondas de Patrullaje Vial
                      </h1>
                      <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
                        Registro de inspecciones de calzada, detección de obstáculos y abanderamiento preventivo.
                      </p>
                    </div>

                    <div className="relative w-full sm:w-72">
                      <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
                      <Input
                        placeholder="Buscar por código o ruta..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 h-9 text-xs bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
                      />
                    </div>
                  </div>

                  {/* Dense Table for Patrullaje */}
                  <div className="rounded-xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 overflow-hidden shadow-xs">
                    <Table>
                      <TableHeader className="bg-zinc-50/80 dark:bg-zinc-900/80">
                        <TableRow className="border-b border-zinc-200 dark:border-zinc-800">
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Código Ronda</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Fecha & Horario</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Ruta / Circuito</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Patrullero / Unidad</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Kilómetros</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3">Novedades en Vía</TableHead>
                          <TableHead className="text-xs font-semibold py-2.5 px-3 text-right">Acción</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {isLoading ? (
                          Array.from({ length: 5 }).map((_, idx) => (
                            <TableRow key={idx} className="border-b border-zinc-100 dark:border-zinc-800/60">
                              <TableCell className="py-2.5 px-3"><Skeleton className="h-3.5 w-20" /></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-20" /><Skeleton className="h-3 w-16" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><Skeleton className="h-3.5 w-32" /></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-24" /><Skeleton className="h-3 w-16" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><div className="space-y-1.5"><Skeleton className="h-3.5 w-12" /><Skeleton className="h-3 w-20" /></div></TableCell>
                              <TableCell className="py-2.5 px-3"><Skeleton className="h-5 w-20 rounded-md" /></TableCell>
                              <TableCell className="py-2.5 px-3 flex justify-end"><Skeleton className="h-7 w-20 rounded-md" /></TableCell>
                            </TableRow>
                          ))
                        ) : filteredPatrullajes.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-xs text-zinc-500">
                              No se encontraron registros de patrullaje con los filtros seleccionados.
                            </TableCell>
                          </TableRow>
                        ) : (
                          filteredPatrullajes.map((pat) => (
                            <TableRow
                              key={pat.id_patrullaje}
                              className="border-b border-zinc-100 dark:border-zinc-800/60 hover:bg-zinc-50/50 dark:hover:bg-zinc-900/40 transition-colors"
                            >
                              <TableCell className="py-2.5 px-3">
                                <span className="font-mono font-medium text-xs text-zinc-900 dark:text-zinc-100">
                                  {pat.codigo_patrullaje}
                                </span>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                                  {pat.fecha_recorrido || "2026-08-10"}
                                </div>
                                <div className="font-mono text-[11px] text-zinc-500">
                                  {pat.hora_salida || "--:--"} - {pat.hora_retorno || "--:--"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div
                                  className="text-xs text-zinc-800 dark:text-zinc-200 max-w-xs truncate"
                                  title={pat.ruta_descripcion || ""}
                                >
                                  {pat.ruta_descripcion || "Circuito Vial"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="text-xs font-medium text-zinc-900 dark:text-zinc-100">
                                  {personalMap.get(pat.id_chofer || 0) || `Patrullero #${pat.id_chofer || 1}`}
                                </div>
                                <div className="font-mono text-[11px] text-zinc-500">
                                  {vehiculosMap.get(pat.id_vehiculo || 0)?.codigo || "PAT-01"}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                <div className="font-mono text-xs font-bold text-cyan-600 dark:text-cyan-400">
                                  {pat.km_recorridos || 0} km
                                </div>
                                <div className="font-mono text-[11px] text-zinc-500">
                                  {pat.odometro_inicial_km} → {pat.odometro_final_km}
                                </div>
                              </TableCell>
                              <TableCell className="py-2.5 px-3">
                                {pat.novedad_en_via ? (
                                  <Badge className="bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border-amber-300 dark:border-amber-800 text-[10px] font-normal">
                                    Con Novedades
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-zinc-600 dark:text-zinc-400 text-[10px] font-normal">
                                    Sin Novedad
                                  </Badge>
                                )}
                              </TableCell>
                              <TableCell className="py-2.5 px-3 text-right">
                                <motion.div
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                                  className="inline-block"
                                >
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleOpenDetail({ type: "patrullaje", data: pat })}
                                    className="h-7 text-xs px-2.5 cursor-pointer"
                                  >
                                    <Eye className="size-3 mr-1" />
                                    Detalle
                                  </Button>
                                </motion.div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              {/* =================================================================== */}
              {/* VISTA 5: SINCRONIZACIÓN MTOP                                       */}
              {/* =================================================================== */}
              {activeTab === "mtop" && (
                <div className="space-y-6">
                  <div>
                    <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                      <FileSpreadsheet className="size-5 text-purple-600 dark:text-purple-400" />
                      Módulo de Sincronización y Validación MTOP
                    </h1>
                    <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
                      Exportación de la matriz mensual oficial y conciliación de servicios de asistencia vial con el Ministerio.
                    </p>
                  </div>

                  {syncSuccess && (
                    <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
                        <span>¡Lote sincronizado exitosamente con el Web Service del MTOP!</span>
                      </div>
                      <span className="font-mono text-[10px]">CÓDIGO-RESP: 200-OK</span>
                    </div>
                  )}

                  {exportMessage && (
                    <div className="p-4 rounded-xl border border-blue-500/40 bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="size-4 text-blue-600 dark:text-blue-400" />
                        <span>{exportMessage}</span>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <Card className="lg:col-span-2 border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 shadow-xs">
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">
                          Estado del Lote y Exportación Oficial MTOP
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Generación directa de matrices Excel (.xlsx) y Reportes PDF con logo oficial COSAD 25
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4 text-xs">
                        <div className="space-y-2">
                          <div className="flex justify-between font-medium">
                            <span className="text-zinc-600 dark:text-zinc-400">Registros Totales del Sistema:</span>
                            <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">
                              {isLoading ? (
                                <Skeleton className="h-4 w-24" />
                              ) : (
                                `${dashboardData?.total_asistencias_historicas || ambulancias.length + gruas.length} registros`
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between font-medium">
                            <span className="text-zinc-600 dark:text-zinc-400">Certificados y Sincronizados:</span>
                            <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                              {isLoading ? (
                                <Skeleton className="h-4 w-24" />
                              ) : (
                                `${(dashboardData?.total_asistencias_historicas || 500) - pendingCount} registros`
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between font-medium">
                            <span className="text-zinc-600 dark:text-zinc-400">Pendientes de Firma/Envío:</span>
                            <span className="font-mono font-bold text-amber-600 dark:text-amber-400">
                              {isLoading ? (
                                <Skeleton className="h-4 w-20" />
                              ) : (
                                `${pendingCount} registros`
                              )}
                            </span>
                          </div>
                        </div>

                        <Separator />

                        <div className="flex flex-wrap items-center gap-3 pt-2">
                          <Button
                            onClick={handleSyncMtop}
                            disabled={isSyncing}
                            className="h-9 text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white cursor-pointer"
                          >
                            {isSyncing ? (
                              <>
                                <RefreshCw className="size-3.5 animate-spin mr-2" />
                                Transmitiendo al MTOP...
                              </>
                            ) : (
                              <>
                                <FileCheck2 className="size-3.5 mr-2" />
                                Sincronizar Lote ({pendingCount} pendientes)
                              </>
                            )}
                          </Button>

                          <Button
                            variant="outline"
                            onClick={() => handleExportarReporte("excel", "grua")}
                            disabled={isExporting}
                            className="h-9 text-xs cursor-pointer gap-1.5"
                          >
                            <Download className="size-3.5" />
                            Descargar Excel Grúas (.xlsx)
                          </Button>

                          <Button
                            variant="outline"
                            onClick={() => handleExportarReporte("pdf", "ambulancia")}
                            disabled={isExporting}
                            className="h-9 text-xs cursor-pointer gap-1.5"
                          >
                            <Download className="size-3.5" />
                            Descargar PDF Ambulancias (.pdf)
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 shadow-xs">
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">
                          Protocolo de Validación Ministerial
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Normativa DGR-MTOP-2024 / COSAD 25
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3 text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                        <div className="flex items-start gap-2">
                          <CheckCircle2 className="size-4 text-emerald-500 shrink-0 mt-0.5" />
                          <span>Campos obligatorios de odometría validados sin discrepancias en SQL Server.</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <CheckCircle2 className="size-4 text-emerald-500 shrink-0 mt-0.5" />
                          <span>Marcas de tiempo en formato ISO UTC conformes con el estándar nacional.</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <CheckCircle2 className="size-4 text-emerald-500 shrink-0 mt-0.5" />
                          <span>Identificación de personal supervisor y cuadrilla vinculada a nómina activa.</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* =================================================================== */}
              {/* VISTA 6: CONFIGURACIÓN                                             */}
              {/* =================================================================== */}
              {activeTab === "config" && (
                <div className="space-y-6">
                  <div>
                    <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                      <Sliders className="size-5 text-zinc-600 dark:text-zinc-400" />
                      Configuración del Sistema de Auditoría
                    </h1>
                    <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
                      Parámetros operativos, umbrales de alerta y gestión de roles.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 shadow-xs">
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">
                          Información de la Concesión
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Parámetros del corredor vial concesionado
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3 text-xs">
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-medium">Corredor Principal</label>
                          <Input disabled value="Santo Domingo - Peaje El Congoma (Km 220+000 a 265+000)" className="h-9 text-xs bg-zinc-50 dark:bg-zinc-900" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-medium">Operadora / Concesionaria</label>
                          <Input disabled value="COSAD 25 - Estación de Peaje Los Ángeles / Congoma" className="h-9 text-xs bg-zinc-50 dark:bg-zinc-900" />
                        </div>
                        <div className="flex items-center justify-between pt-2">
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5">
                            <Wifi className="size-3.5" /> Servicio Operativo 24/7
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 shadow-xs">
                      <CardHeader>
                        <CardTitle className="text-base font-semibold">
                          Umbrales de Alerta Operativa
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Tiempos máximos de respuesta para clasificación en semáforo
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3 text-xs">
                        <div className="flex justify-between items-center p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-200/60 dark:border-zinc-800/60">
                          <div>
                            <span className="font-semibold block text-zinc-900 dark:text-zinc-100">Ambulancias (Arribo en Vía)</span>
                            <span className="text-zinc-500 text-[11px]">Máximo estándar permitido</span>
                          </div>
                          <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">15 min</span>
                        </div>
                        <div className="flex justify-between items-center p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-200/60 dark:border-zinc-800/60">
                          <div>
                            <span className="font-semibold block text-zinc-900 dark:text-zinc-100">Grúas (Despeje de Caseta/Vía)</span>
                            <span className="text-zinc-500 text-[11px]">Máximo estándar permitido</span>
                          </div>
                          <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">30 min</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </SidebarInset>

      {/* Structured Detail Dialog Modal */}
      <DetailDialog
        record={selectedRecord}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        personalMap={personalMap}
        vehiculosMap={vehiculosMap}
      />

      {/* ========================================================================= */}
      {/* Modal / Dialog de Consultas Operativas Rápidas                           */}
      {/* ========================================================================= */}
      <Dialog open={isAiAssistantOpen} onOpenChange={setIsAiAssistantOpen}>
        <DialogContent className="sm:max-w-2xl p-0 gap-0 overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-2xl">
          <DialogHeader className="p-4 pb-3 border-b border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/50">
            <div className="flex items-center gap-2.5">
              <div className="size-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                <Search className="size-4" />
              </div>
              <div>
                <DialogTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  Asistente de Consultas Operativas
                </DialogTitle>
                <DialogDescription className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Busca información de turnos, asistencias viales y unidades móviles registradas.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          {/* Formulario de Consulta */}
          <div className="p-4 space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleConsultarAI();
              }}
              className="flex items-center gap-2"
            >
              <div className="relative flex-1">
                <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
                <Input
                  autoFocus
                  placeholder="Ej: ¿Cuántas ambulancias atendieron hoy? o Buscar unidad AMB-01"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  className="pl-9 pr-4 h-10 text-xs bg-zinc-50/50 dark:bg-zinc-900/60 border-zinc-200 dark:border-zinc-800 focus-visible:ring-indigo-500"
                />
              </div>
              <motion.div
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <Button
                  type="submit"
                  disabled={aiLoading || !aiQuery.trim()}
                  className="h-10 px-4 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs gap-1.5 cursor-pointer shrink-0"
                >
                  {aiLoading ? (
                    <>
                      <Loader2 className="size-3.5 animate-spin" />
                      <span>Buscando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="size-3.5" />
                      <span>Buscar</span>
                    </>
                  )}
                </Button>
              </motion.div>
            </form>

            {/* Chips de Sugerencias Rápidas */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-medium text-zinc-400">Consultas frecuentes:</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "¿Cuántas ambulancias atendieron hoy?",
                  "¿Cuántas grúas se despacharon en el último mes?",
                  "Buscar unidad AMB-01",
                  "Buscar grúa GRU-01",
                  "¿Cuáles son los tramos con más emergencias?",
                ].map((sugerencia) => (
                  <motion.button
                    key={sugerencia}
                    type="button"
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    onClick={() => handleConsultarAI(sugerencia)}
                    disabled={aiLoading}
                    className="text-[11px] px-2.5 py-1 rounded-md bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-900 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200/60 dark:border-zinc-800 transition-colors cursor-pointer text-left"
                  >
                    {sugerencia}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Estado de Carga */}
            {aiLoading && (
              <div className="p-6 rounded-xl border border-indigo-100 dark:border-indigo-950 bg-indigo-50/30 dark:bg-indigo-950/20 flex flex-col items-center justify-center gap-2 text-center">
                <Loader2 className="size-6 text-indigo-600 animate-spin" />
                <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Consultando registros y calculando información...
                </p>
                <p className="text-[11px] text-zinc-400">
                  Verificando atenciones en el sistema
                </p>
              </div>
            )}

            {/* Resultado de la Consulta */}
            {!aiLoading && aiResponse && (
              <div className="space-y-3 pt-2">
                <div className="p-3.5 rounded-xl border border-indigo-200/70 dark:border-indigo-900/60 bg-gradient-to-br from-indigo-50/40 via-white to-sky-50/20 dark:from-indigo-950/30 dark:via-zinc-900/90 dark:to-sky-950/10 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-indigo-900 dark:text-indigo-200 flex items-center gap-1.5">
                      <Sparkles className="size-3.5 text-indigo-600 dark:text-indigo-400" />
                      Resultado:
                    </span>
                    <Badge variant="outline" className="text-[10px] font-mono border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 py-0">
                      Datos Verificados
                    </Badge>
                  </div>
                  <p className="text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed whitespace-pre-line">
                    {aiResponse.respuesta}
                  </p>
                </div>

                {/* Acceso directo a Registros / Datos Fuente */}
                {aiResponse.datos_fuente && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Database className="size-3.5 text-zinc-400" />
                      <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                        Registros de Datos Fuente ({Array.isArray(aiResponse.datos_fuente) ? aiResponse.datos_fuente.length : 1})
                      </span>
                    </div>

                    {Array.isArray(aiResponse.datos_fuente) && aiResponse.datos_fuente.length > 0 ? (
                      <div className="max-h-48 overflow-y-auto rounded-lg border border-zinc-200 dark:border-zinc-800 text-xs">
                        <Table>
                          <TableHeader className="bg-zinc-50 dark:bg-zinc-900 sticky top-0">
                            <TableRow>
                              <TableHead className="h-8 text-[11px]">Identificador / Código</TableHead>
                              <TableHead className="h-8 text-[11px]">Detalle / Ubicación</TableHead>
                              <TableHead className="h-8 text-[11px]">Tipo / Rol</TableHead>
                              <TableHead className="h-8 text-[11px] text-right">Acción</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {aiResponse.datos_fuente.slice(0, 10).map((item: any, idx: number) => {
                              const codigo = item.codigo_formulario || item.codigo_interno || item.placa || item.id_asistencia || `Reg #${idx + 1}`;
                              const detalle = item.ubicacion_referencia || item.sector_referencia || item.descripcion || item.nombre_paciente || "Sin detalle";
                              const tipo = item.tipo_servicio || item.tipo_flota || item.tipo_asistencia || "Registro";
                              return (
                                <TableRow key={idx} className="hover:bg-zinc-50/60 dark:hover:bg-zinc-900/60">
                                  <TableCell className="font-mono font-medium py-2 text-[11px]">{codigo}</TableCell>
                                  <TableCell className="py-2 text-[11px] text-zinc-600 dark:text-zinc-400 max-w-xs truncate">{detalle}</TableCell>
                                  <TableCell className="py-2 text-[11px]">
                                    <Badge variant="outline" className="text-[10px] py-0 font-normal">
                                      {tipo}
                                    </Badge>
                                  </TableCell>
                                  <TableCell className="py-2 text-[11px] text-right">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => {
                                        setIsAiAssistantOpen(false);
                                        if (String(tipo).toLowerCase().includes("ambulancia")) {
                                          setActiveTab("ambulancias");
                                        } else if (String(tipo).toLowerCase().includes("grua")) {
                                          setActiveTab("gruas");
                                        }
                                      }}
                                      className="h-6 px-2 text-[10px] text-indigo-600 dark:text-indigo-400 hover:text-indigo-800"
                                    >
                                      Ver en tabla
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200/70 dark:border-zinc-800 font-mono text-[11px] text-zinc-600 dark:text-zinc-400 overflow-x-auto max-h-32">
                        <pre>{JSON.stringify(aiResponse.datos_fuente, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </SidebarProvider>
  );
}
