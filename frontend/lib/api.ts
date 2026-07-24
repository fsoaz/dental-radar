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
  if (typeof window === "undefined") {
    return (
      process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000/api/v1"
    );
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = response.statusText;
    let code: string | null = null;
    try {
      const body = (await response.json()) as ApiErrorBody | FastApiValidationErrorBody;
      if ("error" in body && body.error?.message) {
        message = body.error.message;
        code = body.error.code ?? null;
      } else if ("detail" in body && Array.isArray(body.detail)) {
        // FastAPI's built-in request validation errors use {"detail": [...]},
        // not this app's custom {"error": {...}} envelope.
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

export function buildClinicListQuery(searchParams: URLSearchParams): ClinicListQuery {
  const minScore = searchParams.get("min_score");
  const maxScore = searchParams.get("max_score");
  const hasWebsite = searchParams.get("has_website");

  return {
    q: searchParams.get("q") ?? undefined,
    state: searchParams.get("state") ?? undefined,
    priority: (searchParams.get("priority") as ClinicListQuery["priority"]) ?? undefined,
    min_score: minScore ? Number(minScore) : undefined,
    max_score: maxScore ? Number(maxScore) : undefined,
    has_website:
      hasWebsite === "true" ? true : hasWebsite === "false" ? false : undefined,
    signal_type: searchParams.get("signal_type") ?? undefined,
    sort: searchParams.get("sort") ?? "-score",
    page: Number(searchParams.get("page") ?? "1"),
    page_size: Number(searchParams.get("page_size") ?? "20"),
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
  if (query.sort) params.set("sort", query.sort);
  if (query.page && query.page > 1) params.set("page", String(query.page));
  if (query.page_size && query.page_size !== 20) params.set("page_size", String(query.page_size));
  return params;
}
