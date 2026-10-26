"use client";

import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { ConfirmPicker } from "@/components/confirm/ConfirmPicker";
import { NotFoundGuidance } from "@/components/confirm/NotFoundGuidance";
import { OrderLeadCard } from "@/components/confirm/OrderLeadCard";
import { PreReraCard } from "@/components/confirm/PreReraCard";
import { SearchProgress } from "@/components/confirm/SearchProgress";
import { searchProjects, wakeServer } from "@/lib/api";
import { describeSearchError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import type { SearchResponse } from "@/lib/types";
import { useStates } from "@/lib/useStates";

type Phase =
  | { kind: "connecting" }
  | { kind: "waking" }
  | { kind: "searching" }
  | { kind: "done"; result: SearchResponse }
  | { kind: "failed"; error: unknown };

// A server that is awake answers the health ping at once; only a slow one gets the notice.
const WAKE_NOTICE_AFTER_MS = 1500;

/**
 * Searches the RERA portals from the browser, straight to the API, so a slow search or a sleeping
 * free-plan server never runs into a hosting platform's function time limit.
 */
export function ProjectSearch({
  query,
  state,
  locality,
}: {
  query: string;
  state?: string;
  locality?: string;
}) {
  const { t } = useLang();
  const load = useStates();
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
        update({ kind: "done", result: await searchProjects(query, state, locality) });
      } catch (error) {
        update({ kind: "failed", error });
      }
    }

    void run();
    return () => {
      cancelled = true;
      clearTimeout(notice);
    };
  }, [query, state, locality, attempt]);

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

  const { candidates, searched_states: searched, pre_rera: notes, order_leads: leads } = phase.result;
  if (candidates.length === 0 && notes.length === 0 && leads.length === 0) {
    const states = load.status === "ready" ? load.states : [];
    return <NotFoundGuidance searched={searched} states={states} t={t} />;
  }
  return (
    <>
      {candidates.length > 0 && (
        <>
          <h1 className="h2 pageTitle">{t.confirm.title(candidates.length, query)}</h1>
          <p className="pageLead">{t.confirm.lead}</p>
          {searched.length > 0 && <p className="pageLead">{t.states.searchedIn(searched.join(", "))}</p>}
          <ConfirmPicker projects={candidates} />
        </>
      )}
      {notes.map((note) => (
        <PreReraCard key={note.source_url} note={note} t={t} />
      ))}
      {leads.map((lead) => (
        <OrderLeadCard key={lead.order_url} lead={lead} t={t} />
      ))}
    </>
  );
}
