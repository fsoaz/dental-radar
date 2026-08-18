import type {
  ApiErrorBody,
  ClinicDetail,
  ClinicListQuery,
  ClinicListResponse,
  FastApiValidationErrorBody,
  ScoringConfig,
} from "@/lib/types";

export class ApiRequestError extends Error {
  status: number;
  code: string | null;

  constructor(message: string, status: number, code: string | null = null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

export function getApiBaseUrl(): string {
  return "/api/backend";
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

function parsePositiveInt(raw: string | null, fallback: number): number {
  if (raw == null || raw === "") return fallback;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 1 ? Math.floor(value) : fallback;
}

function parseOptionalNonNegInt(raw: string | null): number | undefined {
  if (raw == null || raw === "") return undefined;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? Math.floor(value) : undefined;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  const method = (init?.method ?? "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD" && init?.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new ApiRequestError("Can't reach the service. Check that the API is running.", 0, "NETWORK_ERROR");
  }

  if (!response.ok) {
    let message = response.statusText;
    let code: string | null = null;
    try {
      const body = (await response.json()) as ApiErrorBody | FastApiValidationErrorBody;
      if ("error" in body && body.error?.message) {
        message = body.error.message;
        code = body.error.code ?? null;
      } else if ("detail" in body && Array.isArray(body.detail)) {
        message = body.detail
          .map((item) => {
            const field = item.loc?.slice(1).join(".") || "request";
            return `${field}: ${item.msg}`;
          })
          .join("; ");
        code = "VALIDATION_ERROR";
      }
    } catch {
      // ignore parse errors
    }

    if (response.status === 401) {
      message = "Operator authorization is unavailable. Contact the deployment administrator.";
      code = code ?? "UNAUTHORIZED";
    } else if (response.status >= 500 && !code) {
      message = "Something went wrong. Please try again.";
      code = "INTERNAL_ERROR";
    } else if (response.status >= 400 && response.status < 500 && code === "VALIDATION_ERROR") {
      message = "That link isn't valid — reset filters and try again.";
    }

    throw new ApiRequestError(message, response.status, code);
  }

  return (await response.json()) as T;
}

export async function fetchClinics(query: ClinicListQuery = {}): Promise<ClinicListResponse> {
  const qs = buildQuery({
    q: query.q,
    state: query.state,
    priority: query.priority,
    min_score: query.min_score,
    max_score: query.max_score,
    has_website: query.has_website,
    signal_type: query.signal_type,
    sort: query.sort ?? "-score",
    page: query.page ?? 1,
    page_size: query.page_size ?? 20,
  });
  return request<ClinicListResponse>(`/clinics${qs}`);
}

export async function fetchClinicDetail(id: string): Promise<ClinicDetail> {
  return request<ClinicDetail>(`/clinics/${encodeURIComponent(id)}`);
}

export async function fetchScoringConfig(): Promise<ScoringConfig> {
  return request<ScoringConfig>("/scoring-config");
}

export async function updateScoringConfig(body: {
  weights: Record<string, number>;
  bands: Array<{ name: string; min: number; max: number | null }>;
  rescore?: boolean;
}): Promise<ScoringConfig & { rescored?: number }> {
  return request("/scoring-config", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function detectClinicSignals(clinicId: string): Promise<unknown> {
  return request(`/clinics/${encodeURIComponent(clinicId)}/signals:detect`, {
    method: "POST",
  });
}

export async function enrichClinic(clinicId: string, force = false): Promise<unknown> {
  const qs = force ? "?force=true" : "";
  return request(`/clinics/${encodeURIComponent(clinicId)}/enrich${qs}`, {
    method: "POST",
  });
}

export async function scoreClinic(clinicId: string): Promise<unknown> {
  return request(`/clinics/${encodeURIComponent(clinicId)}/score`, {
    method: "POST",
  });
}

export function buildClinicListQuery(searchParams: URLSearchParams): ClinicListQuery {
  const hasWebsite = searchParams.get("has_website");

  return {
    q: searchParams.get("q") ?? undefined,
    state: searchParams.get("state") ?? undefined,
    priority: (searchParams.get("priority") as ClinicListQuery["priority"]) ?? undefined,
    min_score: parseOptionalNonNegInt(searchParams.get("min_score")),
    max_score: parseOptionalNonNegInt(searchParams.get("max_score")),
    has_website:
      hasWebsite === "true" ? true : hasWebsite === "false" ? false : undefined,
    signal_type: searchParams.get("signal_type") ?? undefined,
    sort: searchParams.get("sort") ?? "-score",
    page: parsePositiveInt(searchParams.get("page"), 1),
    page_size: parsePositiveInt(searchParams.get("page_size"), 20),
  };
}

export function clinicListQueryToSearchParams(query: ClinicListQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.state) params.set("state", query.state);
  if (query.priority) params.set("priority", query.priority);
  if (query.min_score != null) params.set("min_score", String(query.min_score));
  if (query.max_score != null) params.set("max_score", String(query.max_score));
  if (query.has_website != null) params.set("has_website", String(query.has_website));
  if (query.signal_type) params.set("signal_type", query.signal_type);
  if (query.sort && query.sort !== "-score") params.set("sort", query.sort);
  if (query.page && query.page > 1) params.set("page", String(query.page));
  if (query.page_size && query.page_size !== 20) params.set("page_size", String(query.page_size));
  return params;
}

export function userFacingFetchError(err: unknown): string {
  if (err instanceof ApiRequestError) {
    if (err.code === "NETWORK_ERROR" || err.status === 0) {
      return "Can't reach the service. Check that the API is running.";
    }
    if (err.status >= 400 && err.status < 500) {
      return err.message || "That link isn't valid — reset filters.";
    }
    if (err.status >= 500) {
      return "Something went wrong. Please try again.";
    }
    return err.message;
  }
  return "Failed to load clinics";
}
