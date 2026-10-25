import type { Strings } from "@/lib/i18n";
import styles from "./SearchProgress.module.css";

/** The wait before results: a shimmering bar, what is happening, and placeholder rows. */
export function SearchProgress({ waking, t }: { waking: boolean; t: Strings }) {
  return (
    <section className={styles.box} aria-busy="true">
      <h1 className={`h2 pageTitle ${styles.title}`} role="status">
        {waking ? t.confirm.waking : t.confirm.searching}
      </h1>
      <p className="pageLead">{t.confirm.searchingNote}</p>
      <div className={styles.track} aria-hidden="true">
        <span className={styles.shimmer} />
      </div>
      <div className={`card ${styles.rows}`} aria-hidden="true">
        {[0, 1, 2].map((row) => (
          <div key={row} className={styles.row}>
            <span className={styles.dot} />
            <span className={styles.line} style={{ width: `${62 - row * 12}%` }} />
            <span className={styles.line} style={{ width: "18%" }} />
          </div>
        ))}
      </div>
    </section>
  );
}
