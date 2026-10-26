import { NeevScore } from "@/components/NeevScore";
import { PillarBars } from "@/components/report/PillarBars";
import { ReasonChips } from "@/components/report/ReasonChips";
import type { Strings } from "@/lib/i18n";
import { BAND_TONE } from "@/lib/neevScore";
import { ledgerRows, topReasons } from "@/lib/scoreV2";
import type { Meta, Report } from "@/lib/types";
import styles from "./CreditHeader.module.css";

interface Props {
  report: Report;
  ids: Map<string, string>;
  meta: Meta;
  t: Strings;
}

/** The credit-report style header: the NeevScore dial, why, and how much was actually read. */
export function CreditHeader({ report, ids, meta, t }: Props) {
  const { display_score: display, score_v2: score } = report;
  const band = t.score.bands[display.band];
  const total = meta.pillars.length;
  const read = total - score.pillars_unread.length;
  // Built from the reason codes by a template; no model writes it and none can change the score.
  const costing = topReasons(score).filter((reason) => reason.code !== "R12" && reason.points < 0);
  const narrative = t.credit.narrative(
    display.value,
    meta.scale.max,
    band,
    costing.map((reason) => t.credit.codes[reason.code] ?? reason.label),
    score.pillars_unread.length,
    total,
  );

  return (
    <section className={`card ${styles.card}`} aria-label={t.credit.title}>
      {display.hard_stop && score.hard_stop_reason && (
        <div className={styles.hardStop} role="alert">
          <b>{t.credit.hardStopTitle}:</b> {t.credit.hardStopBody(score.hard_stop_reason)}
        </div>
      )}
      <div className={styles.top}>
        <div className={styles.dial}>
          <NeevScore value={display.value} band={display.band} variant="dial" />
          <span className={styles.band} data-tone={BAND_TONE[display.band]}>
            {band}
          </span>
          {display.provisional && <p className={styles.provisional}>{t.credit.provisional}</p>}
          <div className={styles.confidence}>
            <div className={styles.confidenceHead}>
              <span>{t.credit.confidenceTitle}</span>
              <span className="mono">{t.credit.confidence(read, total)}</span>
            </div>
            <div
              className={styles.meter}
              role="meter"
              aria-label={t.credit.confidenceTitle}
              aria-valuemin={0}
              aria-valuemax={total}
              aria-valuenow={read}
              aria-valuetext={t.credit.confidence(read, total)}
            >
              <div className={styles.meterFill} style={{ width: `${(read / total) * 100}%` }} />
            </div>
          </div>
        </div>
        <div className={styles.reasons}>
          <ReasonChips
            reasons={topReasons(score)}
            rows={ledgerRows(report, ids)}
            rera={report.rera_name}
          />
        </div>
      </div>
      <p className={styles.narrative}>{narrative}</p>
      <PillarBars score={score} t={t} />
      <p className={styles.notice}>{t.credit.ratingNotice}</p>
    </section>
  );
}
