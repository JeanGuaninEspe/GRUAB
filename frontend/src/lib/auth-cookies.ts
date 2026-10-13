import Cookies from "js-cookie";
import { AuthSession, User } from "@/types/auth";

export const TOKEN_COOKIE_NAME = "token_rc";
export const USER_COOKIE_NAME = "user_rc";

const isSecure =
  process.env.NODE_ENV === "production" ||
  (typeof window !== "undefined" && window.location.protocol === "https:");

const COOKIE_OPTIONS: Cookies.CookieAttributes = {
  path: "/",
  sameSite: "lax",
  secure: isSecure,
};

/**
 * Guarda la sesión de autenticación (JWT y usuario) en cookies seguras y localStorage.
 */
export function setAuthSession(
  token: string,
  user: User,
  remember: boolean = true
): void {
  const options: Cookies.CookieAttributes = {
    ...COOKIE_OPTIONS,
    ...(remember ? { expires: 30 } : {}), // 30 días si recordar está activo
  };

  Cookies.set(TOKEN_COOKIE_NAME, token, options);
  Cookies.set(USER_COOKIE_NAME, JSON.stringify(user), options);

  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(TOKEN_COOKIE_NAME, token);
      localStorage.setItem(USER_COOKIE_NAME, JSON.stringify(user));
    } catch {
      // Ignore localStorage exceptions in private mode
    }
  }
}

/**
 * Obtiene el token JWT actual almacenado en cookies o localStorage.
 */
export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const fromCookie = Cookies.get(TOKEN_COOKIE_NAME);
  if (fromCookie) return fromCookie;
  try {
    return localStorage.getItem(TOKEN_COOKIE_NAME);
  } catch {
    return null;
  }
}

/**
 * Obtiene el objeto de usuario activo parseado desde las cookies o localStorage.
 */
export function getAuthUser(): User | null {
  if (typeof window === "undefined") return null;
  const userCookie = Cookies.get(USER_COOKIE_NAME);
  if (userCookie) {
    try {
      return JSON.parse(userCookie) as User;
    } catch {
      // continue to localStorage
    }
  }

  try {
    const fromStorage = localStorage.getItem(USER_COOKIE_NAME);
    if (fromStorage) {
      return JSON.parse(fromStorage) as User;
    }
  } catch {
    // Ignore error
  }
  return null;
}

/**
 * Obtiene la sesión completa (token y usuario).
 */
export function getAuthSession(): AuthSession {
  return {
    token: getAuthToken(),
    user: getAuthUser(),
  };
}

/**
 * Limpia todas las cookies de sesión y localStorage cerrando la autenticación.
 */
export function clearAuthSession(): void {
  Cookies.remove(TOKEN_COOKIE_NAME, { path: "/" });
  Cookies.remove(USER_COOKIE_NAME, { path: "/" });
  if (typeof window !== "undefined") {
    try {
      localStorage.removeItem(TOKEN_COOKIE_NAME);
      localStorage.removeItem(USER_COOKIE_NAME);
    } catch {
      // Ignore
    }
  }
}
