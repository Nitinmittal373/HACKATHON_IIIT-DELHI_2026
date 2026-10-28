import type { CheckKey, Finding, Report, SourceName } from "@/lib/types";

/** The seven records the report names one by one. The complaint counts are not among them. */
type KeyCheck = Exclude<CheckKey, "rera_complaints">;

/** The source that settles each key check; used to say where an unread check can be done by hand. */
const CHECK_SOURCE: Record<KeyCheck, SourceName> = {
  registration: "uprera",
  completion_date: "uprera",
  extensions: "uprera",
  company_status: "registry",
  insolvency: "insolvency",
  land_dues: "land",
  consumer_cases: "consumer",
};

export const KEY_CHECK_COUNT = Object.keys(CHECK_SOURCE).length;

/** True when the builder's name came from public listings, not from the RERA portal's page. */
export function builderFromListings(findings: Pick<Finding, "kind">[]): boolean {
  return findings.some((finding) => finding.kind === "builder_identity");
}

/** "E1", "E2", ... in the order the evidence list shows them. */
export function evidenceIds(findings: Finding[]): Map<string, string> {
  return new Map(findings.map((finding, index) => [finding.id, `E${index + 1}`]));
}

/** The key checks that no source read, taken from the source runs themselves. */
export function unreadChecks(report: Report): KeyCheck[] {
  const read = new Set(report.check.sources.flatMap((run) => run.checks_read));
  return (Object.keys(CHECK_SOURCE) as KeyCheck[]).filter((check) => !read.has(check));
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
  const entries: UnreadEntry[] = unreadChecks(report).map((check) => {
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
  return KEY_CHECK_COUNT - unreadChecks(report).length;
}
