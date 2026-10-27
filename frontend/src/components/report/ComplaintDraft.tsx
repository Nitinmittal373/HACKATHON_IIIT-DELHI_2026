"use client";

import { useState } from "react";

import { buildComplaintDraft } from "@/lib/complaint";
import { useLang } from "@/lib/LangProvider";
import type { Report } from "@/lib/types";
import styles from "./ComplaintDraft.module.css";

type Feedback = "copied" | "failed" | null;

/** One click builds an editable complaint from the findings; the buyer reviews and files it. */
export function ComplaintDraft({ report }: { report: Report }) {
  const { t, lang } = useLang();
  const [draft, setDraft] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback>(null);

  async function copy() {
    try {
      await navigator.clipboard.writeText(draft ?? "");
      setFeedback("copied");
    } catch {
      setFeedback("failed");
    }
    window.setTimeout(() => setFeedback(null), 3000);
  }

  function print() {
    document.body.dataset.print = "complaint";
    window.addEventListener("afterprint", () => (document.body.dataset.print = ""), { once: true });
    window.print();
  }

  return (
    <section className={`card complaintCard ${styles.card}`} aria-labelledby="complaint-title">
      <h2 id="complaint-title" className={styles.title}>
        {t.complaint.title}
      </h2>
      <p className={styles.lead}>{t.complaint.lead}</p>
      {draft === null ? (
        <button
          type="button"
          className="btn2 noPrint"
          onClick={() => setDraft(buildComplaintDraft(report, t, lang))}
        >
          {t.complaint.build}
        </button>
      ) : (
        <>
          <p className={styles.banner} role="note">
            {t.complaint.banner}
          </p>
          <label className={`${styles.label} noPrint`} htmlFor="complaint-text">
            {t.complaint.editLabel}
          </label>
          <textarea
            id="complaint-text"
            className={`${styles.text} noPrint`}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={16}
          />
          <div className={styles.sheet}>{draft}</div>
          <div className={`${styles.actions} noPrint`}>
            <button type="button" className="btn2" onClick={copy}>
              {t.complaint.copy}
            </button>
            <button type="button" className="btn2" onClick={print}>
              {t.complaint.print}
            </button>
            <a className="btn2" href={report.complaint_url} target="_blank" rel="noopener noreferrer">
              {t.complaint.file}
            </a>
            <span role="status">
              {feedback === "copied" && t.complaint.copied}
              {feedback === "failed" && t.complaint.copyFailed}
            </span>
          </div>
          <p className={`${styles.note} noPrint`}>{t.complaint.fileNote}</p>
        </>
      )}
    </section>
  );
}
