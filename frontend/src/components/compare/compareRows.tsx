import type { ReactNode } from "react";

import { ScoreRing } from "@/components/ScoreRing";
import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import { areaLost, areasComparable, bestColumn, companyRank, insolvencyRank } from "@/lib/compare";
import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Area, Comparison, ComparedProject } from "@/lib/types";
import styles from "./Compare.module.css";

export interface CompareRow {
  key: string;
  label: string;
  /** Rows under a group heading, such as the six scoring areas, are indented under it. */
  group?: string;
  cells: ReactNode[];
  /** The column with the better value, tinted; null when no single column is better. */
  best: number | null;
}

const AREAS: Area[] = ["rera", "execution", "legal", "financial", "builder_history", "news"];

/** Every row of the comparison, in the order a buyer reads them. */
export function compareRows(comparison: Comparison, t: Strings, lang: Lang): CompareRow[] {
  const { projects } = comparison;
  const c = t.compare;
  const text = (value: string | null) => value ?? <span className={styles.muted}>{c.notShown}</span>;
  const unread = <span className={styles.muted}>{c.notRead}</span>;
  const count = (value: number | null) => (value === null ? unread : value.toLocaleString("en-IN"));
  const column = (pick: (project: ComparedProject) => number | null) => projects.map(pick);
  const bestIndex = projects.findIndex((project) => project.check_id === comparison.best);
  const compareAreas = areasComparable(projects);

  return [
    { key: "rera", label: c.rows.rera, cells: projects.map((p) => <span key={p.check_id} className="mono">{p.project.rera_id}</span>), best: null },
    { key: "promoter", label: c.rows.promoter, cells: projects.map((p) => text(p.project.promoter)), best: null },
    { key: "district", label: c.rows.district, cells: projects.map((p) => text(p.project.district)), best: null },
    {
      key: "registered",
      label: c.rows.registered,
      cells: projects.map((p) => text(p.project.registered_on && formatDay(p.project.registered_on, lang))),
      best: null,
    },
    {
      key: "score",
      label: c.rows.score,
      cells: projects.map((p) => (
        <div key={p.check_id} className={styles.score}>
          <ScoreRing value={p.score} band={p.band} size={72} delay={0.1} />
          <div>
            <span className="bandTag" data-band={p.band}>
              {t.report.bands[p.band]}
            </span>
            <p className={styles.small}>{c.confidence(Math.round(p.confidence * 100))}</p>
          </div>
        </div>
      )),
      best: bestIndex >= 0 ? bestIndex : null,
    },
    ...AREAS.map((area) => ({
      key: `area-${area}`,
      label: t.report.areas[area],
      group: c.rows.areas,
      cells: projects.map((p) => {
        const points = p.areas.find((item) => item.area === area);
        if (!points) return unread;
        return (
          <div key={p.check_id} className={styles.area}>
            <i className={styles.bar} aria-hidden="true">
              <b style={{ width: `${points.max ? (points.lost / points.max) * 100 : 0}%` }} />
            </i>
            <span className="num">{c.lost(points.lost, points.max)}</span>
          </div>
        );
      }),
      best: compareAreas ? bestColumn(column((p) => areaLost(p, area)), "lower") : null,
    })),
    {
      key: "delay",
      label: c.rows.delay,
      cells: projects.map((p) => (p.delay_months === null ? unread : c.months(p.delay_months))),
      best: bestColumn(column((p) => p.delay_months), "lower"),
    },
    {
      key: "projectComplaints",
      label: c.rows.projectComplaints,
      cells: projects.map((p) => count(p.project_complaints)),
      best: bestColumn(column((p) => p.project_complaints), "lower"),
    },
    {
      key: "promoterComplaints",
      label: c.rows.promoterComplaints,
      cells: projects.map((p) => count(p.promoter_complaints)),
      best: bestColumn(column((p) => p.promoter_complaints), "lower"),
    },
    {
      key: "insolvency",
      label: c.rows.insolvency,
      cells: projects.map((p) => (p.insolvency === null ? unread : c.insolvency[p.insolvency])),
      best: bestColumn(column(insolvencyRank), "lower"),
    },
    {
      key: "company",
      label: c.rows.company,
      cells: projects.map((p) => (p.company_status === null ? unread : p.company_status)),
      best: bestColumn(column(companyRank), "lower"),
    },
    {
      key: "unread",
      label: c.rows.unread,
      cells: projects.map((p) =>
        p.unread.length === 0 ? c.allRead : p.unread.map((key) => t.report.checks[key]).join(", "),
      ),
      best: bestColumn(column((p) => p.unread.length), "lower"),
    },
    {
      key: "findings",
      label: c.rows.findings,
      cells: projects.map((p) =>
        p.top_findings.length === 0 ? (
          <span key={p.check_id} className={styles.muted}>{c.noFindings}</span>
        ) : (
          <ul key={p.check_id} className={styles.findings}>
            {p.top_findings.map((finding) => (
              <li key={finding.title}>
                <a href={finding.source_url} target="_blank" rel="noopener noreferrer">
                  {finding.title}
                  <ExternalLinkIcon />
                  <span className="sr"> ({t.common.opensInNewTab})</span>
                </a>
                <span className={`num ${styles.points}`}>{c.points(finding.points)}</span>
              </li>
            ))}
          </ul>
        ),
      ),
      best: null,
    },
  ];
}
