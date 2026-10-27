"use client";

import { useState } from "react";

import { AddToCompare } from "@/components/report/AddToCompare";
import { WatchButton } from "@/components/sentinel/WatchButton";
import { useLang } from "@/lib/LangProvider";
import { useMeta } from "@/lib/MetaProvider";
import type { DisplayScore, Project } from "@/lib/types";
import styles from "./ReportActions.module.css";

interface Props {
  reportId: string;
  project: Pick<Project, "rera_id" | "details_url" | "name">;
  score: DisplayScore;
}

type Feedback = "copied" | "failed" | null;

/** Report header buttons: watch with Sentinel and share. Sharing copies this page's link. */
export function ReportActions({ reportId, project, score }: Props) {
  const { t } = useLang();
  const meta = useMeta();
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

  function shareOnWhatsApp() {
    const link = `${window.location.origin}/report/${reportId}`;
    const name = project.name ?? project.rera_id;
    const text = t.insights.whatsapp.text(
      name,
      t.score.label(score.value, meta.scale.max, t.score.bands[score.band]),
      link,
    );
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer");
  }

  return (
    <div className={`${styles.actions} noPrint`}>
      <WatchButton project={project} />
      <AddToCompare reportId={reportId} />
      <button type="button" className="btn2" onClick={() => window.print()}>
        {t.report.download}
      </button>
      <button type="button" className="btn2" onClick={share}>
        {t.report.share}
      </button>
      <button type="button" className="btn2" onClick={shareOnWhatsApp}>
        {t.insights.whatsapp.button}
      </button>
      <span className={styles.status} role="status">
        {feedback === "copied" && t.report.linkCopied}
        {feedback === "failed" && t.report.copyFailed}
      </span>
    </div>
  );
}
