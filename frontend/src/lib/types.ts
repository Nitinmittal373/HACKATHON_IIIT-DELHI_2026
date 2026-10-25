/** The backend's response shapes (backend/app/models.py). Keep the two in step. */

export type SourceName = "uprera" | "registry" | "insolvency" | "land" | "consumer" | "news";
export type Area = "rera" | "execution" | "legal" | "financial" | "builder_history" | "news";
export type Reliability = "primary" | "secondary";
export type Verdict = "ok" | "fail" | "red_flag" | "review" | "context" | "not_found";
export type Band = "Low" | "Moderate" | "High" | "Critical" | "insufficient_evidence";
export type CheckStatus = "queued" | "running" | "completed" | "failed";
export type RunStatus = "running" | "completed" | "blocked" | "failed" | "unavailable";
export type CheckKey =
  | "registration"
  | "completion_date"
  | "extensions"
  | "company_status"
  | "insolvency"
  | "land_dues"
  | "consumer_cases";

export interface Project {
  rera_id: string;
  name: string | null;
  promoter: string | null;
  registered_on: string | null;
  district: string | null;
  details_url: string;
}

export interface SearchResponse {
  query: string;
  candidates: Project[];
}

export interface SourceRun {
  source: SourceName;
  status: RunStatus;
  live_url: string | null;
  message: string | null;
  checks_read: CheckKey[];
}

export interface Check {
  id: string;
  rera_id: string;
  details_url: string;
  status: CheckStatus;
  started_at: string;
  completed_at: string | null;
  sources: SourceRun[];
  /** Set when an earlier check of the same project was reused instead of starting a new one. */
  reused?: boolean;
}

export interface Finding {
  id: string;
  source: SourceName;
  kind: string;
  title: string;
  area: Area | null;
  verdict: Verdict;
  reliability: Reliability;
  source_url: string;
  read_on: string;
  read_at: string | null;
  occurred_on: string | null;
  count: number | null;
  months: number | null;
  scope: "company" | "this_project" | "other_project" | null;
  points?: number | null;
}

export interface Driver {
  finding_id: string;
  title: string;
  area: Area;
  penalty: number;
  points: number;
}

export interface AreaScore {
  area: Area;
  label: string;
  weight: number;
  penalty: number;
}

export interface Score {
  value: number;
  band: Band;
  band_label: string;
  confidence: number;
  provisional: boolean;
  hard_stop: boolean;
  hard_stop_reason: string | null;
  drivers: Driver[];
  areas: AreaScore[];
  checks_unread: CheckKey[];
}

export interface Report {
  check: Check;
  project: Project;
  score: Score;
  findings: Finding[];
  timeline: Finding[];
}

export type EventType =
  | "source.started"
  | "source.live_url"
  | "source.progress"
  | "finding.added"
  | "source.blocked"
  | "source.completed"
  | "check.completed";

export interface CheckEvent {
  type: EventType;
  check_id: string;
  source: SourceName | "check";
  ts: string;
  data: Record<string, unknown>;
}

/** The score summary sent with check.completed. */
export interface ScoreSummary {
  value: number;
  band: Band;
  band_label: string;
  confidence: number;
  provisional: boolean;
  hard_stop: boolean;
}

export interface Watch {
  id: string;
  rera_id: string;
  email: string;
  language: "en" | "hi";
  created_at: string;
}

export interface AlertChange {
  title: string;
  source_url: string | null;
}

export interface Alert {
  id: string;
  watch_id: string;
  rera_id: string;
  check_id: string;
  project_name: string | null;
  created_at: string;
  old_score: number | null;
  new_score: number | null;
  added: AlertChange[];
  removed: AlertChange[];
  changed: AlertChange[];
}

/** One line of "My reports" (GET /api/checks?ids=). */
export interface CheckSummary {
  id: string;
  rera_id: string;
  details_url: string;
  project: string | null;
  promoter: string | null;
  status: CheckStatus;
  score: number | null;
  band: Band | null;
  confidence: number | null;
  created_at: string;
  completed_at: string | null;
}

/** A finished check shown on the home page (GET /api/checks/recent). */
export interface RecentCheck extends CheckSummary {
  registered_on: string | null;
  sources_read: number;
  drivers: Driver[];
}
