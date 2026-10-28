"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { ConfirmPicker } from "@/components/confirm/ConfirmPicker";
import styles from "@/components/confirm/ResultCards.module.css";
import { SearchProgress } from "@/components/confirm/SearchProgress";
import { searchBuilder, wakeServer } from "@/lib/api";
import { useAccount } from "@/lib/account";
import { describeSearchError } from "@/lib/apiMessages";
import { searchToken } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { PromoterSearchResponse } from "@/lib/types";

type Phase =
  | { kind: "searching" }
  | { kind: "done"; result: PromoterSearchResponse }
  | { kind: "failed"; error: unknown };

/** A builder's registered projects, and the company pages that carry a similar name. */
export function BuilderSearch({ builder, city }: { builder: string; city?: string }) {
  const { t } = useLang();
  const signedIn = useAccount().status === "in";
  const copy = t.find.builderResults;
  const [phase, setPhase] = useState<Phase>({ kind: "searching" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setPhase({ kind: "searching" });
    void (async () => {
      await wakeServer();
      try {
        const result = await searchBuilder(builder, city, await searchToken());
        if (!cancelled) setPhase({ kind: "done", result });
      } catch (error) {
        if (!cancelled) setPhase({ kind: "failed", error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [builder, city, attempt]);

  if (phase.kind === "failed") {
    const { text, reason } = describeSearchError(phase.error, t, signedIn);
    return (
      <PageMessage
        alert
        title={t.confirm.searchFailedTitle}
        actions={
          <button type="button" className="btn" onClick={() => setAttempt((n) => n + 1)}>
            {t.common.tryAgain}
          </button>
        }
      >
        <p>{text}</p>
        {reason && <p className="mono">{t.confirm.reason(reason)}</p>}
      </PageMessage>
    );
  }
  if (phase.kind === "searching") return <SearchProgress waking={false} t={t} />;

  const { projects, companies } = phase.result;
  return (
    <>
      {projects.length > 0 ? (
        <>
          <h1 className="h2 pageTitle">{copy.title(builder)}</h1>
          <p className="pageLead">{copy.lead}</p>
          {city && <p className="pageLead">{copy.inCity(city)}</p>}
          <ConfirmPicker projects={projects} />
        </>
      ) : (
        <PageMessage
          title={copy.noneTitle}
          actions={
            <Link href="/#more" className="btn">
              {t.find.notFound.tryButton}
            </Link>
          }
        >
          <p>{copy.noneBody(builder)}</p>
        </PageMessage>
      )}
      {companies.length > 0 && (
        <section className={`card ${styles.card}`} aria-label={copy.companiesTitle}>
          <h2 className={styles.title}>{copy.companiesTitle}</h2>
          <p className={styles.body}>{copy.companiesNote}</p>
          <ul className={styles.list}>
            {companies.map((company) => (
              <li key={company.name} className={styles.item}>
                <span>
                  <b>{company.name}</b>
                  {company.cin && (
                    <span className={`mono ${styles.meta}`}>
                      {copy.cin}: {company.cin}
                    </span>
                  )}
                </span>
                <a className={styles.link} href={company.source_url} target="_blank" rel="noopener noreferrer">
                  {copy.openPage}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
