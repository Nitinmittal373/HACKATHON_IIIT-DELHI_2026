import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Finding, Report } from "@/lib/types";

const COMPLAINT_KINDS = [
  "past_end_date",
  "completion_extended",
  "qpr_missed",
  "registration_revoked",
  "project_complaints",
  "promoter_complaints",
  "penalty",
];

/** Findings a complaint can rely on: facts about the project's own filings, from official pages. */
export function complaintFindings(report: Report): Finding[] {
  return report.findings.filter(
    (finding) =>
      finding.reliability === "primary" &&
      finding.verdict !== "ok" &&
      finding.verdict !== "not_found" &&
      COMPLAINT_KINDS.some((kind) => finding.kind.startsWith(kind)),
  );
}

/**
 * A complaint draft built only from findings, each one cited by its annexure number.
 * Nothing is added that the records do not say; the buyer completes the personal parts.
 */
export function buildComplaintDraft(report: Report, t: Strings, lang: Lang): string {
  const c = t.complaint;
  const facts = complaintFindings(report);
  const { project } = report;
  const readOn = formatDay(report.check.completed_at?.slice(0, 10) ?? report.check.started_at.slice(0, 10), lang);

  const lines = [
    c.to,
    "",
    c.subject(project.name ?? project.rera_id, project.rera_id),
    "",
    c.intro(project.promoter ?? c.promoterUnknown, project.rera_id, readOn),
    "",
    facts.length > 0 ? c.factsHeading : c.noFacts,
    ...facts.map((finding, index) => `${index + 1}. ${finding.title} [${c.annexure} ${index + 1}]`),
    "",
    c.prayer,
    "",
    c.buyerDetails,
    "",
    c.annexureHeading,
    ...facts.map(
      (finding, index) =>
        `${c.annexure} ${index + 1}: ${finding.source_url} (${c.readOn} ${formatDay(finding.read_on, lang)})`,
    ),
  ];
  return lines.join("\n");
}
