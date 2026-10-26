"use client";

import { useLang } from "@/lib/LangProvider";
import { useMeta } from "@/lib/MetaProvider";
import { BAND_TONE, scalePosition } from "@/lib/neevScore";
import type { BandV2 } from "@/lib/types";
import styles from "./NeevScore.module.css";

export type NeevScoreVariant = "dial" | "ring" | "chip";

interface Props {
  /** display_score.value */
  value: number;
  /** display_score.band */
  band: BandV2;
  variant?: NeevScoreVariant;
  /** Pixel width of the dial or ring; a chip sizes itself. */
  size?: number;
  /** Seconds before the arc starts drawing. */
  delay?: number;
  /** A chip normally reads "621 Watch"; without the value it is just the band's tag. */
  showValue?: boolean;
}

// Arc lengths of the two drawings, in their own units: a circle of radius 48 and a half circle
// of radius 80.
const RING_LENGTH = 302;
const DIAL_LENGTH = 252;
const RING_RADIUS = 48;
const DIAL_RADIUS = 80;

/**
 * The one way the NeevScore is drawn. The scale comes from /api/meta and the band label from the
 * reader's language, so no screen carries its own idea of 300, 900 or the band edges. Colour
 * never stands alone: the band is always written out.
 */
export function NeevScore({ value, band, variant = "ring", size, delay = 0.2, showValue = true }: Props) {
  const { t } = useLang();
  const meta = useMeta();
  const label = t.score.bands[band];
  const tone = BAND_TONE[band];
  const position = scalePosition(meta, value);
  const aria = t.score.label(value, meta.scale.max, label);

  if (variant === "chip") {
    return (
      <span className={styles.chip} data-tone={tone} data-band={band}>
        {showValue && <b className="num">{value}</b>}
        <span>{label}</span>
      </span>
    );
  }

  if (variant === "dial") {
    const arc = `M 20 100 A ${DIAL_RADIUS} ${DIAL_RADIUS} 0 0 1 180 100`;
    return (
      <div
        className={styles.dial}
        data-tone={tone}
        data-band={band}
        role="img"
        aria-label={aria}
        style={size ? { maxWidth: size } : undefined}
      >
        <svg viewBox="0 0 200 118" aria-hidden="true">
          <path d={arc} className={styles.track} />
          <path
            d={arc}
            className={styles.fill}
            strokeDasharray={DIAL_LENGTH}
            strokeDashoffset={DIAL_LENGTH * (1 - position)}
            style={{ ["--len" as string]: DIAL_LENGTH, animationDelay: `${delay}s` }}
          />
        </svg>
        <div className={styles.read} aria-hidden="true">
          <span className={`num ${styles.dialValue}`}>{value}</span>
          <span className={`mono ${styles.of}`}>{t.score.outOf(meta.scale.max)}</span>
        </div>
        <div className={`mono ${styles.ends}`} aria-hidden="true">
          <span>{meta.scale.min}</span>
          <span>{meta.scale.max}</span>
        </div>
      </div>
    );
  }

  const pixels = size ?? 140;
  return (
    <div
      className={styles.ring}
      data-tone={tone}
      data-band={band}
      role="img"
      aria-label={aria}
      style={{ width: pixels, height: pixels }}
    >
      <svg width={pixels} height={pixels} viewBox="0 0 110 110" aria-hidden="true">
        <circle cx={55} cy={55} r={RING_RADIUS} className={styles.ringTrack} />
        <circle
          cx={55}
          cy={55}
          r={RING_RADIUS}
          className={styles.ringFill}
          strokeDasharray={RING_LENGTH}
          strokeDashoffset={RING_LENGTH * (1 - position)}
          transform="rotate(-90 55 55)"
          style={{ ["--len" as string]: RING_LENGTH, animationDelay: `${delay}s` }}
        />
      </svg>
      <div className={styles.ringLabel} aria-hidden="true">
        <span className={`num ${styles.ringValue}`} style={{ fontSize: pixels * 0.3 }}>
          {value}
        </span>
        <span className={`mono ${styles.ringOf}`}>/ {meta.scale.max}</span>
      </div>
    </div>
  );
}
