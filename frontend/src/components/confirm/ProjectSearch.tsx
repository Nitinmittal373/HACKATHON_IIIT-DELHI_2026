"use client";

import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { ConfirmPicker } from "@/components/confirm/ConfirmPicker";
import { NotFoundGuidance } from "@/components/confirm/NotFoundGuidance";
import { OrderLeadCard } from "@/components/confirm/OrderLeadCard";
import { SearchProgress } from "@/components/confirm/SearchProgress";
import { searchProjects, wakeServer } from "@/lib/api";
import { describeSearchError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import type { SearchResponse } from "@/lib/types";

type Phase =
  | { kind: "connecting" }
  | { kind: "waking" }
  | { kind: "searching" }
  | { kind: "done"; result: SearchResponse }
  | { kind: "failed"; error: unknown };

// A server that is awake answers the health ping at once; only a slow one gets the notice.
const WAKE_NOTICE_AFTER_MS = 1500;

/**
 * Searches UP-RERA from the browser, straight to the API, so a slow search or a sleeping
 * free-plan server never runs into a hosting platform's function time limit.
 */
export function ProjectSearch({ query, locality }: { query: string; locality?: string }) {
  const { t } = useLang();
  const [phase, setPhase] = useState<Phase>({ kind: "connecting" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const update = (next: Phase) => !cancelled && setPhase(next);
    update({ kind: "connecting" });
    const notice = setTimeout(() => update({ kind: "waking" }), WAKE_NOTICE_AFTER_MS);

    async function run() {
      // If the ping fails the search still runs and reports the real reason.
      await wakeServer();
      clearTimeout(notice);
      update({ kind: "searching" });
      try {
        update({ kind: "done", result: await searchProjects(query, locality) });
      } catch (error) {
        update({ kind: "failed", error });
      }
    }

    void run();
    return () => {
      cancelled = true;
      clearTimeout(notice);
    };
  }, [query, locality, attempt]);

  if (phase.kind === "failed") {
    const { text, reason } = describeSearchError(phase.error, t);
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

  if (phase.kind !== "done") return <SearchProgress waking={phase.kind === "waking"} t={t} />;

  const { candidates, order_leads: leads, outside_up: outsideUp } = phase.result;
  if (candidates.length === 0 && leads.length === 0) {
    return <NotFoundGuidance outsideUp={outsideUp} t={t} />;
  }
  return (
    <>
      {candidates.length > 0 && (
        <>
          <h1 className="h2 pageTitle">{t.confirm.title(candidates.length, query)}</h1>
          <p className="pageLead">{t.confirm.lead}</p>
          <ConfirmPicker projects={candidates} />
        </>
      )}
      {leads.map((lead) => (
        <OrderLeadCard key={lead.order_url} lead={lead} t={t} />
      ))}
    </>
  );
}
