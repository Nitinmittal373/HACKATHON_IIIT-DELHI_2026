import type { CamState, SourceStatus } from "@/lib/checkState";
import type { SourceName } from "@/lib/types";

export type LaneId = "uprera" | "registry" | "group" | "insolvency" | "land" | "news";

/**
 * "skipped" is a lane whose sources never started in a check that has already ended;
 * "partial" is a lane where one source was read and another could not be.
 */
export type LaneStatus = SourceStatus | "skipped" | "partial";

interface LaneDef {
  id: LaneId;
  /** The sources that report into this lane, most important first. */
  sources: SourceName[];
}

/** The six parallel lanes of the War Room. Every source belongs to exactly one lane. */
export const LANES: LaneDef[] = [
  { id: "uprera", sources: ["uprera"] },
  { id: "registry", sources: ["registry"] },
  { id: "group", sources: ["group"] },
  { id: "insolvency", sources: ["insolvency", "consumer"] },
  { id: "land", sources: ["land"] },
  { id: "news", sources: ["news", "sarfaesi"] },
];

export interface LaneView {
  id: LaneId;
  status: LaneStatus;
  /** The latest note of the source working now, else the last note any source left. */
  ticker: string | null;
  findings: number;
  /** The live browser of the lane's running source, when it has one. */
  liveUrl: string | null;
  /** The source the big view shows when this lane is opened. */
  focus: SourceName;
}

export function laneView(state: CamState, lane: LaneDef): LaneView {
  const views = lane.sources.map((name) => ({ name, view: state.sources[name] }));
  const running = views.find(({ view }) => view.status === "running");
  const noted = [...views].reverse().find(({ view }) => view.note);
  const started = views.filter(({ view }) => view.status !== "waiting");
  return {
    id: lane.id,
    status: combine(views.map(({ view }) => view.status), state.outcome !== null),
    ticker: (running ?? noted)?.view.note ?? null,
    findings: state.findings.filter((finding) => lane.sources.includes(finding.source)).length,
    liveUrl: running?.view.liveUrl ?? null,
    focus: (running ?? started[0])?.name ?? lane.sources[0] ?? "uprera",
  };
}

function combine(statuses: SourceStatus[], checkEnded: boolean): LaneStatus {
  if (statuses.includes("running")) return "running";
  if (statuses.every((status) => status === "waiting")) return checkEnded ? "skipped" : "waiting";
  // Some source has finished, but another may still be about to start.
  if (!checkEnded && statuses.includes("waiting")) return "running";
  const stopped = statuses.includes("blocked") || statuses.includes("unread");
  if (statuses.includes("done")) return stopped ? "partial" : "done";
  return statuses.includes("blocked") ? "blocked" : "unread";
}
