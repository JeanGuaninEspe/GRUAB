"use client";

import * as React from "react";
import { DashboardView } from "@/components/dashboard/dashboard-view";
import { useAuth } from "@/context/auth-context";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

function DashboardContent() {
  const { logout, user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isLoading, isAuthenticated, router]);

  React.useEffect(() => {
    const error = searchParams.get("error");
    if (error === "unauthorized_role_visualizador") {
      toast.error(
        "Acceso denegado: Tu perfil de VISUALIZADOR no tiene permisos para crear o modificar asistencias."
      );
    } else if (error === "unauthorized_role_admin_only") {
      toast.error(
        "Acceso denegado: El módulo de configuración está reservado exclusivamente para ADMINISTRADORES."
      );
    } else if (error === "unauthorized") {
      toast.error("No tienes permisos suficientes para realizar esta acción.");
    }
  }, [searchParams]);

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-white dark:bg-zinc-950">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100 animate-spin" />
          <span className="text-xs text-zinc-500 font-medium">Verificando credenciales...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <DashboardView onLogout={logout} />;
}

export default function DashboardPage() {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen w-full flex items-center justify-center bg-white dark:bg-zinc-950">
          <div className="flex flex-col items-center gap-3">
            <div className="size-8 rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100 animate-spin" />
            <span className="text-xs text-zinc-500 font-medium">Cargando dashboard...</span>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </React.Suspense>
  );
}
