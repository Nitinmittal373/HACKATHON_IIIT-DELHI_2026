"use client";

import { useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { unsubscribe } from "@/lib/api";
import { useLang } from "@/lib/LangProvider";

type Step = "ask" | "sending" | "done" | "failed";

/** Asks first, then stops the watch. The request is only sent by the button, never by opening the page. */
export function StopAlerts({ token }: { token: string }) {
  const { t } = useLang();
  const copy = t.alerts.stop;
  const [step, setStep] = useState<Step>("ask");

  async function stop() {
    setStep("sending");
    try {
      await unsubscribe(token);
      setStep("done");
    } catch {
      setStep("failed");
    }
  }

  if (step === "done") return <PageMessage title={copy.doneTitle}>{copy.done}</PageMessage>;
  return (
    <>
      {step === "failed" && (
        <PageMessage alert title={copy.failedTitle}>
          {copy.failed}
        </PageMessage>
      )}
      <h1 className="h2 pageTitle">{copy.title}</h1>
      <p className="pageLead">{copy.lead}</p>
      <p>
        <button type="button" className="btn" disabled={step === "sending"} onClick={() => void stop()}>
          {copy.button}
        </button>
      </p>
    </>
  );
}
