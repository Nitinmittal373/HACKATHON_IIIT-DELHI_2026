import type { Alert, Check, Project, Report, SearchResponse, Watch } from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Search reads live pages, so it is allowed to take a while; everything else is quick.
const SEARCH_TIMEOUT_MS = 90_000;
const REQUEST_TIMEOUT_MS = 20_000;

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
  options: { method?: "GET" | "POST"; body?: unknown; timeoutMs?: number } = {},
): Promise<T> {
  const { method = "GET", body, timeoutMs = REQUEST_TIMEOUT_MS } = options;
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      cache: "no-store",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch {
    throw new ApiError("The NeevCheck service could not be reached", UNREACHABLE);
  }
  if (!response.ok) throw await toApiError(response);
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
    // The body was not JSON; the status message above is enough.
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

export function searchProjects(query: string): Promise<SearchResponse> {
  return request(`/api/projects/search?q=${encodeURIComponent(query)}`, {
    timeoutMs: SEARCH_TIMEOUT_MS,
  });
}

/** `fresh` skips the reuse of a check from the last 24 hours ("Re-check now"). */
export function createCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  // Old-format numbers have a fixed page; only new-format ones need the link from search.
  const body = {
    rera_id: project.rera_id,
    ...(project.rera_id.includes("/") ? { details_url: project.details_url } : {}),
    ...(options.fresh ? { fresh: true } : {}),
  };
  return request("/api/checks", { method: "POST", body });
}

export function createWatch(
  project: Pick<Project, "rera_id" | "details_url">,
  email: string,
  language: "en" | "hi",
): Promise<Watch> {
  const body = {
    rera_id: project.rera_id,
    ...(project.rera_id.includes("/") ? { details_url: project.details_url } : {}),
    email,
    language,
  };
  return request("/api/sentinel", { method: "POST", body });
}

export function getAlerts(email: string): Promise<Alert[]> {
  return request(`/api/sentinel/alerts?email=${encodeURIComponent(email)}`);
}

export function getCheck(id: string): Promise<Check> {
  return request(`/api/checks/${id}`);
}

export function getReport(id: string): Promise<Report> {
  return request(`/api/checks/${id}/report`);
}

export function eventsUrl(id: string): string {
  return `${API_URL}/api/checks/${id}/events`;
}
