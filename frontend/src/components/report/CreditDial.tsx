import type { Strings } from "@/lib/i18n";
import { scalePosition, V2_TONE } from "@/lib/scoreV2";
import type { ScoreV2 } from "@/lib/types";
import styles from "./CreditDial.module.css";

const RADIUS = 80;
// Half a circle: the arc runs from the left end of the scale to the right end.
const ARC_LENGTH = Math.PI * RADIUS;

/** The 300-900 dial: a half circle that fills as the score rises. Colour never stands alone. */
export function CreditDial({ score, t }: { score: ScoreV2; t: Strings }) {
  const band = t.credit.bands[score.band];
  const filled = ARC_LENGTH * scalePosition(score.value);
  const arc = `M 20 100 A ${RADIUS} ${RADIUS} 0 0 1 180 100`;

  return (
    <div className={styles.dial} data-tone={V2_TONE[score.band]} role="img" aria-label={t.credit.dialLabel(score.value, band)}>
      <svg viewBox="0 0 200 118" aria-hidden="true">
        <path d={arc} className={styles.track} />
        <path
          d={arc}
          className={styles.fill}
          strokeDasharray={ARC_LENGTH}
          strokeDashoffset={ARC_LENGTH - filled}
        />
      </svg>
      <div className={styles.read} aria-hidden="true">
        <span className={`num ${styles.value}`}>{score.value}</span>
        <span className={`mono ${styles.of}`}>{t.credit.outOf}</span>
      </div>
      <div className={`mono ${styles.scale}`} aria-hidden="true">
        <span>{t.credit.scaleLow}</span>
        <span>{t.credit.scaleHigh}</span>
      </div>
    </div>
  );
}
