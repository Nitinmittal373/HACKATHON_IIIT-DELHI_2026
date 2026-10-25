import styles from "./SourcesMarquee.module.css";

const SOURCES = [
  "UP-RERA",
  "MINISTRY OF CORPORATE AFFAIRS",
  "IBBI",
  "NCLT",
  "NCLAT",
  "GREATER NOIDA AUTHORITY",
  "NOIDA AUTHORITY",
  "YEIDA",
  "E-JAGRITI",
  "COURT REPORTS",
];

/** A slow ticker of the public sources NeevCheck reads. The second copy only makes the loop seamless. */
export function SourcesMarquee({ label }: { label: string }) {
  return (
    <section className={styles.rail} aria-label={label}>
      <ul className={styles.track}>
        {[...SOURCES, ...SOURCES].map((source, index) => (
          <li
            key={`${source}-${index}`}
            className={styles.item}
            aria-hidden={index >= SOURCES.length ? true : undefined}
          >
            <span className={`mono ${styles.tag}`}>{source}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
