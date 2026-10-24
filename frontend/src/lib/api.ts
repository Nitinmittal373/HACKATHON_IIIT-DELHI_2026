import type { Alert, AskAnswer, Evidence, Report, ReportSummary } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Can't reach the NeevCheck server. Is the backend running on " + API_URL + "?");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep status text */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ ok: boolean; demo_mode: boolean; key_loaded: boolean; watch_ready: boolean }>("/api/health"),
  startInvestigation: (query: string) =>
    request<{ id: string }>("/api/investigations", { method: "POST", body: JSON.stringify({ query }) }),
  investigation: (id: string) =>
    request<{ id: string; status: "running" | "done" | "failed"; report_id: string | null }>(`/api/investigations/${id}`),
  eventsUrl: (id: string) => `${API_URL}/api/investigations/${encodeURIComponent(id)}/events`,
  reports: () => request<ReportSummary[]>("/api/reports"),
  report: (id: string) => request<Report>(`/api/reports/${encodeURIComponent(id)}`),
  evidence: (id: string) => request<Evidence[]>(`/api/projects/${encodeURIComponent(id)}/evidence`),
  ask: (id: string, question: string) =>
    request<AskAnswer>(`/api/reports/${encodeURIComponent(id)}/ask`, { method: "POST", body: JSON.stringify({ question }) }),
  complaint: (id: string) =>
    request<{ text: string }>(`/api/reports/${encodeURIComponent(id)}/complaint-draft`, { method: "POST" }),
  watch: (id: string) =>
    request<{ watching: boolean; monitors: number }>(`/api/projects/${encodeURIComponent(id)}/watch`, { method: "POST" }),
  watches: () => request<{ report_id: string; created_at: string }[]>("/api/watches"),
  alerts: () => request<Alert[]>("/api/alerts"),
};
