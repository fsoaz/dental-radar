export type PriorityLevel = "COLD" | "WARM" | "HOT" | "IMMEDIATE";

export interface ClinicListItem {
  id: string;
  name: string;
  city: string | null;
  state: string | null;
  score: number | null;
  priority: PriorityLevel | null;
  growth_probability: number | null;
}

export interface ClinicListResponse {
  data: ClinicListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface Address {
  street: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string | null;
}

export interface Signal {
  type: string;
  applied_weight: number;
  evidence: string | null;
  confidence: number;
  detected_at: string | null;
}

export interface Score {
  total: number;
  priority: PriorityLevel;
  breakdown: Record<string, number>;
  config_version: number | null;
}

export interface Enrichment {
  growth_probability: number | null;
  technology_maturity: number | null;
  marketing_sophistication: number | null;
  expansion_probability: number | null;
  explanation: string | null;
}

export interface ClinicDetail {
  id: string;
  name: string;
  place_id: string;
  address: Address | null;
  phone: string | null;
  website: string | null;
  google_rating: number | null;
  google_review_count: number;
  locations_count: number;
  social_urls: string[];
  signals: Signal[];
  score: Score | null;
  enrichment: Enrichment | null;
}

export interface ScoreBand {
  name: string;
  min: number;
  max: number | null;
}

export interface ScoringConfig {
  version: number;
  active: boolean;
  weights: Record<string, number>;
  bands: ScoreBand[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown> | null;
  };
}

// FastAPI's default shape for its own built-in request validation errors —
// distinct from this app's custom ApiErrorBody envelope above.
export interface FastApiValidationErrorBody {
  detail: Array<{
    loc: Array<string | number>;
    msg: string;
    type: string;
  }>;
}

export interface ClinicListQuery {
  q?: string;
  state?: string;
  priority?: PriorityLevel | "";
  min_score?: number;
  max_score?: number;
  has_website?: boolean;
  signal_type?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

export const PRIORITY_OPTIONS: { value: PriorityLevel | ""; label: string }[] = [
  { value: "", label: "All priorities" },
  { value: "COLD", label: "Cold" },
  { value: "WARM", label: "Warm" },
  { value: "HOT", label: "Hot" },
  { value: "IMMEDIATE", label: "Immediate" },
];

export const SIGNAL_TYPE_OPTIONS = [
  { value: "", label: "All signals" },
  { value: "HIRING", label: "Hiring" },
  { value: "ADVERTISING", label: "Advertising" },
  { value: "WEBSITE_QUALITY", label: "Website quality" },
  { value: "MULTI_LOCATION", label: "Multi-location" },
  { value: "HIGH_TICKET", label: "High ticket" },
];
