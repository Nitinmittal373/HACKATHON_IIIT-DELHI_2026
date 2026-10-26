/** The backend's response shapes (backend/app/models.py). Keep the two in step. */

export type SourceName =
  | "uprera"
  | "registry"
  | "insolvency"
  | "land"
  | "consumer"
  | "news"
  | "group"
  | "sarfaesi";
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
  /** Share-style facts such as "3 of 5 group projects delayed". */
  total?: number | null;
  /** The words on the page behind the claim, at most 300 characters. */
  snippet?: string | null;
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

export type BandV2 = "Low" | "Watch" | "Elevated" | "High" | "insufficient_evidence";
export type PillarId = "P1" | "P2" | "P3" | "P4" | "P5" | "P6";

export interface Pillar {
  id: PillarId;
  name: string;
  weight: number;
  /** 0 to 100, after the pillar's cap. */
  penalty: number;
  /** Points lost on the 300-900 scale, negative. */
  points: number;
}

export interface DriverV2 {
  finding_id: string;
  pillar: PillarId;
  code: string;
  penalty: number;
  points: number;
}

export interface ReasonCode {
  code: string;
  label: string;
  finding_ids: string[];
  points: number;
}

/** NeevScore v2 (300-900). Absent on reports made before it existed. */
export interface ScoreV2 {
  value: number;
  band: BandV2;
  band_label: string;
  provisional: boolean;
  hard_stop: boolean;
  hard_stop_reason: string | null;
  confidence: number;
  pillars: Pillar[];
  reason_codes: ReasonCode[];
  drivers: DriverV2[];
  pillars_unread: PillarId[];
}

export type FamilyFlag = "cirp" | "struck_off";
export type FamilyProjectState = "ok" | "delayed" | "lapsed" | "unread";

export interface FamilyProject {
  rera_id: string;
  name: string | null;
  details_url: string;
  state: FamilyProjectState;
}

export interface FamilyCompany {
  name: string;
  status: string | null;
  status_url: string | null;
  flag: FamilyFlag | null;
  projects: FamilyProject[];
}

/** The builder's group: directors by name and DIN only, related companies and their projects. */
export interface FamilyTree {
  promoter: string;
  source_url: string;
  directors: { name: string; din: string }[];
  promoter_projects: FamilyProject[];
  companies: FamilyCompany[];
}

export interface Report {
  check: Check;
  project: Project;
  score: Score;
  findings: Finding[];
  timeline: Finding[];
  score_v2?: ScoreV2 | null;
  family?: FamilyTree | null;
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

export type InsolvencyStatus =
  | "none_found"
  | "admitted"
  | "other_project"
  | "this_project"
  | "company"
  | "unverified";

export interface AreaPoints {
  area: Area;
  label: string;
  lost: number;
  max: number;
}

export interface FindingLine {
  title: string;
  source_url: string;
  points: number;
}

/** One column of a comparison. null means the check could not read it, never "clean". */
export interface ComparedProject {
  check_id: string;
  project: Project;
  score: number;
  band: Band;
  confidence: number;
  hard_stop: boolean;
  areas: AreaPoints[];
  delay_months: number | null;
  project_complaints: number | null;
  promoter_complaints: number | null;
  insolvency: InsolvencyStatus | null;
  company_status: string | null;
  unread: CheckKey[];
  top_findings: FindingLine[];
}

export interface Comparison {
  projects: ComparedProject[];
  best: string | null;
  reason: "best_score" | "tie" | "not_enough_evidence";
}

/** A promoter's other UP-RERA projects, from Search on up-rera.in (GET /api/promoters/projects). */
export interface TrackRecord {
  promoter: string;
  projects: Project[];
  searched_at: string;
}

/** GET /api/meta: the score scale, band edges and pillar weights (backend/app/meta.py). */
export type Meta = import("@/lib/api-schema").components["schemas"]["Meta"];
