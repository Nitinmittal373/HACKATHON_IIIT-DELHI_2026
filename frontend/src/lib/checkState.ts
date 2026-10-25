import { SOURCE_ORDER } from "@/lib/sources";
import type { Check, CheckEvent, Finding, ScoreSummary, SourceName, SourceRun } from "@/lib/types";

/** What the Agent Cam shows for one source. "unread" means the source could not be read. */
export type SourceStatus = "waiting" | "running" | "done" | "blocked" | "unread";

export interface SourceView {
  status: SourceStatus;
  liveUrl: string | null;
  /** The agent's latest note, one line. */
  note: string | null;
  /** How many notes arrived; drives the replica page cursor. */
  notes: number;
  /** Why the source stopped, when blocked or unread. */
  reason: string | null;
}

export type Outcome =
  | { status: "completed"; score: ScoreSummary | null }
  | { status: "failed"; message: string };

export interface CamState {
  sources: Record<SourceName, SourceView>;
  /** Newest first, so each new finding lands on top. */
  findings: Finding[];
  outcome: Outcome | null;
}

const BLANK_SOURCE: SourceView = {
  status: "waiting",
  liveUrl: null,
  note: null,
  notes: 0,
  reason: null,
};

export function initialState(): CamState {
  const sources = Object.fromEntries(
    SOURCE_ORDER.map((name) => [name, { ...BLANK_SOURCE }]),
  ) as Record<SourceName, SourceView>;
  return { sources, findings: [], outcome: null };
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

/** Only https pages are ever put in the live-view frame. */
function isHttps(url: string): boolean {
  try {
    return new URL(url).protocol === "https:";
  } catch {
    return false;
  }
}

function patch(state: CamState, name: SourceName, change: Partial<SourceView>): CamState {
  return { ...state, sources: { ...state.sources, [name]: { ...state.sources[name], ...change } } };
}

function finishedStatus(status: string | null): SourceStatus {
  if (status === "completed") return "done";
  if (status === "blocked") return "blocked";
  return "unread";
}

function readFinding(value: unknown): Finding | null {
  const finding = value as Finding | null;
  return finding && typeof finding.id === "string" && typeof finding.title === "string"
    ? finding
    : null;
}

function readScore(value: unknown): ScoreSummary | null {
  const score = value as ScoreSummary | null;
  return score && typeof score.value === "number" ? score : null;
}

/**
 * Folds one event into the state. Applying the same event twice changes nothing more: a
 * browser that reconnects receives the run again from the start.
 */
export function applyEvent(state: CamState, event: CheckEvent): CamState {
  if (event.source === "check") {
    if (event.type !== "check.completed") return state;
    if (event.data.status === "completed") {
      return { ...state, outcome: { status: "completed", score: readScore(event.data.score) } };
    }
    const message = text(event.data.message) ?? "The check could not be completed";
    return { ...state, outcome: { status: "failed", message } };
  }

  const name = event.source;
  switch (event.type) {
    case "source.started":
      return patch(state, name, { status: "running" });
    case "source.live_url": {
      const url = text(event.data.url);
      return url && isHttps(url) ? patch(state, name, { liveUrl: url }) : state;
    }
    case "source.progress": {
      const note = text(event.data.text);
      return note ? patch(state, name, { note, notes: state.sources[name].notes + 1 }) : state;
    }
    case "finding.added": {
      const finding = readFinding(event.data.finding);
      if (!finding || state.findings.some((known) => known.id === finding.id)) return state;
      return { ...state, findings: [finding, ...state.findings] };
    }
    case "source.blocked":
      return patch(state, name, { status: "blocked", reason: text(event.data.reason) });
    case "source.completed": {
      const status = finishedStatus(text(event.data.status));
      const reason = text(event.data.message) ?? state.sources[name].reason;
      return patch(state, name, { status, reason });
    }
    default:
      return state;
  }
}

/** Brings the state up to date from a polled check when the live stream is unavailable. */
export function applyCheck(state: CamState, check: Check): CamState {
  return check.sources.reduce(applyRun, state);
}

function applyRun(state: CamState, run: SourceRun): CamState {
  const status: SourceStatus = run.status === "running" ? "running" : finishedStatus(run.status);
  const liveUrl = run.live_url && isHttps(run.live_url) ? run.live_url : null;
  return patch(state, run.source, { status, liveUrl, reason: run.message });
}

/** Overall progress, 0 to 100: a finished source counts fully, a running one partly. */
export function progressPercent(state: CamState): number {
  if (state.outcome) return 100;
  const views = Object.values(state.sources);
  const running = views.filter((view) => view.status === "running").length;
  const waiting = views.filter((view) => view.status === "waiting").length;
  const finished = views.length - running - waiting;
  return Math.min(95, Math.round(((finished + running * 0.4) / views.length) * 100));
}

/** The source the Agent Cam follows by default: the one working now, else the last to start. */
export function activeSource(state: CamState): SourceName {
  const running = SOURCE_ORDER.find((name) => state.sources[name].status === "running");
  if (running) return running;
  const started = SOURCE_ORDER.filter((name) => state.sources[name].status !== "waiting");
  return started[started.length - 1] ?? "uprera";
}
