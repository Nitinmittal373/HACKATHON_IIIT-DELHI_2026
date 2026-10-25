"use client";

import { useState } from "react";

import { WatchButton } from "@/components/sentinel/WatchButton";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";
import styles from "./ReportActions.module.css";

interface Props {
  reportId: string;
  project: Pick<Project, "rera_id" | "details_url">;
}

type Feedback = "copied" | "failed" | null;

/** Report header buttons: watch with Sentinel and share. Sharing copies this page's link. */
export function ReportActions({ reportId, project }: Props) {
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
    <div className={`${styles.actions} noPrint`}>
      <WatchButton project={project} />
      <button type="button" className="btn2" onClick={() => window.print()}>
        {t.report.download}
      </button>
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
