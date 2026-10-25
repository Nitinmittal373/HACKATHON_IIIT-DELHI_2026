import styles from "./ScoreRing.module.css";

export type BandKey = "Low" | "Moderate" | "High" | "Critical" | "insufficient_evidence";

interface Props {
  /** The NeevScore, 0 to 100. */
  value: number;
  band: BandKey;
  /** Pixel size of the ring; the number inside scales with it. */
  size?: number;
  /** Seconds before the ring starts drawing. */
  delay?: number;
}

const RADIUS = 48;
const CIRCUMFERENCE = 302; // 2 * pi * RADIUS, rounded

/** The score ring. A score without enough evidence is drawn paler: it is provisional. */
export function ScoreRing({ value, band, size = 140, delay = 2 }: Props) {
  const provisional = band === "insufficient_evidence";

  return (
    <div className={styles.ring} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 110 110" aria-hidden="true">
        <circle cx={55} cy={55} r={RADIUS} fill="none" stroke="#F3EEE9" strokeWidth={9} />
        <circle
          className={styles.arc}
          cx={55}
          cy={55}
          r={RADIUS}
          fill="none"
          stroke="#F26B1D"
          strokeOpacity={provisional ? 0.6 : 1}
          strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - value / 100)}
          transform="rotate(-90 55 55)"
          style={{ animationDelay: `${delay}s` }}
        />
      </svg>
      <div className={styles.label}>
        <span className={`num ${styles.value}`} style={{ fontSize: size * 0.33 }}>
          {value}
        </span>
        <span className={`mono ${styles.of}`}>/ 100</span>
      </div>
    </div>
  );
}
