"use client";

import { useId, useState, type FormEvent } from "react";

import { ApiError, sendCorrection } from "@/lib/api";
import { useLang } from "@/lib/LangProvider";
import type { Finding } from "@/lib/types";
import styles from "./CorrectionForm.module.css";

type Phase = "closed" | "form" | "sending" | "sent";

/** Right of reply: anyone can say a finding is wrong; the operator reads the messages. */
export function CorrectionForm({ reportId, findings }: { reportId: string; findings: Finding[] }) {
  const { t } = useLang();
  const id = useId();
  const [phase, setPhase] = useState<Phase>("closed");
  const [problem, setProblem] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = String(form.get("message") ?? "").trim();
    if (message.length < 5) {
      setProblem(t.legal.correction.tooShort);
      return;
    }
    const finding = String(form.get("finding") ?? "");
    const contact = String(form.get("contact") ?? "").trim();
    setPhase("sending");
    setProblem(null);
    try {
      await sendCorrection({
        report_id: reportId,
        message,
        ...(finding && { finding_id: finding }),
        ...(contact && { contact }),
      });
      setPhase("sent");
    } catch (error) {
      const busy = error instanceof ApiError && error.status === 429;
      setProblem(busy ? t.legal.correction.tooMany : t.legal.correction.failed);
      setPhase("form");
    }
  }

  return (
    <section className={`card ${styles.card} noPrint`} aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className={styles.title}>
        {t.legal.correction.title}
      </h2>
      <p className={styles.lead}>{t.legal.correction.lead}</p>
      {phase === "closed" && (
        <button type="button" className="btn2" onClick={() => setPhase("form")}>
          {t.legal.correction.open}
        </button>
      )}
      {(phase === "form" || phase === "sending") && (
        <form className={styles.form} onSubmit={submit}>
          <label htmlFor={`${id}-finding`}>{t.legal.correction.findingLabel}</label>
          <select id={`${id}-finding`} name="finding" className={styles.input} defaultValue="">
            <option value="">{t.legal.correction.wholeReport}</option>
            {findings.map((finding) => (
              <option key={finding.id} value={finding.id}>
                {finding.title.slice(0, 90)}
              </option>
            ))}
          </select>
          <label htmlFor={`${id}-message`}>{t.legal.correction.messageLabel}</label>
          <textarea id={`${id}-message`} name="message" className={styles.input} rows={4} maxLength={2000} />
          <label htmlFor={`${id}-contact`}>{t.legal.correction.contactLabel}</label>
          <input id={`${id}-contact`} name="contact" type="email" className={styles.input} maxLength={254} />
          {problem && (
            <p className={styles.problem} role="alert">
              {problem}
            </p>
          )}
          <div className={styles.actions}>
            <button type="submit" className="btn" disabled={phase === "sending"}>
              {phase === "sending" ? t.legal.correction.sending : t.legal.correction.send}
            </button>
            <button type="button" className="btn2" onClick={() => setPhase("closed")}>
              {t.legal.correction.cancel}
            </button>
          </div>
        </form>
      )}
      {phase === "sent" && (
        <p className={styles.thanks} role="status">
          {t.legal.correction.thanks}
        </p>
      )}
    </section>
  );
}
