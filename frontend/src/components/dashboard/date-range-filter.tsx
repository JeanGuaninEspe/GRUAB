"use client";

import * as React from "react";
import { Calendar, X, Check, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverClose,
} from "@/components/ui/popover";
import { motion } from "motion/react";

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onDateChange: (start: string, end: string) => void;
  className?: string;
  placeholder?: string;
}

export function DateRangeFilter({
  startDate,
  endDate,
  onDateChange,
  className = "",
  placeholder = "Filtrar por fecha...",
}: DateRangeFilterProps) {
  const [tempStart, setTempStart] = React.useState(startDate);
  const [tempEnd, setTempEnd] = React.useState(endDate);
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    setTempStart(startDate);
    setTempEnd(endDate);
  }, [startDate, endDate]);

  const hasFilter = Boolean(startDate || endDate);

  // Formato amigable de presentación en el botón
  const displayLabel = React.useMemo(() => {
    if (!startDate && !endDate) return placeholder;
    const formatD = (dStr: string) => {
      if (!dStr) return "";
      const [y, m, d] = dStr.split("-");
      return `${d}/${m}/${y}`;
    };

    if (startDate && endDate) {
      if (startDate === endDate) return formatD(startDate);
      return `${formatD(startDate)} — ${formatD(endDate)}`;
    }
    if (startDate) return `Desde ${formatD(startDate)}`;
    return `Hasta ${formatD(endDate)}`;
  }, [startDate, endDate, placeholder]);

  const aplicarPresets = (start: string, end: string) => {
    setTempStart(start);
    setTempEnd(end);
    onDateChange(start, end);
    setOpen(false);
  };

  const handleApply = () => {
    onDateChange(tempStart, tempEnd);
    setOpen(false);
  };

  const handleClear = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setTempStart("");
    setTempEnd("");
    onDateChange("", "");
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <div className={`relative flex items-center ${className}`}>
        <PopoverTrigger
          type="button"
          className={`group inline-flex items-center w-full h-9 px-3 rounded-lg text-xs font-normal border cursor-pointer transition-all select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 dark:focus-visible:ring-zinc-600 ${
            hasFilter
              ? "border-blue-500/50 bg-blue-50/50 text-blue-900 dark:border-blue-700/50 dark:bg-blue-950/30 dark:text-blue-300 font-medium"
              : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
          }`}
        >
          <Calendar
            className={`size-3.5 mr-2 shrink-0 ${
              hasFilter ? "text-blue-600 dark:text-blue-400" : "text-zinc-400"
            }`}
          />
          <span className="truncate flex-1 text-left">{displayLabel}</span>
          {hasFilter && (
            <span
              role="button"
              tabIndex={0}
              onClick={handleClear}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") handleClear(e as any);
              }}
              className="ml-1 p-0.5 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors z-10"
              title="Quitar filtro de fecha"
            >
              <X className="size-3" />
            </span>
          )}
        </PopoverTrigger>
      </div>

      <PopoverContent className="w-80 p-4 space-y-3.5" align="start">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <Calendar className="size-3.5 text-blue-600 dark:text-blue-400" />
            <span>Filtrar por Rango de Fecha</span>
          </div>
          {hasFilter && (
            <button
              onClick={() => handleClear()}
              className="text-[11px] text-zinc-400 hover:text-rose-500 transition-colors cursor-pointer"
            >
              Limpiar
            </button>
          )}
        </div>

        {/* Presets Rápidos */}
        <div className="space-y-1.5">
          <span className="text-[10px] font-semibold tracking-wider uppercase text-zinc-400">
            Accesos Rápidos
          </span>
          <div className="grid grid-cols-2 gap-1.5">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => aplicarPresets("2026-10-01", "2026-10-31")}
              className="h-7 text-[11px] justify-start px-2 border-zinc-200 dark:border-zinc-800 cursor-pointer"
            >
              Octubre 2026
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => aplicarPresets("2026-10-02", "2026-10-09")}
              className="h-7 text-[11px] justify-start px-2 border-zinc-200 dark:border-zinc-800 cursor-pointer"
            >
              Últimos 7 días
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => aplicarPresets("2026-09-09", "2026-10-09")}
              className="h-7 text-[11px] justify-start px-2 border-zinc-200 dark:border-zinc-800 cursor-pointer"
            >
              Últimos 30 días
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => aplicarPresets("2026-05-01", "2026-05-31")}
              className="h-7 text-[11px] justify-start px-2 border-zinc-200 dark:border-zinc-800 cursor-pointer"
            >
              Mayo 2026
            </Button>
          </div>
        </div>

        {/* Inputs Personalizados */}
        <div className="space-y-2 pt-1 border-t border-zinc-100 dark:border-zinc-800">
          <span className="text-[10px] font-semibold tracking-wider uppercase text-zinc-400">
            Rango Personalizado
          </span>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-[11px] text-zinc-500 font-medium">Desde</label>
              <Input
                type="date"
                value={tempStart}
                onChange={(e) => setTempStart(e.target.value)}
                className="h-8 text-xs font-mono px-2 bg-zinc-50 dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-zinc-500 font-medium">Hasta</label>
              <Input
                type="date"
                value={tempEnd}
                onChange={(e) => setTempEnd(e.target.value)}
                className="h-8 text-xs font-mono px-2 bg-zinc-50 dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700"
              />
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
          <PopoverClose
            type="button"
            className="h-7 px-2.5 rounded-md text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer transition-colors"
          >
            Cancelar
          </PopoverClose>
          <Button
            type="button"
            size="sm"
            onClick={handleApply}
            className="h-7 text-xs bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 font-medium px-3 cursor-pointer gap-1"
          >
            <Check className="size-3" />
            <span>Aplicar</span>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
