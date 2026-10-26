import { ALL_SOURCES, EXTRA_SOURCES, SOURCE_ORDER } from "@/lib/sources";
import type {
  Check,
  CheckEvent,
  Finding,
  RunStatus,
  ScoreSummary,
  SourceName,
  SourceRun,
} from "@/lib/types";

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
    ALL_SOURCES.map((name) => [name, { ...BLANK_SOURCE }]),
  ) as Record<SourceName, SourceView>;
  return { sources, findings: [], outcome: null };
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

function finishedStatus(status: RunStatus): SourceStatus {
  if (status === "completed") return "done";
  if (status === "blocked") return "blocked";
  return "unread";
}

/**
 * Folds one event into the state. Applying the same event twice changes nothing more: a
 * browser that reconnects receives the run again from the start.
 */
export function applyEvent(state: CamState, event: CheckEvent): CamState {
  switch (event.type) {
    case "source.started":
      return patch(state, event.source, { status: "running" });
    case "source.live_url": {
      const { url } = event.data;
      return url && isHttps(url) ? patch(state, event.source, { liveUrl: url }) : state;
    }
    case "source.progress": {
      const note = event.data.text;
      if (!note) return state;
      return patch(state, event.source, { note, notes: state.sources[event.source].notes + 1 });
    }
    case "finding.added": {
      const { finding } = event.data;
      if (state.findings.some((known) => known.id === finding.id)) return state;
      return { ...state, findings: [finding, ...state.findings] };
    }
    case "source.blocked":
      return patch(state, event.source, { status: "blocked", reason: event.data.reason || null });
    case "source.completed": {
      const status = finishedStatus(event.data.status);
      const reason = event.data.message ?? state.sources[event.source].reason;
      return patch(state, event.source, { status, reason });
    }
    case "check.completed": {
      if (event.data.status === "completed") {
        return { ...state, outcome: { status: "completed", score: event.data.score } };
      }
      const message = event.data.message ?? "The check could not be completed";
      return { ...state, outcome: { status: "failed", message } };
    }
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

/** The six usual sources, plus any v2 source the backend has actually started. */
export function visibleSources(state: CamState): SourceName[] {
  return [
    ...SOURCE_ORDER,
    ...EXTRA_SOURCES.filter((name) => state.sources[name].status !== "waiting"),
  ];
}

/** Overall progress, 0 to 100: a finished source counts fully, a running one partly. */
export function progressPercent(state: CamState): number {
  if (state.outcome) return 100;
  const views = visibleSources(state).map((name) => state.sources[name]);
  const running = views.filter((view) => view.status === "running").length;
  const waiting = views.filter((view) => view.status === "waiting").length;
  const finished = views.length - running - waiting;
  return Math.min(95, Math.round(((finished + running * 0.4) / views.length) * 100));
}

/** The source the Agent Cam follows by default: the one working now, else the last to start. */
export function activeSource(state: CamState): SourceName {
  const running = visibleSources(state).find((name) => state.sources[name].status === "running");
  if (running) return running;
  const started = visibleSources(state).filter((name) => state.sources[name].status !== "waiting");
  return started[started.length - 1] ?? "uprera";
}
