import type { ComparedProject, InsolvencyStatus } from "@/lib/types";

/**
 * The column holding the single best value of a row, or null. A row with an unread value is
 * never highlighted: next to "not read", any known value would wrongly look like the better one.
 */
export function bestColumn(values: (number | null)[], better: "lower" | "higher"): number | null {
  if (values.length < 2 || values.some((value) => value === null)) return null;
  const known = values as number[];
  const top = better === "lower" ? Math.min(...known) : Math.max(...known);
  const winners = known.flatMap((value, index) => (value === top ? [index] : []));
  return winners.length === 1 ? (winners[0] ?? null) : null;
}

/** Lower is better: nothing found, then a case about another project, up to the whole company. */
const INSOLVENCY_RANK: Record<InsolvencyStatus, number> = {
  none_found: 0,
  other_project: 1,
  admitted: 2,
  unverified: 2,
  this_project: 3,
  company: 3,
};

export function insolvencyRank(project: ComparedProject): number | null {
  return project.insolvency === null ? null : INSOLVENCY_RANK[project.insolvency];
}

/** An active company is better than any other registry status; the status words vary. */
export function companyRank(project: ComparedProject): number | null {
  if (project.company_status === null) return null;
  return project.company_status.toLowerCase() === "active" ? 0 : 1;
}

// The share of key checks a score needs before it gets a band (MIN_CONFIDENCE_FOR_BAND).
const ENOUGH_EVIDENCE = 0.5;

/**
 * Zero points lost in an area can mean nothing was found or nothing was read, so area rows are
 * only compared when every check read at least half of its key records.
 */
export function areasComparable(projects: ComparedProject[]): boolean {
  return projects.every((project) => project.confidence >= ENOUGH_EVIDENCE);
}

/** Points the area took off, or null when the column has no such area. */
export function areaLost(project: ComparedProject, area: string): number | null {
  return project.areas.find((points) => points.area === area)?.lost ?? null;
}
