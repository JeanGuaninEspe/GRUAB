"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { AppSidebar, DashboardTab } from "@/components/dashboard/app-sidebar";
import { UserDropdown } from "@/components/dashboard/user-dropdown";
import { RegistroOperacionesForm } from "@/components/operaciones/registro-form";
import { useAuth } from "@/context/auth-context";

export default function NuevoRegistroGruaPage() {
  const router = useRouter();
  const { user, logout, hasRole } = useAuth();
  const [activeTab, setActiveTab] = React.useState<DashboardTab>("gruas");

  React.useEffect(() => {
    // Protección a nivel de cliente si entra como VISUALIZADOR
    if (user && !hasRole(["ADMIN", "JEFE_OPERATIVO"])) {
      router.push("/dashboard?error=unauthorized_role_visualizador");
    }
  }, [user, hasRole, router]);

  const handleTabChange = (tab: DashboardTab) => {
    setActiveTab(tab);
    router.push(`/dashboard?tab=${tab}`);
  };

  return (
    <SidebarProvider defaultOpen={true}>
      <AppSidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onLogout={logout}
      />

      <SidebarInset className="bg-zinc-50/60 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col min-h-screen overflow-x-hidden">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <SidebarTrigger className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 cursor-pointer" />
            <Separator orientation="vertical" className="h-4 hidden sm:block" />

            <Breadcrumb className="hidden sm:block">
              <BreadcrumbList className="text-xs">
                <BreadcrumbItem>
                  <BreadcrumbLink
                    onClick={() => router.push("/dashboard")}
                    className="cursor-pointer text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                  >
                    VehículosRC
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbLink
                    onClick={() => router.push("/dashboard?tab=gruas")}
                    className="cursor-pointer text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                  >
                    Grúas
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage className="font-semibold text-zinc-900 dark:text-zinc-100">
                    Nueva Orden de Grúa
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <UserDropdown />
          </div>
        </header>

        {/* Formulario Específico de Grúa */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto w-full">
          <RegistroOperacionesForm fixedService="grua" />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
