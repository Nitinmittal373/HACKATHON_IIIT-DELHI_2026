import { NeevScore } from "@/components/NeevScore";
import type { Strings } from "@/lib/i18n";
import { readCheckCount, readSourceCount, KEY_CHECK_COUNT } from "@/lib/reportView";
import { summarize } from "@/lib/summary";
import type { Report } from "@/lib/types";
import styles from "./ScoreCard.module.css";

interface Props {
  report: Report;
  t: Strings;
}

/** The score in one line, what it is made of in plain words, and how much was read. */
export function ScoreCard({ report, t }: Props) {
  const { display_score: display } = report;

  return (
    <section className={`card ${styles.card}`} aria-label={t.report.summaryLabel}>
      <div className={styles.head}>
        <NeevScore score={display} variant="chip" />
        {display.provisional && <span className={styles.provisional}>{t.report.provisional}</span>}
      </div>
      <p className={styles.summary}>{summarize(report, t)}</p>
      {display.hard_stop && report.score_v2.hard_stop_reason && (
        <p className={styles.hardStop}>
          <b>{t.report.hardStop}:</b> {report.score_v2.hard_stop_reason}
        </p>
      )}
      <ul className={styles.facts}>
        <li>{display.hard_stop ? t.report.hardStop : t.report.noHardStop}</li>
        <li>{t.report.confidence(Math.round(display.confidence * 100))}</li>
        <li>{t.report.keyChecks(readCheckCount(report), KEY_CHECK_COUNT)}</li>
        <li>{t.report.records(report.findings.length, readSourceCount(report))}</li>
      </ul>
    </section>
  );
}
