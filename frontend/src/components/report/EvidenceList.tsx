import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import { formatDay, formatTime } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import { unreadEntries } from "@/lib/reportView";
import { SOURCE_INFO } from "@/lib/sources";
import { stopReason } from "@/lib/stopReason";
import type { Finding, Report } from "@/lib/types";
import { toneOf } from "@/lib/verdict";
import styles from "./EvidenceList.module.css";

interface Props {
  report: Report;
  ids: Map<string, string>;
  t: Strings;
  lang: Lang;
}

export function EvidenceList({ report, ids, t, lang }: Props) {
  const points = new Map(report.score_v2.drivers.map((driver) => [driver.finding_id, driver.points]));
  const unread = unreadEntries(report);

  return (
    <section className={`card ${styles.card}`} aria-labelledby="evidence-title">
      <h2 id="evidence-title" className={styles.title}>
        {t.report.evidence}
      </h2>
      <ul className={styles.list}>
        {report.findings.map((finding) => (
          <FindingRow
            key={finding.id}
            finding={finding}
            id={ids.get(finding.id) ?? ""}
            points={points.get(finding.id)}
            t={t}
            lang={lang}
          />
        ))}
        {unread.map((entry) => (
          <li key={`${entry.source}-${entry.check ?? "run"}`} className={`${styles.row} ${styles.unread}`}>
            <span className={`mono ${styles.id}`}>–</span>
            <span className={styles.body}>
              <span className={styles.name}>
                {entry.check ? t.report.checks[entry.check] : t.cam.sourceLabels[entry.source]}
                {": "}
                {t.report.notRead}
              </span>
              <span className={styles.sub}>
                {t.cam.sourceLabels[entry.source]} · {stopReason(entry.reason, t)}
              </span>
              <span className={styles.sub}>{t.report.notReadBody}</span>
            </span>
            <span className={styles.side}>
              <span className={`${styles.pill} tone-neutral`}>{t.cam.verdict.blocked}</span>
              <a
                className={styles.howto}
                href={SOURCE_INFO[entry.source].officialUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                {t.report.howToCheck}
                <ExternalLinkIcon />
                <span className="sr"> ({t.common.opensInNewTab})</span>
              </a>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

interface RowProps {
  finding: Finding;
  id: string;
  points: number | undefined;
  t: Strings;
  lang: Lang;
}

function FindingRow({ finding, id, points, t, lang }: RowProps) {
  const time = finding.read_at ? formatTime(finding.read_at, lang) : null;
  const readOn = t.report.readOn(formatDay(finding.read_on, lang), time);
  const verdict = finding.verdict === "red_flag" ? "fail" : finding.verdict;
  const lost = points ? `−${Math.abs(Math.round(points))}` : null;

  return (
    <li className={styles.row}>
      <span className={`mono ${styles.id}`}>{id}</span>
      <span className={styles.body}>
        <span className={styles.name}>{finding.title}</span>
        <span className={styles.sub}>
          {t.cam.sourceLabels[finding.source]} · {readOn} · {t.report.reliability[finding.reliability]}
        </span>
      </span>
      <span className={styles.side}>
        {lost && <span className={`num ${styles.lost}`}>{lost}</span>}
        <span className={`${styles.pill} tone-${toneOf(finding.verdict)}`}>{t.report.verdict[verdict]}</span>
        <a
          className={styles.link}
          href={finding.source_url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`${t.common.openSource}: ${finding.title} (${t.common.opensInNewTab})`}
        >
          <ExternalLinkIcon />
        </a>
      </span>
    </li>
  );
}
