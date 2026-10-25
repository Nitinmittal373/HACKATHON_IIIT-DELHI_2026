import styles from "./ScoreScale.module.css";

/** Area weights, the same as docs/scoring.md. */
const WEIGHTS = [
  "UP-RERA compliance 25%",
  "Project execution 20%",
  "Legal & courts 15%",
  "Financial & insolvency 15%",
  "Builder history 15%",
  "News 10%",
];

const BANDS = [
  { key: "critical", name: "Critical", range: "0–39" },
  { key: "high", name: "High", range: "40–59" },
  { key: "moderate", name: "Moderate", range: "60–79" },
  { key: "low", name: "Low", range: "80–100" },
] as const;

/** The 0 to 100 scale with a marker that slides to the example score as the section scrolls in. */
export function ScoreScale({ score }: { score: number }) {
  return (
    <section className="wrap section" aria-labelledby="scale-title">
      <div className={`${styles.box} rv`}>
        <div className={styles.head}>
          <div>
            <div className="eyebrow">NeevScore</div>
            <h2 id="scale-title" className={`h2 ${styles.title}`}>
              One honest number, 0 to 100
            </h2>
          </div>
          <p className={styles.lead}>
            Everyone starts at 100. Points come off only for records we find. A source we cannot read
            lowers confidence, never adds points.
          </p>
        </div>

        <div className={styles.scale} style={{ ["--at" as string]: `${score}%` }}>
          <ol className={styles.bands}>
            {BANDS.map((band) => (
              <li key={band.key} className={styles[band.key]}>
                {band.name}
                <em>{band.range}</em>
              </li>
            ))}
          </ol>
          <div className={styles.marker}>
            <span className="num">{score}</span>
          </div>
        </div>
        <p className={styles.caption}>
          Marker: the score of the example check above. With fewer than half the key checks read, the
          score is shown without a band.
        </p>

        <ul className={styles.weights}>
          {WEIGHTS.map((weight) => (
            <li key={weight}>{weight}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
