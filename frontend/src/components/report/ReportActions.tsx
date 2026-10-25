"use client";

import { useState } from "react";

import { useLang } from "@/lib/LangProvider";
import styles from "./ReportActions.module.css";

type Feedback = "copied" | "failed" | null;

/** Report header buttons. Sharing copies this page's link. */
export function ReportActions({ reportId }: { reportId: string; reraId: string }) {
  const { t } = useLang();
  const [feedback, setFeedback] = useState<Feedback>(null);

  async function share() {
    const link = `${window.location.origin}/report/${reportId}`;
    try {
      await navigator.clipboard.writeText(link);
      setFeedback("copied");
    } catch {
      setFeedback("failed");
    }
    window.setTimeout(() => setFeedback(null), 3000);
  }

  return (
    <div className={styles.actions}>
      <button type="button" className="btn2" onClick={share}>
        {t.report.share}
      </button>
      <span className={styles.status} role="status">
        {feedback === "copied" && t.report.linkCopied}
        {feedback === "failed" && t.report.copyFailed}
      </span>
    </div>
  );
}
