import type { Strings } from "@/lib/i18n";
import styles from "./ScoreScale.module.css";

const BANDS = [
  { key: "critical", range: "0–39" },
  { key: "high", range: "40–59" },
  { key: "moderate", range: "60–79" },
  { key: "low", range: "80–100" },
] as const;

/** The 0 to 100 scale with a marker that slides to the example score as the section scrolls in. */
export function ScoreScale({ score, t }: { score: number; t: Strings }) {
  return (
    <section className="wrap section" aria-labelledby="scale-title">
      <div className={`${styles.box} rv`}>
        <div className={styles.head}>
          <div>
            <div className="eyebrow">{t.home.scale.eyebrow}</div>
            <h2 id="scale-title" className={`h2 ${styles.title}`}>
              {t.home.scale.title}
            </h2>
          </div>
          <p className={styles.lead}>
            {t.home.scale.lead}
          </p>
        </div>

        <div className={styles.scale} style={{ ["--at" as string]: `${score}%` }}>
          <ol className={styles.bands}>
            {BANDS.map((band) => (
              <li key={band.key} className={styles[band.key]}>
                {t.home.scale.bands[band.key]}
                <em>{band.range}</em>
              </li>
            ))}
          </ol>
          <div className={styles.marker}>
            <span className="num">{score}</span>
          </div>
        </div>
        <p className={styles.caption}>
          {t.home.scale.caption}
        </p>

        <ul className={styles.weights}>
          {t.home.scale.weights.map((weight) => (
            <li key={weight}>{weight}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
