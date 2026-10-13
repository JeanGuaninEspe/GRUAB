"use client";

import * as React from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/auth-context";
import { motion } from "motion/react";
import { History, LogOut, User } from "lucide-react";
import { toast } from "sonner";
import { cn } from "cn";

export function UserDropdown() {
  const { user, logout } = useAuth();

  const getInitials = (name?: string) => {
    if (!name) return "RC";
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const getRoleDotClass = (role?: string) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-600";
      case "JEFE_OPERATIVO":
        return "bg-blue-600";
      case "VISUALIZADOR":
        return "bg-zinc-400 dark:bg-zinc-500";
      default:
        return "bg-zinc-400";
    }
  };

  const renderRoleBadge = () => {
    switch (user?.rol) {
      case "ADMIN":
        return (
          <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300 border-purple-300 dark:border-purple-800 text-[10px] font-semibold px-2 py-0.5">
            ADMIN
          </Badge>
        );
      case "JEFE_OPERATIVO":
        return (
          <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300 border-blue-300 dark:border-blue-800 text-[10px] font-semibold px-2 py-0.5">
            JEFE OPERATIVO
          </Badge>
        );
      case "VISUALIZADOR":
        return (
          <Badge className="bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700 text-[10px] font-semibold px-2 py-0.5">
            VISUALIZADOR
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-[10px] font-semibold px-2 py-0.5">
            USUARIO
          </Badge>
        );
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="outline-none border-0 p-0 bg-transparent cursor-pointer rounded-full focus:outline-none"
        data-testid="user-dropdown-trigger"
        aria-label="Menú de perfil y sesión de usuario"
      >
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
          className="relative rounded-full focus:outline-none cursor-pointer group"
        >
          <Avatar className="h-9 w-9 border border-zinc-200/80 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-800 shadow-xs transition-all duration-200 group-hover:shadow-md group-hover:border-zinc-300 dark:group-hover:border-zinc-700">
            <AvatarFallback className="bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-semibold text-xs">
              {getInitials(user?.nombre)}
            </AvatarFallback>
          </Avatar>

          {/* Dot de rol perimetral en la esquina */}
          <span
            className={cn(
              "absolute -bottom-0.5 -right-0.5 size-3 rounded-full ring-2 ring-white dark:ring-zinc-950 shadow-xs",
              getRoleDotClass(user?.rol)
            )}
            title={`Perfil: ${user?.rol || "Sin rol"}`}
          />
        </motion.div>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={8}
        className="w-64 p-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xl rounded-xl animate-in fade-in-0 zoom-in-95 data-[side=bottom]:slide-in-from-top-2 duration-150 z-50"
      >
        {/* Cabecera del Menú */}
        <DropdownMenuLabel className="p-2 font-normal">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 truncate max-w-[140px]">
                {user?.nombre || "Usuario Activo"}
              </span>
              {renderRoleBadge()}
            </div>
            <p className="text-xs text-muted-foreground truncate">
              {user?.email || "usuario@concesion.com"}
            </p>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator className="my-1.5 bg-zinc-100 dark:bg-zinc-800" />

        {/* Opciones Futuras */}
        <DropdownMenuItem
          onClick={() => toast.info("Módulo de Preferencias disponible próximamente")}
          className="cursor-pointer gap-2 py-2 px-2.5 rounded-lg text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <User className="size-4 text-zinc-500" />
          <span>Mi Cuenta / Preferencias</span>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => toast.info("Historial de actividad disponible próximamente")}
          className="cursor-pointer gap-2 py-2 px-2.5 rounded-lg text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <History className="size-4 text-zinc-500" />
          <span>Registro de Actividad</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator className="my-1.5 bg-zinc-100 dark:bg-zinc-800" />

        {/* Opción de Salida */}
        <DropdownMenuItem
          onClick={logout}
          data-testid="dropdown-logout-item"
          className="cursor-pointer gap-2 py-2 px-2.5 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 focus:bg-rose-50 dark:focus:bg-rose-950/40 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
        >
          <LogOut className="size-4 text-rose-600 dark:text-rose-400" />
          <span>Cerrar Sesión</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
