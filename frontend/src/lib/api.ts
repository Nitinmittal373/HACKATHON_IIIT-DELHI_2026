import type {
  Alert,
  Check,
  CheckCreate,
  CheckSummary,
  Comparison,
  CorrectionCreate,
  ExtractResponse,
  Project,
  PromoterSearchResponse,
  RecentCheck,
  Report,
  SearchResponse,
  TrackRecord,
  Watch,
  WatchCreate,
} from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Search reads live pages and the free-plan server may first need a minute to wake up, so it
// is allowed to take a while; everything else is quick.
const SEARCH_TIMEOUT_MS = 120_000;
const WAKE_TIMEOUT_MS = 90_000;
const REQUEST_TIMEOUT_MS = 20_000;
// A server that answered recently is still awake; the free plan sleeps after 15 idle minutes.
const AWAKE_FOR_MS = 5 * 60_000;
// Proxy answers while the server starts. Our own errors carry a code and are never retried.
const STARTING_UP_STATUSES = [502, 503, 504];

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** Seconds to wait before trying again, from a 429 answer. */
    readonly retryAfter: number | null = null,
    /** A short machine-readable reason some answers carry, such as "daily_cap". */
    readonly code: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** 0 means the backend could not be reached at all. */
export const UNREACHABLE = 0;

async function request<T>(
  path: string,
  options: {
    method?: "GET" | "POST" | "DELETE";
    body?: unknown;
    file?: File;
    timeoutMs?: number;
    /** The sign-in token from /api/bridge-token, for the account routes. */
    token?: string;
  } = {},
): Promise<T> {
  const { method = "GET", body, file, timeoutMs = REQUEST_TIMEOUT_MS, token } = options;
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      cache: "no-store",
      headers: {
        ...(file ? { "Content-Type": "application/pdf" } : {}),
        ...(!file && body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      // A file goes as the raw request body, so the server needs no multipart parser.
      body: file ?? (body === undefined ? undefined : JSON.stringify(body)),
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    // A request we gave up on is not a dropped connection, and retrying it would double the wait.
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    throw new ApiError(
      timedOut ? "The NeevCheck service did not answer in time" : "The NeevCheck service could not be reached",
      UNREACHABLE,
      null,
      timedOut ? "client_timeout" : null,
    );
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  const retry = Number(response.headers.get("Retry-After"));
  let message = `The request failed (${response.status})`;
  let code: string | null = null;
  try {
    const payload = (await response.json()) as { detail?: unknown };
    message = describeDetail(payload.detail) ?? message;
    code = codeOf(payload.detail);
  } catch {
    // The body was not JSON (a proxy page, for example); the status message above is enough.
  }
  const wait = Number.isFinite(retry) && retry > 0 ? retry : null;
  return new ApiError(message, response.status, wait, code);
}

function describeDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown } | undefined;
    if (first && typeof first.msg === "string") return first.msg;
  }
  const message = (detail as { message?: unknown } | null)?.message;
  return typeof message === "string" ? message : null;
}

function codeOf(detail: unknown): string | null {
  const code = (detail as { code?: unknown } | null)?.code;
  return typeof code === "string" ? code : null;
}

let awakeSince = 0;
let wakePing: Promise<boolean> | null = null;

/**
 * A silent GET /api/health that wakes a sleeping free-plan server. The home page fires it on
 * load and the confirm page waits for the same request, so a visitor pays the start-up once.
 */
export function wakeServer(): Promise<boolean> {
  if (Date.now() - awakeSince < AWAKE_FOR_MS) return Promise.resolve(true);
  wakePing ??= request<{ status: string }>("/api/health", { timeoutMs: WAKE_TIMEOUT_MS }).then(
    () => {
      awakeSince = Date.now();
      wakePing = null;
      return true;
    },
    () => {
      wakePing = null;
      return false;
    },
  );
  return wakePing;
}

/** A dropped connection or a proxy error while the server starts: worth one more try. */
export function isTransient(error: unknown): boolean {
  if (!(error instanceof ApiError) || error.code !== null) return false;
  return error.status === UNREACHABLE || STARTING_UP_STATUSES.includes(error.status);
}

/** Runs in the browser, straight to the API, and tries once more after a transient failure. */
export async function searchProjects(query: string, locality?: string): Promise<SearchResponse> {
  const place = locality ? `&locality=${encodeURIComponent(locality)}` : "";
  const search = () =>
    request<SearchResponse>(`/api/projects/search?q=${encodeURIComponent(query)}${place}`, {
      timeoutMs: SEARCH_TIMEOUT_MS,
    });
  try {
    return await search();
  } catch (error) {
    if (!isTransient(error)) throw error;
    return search();
  }
}

/** A builder's registered projects and company pages, from up-rera.in and the open web. */
export function searchBuilder(builder: string, city?: string): Promise<PromoterSearchResponse> {
  const extra = city ? `&city=${encodeURIComponent(city)}` : "";
  return request<PromoterSearchResponse>(
    `/api/promoters/search?q=${encodeURIComponent(builder)}${extra}`,
    { timeoutMs: SEARCH_TIMEOUT_MS },
  );
}

/** Numbers in a PDF the visitor chose. The file is read in memory by the server and not kept. */
export function extractFromPdf(file: File): Promise<ExtractResponse> {
  return request<ExtractResponse>("/api/extract", {
    method: "POST",
    file,
    timeoutMs: SEARCH_TIMEOUT_MS,
  });
}

/** Numbers in the text a QR code held; the picture itself never leaves the device. */
export function extractFromText(text: string): Promise<ExtractResponse> {
  return request<ExtractResponse>("/api/extract", {
    method: "POST",
    body: { text },
    timeoutMs: SEARCH_TIMEOUT_MS,
  });
}

/** `fresh` skips the reuse of a check from the last 24 hours ("Re-check now"). */
export function createCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  // The page search confirmed: many numbers registered after 2018 have no stable address.
  const body: CheckCreate = {
    rera_id: project.rera_id,
    details_url: project.details_url,
    ...(options.fresh ? { fresh: true } : {}),
  };
  return request<Check>("/api/checks", { method: "POST", body });
}

/** Watches a project; the alert goes to the signed-in account's email, which the API knows. */
export function createWatch(
  token: string,
  project: Pick<Project, "rera_id" | "details_url">,
  language: WatchCreate["language"],
): Promise<Watch> {
  const body: WatchCreate = { rera_id: project.rera_id, details_url: project.details_url, language };
  return request<Watch>("/api/sentinel", { method: "POST", body, token });
}

export function sendCorrection(body: CorrectionCreate): Promise<{ id: string }> {
  return request<{ id: string }>("/api/corrections", { method: "POST", body });
}

/** Stops the watch behind a link in an alert email. Answers the same for any token. */
export function unsubscribe(token: string): Promise<void> {
  return request<void>("/api/sentinel/unsubscribe", { method: "POST", body: { token } });
}

export function removeWatch(token: string, watchId: string): Promise<void> {
  return request<void>(`/api/sentinel/${watchId}`, { method: "DELETE", token });
}

/** The signed-in account's alerts, newest first. */
export function getAlerts(token: string): Promise<Alert[]> {
  return request<Alert[]>("/api/sentinel/alerts", { token, timeoutMs: WAKE_TIMEOUT_MS });
}

/** The checks a visitor started, for "My reports". Ids the server no longer has are left out. */
export function listChecks(ids: string[]): Promise<CheckSummary[]> {
  return request<CheckSummary[]>(`/api/checks?ids=${ids.join(",")}`, { timeoutMs: WAKE_TIMEOUT_MS });
}

/** Two or three finished checks side by side. */
export function compareChecks(ids: string[]): Promise<Comparison> {
  return request<Comparison>(`/api/checks/compare?ids=${ids.join(",")}`, {
    timeoutMs: WAKE_TIMEOUT_MS,
  });
}

/** A promoter's other projects, found with Search on up-rera.in. */
export function promoterProjects(promoter: string, exclude: string): Promise<TrackRecord> {
  const query = `name=${encodeURIComponent(promoter)}&exclude=${encodeURIComponent(exclude)}`;
  return request<TrackRecord>(`/api/promoters/projects?${query}`, { timeoutMs: WAKE_TIMEOUT_MS });
}

const RECENT_FRESH_FOR_MS = 60_000;
let recent: { at: number; checks: Promise<RecentCheck[]> } | null = null;

/** The latest finished checks site-wide. The hero card and the strip below it share one request. */
export function recentChecks(): Promise<RecentCheck[]> {
  if (!recent || Date.now() - recent.at > RECENT_FRESH_FOR_MS) {
    const checks = request<RecentCheck[]>("/api/checks/recent", { timeoutMs: WAKE_TIMEOUT_MS });
    recent = { at: Date.now(), checks };
    checks.catch(() => (recent = null));
  }
  return recent.checks;
}

/** The checks saved to the signed-in account, newest first. */
export function listAccountReports(token: string): Promise<CheckSummary[]> {
  return request<CheckSummary[]>("/api/me/reports", { token, timeoutMs: WAKE_TIMEOUT_MS });
}

/** Saves check ids (newest first) to the account; answers with the account's whole list. */
export function saveAccountReports(token: string, ids: string[]): Promise<CheckSummary[]> {
  return request<CheckSummary[]>("/api/me/reports", { method: "POST", body: { ids }, token });
}

/** Deletes the account and its saved reports. */
export function deleteAccount(token: string): Promise<void> {
  return request<void>("/api/me", { method: "DELETE", token });
}

export function forgetAccountReport(token: string, id: string): Promise<void> {
  return request<void>(`/api/me/reports/${id}`, { method: "DELETE", token });
}

export function getCheck(id: string): Promise<Check> {
  return request<Check>(`/api/checks/${id}`);
}

export function getReport(id: string): Promise<Report> {
  return request<Report>(`/api/checks/${id}/report`);
}

export function eventsUrl(id: string): string {
  return `${API_URL}/api/checks/${id}/events`;
}
