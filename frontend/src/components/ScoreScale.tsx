"use client";

import { useLang } from "@/lib/LangProvider";
import { useMeta } from "@/lib/MetaProvider";
import { BAND_TONE, bandShare, scalePosition, weightPercent } from "@/lib/neevScore";
import { useRecentChecks } from "@/lib/useRecentChecks";
import styles from "./ScoreScale.module.css";

/**
 * The NeevScore scale, drawn from /api/meta. The marker sits at the latest real check on
 * NeevCheck; with none yet there is no marker, because nothing here is made up.
 */
export function ScoreScale() {
  const { t } = useLang();
  const meta = useMeta();
  const recent = useRecentChecks();
  const latest =
    recent.status === "ready" ? recent.checks.find((check) => check.display_score !== null) : undefined;
  const display = latest?.display_score ?? null;
  // The scale reads left to right from the highest risk to the lowest.
  const bands = [...meta.bands].reverse();

  return (
    <section className="wrap section" aria-labelledby="scale-title">
      <div className={`${styles.box} rv`}>
        <div className={styles.head}>
          <div>
            <div className="eyebrow">{t.home.scale.eyebrow}</div>
            <h2 id="scale-title" className={`h2 ${styles.title}`}>
              {t.home.scale.title(meta.scale.min, meta.scale.max)}
            </h2>
          </div>
          <p className={styles.lead}>{t.home.scale.lead(meta.scale.max)}</p>
        </div>

        <div
          className={styles.scale}
          style={display ? { ["--at" as string]: `${scalePosition(meta, display.value) * 100}%` } : undefined}
        >
          <ol
            className={styles.bands}
            style={{ gridTemplateColumns: bands.map((band) => `${bandShare(meta, band)}fr`).join(" ") }}
          >
            {bands.map((band) => (
              <li key={band.key} className={styles[BAND_TONE[band.key]]}>
                {t.score.bands[band.key]}
                <em>
                  {band.min}–{band.max}
                </em>
              </li>
            ))}
          </ol>
          {display && (
            <div className={styles.marker}>
              <span className="num">{display.value}</span>
            </div>
          )}
        </div>
        <p className={styles.caption}>
          {latest ? t.home.scale.caption(latest.project ?? latest.rera_id) : t.home.scale.captionEmpty}
        </p>

        <ul className={styles.weights} aria-label={t.home.scale.weightsLabel}>
          {meta.pillars.map((pillar) => (
            <li key={pillar.id}>
              {t.credit.pillars[pillar.id]} {weightPercent(pillar.weight)}%
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
