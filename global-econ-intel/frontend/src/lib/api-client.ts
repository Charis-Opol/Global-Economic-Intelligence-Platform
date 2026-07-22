import type {
  Country,
  Crypto,
  ExchangeRate,
  GDPRecord,
  Inflation,
  NewsArticle,
  Page,
  PipelineStatusEntry,
  PredictionResponse,
  RegisteredModel,
  ServiceHealthEntry,
  TokenResponse,
  Weather,
} from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const TOKEN_STORAGE_KEY = "gei_access_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/** Fired whenever a request comes back 401 - AuthProvider listens for this
 * to clear state and bounce to /login, so any call site (a query, a form
 * submit) gets the same session-expiry behavior for free. */
export const UNAUTHORIZED_EVENT = "gei:unauthorized";

type QueryParams = Record<string, string | number | boolean | undefined | null>;

function buildQuery(params: QueryParams): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401) {
    setStoredToken(null);
    window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
    throw new ApiError(401, "Not authenticated");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}) as { detail?: string });
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  countries: (params: { search?: string; limit?: number; offset?: number } = {}) =>
    request<Page<Country>>(`/countries${buildQuery(params)}`),

  gdp: (
    params: {
      country?: string;
      indicator_id?: string;
      year_min?: number;
      year_max?: number;
      limit?: number;
      offset?: number;
    } = {},
  ) => request<Page<GDPRecord>>(`/gdp${buildQuery(params)}`),

  inflation: (
    params: {
      country?: string;
      indicator_id?: string;
      year_min?: number;
      year_max?: number;
      limit?: number;
      offset?: number;
    } = {},
  ) => request<Page<Inflation>>(`/inflation${buildQuery(params)}`),

  exchangeRates: (
    params: {
      base?: string;
      quote?: string;
      date_from?: string;
      date_to?: string;
      limit?: number;
      offset?: number;
    } = {},
  ) => request<Page<ExchangeRate>>(`/exchange${buildQuery(params)}`),

  weather: (
    params: {
      latitude?: number;
      longitude?: number;
      date_from?: string;
      date_to?: string;
      limit?: number;
      offset?: number;
    } = {},
  ) => request<Page<Weather>>(`/weather${buildQuery(params)}`),

  crypto: (
    params: { coin_id?: string; date_from?: string; date_to?: string; limit?: number; offset?: number } = {},
  ) => request<Page<Crypto>>(`/crypto${buildQuery(params)}`),

  news: (
    params: {
      source?: string;
      date_from?: string;
      date_to?: string;
      q?: string;
      limit?: number;
      offset?: number;
    } = {},
  ) => request<Page<NewsArticle>>(`/news${buildQuery(params)}`),

  predict: (params: {
    domain: string;
    country?: string;
    base?: string;
    quote?: string;
    coin_id?: string;
  }) => request<PredictionResponse>(`/predictions${buildQuery(params)}`),

  models: () => request<RegisteredModel[]>("/models"),

  pipelineStatus: () => request<PipelineStatusEntry[]>("/pipeline-status"),

  serviceHealth: () => request<ServiceHealthEntry[]>("/monitoring/services"),

  supersetGuestToken: (dashboard: string) =>
    request<{ token: string; dashboard_id: string }>(`/superset/guest-token${buildQuery({ dashboard })}`),
};
