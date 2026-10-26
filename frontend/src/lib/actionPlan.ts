import { unreadChecks } from "@/lib/reportView";
import type { Report } from "@/lib/types";

export type PlanKey =
  | "delay"
  | "insolvency"
  | "complaints"
  | "land"
  | "news"
  | "unread"
  | "verify"
  | "agreement"
  | "pay";

const KINDS: Record<Exclude<PlanKey, "unread" | "verify" | "agreement" | "pay">, string[]> = {
  delay: ["past_end_date", "completion_extended"],
  insolvency: ["insolvency_admitted", "insolvency_scope", "insolvency_scope_unverified"],
  complaints: ["project_complaints", "promoter_complaints"],
  land: ["land_dues"],
  news: ["news_story"],
};

const STEPS_SHOWN = 4;

/**
 * Four steps for the buyer, chosen by simple rules from what was found. The steps that match
 * a finding come first; general ones fill the list; paying only into the RERA account is
 * always last.
 */
export function actionPlan(report: Report): PlanKey[] {
  const kinds = new Set(report.findings.map((finding) => finding.kind));
  const matched = (Object.keys(KINDS) as (keyof typeof KINDS)[]).filter((key) =>
    KINDS[key].some((kind) => kinds.has(kind)),
  );
  const fillers: PlanKey[] = [
    ...(unreadChecks(report).length > 0 ? (["unread"] as const) : []),
    "verify",
    "agreement",
  ];
  const steps = [...matched, ...fillers].slice(0, STEPS_SHOWN - 1);
  return [...steps, "pay"];
}
