import Link from "next/link";

import type { Strings } from "@/lib/i18n";
import type { StateInfo } from "@/lib/types";
import styles from "./ResultCards.module.css";

interface Props {
  /** The states whose portals were searched; their report links are offered. */
  searched: string[];
  states: StateInfo[];
  t: Strings;
}

// More than this and "the states searched" is every state; a link to each would be a wall.
const MAX_REPORT_LINKS = 3;

/**
 * When every path found nothing. It says what is true (no record was found in public pages, which
 * is not a finding about the project) and what a buyer can do. It never calls the project illegal
 * or unregistered: a search can miss a project.
 */
export function NotFoundGuidance({ searched, states, t }: Props) {
  const copy = t.find.notFound;
  const chosen = searched.length <= MAX_REPORT_LINKS ? states.filter((s) => searched.includes(s.code)) : [];
  return (
    <section className={`card ${styles.card}`} aria-labelledby="not-found-title">
      <h2 id="not-found-title" className={styles.title}>
        {copy.title}
      </h2>
      <p className={styles.body}>{copy.note}</p>

      <h3 className={styles.sub}>{copy.stepsTitle}</h3>
      <ol className={styles.steps}>
        {copy.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>

      <h3 className={styles.sub}>{copy.reportTitle}</h3>
      <p className={styles.body}>
        {chosen.map((state) => (
          <span key={state.code}>
            <a className={styles.link} href={state.unregistered_url} target="_blank" rel="noopener noreferrer">
              {copy.reportLink(state.rera_name)}
            </a>
            {" · "}
          </span>
        ))}
        <Link className={styles.link} href="/coverage">
          {copy.reportOther}
        </Link>
      </p>

      <h3 className={styles.sub}>{copy.tryTitle}</h3>
      <ul className={styles.steps}>
        {copy.tryItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <div className={styles.actions}>
        <Link href="/#more" className="btn">
          {copy.tryButton}
        </Link>
      </div>
    </section>
  );
}
