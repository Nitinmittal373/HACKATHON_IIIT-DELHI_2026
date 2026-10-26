import type { Metadata } from "next";

import { PageMessage } from "@/components/PageMessage";
import { CoverageTable } from "@/components/coverage/CoverageTable";
import { getStrings } from "@/lib/i18n/server";
import { loadStates } from "@/lib/statesServer";
import styles from "./coverage.module.css";

export const metadata: Metadata = { title: "Coverage · NeevCheck" };

/** Which state portals are read, and how deeply. Generated from GET /api/states. */
export default async function CoveragePage() {
  const [{ t, lang }, states] = await Promise.all([getStrings(), loadStates()]);
  const c = t.states.coverage;

  return (
    <>
      <h1 className="h2 pageTitle">{c.title}</h1>
      <p className="pageLead">{c.lead}</p>

      <section className={`card ${styles.legend}`} aria-labelledby="legend-title">
        <h2 id="legend-title" className={styles.heading}>
          {c.legendTitle}
        </h2>
        <dl>
          {(["full", "partial", "search_only"] as const).map((level) => (
            <div key={level} className={styles.legendRow}>
              <dt>{t.states.levels[level]}</dt>
              <dd>{c.legend[level]}</dd>
            </div>
          ))}
        </dl>
      </section>

      {states ? (
        <CoverageTable states={states} t={t} lang={lang} />
      ) : (
        <PageMessage alert title={c.title}>
          {c.loadFailed}
        </PageMessage>
      )}

      <section className={styles.national} aria-labelledby="national-title">
        <h2 id="national-title" className={styles.heading}>
          {c.nationalTitle}
        </h2>
        <p>{c.national}</p>
      </section>
    </>
  );
}
