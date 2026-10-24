// Mirrors backend/app/models.py and backend/app/scoring.py. Keep the two in sync.

export type Lane = "rera" | "mca" | "ibbi" | "authority" | "news";
export type EvidenceStatus = "verified" | "partially_verified" | "requires_review";
export type SourceType = "official" | "registry_mirror" | "news" | "other";
export type CheckOutcome = "found" | "not_found" | "unavailable" | "captcha" | "skipped";

export interface Evidence {
  n: number;
  lane: Lane;
  claim: string;
  source_url: string;
  source_type: SourceType;
  status: EvidenceStatus;
  snippet: string;
  fetched_at: string;
}

export interface Check {
  lane: Lane;
  what: string;
  outcome: CheckOutcome;
  detail: string;
}

export interface Signals {
  registration_status: string | null;
  extensions_count: number | null;
  force_majeure_extensions: number | null;
  delay_months: number | null;
  qprs_missed_last4: number | null;
  rera_penalty_orders: number | null;
  rera_complaints: number | null;
  total_units: number | null;
  promised_completion: string | null;
  revised_completion: string | null;
  promoter_in_cirp: boolean | null;
  cirp_scope: "company" | "this_project" | "other_project" | null;
  insolvency_case_found: boolean | null;
  insolvency_reported_in_news: boolean | null;
  company_status: string | null;
  open_charges: number | null;
  directors: number | null;
  cin: string | null;
  authority_defaulter: boolean | null;
  adverse_news_count: number | null;
}

export interface Reason {
  code: string;
  impact: number;
  pillar: string | null;
  text: string;
  status: "verified" | "requires_review";
}

export interface Pillar {
  name: string;
  weight: number;
  penalty: number;
  checked: boolean;
}

export interface Score {
  version: string;
  score: number;
  band: string;
  hard_stop: boolean;
  hard_stop_code: string | null;
  formula_score: number;
  weighted_penalty: number;
  confidence: number;
  signals_checked: string[];
  signals_missing: string[];
  pillars: Record<string, Pillar>;
  reasons: Reason[];
}

export interface GraphNode {
  id: string;
  label: string;
  kind: "promoter" | "project" | "group";
  status: string;
  risk: "high" | "review" | "none";
}

export interface GraphEdge {
  source: string;
  target: string;
  verified: boolean;
  label: string;
}

export interface Report {
  id: string;
  query: string;
  project_name: string | null;
  rera_number: string | null;
  promoter_name: string | null;
  rera_url: string | null;
  photo_url: string | null;
  signals: Signals;
  evidence: Evidence[];
  checks: Check[];
  lanes: { lane: Lane; ok: boolean; message: string }[];
  score: Score;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  demo_replay: boolean;
  created_at: string;
}

export interface ReportSummary {
  id: string;
  query: string;
  project_name: string | null;
  promoter_name: string | null;
  score: number;
  band: string;
  confidence: number;
  hard_stop: boolean;
  created_at: string;
  watching: boolean;
}

export interface LiveEvent {
  lane: Lane | "score";
  type: "started" | "progress" | "streaming_url" | "done" | "error" | "report";
  message: string;
  ts: string;
  score?: number;
  band?: string;
}

export interface AskAnswer {
  intent: string | null;
  answer: string;
  citations: number[];
}

export interface Alert {
  id: number;
  report_id: string | null;
  received_at: string;
  payload: Record<string, unknown>;
}
