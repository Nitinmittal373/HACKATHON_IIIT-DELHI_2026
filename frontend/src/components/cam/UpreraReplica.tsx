import type { Strings } from "@/lib/i18n";
import styles from "./UpreraReplica.module.css";

interface Props {
  /** How many notes the agent has sent; each one moves the highlight to the next row. */
  notes: number;
  t: Strings;
}

/**
 * An illustration of the UP-RERA project page for sources with no live browser view. It shows
 * the labels only: the values are never drawn here, because nothing on this page is read from
 * the real record. The findings panel shows what was actually read.
 */
export function UpreraReplica({ notes, t }: Props) {
  const rows = t.cam.replicaRows;
  const active = notes % rows.length;

  return (
    <div className={styles.page} role="img" aria-label={t.cam.replicaLabel}>
      <div className={styles.head}>{t.cam.readingOfficialPage}</div>
      {rows.map((label) => (
        <div key={label} className={styles.row}>
          <span>{label}</span>
          <i className={styles.value} />
        </div>
      ))}
      <div className={styles.highlight} style={{ ["--row" as string]: active }} />
      <svg className={styles.cursor} style={{ ["--row" as string]: active }} viewBox="0 0 24 24">
        <path d="M4 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    </div>
  );
}
