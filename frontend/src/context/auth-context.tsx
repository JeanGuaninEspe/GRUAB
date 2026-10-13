"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { User, UserRole, LoginCredentials, AuthResponse } from "@/types/auth";
import {
  setAuthSession,
  getAuthSession,
  clearAuthSession,
} from "@/lib/auth-cookies";
import { API_BASE_URL } from "@/lib/api-client";
import { toast } from "sonner";

// Cuentas de prueba preconfiguradas con perfiles RBAC
export const TEST_ACCOUNTS: Record<string, { user: User; token: string }> = {
  "admin@concesion.com": {
    user: {
      id: 1,
      email: "admin@concesion.com",
      nombre: "Ing. Carlos Mendoza",
      rol: "ADMIN",
      activo: true,
    },
    token: "mock_jwt_token_admin_role_2026_vehiculosrc_secure",
  },
  "operaciones@concesion.com": {
    user: {
      id: 2,
      email: "operaciones@concesion.com",
      nombre: "Myr. Roberto Paredes",
      rol: "JEFE_OPERATIVO",
      activo: true,
    },
    token: "mock_jwt_token_jefe_operativo_2026_vehiculosrc_secure",
  },
  "auditoria@concesion.com": {
    user: {
      id: 3,
      email: "auditoria@concesion.com",
      nombre: "Dra. Elena Salazar",
      rol: "VISUALIZADOR",
      activo: true,
    },
    token: "mock_jwt_token_visualizador_2026_vehiculosrc_secure",
  },
};

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials, remember?: boolean) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const router = useRouter();

  // Inicialización de sesión desde Cookies al cargar
  React.useEffect(() => {
    try {
      const session = getAuthSession();
      if (session.token && session.user) {
        setUser(session.user);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Método de Login con intento a Backend FastAPI y Fallback a Cuentas Mock
   */
  const login = async (
    credentials: LoginCredentials,
    remember: boolean = true
  ): Promise<void> => {
    setIsLoading(true);

    const emailNorm = credentials.email.trim().toLowerCase();

    // 1. Cuentas de Prueba Preconfiguradas (Acceso rápido instantáneo sin bloqueos de red)
    const testAccount = TEST_ACCOUNTS[emailNorm];
    if (testAccount) {
      await new Promise((resolve) => setTimeout(resolve, 150));
      setAuthSession(testAccount.token, testAccount.user, remember);
      setUser(testAccount.user);
      toast.success(`Sesión iniciada como ${testAccount.user.rol}: ${testAccount.user.nombre}`);
      if (typeof window !== "undefined") {
        window.location.href = "/dashboard";
      } else {
        router.push("/dashboard");
      }
      return;
    }

    // 2. Intento con API Backend real (con timeout de 3.5s para evitar cuelgues)
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data: AuthResponse = await response.json();
        setAuthSession(data.access_token, data.user, remember);
        setUser(data.user);
        toast.success(`Bienvenido, ${data.user.nombre}`);
        if (typeof window !== "undefined") {
          window.location.href = "/dashboard";
        } else {
          router.push("/dashboard");
        }
        return;
      }
    } catch {
      // Fallback si no hay endpoint o el backend no responde
    }

    // 3. Fallback para cualquier otro email con rol por defecto JEFE_OPERATIVO
    if (credentials.password.length >= 4) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      const fallbackUser: User = {
        id: 99,
        email: emailNorm,
        nombre: emailNorm.split("@")[0].toUpperCase(),
        rol: "JEFE_OPERATIVO",
        activo: true,
      };
      const fallbackToken = `mock_token_${Date.now()}`;
      setAuthSession(fallbackToken, fallbackUser, remember);
      setUser(fallbackUser);
      toast.success(`Bienvenido al sistema: ${fallbackUser.nombre}`);
      if (typeof window !== "undefined") {
        window.location.href = "/dashboard";
      } else {
        router.push("/dashboard");
      }
      return;
    }

    throw new Error("Credenciales inválidas. Verifica tu correo y contraseña.");
  };

  /**
   * Método de Logout
   */
  const logout = (): void => {
    clearAuthSession();
    setUser(null);
    toast.info("Has cerrado sesión exitosamente");
    if (typeof window !== "undefined") {
      window.location.href = "/";
    } else {
      router.push("/");
    }
  };

  /**
   * Valida si el rol del usuario está permitido
   */
  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return false;
    return roles.includes(user.rol);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe ser utilizado dentro de un <AuthProvider>");
  }
  return context;
}
