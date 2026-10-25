"use client";

import { useState } from "react";

import { useLang } from "@/lib/LangProvider";
import styles from "./BuilderQuestions.module.css";

type Feedback = "copied" | "failed" | null;

export function CopyQuestions({ text }: { text: string }) {
  const { t } = useLang();
  const [feedback, setFeedback] = useState<Feedback>(null);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setFeedback("copied");
    } catch {
      setFeedback("failed");
    }
    window.setTimeout(() => setFeedback(null), 3000);
  }

  return (
    <p className={`${styles.copy} noPrint`}>
      <button type="button" className="btn2" onClick={copy}>
        {t.insights.questions.copy}
      </button>
      <span role="status">
        {feedback === "copied" && t.insights.questions.copied}
        {feedback === "failed" && t.insights.questions.copyFailed}
      </span>
    </p>
  );
}
