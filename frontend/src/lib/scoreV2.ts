import type { Lang } from "@/lib/i18n";
import type { Finding, ReasonCode, Report, ScoreV2, SourceName, Verdict } from "@/lib/types";

const REASONS_SHOWN = 4;

/** The reason codes that cost points, biggest first, at most four; R12 is listed after them. */
export function topReasons(score: ScoreV2) {
  const costing = score.reason_codes.filter((reason) => reason.code !== "R12");
  const unavailable = score.reason_codes.filter((reason) => reason.code === "R12");
  return [...costing.slice(0, REASONS_SHOWN), ...unavailable];
}

/** One line of the evidence ledger. Plain data, so it can pass from the server to the drawer. */
export interface LedgerRow {
  evidenceId: string;
  title: string;
  source: SourceName;
  sourceUrl: string;
  readOn: string;
  readAt: string | null;
  snippet: string | null;
  reliability: Finding["reliability"];
  verdict: Verdict;
  /** Points lost in NeevScore v2 (negative), or null when the record cost nothing. */
  points: number | null;
  code: string | null;
}

export function ledgerRows(report: Report, ids: Map<string, string>): LedgerRow[] {
  const drivers = new Map(report.score_v2.drivers.map((driver) => [driver.finding_id, driver]));
  return report.findings.map((finding) => {
    const driver = drivers.get(finding.id);
    return {
      evidenceId: ids.get(finding.id) ?? "",
      title: finding.title,
      source: finding.source,
      sourceUrl: finding.source_url,
      readOn: finding.read_on,
      readAt: finding.read_at,
      snippet: finding.snippet ?? null,
      reliability: finding.reliability,
      verdict: finding.verdict,
      points: driver ? driver.points : null,
      code: driver ? driver.code : null,
    };
  });
}

/** The evidence ids behind one reason code, in the order the evidence list shows them. */
export function evidenceOfCode(report: Report, ids: Map<string, string>, code: string): string[] {
  const reason = report.score_v2.reason_codes.find((entry) => entry.code === code);
  return (reason?.finding_ids ?? []).map((id) => ids.get(id) ?? "").filter(Boolean);
}

/** English shows the backend's own label, which carries the counts; Hindi shows the fixed label. */
export function reasonLabel(reason: ReasonCode, codes: Record<string, string>, lang: Lang): string {
  return lang === "en" ? reason.label : (codes[reason.code] ?? reason.label);
}
