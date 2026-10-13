"use client";

import * as React from "react";
import {
  Activity,
  Ambulance,
  Calendar,
  Clock,
  FileCheck2,
  Gauge,
  MapPin,
  ShieldAlert,
  Truck,
  User,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { AsistenciaAmbulancia, AsistenciaGrua, BitacoraPatrullaje } from "@/types/asistencias";
import { AmbulanciaApiRead, GruaApiRead, PatrullajeApiRead } from "@/types/api";

type SelectedRecord =
  | { type: "ambulancia"; data: AsistenciaAmbulancia | AmbulanciaApiRead }
  | { type: "grua"; data: AsistenciaGrua | GruaApiRead }
  | { type: "patrullaje"; data: BitacoraPatrullaje | PatrullajeApiRead };

interface DetailDialogProps {
  record: SelectedRecord | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  personalMap?: Map<number, string>;
  vehiculosMap?: Map<number, { codigo: string; placa: string }>;
}

export function DetailDialog({
  record,
  open,
  onOpenChange,
  personalMap,
  vehiculosMap,
}: DetailDialogProps) {
  if (!record) return null;

  const formatIsoDate = (isoString?: string | null) => {
    if (!isoString) return "--/--/----";
    try {
      const s = String(isoString).trim();
      const datePart = s.split("T")[0].split(" ")[0];
      const parts = datePart.split("-");
      if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
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
      // Extrae la porción de tiempo directamente del string para evitar distorsiones de UTC/zona horaria
      const timePart = s.includes("T")
        ? s.split("T")[1]
        : s.includes(" ")
        ? s.split(" ")[1]
        : s;
      const parts = timePart.split(":");
      if (parts.length >= 2) {
        return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}`;
      }
      const date = new Date(isoString);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString("es-EC", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        });
      }
      return isoString;
    } catch {
      return "--:--";
    }
  };

  const getSeveridadBadge = (sev?: string | null) => {
    switch (sev) {
      case "FATAL":
        return (
          <Badge variant="destructive" className="font-semibold text-xs px-2 py-0.5">
            FATAL
          </Badge>
        );
      case "GRAVE":
        return (
          <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 text-xs px-2 py-0.5">
            GRAVE
          </Badge>
        );
      case "LEVE":
      default:
        return (
          <Badge className="bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 text-xs px-2 py-0.5">
            LEVE
          </Badge>
        );
    }
  };

  // Helper para resolver nombres de personal
  const getPersonalName = (id?: number | null, directName?: string) => {
    if (directName) return directName;
    if (id && personalMap && personalMap.has(id)) return personalMap.get(id);
    if (id) return `Operador #${id}`;
    return "No especificado";
  };

  // Helper para resolver código de vehículo
  const getVehiculoCode = (id?: number | null, directCode?: string) => {
    if (directCode) return directCode;
    if (id && vehiculosMap && vehiculosMap.has(id)) return vehiculosMap.get(id)?.codigo;
    if (id) return `Unidad #${id}`;
    return "Móvil Asignado";
  };

  const anyData = record.data as any;
  const abscisa = anyData.abscisa_km !== undefined && anyData.abscisa_km !== null
    ? Number(anyData.abscisa_km).toFixed(1)
    : "N/A";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full sm:max-w-2xl max-h-[85vh] flex flex-col p-0 gap-0 border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 shadow-2xl overflow-hidden">
        {/* Header con código y tipo */}
        <DialogHeader className="p-5 pb-4 border-b border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/70 dark:bg-zinc-900/60 shrink-0">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="flex size-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 shadow-xs">
                {record.type === "ambulancia" && <Ambulance className="size-4 text-emerald-600 dark:text-emerald-400" />}
                {record.type === "grua" && <Truck className="size-4 text-blue-600 dark:text-blue-400" />}
                {record.type === "patrullaje" && <Activity className="size-4 text-cyan-600 dark:text-cyan-400" />}
              </div>
              <div>
                <DialogTitle className="text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
                  {record.type === "ambulancia" && `Expediente Médico ${anyData.codigo_formulario}`}
                  {record.type === "grua" && `Registro de Remolque ${anyData.codigo_formulario}`}
                  {record.type === "patrullaje" && `Ronda de Patrullaje ${anyData.codigo_patrullaje}`}
                </DialogTitle>
                <DialogDescription className="text-xs text-zinc-500 dark:text-zinc-400">
                  Auditoría detallada de tiempos de respuesta, personal asignado y odometría
                </DialogDescription>
              </div>
            </div>

            {"severidad" in anyData && getSeveridadBadge(anyData.severidad)}
          </div>
        </DialogHeader>

        <div className="p-6 space-y-6 text-sm overflow-y-auto flex-1">
          {/* 1. Línea de tiempo operativa */}
          {record.type !== "patrullaje" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                <span className="flex items-center gap-1.5">
                  <Clock className="size-3.5 text-zinc-400" />
                  Línea de Tiempo Operativa
                </span>
                <span className="text-zinc-500 font-normal">
                  {anyData.ts_llamada ? `${formatIsoDate(anyData.ts_llamada)} • ` : ""}Turno {anyData.turno || 1}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2 p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200/80 dark:border-zinc-800/80">
                <div className="text-center space-y-1">
                  <span className="text-[10px] text-zinc-400 uppercase font-medium">Llamada</span>
                  <div className="font-mono text-xs font-bold text-zinc-800 dark:text-zinc-200">
                    {formatIsoTime(anyData.ts_llamada)}
                  </div>
                </div>
                <div className="text-center space-y-1 border-l border-zinc-200 dark:border-zinc-800">
                  <span className="text-[10px] text-zinc-400 uppercase font-medium">Arribo Sitio</span>
                  <div className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    {formatIsoTime(anyData.ts_arribo)}
                  </div>
                </div>
                <div className="text-center space-y-1 border-l border-zinc-200 dark:border-zinc-800">
                  <span className="text-[10px] text-zinc-400 uppercase font-medium">Término</span>
                  <div className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                    {formatIsoTime(anyData.ts_termino)}
                  </div>
                </div>
                <div className="text-center space-y-1 border-l border-zinc-200 dark:border-zinc-800">
                  <span className="text-[10px] text-zinc-400 uppercase font-medium">Retorno Base</span>
                  <div className="font-mono text-xs font-bold text-zinc-600 dark:text-zinc-400">
                    {formatIsoTime(anyData.ts_retorno)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 2. Ubicación & Georreferencia */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
              <MapPin className="size-3.5 text-zinc-400" />
              Ubicación y Sectorización
            </span>
            <div className="p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-zinc-400 block text-[11px]">Sector de Referencia</span>
                <span className="font-medium text-zinc-800 dark:text-zinc-200">
                  {anyData.sector_referencia || anyData.ruta_descripcion || "No especificado"}
                </span>
              </div>
              {anyData.abscisa_km !== undefined && anyData.abscisa_km !== null && (
                <div>
                  <span className="text-zinc-400 block text-[11px]">Abscisa / Progresiva</span>
                  <span className="font-mono font-medium text-zinc-800 dark:text-zinc-200">
                    Km {abscisa}
                  </span>
                </div>
              )}
              {anyData.sentido && (
                <div>
                  <span className="text-zinc-400 block text-[11px]">Sentido de Circulación</span>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">
                    {anyData.sentido}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* 3. Diagnóstico Médico o Detalle de Grúa */}
          {record.type === "ambulancia" && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                <ShieldAlert className="size-3.5 text-zinc-400" />
                Diagnóstico y Atención del Paciente
              </span>
              <div className="p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 space-y-2.5 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Nombre del Paciente</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {anyData.nombre_paciente || "Paciente Anónimo"} {anyData.rango_edad ? `(${anyData.rango_edad})` : ""}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Destino / Hospital</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {anyData.destino_paciente || "Establecimiento de Salud"}
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-zinc-400 block text-[11px]">Motivo de Atención</span>
                  <p className="text-zinc-700 dark:text-zinc-300 mt-0.5">
                    {anyData.motivo_atencion || "Asistencia en vía"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {record.type === "grua" && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                <Truck className="size-3.5 text-zinc-400" />
                Detalle del Vehículo Remolcado
              </span>
              <div className="p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 space-y-2 text-xs">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Placa Asistida</span>
                    <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">
                      {anyData.placa_asistida || "S/P"}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Tipo de Vehículo</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {anyData.tipo_vehiculo_asistido || "Vehículo Liviano"}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Tipo de Grúa</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {anyData.tipo_grua || "Plataforma"}
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-zinc-400 block text-[11px]">Posible Causa / Avería</span>
                  <p className="text-zinc-700 dark:text-zinc-300">
                    {anyData.posible_causa || anyData.motivo_atencion || "Falla Mecánica"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 4. Odometría y Desplazamiento */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
              <Gauge className="size-3.5 text-zinc-400" />
              Odometría y Control de Kilometraje
            </span>
            <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 text-xs">
              <div>
                <span className="text-zinc-400 block text-[11px]">Odómetro Salida</span>
                <span className="font-mono text-zinc-700 dark:text-zinc-300">
                  {anyData.odometro_salida_km !== undefined && anyData.odometro_salida_km !== null
                    ? `${Number(anyData.odometro_salida_km).toLocaleString()} km`
                    : anyData.odometro_inicial_km !== undefined
                    ? `${Number(anyData.odometro_inicial_km).toLocaleString()} km`
                    : "-- km"}
                </span>
              </div>
              <div>
                <span className="text-zinc-400 block text-[11px]">Odómetro Llegada</span>
                <span className="font-mono text-zinc-700 dark:text-zinc-300">
                  {anyData.odometro_llegada_km !== undefined && anyData.odometro_llegada_km !== null
                    ? `${Number(anyData.odometro_llegada_km).toLocaleString()} km`
                    : anyData.odometro_final_km !== undefined
                    ? `${Number(anyData.odometro_final_km).toLocaleString()} km`
                    : "-- km"}
                </span>
              </div>
              <div>
                <span className="text-zinc-400 block text-[11px]">Recorrido Total</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                  {anyData.km_recorridos || 0} km
                </span>
              </div>
            </div>
          </div>

          {/* 5. Personal Responsable */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
              <User className="size-3.5 text-zinc-400" />
              Tripulación y Personal Asignado
            </span>
            <div className="p-3.5 rounded-xl bg-zinc-50/70 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-zinc-400 block text-[11px]">Supervisor de Turno</span>
                <span className="font-medium text-zinc-800 dark:text-zinc-200">
                  {getPersonalName(anyData.id_supervisor, anyData.supervisor_nombre)}
                </span>
              </div>
              {record.type === "ambulancia" && (
                <div>
                  <span className="text-zinc-400 block text-[11px]">Paramédico</span>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">
                    {getPersonalName(anyData.id_paramedico, anyData.paramedico_nombre)}
                  </span>
                </div>
              )}
              {record.type !== "patrullaje" && (
                <div>
                  <span className="text-zinc-400 block text-[11px]">Conductor</span>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">
                    {getPersonalName(anyData.id_chofer, anyData.chofer_nombre)}
                  </span>
                </div>
              )}
              {record.type === "patrullaje" && (
                <div>
                  <span className="text-zinc-400 block text-[11px]">Patrullero</span>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">
                    {getPersonalName(anyData.id_chofer, anyData.patrullero_nombre)}
                  </span>
                </div>
              )}
              <div>
                <span className="text-zinc-400 block text-[11px]">Unidad Asignada</span>
                <span className="font-mono text-zinc-800 dark:text-zinc-200">
                  {getVehiculoCode(anyData.id_vehiculo, anyData.vehiculo_codigo)}
                </span>
              </div>
            </div>
          </div>

          {/* 6. Observaciones y Estado MTOP */}
          {anyData.observaciones && (
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                Observaciones de Campo
              </span>
              <p className="text-xs p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/30 border border-zinc-200/60 dark:border-zinc-800/60 text-zinc-600 dark:text-zinc-400 leading-relaxed">
                {anyData.observaciones}
              </p>
            </div>
          )}

          {"reportado_mtop" in anyData && (
            <div className="flex items-center justify-between pt-2 border-t border-zinc-100 dark:border-zinc-800 text-xs">
              <span className="text-zinc-500">Estado de Sincronización MTOP:</span>
              {anyData.reportado_mtop ? (
                <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800 gap-1">
                  <FileCheck2 className="size-3" />
                  Sincronizado con Matriz MTOP
                </Badge>
              ) : (
                <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-700">
                  Pendiente de Envío
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Footer with action */}
        <div className="p-4 border-t border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/40 flex justify-end">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="inline-flex items-center justify-center rounded-lg text-xs font-medium bg-zinc-900 text-zinc-50 hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 h-8 px-4 cursor-pointer transition-colors shadow-xs"
          >
            Cerrar Auditoría
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
