"use client";

import { useState } from "react";

import { BrowserWindow } from "@/components/cam/BrowserWindow";
import { FindingsPanel } from "@/components/cam/FindingsPanel";
import { ResultCard } from "@/components/cam/ResultCard";
import { SourceTabs } from "@/components/cam/SourceTabs";
import { WarRoom } from "@/components/cam/WarRoom";
import { activeSource, progressPercent, visibleSources, type CamState } from "@/lib/checkState";
import { useLang } from "@/lib/LangProvider";
import { SOURCE_INFO } from "@/lib/sources";
import type { SourceName } from "@/lib/types";
import { useCheckEvents } from "@/lib/useCheckEvents";
import styles from "./AgentCam.module.css";

interface Props {
  checkId: string;
  reraId: string;
  /** The UP-RERA page the check reads; shown in the address bar until a finding names a page. */
  detailsUrl: string;
}

/** The live check: source tabs, the agent's browser, and the findings as they arrive. */
export function AgentCam({ checkId, reraId, detailsUrl }: Props) {
  const { t } = useLang();
  const { state, connection } = useCheckEvents(checkId);
  // Until a tab is clicked the window follows whichever source is working.
  const [picked, setPicked] = useState<SourceName | null>(null);
  const shown = picked ?? activeSource(state);
  const percent = progressPercent(state);

  return (
    <>
      <div className={styles.head}>
        <div>
          <div className="eyebrow">{t.cam.step}</div>
          <h1 className="h2 pageTitle">{t.cam.title}</h1>
        </div>
        <div className={styles.agent}>
          <span className={`${styles.rec} ${state.outcome ? styles.recOff : ""}`} aria-hidden="true" />
          {t.cam.agentCam}
        </div>
      </div>

      {connection === "reconnecting" && <p className={styles.notice} role="status">{t.cam.reconnecting}</p>}
      {connection === "polling" && <p className={styles.notice} role="status">{t.cam.polling}</p>}

      <WarRoom state={state} shown={shown} onOpen={setPicked} t={t} />

      <SourceTabs
        sources={state.sources}
        names={visibleSources(state)}
        selected={shown}
        onSelect={setPicked}
        t={t}
      />

      <div className={styles.grid}>
        <BrowserWindow
          name={shown}
          view={state.sources[shown]}
          address={addressFor(shown, state, detailsUrl)}
          percent={percent}
          t={t}
        />
        <FindingsPanel findings={state.findings} t={t} />
      </div>

      {state.outcome && <ResultCard outcome={state.outcome} checkId={checkId} reraId={reraId} t={t} />}
    </>
  );
}

function addressFor(name: SourceName, state: CamState, detailsUrl: string): string {
  const latest = state.findings.find((finding) => finding.source === name);
  const url = latest?.source_url ?? (name === "uprera" ? detailsUrl : `https://${SOURCE_INFO[name].site}`);
  return url.replace(/^https?:\/\//, "");
}
