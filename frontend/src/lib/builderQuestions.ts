import { unreadChecks } from "@/lib/reportView";
import type { Report } from "@/lib/types";

export type QuestionKey =
  | "delay"
  | "complaints"
  | "insolvency"
  | "land"
  | "cases"
  | "progress"
  | "approvals"
  | "account";

const QUESTIONS_SHOWN = 5;
const DELAY = ["past_end_date", "completion_extended"];
const INSOLVENCY = ["insolvency_admitted", "insolvency_scope", "insolvency_scope_unverified"];

/**
 * Five questions for the builder, chosen by simple rules from the report. Questions that a
 * finding calls for come first, general ones fill the list, and the RERA collection account
 * number is always asked, last.
 */
export function builderQuestions(report: Report): QuestionKey[] {
  const has = (kinds: string[]) => report.findings.some((finding) => kinds.includes(finding.kind));
  const complaints = report.findings.some(
    (finding) => finding.kind.endsWith("_complaints") && (finding.count ?? 0) > 0,
  );

  const asked: QuestionKey[] = [];
  if (has(DELAY)) asked.push("delay");
  if (complaints) asked.push("complaints");
  if (has(INSOLVENCY)) asked.push("insolvency");
  if (has(["land_dues"])) asked.push("land");
  // Cases first when e-Jagriti could not be read; otherwise they are only a general question.
  if (unreadChecks(report).includes("consumer_cases")) asked.push("cases");
  for (const filler of ["progress", "approvals", "cases"] as const) {
    if (!asked.includes(filler)) asked.push(filler);
  }
  return [...asked.slice(0, QUESTIONS_SHOWN - 1), "account"];
}
