import type { Metadata } from "next";

import { formatDay } from "@/lib/format";
import { getStrings } from "@/lib/i18n/server";
import { PRIVACY_EMAIL, PRIVACY_UPDATED } from "@/lib/i18n/en/privacy";
import styles from "./privacy.module.css";

export const metadata: Metadata = { title: "Privacy · NeevCheck" };

/** What is kept about a visitor, in plain words. Read in the visitor's language. */
export default async function PrivacyPage() {
  const { t, lang } = await getStrings();
  const copy = t.privacy;

  return (
    <article className={styles.page}>
      <h1 className="h2 pageTitle">{copy.title}</h1>
      <p className={styles.updated}>{copy.updated(formatDay(PRIVACY_UPDATED, lang))}</p>
      <p className="pageLead">{copy.lead}</p>

      {copy.sections.map((section) => (
        <section key={section.title} className={styles.section}>
          <h2 className={styles.heading}>{section.title}</h2>
          <ul>
            {section.points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </section>
      ))}

      <section className={styles.section}>
        <h2 className={styles.heading}>{copy.remove.title}</h2>
        <ul>
          <li>{copy.remove.menu}</li>
          <li>
            {copy.remove.emailLead} <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>
          </li>
        </ul>
      </section>
    </article>
  );
}
