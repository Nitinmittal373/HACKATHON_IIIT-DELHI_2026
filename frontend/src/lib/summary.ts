import type { Strings } from "@/lib/i18n";
import type { Finding, Report } from "@/lib/types";

function first(findings: Finding[], ...kinds: string[]): Finding | undefined {
  return findings.find((finding) => kinds.includes(finding.kind));
}

/** The issues found, as short phrases in the reader's language. */
function issues(findings: Finding[], t: Strings["report"]["summary"]): string[] {
  const found: string[] = [];
  if (first(findings, "registration_revoked")) found.push(t.revoked);

  const late = first(findings, "past_end_date");
  if (late?.months) found.push(t.delay(late.months));
  const extended = first(findings, "completion_extended");
  if (extended?.count) found.push(t.extended(extended.count));

  const scope = first(findings, "insolvency_scope");
  if (scope?.scope === "this_project") found.push(t.insolvencyThis);
  else if (scope?.scope === "company") found.push(t.insolvencyCompany);
  else if (scope?.scope === "other_project") found.push(t.insolvencyOther);
  else if (first(findings, "insolvency_scope_unverified", "insolvency_admitted")) {
    found.push(t.insolvencyUnverified);
  }

  const complaints = first(findings, "project_complaints");
  if (complaints?.count) found.push(t.complaints(complaints.count));
  if (first(findings, "land_dues")) found.push(t.land);
  const stories = findings.filter((finding) => finding.kind === "news_story").length;
  if (stories > 0) found.push(t.news(stories));
  return found;
}

/** One sentence that says what the score is made of, built only from the findings. */
export function summarize(report: Report, t: Strings): string {
  const found = issues(report.findings, t.report.summary);
  if (found.length === 0) return t.report.summary.clean;
  return t.report.summary.withIssues(t.report.summary.join(found));
}
