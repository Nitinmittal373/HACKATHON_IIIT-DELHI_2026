import Link from "next/link";

import type { Strings } from "@/lib/i18n";
import type { PreReraNote } from "@/lib/types";
import styles from "./ResultCards.module.css";

/** A project that public pages say was finished before RERA: their words, their link, no score. */
export function PreReraCard({ note, t }: { note: PreReraNote; t: Strings }) {
  const copy = t.find.preRera;
  return (
    <section className={`card ${styles.card} ${styles.soft}`} aria-label={copy.title}>
      <h2 className={styles.title}>{copy.title}</h2>
      <p className={styles.body}>{copy.body(note.name)}</p>
      <blockquote className={styles.quote}>“{note.statement}”</blockquote>
      <p className={styles.body}>
        <a className={styles.link} href={note.source_url} target="_blank" rel="noopener noreferrer">
          {copy.source}
        </a>
      </p>
      <p className={styles.body}>{copy.next}</p>
      <div className={styles.actions}>
        <Link href={`/check?builder=${encodeURIComponent(builderWord(note.name))}`} className="btn2">
          {copy.builderButton}
        </Link>
      </div>
    </section>
  );
}

/** The first word of a project name is usually the builder's brand ("DLF The Camellias"). */
function builderWord(name: string): string {
  const first = name.trim().split(/\s+/)[0] ?? name;
  return first.length >= 3 ? first : name;
}
