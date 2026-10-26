import { CreditDial } from "@/components/report/CreditDial";
import { PillarBars } from "@/components/report/PillarBars";
import { ReasonChips } from "@/components/report/ReasonChips";
import type { Strings } from "@/lib/i18n";
import { ledgerRows, topReasons, V2_TONE } from "@/lib/scoreV2";
import type { Report } from "@/lib/types";
import styles from "./CreditHeader.module.css";

interface Props {
  report: Report;
  ids: Map<string, string>;
  t: Strings;
}

const PILLAR_COUNT = 6;

/** The credit-report style header: the 300-900 dial, why, and how much was actually read. */
export function CreditHeader({ report, ids, t }: Props) {
  const score = report.score_v2;
  if (!score) return null;
  const band = t.credit.bands[score.band];
  const read = PILLAR_COUNT - score.pillars_unread.length;
  // Built from the reason codes by a template; no model writes it and none can change the score.
  const costing = topReasons(score).filter((reason) => reason.code !== "R12" && reason.points < 0);
  const narrative = t.credit.narrative(
    score.value,
    band,
    costing.map((reason) => t.credit.codes[reason.code] ?? reason.label),
    score.pillars_unread.length,
  );

  return (
    <section className={`card ${styles.card}`} aria-label={t.credit.title}>
      {score.hard_stop && score.hard_stop_reason && (
        <div className={styles.hardStop} role="alert">
          <b>{t.credit.hardStopTitle}:</b> {t.credit.hardStopBody(score.hard_stop_reason)}
        </div>
      )}
      <div className={styles.top}>
        <div className={styles.dial}>
          <CreditDial score={score} t={t} />
          <span className={styles.band} data-tone={V2_TONE[score.band]}>
            {band}
          </span>
          {score.provisional && <p className={styles.provisional}>{t.credit.provisional}</p>}
          <div className={styles.confidence}>
            <div className={styles.confidenceHead}>
              <span>{t.credit.confidenceTitle}</span>
              <span className="mono">{t.credit.confidence(read, PILLAR_COUNT)}</span>
            </div>
            <div
              className={styles.meter}
              role="meter"
              aria-label={t.credit.confidenceTitle}
              aria-valuemin={0}
              aria-valuemax={PILLAR_COUNT}
              aria-valuenow={read}
              aria-valuetext={t.credit.confidence(read, PILLAR_COUNT)}
            >
              <div className={styles.meterFill} style={{ width: `${(read / PILLAR_COUNT) * 100}%` }} />
            </div>
          </div>
        </div>
        <div className={styles.reasons}>
          <ReasonChips reasons={topReasons(score)} rows={ledgerRows(report, ids)} />
        </div>
      </div>
      <p className={styles.narrative}>{narrative}</p>
      <PillarBars score={score} t={t} />
      <p className={styles.notice}>{t.credit.ratingNotice}</p>
    </section>
  );
}
