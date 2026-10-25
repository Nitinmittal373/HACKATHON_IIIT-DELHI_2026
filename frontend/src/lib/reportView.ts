import type { CheckKey, Finding, Report, SourceName } from "@/lib/types";

/** The source that settles each key check; used to say where an unread check can be done by hand. */
const CHECK_SOURCE: Record<CheckKey, SourceName> = {
  registration: "uprera",
  completion_date: "uprera",
  extensions: "uprera",
  company_status: "registry",
  insolvency: "insolvency",
  land_dues: "land",
  consumer_cases: "consumer",
};

export const KEY_CHECK_COUNT = Object.keys(CHECK_SOURCE).length;

/** "E1", "E2", ... in the order the evidence list shows them. */
export function evidenceIds(findings: Finding[]): Map<string, string> {
  return new Map(findings.map((finding, index) => [finding.id, `E${index + 1}`]));
}

export interface UnreadEntry {
  /** The key check that stayed unread, when it was one. */
  check: CheckKey | null;
  source: SourceName;
  /** Why the source stopped, as the backend reported it. */
  reason: string | null;
}

/** Everything we could not read, so the report can say so and point to the official site. */
export function unreadEntries(report: Report): UnreadEntry[] {
  const runs = new Map(report.check.sources.map((run) => [run.source, run]));
  const entries: UnreadEntry[] = report.score.checks_unread.map((check) => {
    const source = CHECK_SOURCE[check];
    return { check, source, reason: runs.get(source)?.message ?? null };
  });
  const listed = new Set(entries.map((entry) => entry.source));
  for (const run of report.check.sources) {
    const stopped = run.status !== "completed";
    if (stopped && !listed.has(run.source)) {
      entries.push({ check: null, source: run.source, reason: run.message });
    }
  }
  return entries;
}

export function readSourceCount(report: Report): number {
  return new Set(report.findings.map((finding) => finding.source)).size;
}

export function readCheckCount(report: Report): number {
  return KEY_CHECK_COUNT - report.score.checks_unread.length;
}
