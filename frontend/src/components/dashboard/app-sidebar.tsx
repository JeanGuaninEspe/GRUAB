"use client";

import * as React from "react";
import {
  Ambulance,
  FileSpreadsheet,
  Layers,
  LayoutDashboard,
  ShieldCheck,
  Sliders,
  Truck,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";

import { motion } from "motion/react";

export type DashboardTab = "kpi" | "ambulancias" | "gruas" | "patrullaje" | "mtop" | "config";

interface AppSidebarProps {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
  pendingAmbMtopCount?: number;
  onLogout?: () => void;
}

export function AppSidebar({
  activeTab,
  onTabChange,
  pendingAmbMtopCount = 2,
}: AppSidebarProps) {
  const menuItems = [
    {
      group: "Operaciones y Registro",
      items: [
        {
          id: "kpi" as DashboardTab,
          label: "KPIs Generales",
          icon: LayoutDashboard,
          iconColor: "",
          badge: null,
        },
        {
          id: "ambulancias" as DashboardTab,
          label: "Ambulancias",
          icon: Ambulance,
          iconColor: "text-emerald-600 dark:text-emerald-400",
          badge: pendingAmbMtopCount > 0 ? pendingAmbMtopCount : null,
        },
        {
          id: "gruas" as DashboardTab,
          label: "Grúas",
          icon: Truck,
          iconColor: "text-blue-600 dark:text-blue-400",
          badge: null,
        },
        {
          id: "patrullaje" as DashboardTab,
          label: "Patrullaje",
          icon: ShieldCheck,
          iconColor: "text-cyan-600 dark:text-cyan-400",
          badge: null,
        },
      ],
    },
    {
      group: "Auditoría & Sistema",
      items: [
        {
          id: "mtop" as DashboardTab,
          label: "Sincronización MTOP",
          icon: FileSpreadsheet,
          iconColor: "text-purple-600 dark:text-purple-400",
          badge: null,
        },
        {
          id: "config" as DashboardTab,
          label: "Configuración",
          icon: Sliders,
          iconColor: "",
          badge: null,
        },
      ],
    },
  ];

  return (
    <Sidebar collapsible="icon" className="border-r border-zinc-200 dark:border-zinc-800">
      {/* Header */}
      <SidebarHeader className="p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="hover:bg-transparent">
              <div className="flex size-8 items-center justify-center rounded-lg bg-zinc-900 text-zinc-100 dark:bg-zinc-100 dark:text-zinc-900 shadow-sm">
                <Layers className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
                  VehículosRC
                </span>
                <span className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                  Auditoría y Operaciones
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarSeparator />

      {/* Main Navigation */}
      <SidebarContent>
        {menuItems.map((group) => (
          <SidebarGroup key={group.group}>
            <SidebarGroupLabel className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">
              {group.group}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <SidebarMenuItem key={item.id} className="relative">
                      <motion.div
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.97 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                        className="w-full relative"
                      >
                        {isActive && (
                          <motion.div
                            layoutId="active-sidebar-indicator"
                            className="absolute inset-0 bg-zinc-100 dark:bg-zinc-800/90 rounded-lg -z-0"
                            transition={{ type: "spring", stiffness: 400, damping: 30 }}
                          />
                        )}
                        <SidebarMenuButton
                          isActive={isActive}
                          onClick={() => onTabChange(item.id)}
                          tooltip={item.label}
                          data-tab={item.id}
                          data-testid={`nav-${item.id}`}
                          className="cursor-pointer relative z-10"
                        >
                          <Icon className={`size-4 ${item.iconColor}`} />
                          <span className="font-medium">{item.label}</span>
                        </SidebarMenuButton>
                      </motion.div>
                      {item.badge !== null && (
                        <SidebarMenuBadge className="bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-400 text-[10px] font-medium border border-amber-300 dark:border-amber-800 z-10">
                          {item.badge}
                        </SidebarMenuBadge>
                      )}
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarSeparator />

      {/* Sidebar Footer Minimalista */}
      <SidebarFooter className="p-3">
        <div className="flex items-center justify-center py-1 text-[11px] text-zinc-400 dark:text-zinc-500 font-mono select-none">
          v1.0 • COSAD 25
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
