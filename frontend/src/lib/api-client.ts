/**
 * Cliente HTTP Centralizado para la API FastAPI de VehículosRC
 * Base URL: NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
 * Soporte integrado para Tokens JWT (Authorization: Bearer <token>) e interceptor 401
 */

import { getAuthToken, clearAuthSession } from "@/lib/auth-cookies";

export class ApiError extends Error {
  public status: number;
  public statusText: string;
  public data: any;
  public url: string;

  constructor(message: string, status: number, statusText: string, data: any, url: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.data = data;
    this.url = url;
  }
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined"
    ? "/api/v1"
    : "http://127.0.0.1:8000/api/v1");

/**
 * Genera los headers estándar incluyendo el JWT de la cookie si existe
 */
function getStandardHeaders(customHeaders?: HeadersInit): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (customHeaders) {
    if (customHeaders instanceof Headers) {
      customHeaders.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(customHeaders)) {
      customHeaders.forEach(([key, value]) => {
        headers[key] = value;
      });
    } else {
      Object.assign(headers, customHeaders);
    }
  }

  return headers;
}

/**
 * Manejador centralizado de respuestas y captura de 401 (No autorizado)
 */
async function handleResponse(response: Response, endpoint: string, url: string) {
  if (response.status === 401) {
    if (typeof window !== "undefined") {
      clearAuthSession();
      // Redireccionar al login si no estamos ya en él
      if (window.location.pathname !== "/") {
        window.location.href = "/?session=expired";
      }
    }
    throw new ApiError(
      "Sesión expirada o no autorizada. Por favor inicia sesión nuevamente.",
      401,
      response.statusText,
      null,
      url
    );
  }

  if (!response.ok) {
    let errorData: any;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    throw new ApiError(
      `Error en ${endpoint}: ${response.status} ${response.statusText}`,
      response.status,
      response.statusText,
      errorData,
      url
    );
  }
}

/**
 * Convierte un objeto de parámetros en un string de query URL, ignorando nulos o undefined.
 */
function buildQueryString(params?: Record<string, any>): string {
  if (!params) return "";
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        value.forEach((val) => query.append(key, String(val)));
      } else {
        query.append(key, String(value));
      }
    }
  });

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * Normaliza la URL relativa contra el API_BASE_URL
 */
function formatUrl(endpoint: string, params?: Record<string, any>): string {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const base = API_BASE_URL.endsWith("/") ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${base}${cleanEndpoint}${buildQueryString(params)}`;
}

/**
 * Cliente HTTP con manejo de errores, inyección de JWT y tipado
 */
export const apiClient = {
  /**
   * Petición GET
   */
  async get<T>(
    endpoint: string,
    params?: Record<string, any>,
    customHeaders?: HeadersInit
  ): Promise<T> {
    const url = formatUrl(endpoint, params);
    const response = await fetch(url, {
      method: "GET",
      headers: getStandardHeaders(customHeaders),
    });

    await handleResponse(response, `GET ${endpoint}`, url);
    return response.json() as Promise<T>;
  },

  /**
   * Petición POST
   */
  async post<T>(
    endpoint: string,
    body?: any,
    params?: Record<string, any>,
    customHeaders?: HeadersInit
  ): Promise<T> {
    const url = formatUrl(endpoint, params);
    const response = await fetch(url, {
      method: "POST",
      headers: getStandardHeaders(customHeaders),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    await handleResponse(response, `POST ${endpoint}`, url);

    // Manejar respuestas 204 o sin contenido
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json() as Promise<T>;
    }
    return {} as T;
  },

  /**
   * Petición PUT
   */
  async put<T>(
    endpoint: string,
    body?: any,
    params?: Record<string, any>,
    customHeaders?: HeadersInit
  ): Promise<T> {
    const url = formatUrl(endpoint, params);
    const response = await fetch(url, {
      method: "PUT",
      headers: getStandardHeaders(customHeaders),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    await handleResponse(response, `PUT ${endpoint}`, url);
    return response.json() as Promise<T>;
  },

  /**
   * Petición DELETE
   */
  async delete<T>(
    endpoint: string,
    params?: Record<string, any>,
    customHeaders?: HeadersInit
  ): Promise<T> {
    const url = formatUrl(endpoint, params);
    const response = await fetch(url, {
      method: "DELETE",
      headers: getStandardHeaders(customHeaders),
    });

    await handleResponse(response, `DELETE ${endpoint}`, url);

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json() as Promise<T>;
    }
    return {} as T;
  },

  /**
   * Descarga de archivos binarios (Excel, PDF)
   */
  async downloadBlob(
    endpoint: string,
    params?: Record<string, any>
  ): Promise<{ blob: Blob; filename: string }> {
    const url = formatUrl(endpoint, params);
    const response = await fetch(url, {
      method: "GET",
      headers: getStandardHeaders(),
    });

    await handleResponse(response, `DOWNLOAD ${endpoint}`, url);

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    let filename = "reporte_exportado";

    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    return { blob, filename };
  },
};
