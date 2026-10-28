import Link from "next/link";

import type { Strings } from "@/lib/i18n";
import styles from "./ResultCards.module.css";

const UNREGISTERED_URL = "https://www.up-rera.in/NonRegistration";

interface Props {
  /** True when the text was another state's number or a place outside Uttar Pradesh. */
  outsideUp: boolean;
  t: Strings;
}

/**
 * When every path found nothing. It says what is true (no record was found in public pages, which
 * is not a finding about the project) and what a buyer can do. It never calls the project illegal
 * or unregistered: a search can miss a project. A project of another state gets one calm line.
 */
export function NotFoundGuidance({ outsideUp, t }: Props) {
  const copy = t.find.notFound;
  if (outsideUp) {
    return (
      <section className={`card ${styles.card}`} aria-labelledby="outside-up-title">
        <h2 id="outside-up-title" className={styles.title}>
          {t.find.outsideUp}
        </h2>
        <div className={styles.actions}>
          <Link href="/check" className="btn">
            {copy.tryButton}
          </Link>
        </div>
      </section>
    );
  }
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
        <a className={styles.link} href={UNREGISTERED_URL} target="_blank" rel="noopener noreferrer">
          {copy.reportLink}
        </a>
      </p>

      <h3 className={styles.sub}>{copy.tryTitle}</h3>
      <ul className={styles.steps}>
        {copy.tryItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <div className={styles.actions}>
        <Link href="/check" className="btn">
          {copy.tryButton}
        </Link>
      </div>
    </section>
  );
}
