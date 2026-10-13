"use client";

import * as React from "react";
import { UserRole } from "@/types/auth";
import { useAuth } from "@/context/auth-context";

interface RoleGateProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Componente que renderiza sus hijos solo si el usuario autenticado posee uno de los roles permitidos.
 */
export function RoleGate({
  allowedRoles,
  children,
  fallback = null,
}: RoleGateProps) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated || !user) {
    return <>{fallback}</>;
  }

  if (!allowedRoles.includes(user.rol)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
