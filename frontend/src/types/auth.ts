export type UserRole = "ADMIN" | "JEFE_OPERATIVO" | "VISUALIZADOR";

export interface User {
  id: number;
  email: string;
  nombre: string;
  rol: UserRole;
  activo: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthSession {
  token: string | null;
  user: User | null;
}
