/**
 * Cliente HTTP tipado para la API de ALMATE Propiedades.
 *
 * * Usa `fetch` (sin dependencias).
 * * Adjunta el token Bearer guardado en `localStorage` cuando `auth` es true.
 * * Normaliza los errores del backend en `ApiError` (mensaje + detalle por campo).
 * * En 401 limpia la sesión para que el guard de rutas redirija al login.
 */

const TOKEN_KEY = "almate.token";
const USER_KEY = "almate.user";

export class ApiError extends Error {
  readonly status: number;
  readonly errors: { loc: string[]; msg: string; type?: string }[];

  constructor(
    status: number,
    message: string,
    errors: { loc: string[]; msg: string; type?: string }[] = [],
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errors = errors;
  }

  /** Devuelve el mensaje de un campo concreto, si el backend lo detalló. */
  fieldError(field: string): string | undefined {
    const found = this.errors.find((error) => error.loc.includes(field));
    return found?.msg;
  }
}

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string | null, userJson: string | null): void {
  if (token && userJson) {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.localStorage.setItem(USER_KEY, userJson);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  }
}

export function getStoredUser<T>(): T | null {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
}

async function parseError(response: Response): Promise<ApiError> {
  let message = "Ocurrió un error inesperado.";
  let errors: { loc: string[]; msg: string; type?: string }[] = [];
  try {
    const payload = (await response.json()) as {
      message?: string;
      errors?: { loc: string[]; msg: string; type?: string }[];
    };
    if (payload.message) message = payload.message;
    if (Array.isArray(payload.errors)) errors = payload.errors;
  } catch {
    // Respuesta sin JSON: mantenemos el mensaje genérico.
  }
  if (response.status === 401) setSession(null, null);
  return new ApiError(response.status, message, errors);
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = false, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };

  if (body !== undefined && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      signal,
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "No pudimos conectar con el servidor. Reintentá en unos minutos.");
  }

  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string, options: RequestOptions = {}) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  put: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options: RequestOptions = {}) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

/** Convierte parámetros de filtro a query string (omite vacíos). */
export function toQuery(params: Record<string, string | number | boolean | null | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "" || value === false) continue;
    query.set(key, String(value));
  }
  const text = query.toString();
  return text ? `?${text}` : "";
}
