import { ScoreRing } from "@/components/ScoreRing";
import type { Strings } from "@/lib/i18n";
import { readCheckCount, readSourceCount, KEY_CHECK_COUNT } from "@/lib/reportView";
import { summarize } from "@/lib/summary";
import type { Report } from "@/lib/types";
import styles from "./ScoreCard.module.css";

interface Props {
  report: Report;
  t: Strings;
  /** Shown small under the 300-900 header, which leads the report. */
  compact?: boolean;
}

export function ScoreCard({ report, t, compact = false }: Props) {
  const { score } = report;
  const band = t.report.bands[score.band];

  return (
    <section
      className={`card ${styles.card} ${compact ? styles.compact : ""}`}
      aria-label={t.report.scoreLabel(score.value, band)}
    >
      <ScoreRing value={score.value} band={score.band} size={compact ? 110 : 180} delay={0.3} />
      <div>
        {compact && (
          <p className={styles.classic}>
            <b>{t.credit.classicTitle}</b> · {t.credit.classicNote}
          </p>
        )}
        <span className={styles.band} data-band={score.band}>
          {band}
        </span>
        {score.provisional && <span className={styles.provisional}>{t.report.provisional}</span>}
        <p className={styles.summary}>{summarize(report, t)}</p>
        {score.hard_stop && score.hard_stop_reason && (
          <p className={styles.hardStop}>
            <b>{t.report.hardStop}:</b> {score.hard_stop_reason}
          </p>
        )}
        <ul className={styles.facts}>
          <li>{score.hard_stop ? t.report.hardStop : t.report.noHardStop}</li>
          <li>{t.report.confidence(Math.round(score.confidence * 100))}</li>
          <li>{t.report.keyChecks(readCheckCount(report), KEY_CHECK_COUNT)}</li>
          <li>{t.report.records(report.findings.length, readSourceCount(report))}</li>
        </ul>
      </div>
    </section>
  );
}
