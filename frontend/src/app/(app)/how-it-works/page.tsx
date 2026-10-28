import type { Metadata } from "next";
import Link from "next/link";

import { BandsList } from "@/components/pages/BandsList";
import { PageHead } from "@/components/pages/PageHead";
import styles from "@/components/pages/pages.module.css";
import { Steps } from "@/components/pages/Steps";
import { getStrings } from "@/lib/i18n/server";
import { loadMeta } from "@/lib/meta";
import { weightPercent } from "@/lib/neevScore";
import { SOURCE_INFO } from "@/lib/sources";
import type { SourceName } from "@/lib/types";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getStrings();
  return { title: t.pages.how.metaTitle, description: t.pages.how.metaDescription };
}

/** The method in plain words: the steps, the pillars, the scale, and where each record comes from. */
export default async function HowItWorksPage() {
  const [{ t }, meta] = await Promise.all([getStrings(), loadMeta()]);
  const copy = t.pages.how;

  return (
    <>
      <PageHead title={copy.title} lead={copy.lead} />

      <section className={styles.section} aria-labelledby="steps-title">
        <h2 id="steps-title" className={styles.heading}>
          {copy.stepsTitle}
        </h2>
        <Steps steps={copy.steps} />
      </section>

      <section className={styles.section} aria-labelledby="pillars-title">
        <h2 id="pillars-title" className={styles.heading}>
          {copy.pillarsTitle}
        </h2>
        <p className={styles.text}>{copy.pillarsLead}</p>
        <ul className={styles.rows}>
          {meta.pillars.map((pillar) => (
            <li key={pillar.id}>
              <span>
                <span className={styles.rowName}>{t.credit.pillars[pillar.id]}</span>
                <span className={styles.rowText}>{copy.pillarNotes[pillar.id]}</span>
              </span>
              <span className={styles.weight}>{weightPercent(pillar.weight)}%</span>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="scale-title">
        <h2 id="scale-title" className={styles.heading}>
          {copy.scaleTitle(meta.scale.min, meta.scale.max)}
        </h2>
        <p className={styles.text}>{copy.scaleLead(meta.scale.max)}</p>
        <BandsList meta={meta} t={t} />
      </section>

      <section className={styles.section} aria-labelledby="unrated-title">
        <h2 id="unrated-title" className={styles.heading}>
          {copy.unratedTitle}
        </h2>
        <ul className={styles.list}>
          {copy.unrated.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <h3 className={styles.rowName} style={{ marginTop: 18 }}>
          {copy.partlyTitle}
        </h3>
        <p className={styles.text}>{copy.partly}</p>
      </section>

      <section className={styles.section} aria-labelledby="sources-title">
        <h2 id="sources-title" className={styles.heading}>
          {copy.sourcesTitle}
        </h2>
        <p className={styles.text}>{copy.sourcesLead}</p>
        <ul className={styles.rows}>
          {copy.sources.map((source) => (
            <li key={source.key}>
              <span>
                <span className={styles.rowName}>{source.name}</span>
                <span className={styles.rowText}>{source.what}</span>
              </span>
              <a
                className={styles.weight}
                href={SOURCE_INFO[source.key as SourceName].officialUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                {SOURCE_INFO[source.key as SourceName].site}
                <span className="sr"> ({t.common.opensInNewTab})</span>
              </a>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="only-up-title">
        <h2 id="only-up-title" className={styles.heading}>
          {copy.onlyUpTitle}
        </h2>
        <p className={styles.text}>{copy.onlyUp}</p>
        <p className={styles.text}>
          {copy.privacyLead} <Link href="/privacy">{copy.privacyLink}</Link>.
        </p>
      </section>
    </>
  );
}
