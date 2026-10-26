"use client";

import { useId, useState, type ChangeEvent } from "react";

import { ExtractedNumbers } from "@/components/find/ExtractedNumbers";
import { extractFromPdf } from "@/lib/api";
import { describeApiError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import type { ExtractResponse } from "@/lib/types";
import styles from "./MoreWays.module.css";

const MAX_BYTES = 5 * 1024 * 1024;

type Phase =
  | { kind: "idle" }
  | { kind: "reading" }
  | { kind: "done"; result: ExtractResponse }
  | { kind: "failed"; message: string };

/** A brochure or agreement as a PDF: the server finds the RERA number and keeps nothing. */
export function DocumentUpload() {
  const { t } = useLang();
  const inputId = useId();
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const copy = t.find.more.document;

  async function chosen(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_BYTES) return setPhase({ kind: "failed", message: copy.tooBig });
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      return setPhase({ kind: "failed", message: copy.notPdf });
    }
    setPhase({ kind: "reading" });
    try {
      setPhase({ kind: "done", result: await extractFromPdf(file) });
    } catch (error) {
      setPhase({ kind: "failed", message: describeApiError(error, t) || copy.failed });
    }
  }

  return (
    <div className={styles.drop}>
      <label htmlFor={inputId} className={styles.help}>
        {copy.limit}
      </label>
      <input id={inputId} className={styles.file} type="file" accept="application/pdf,.pdf" onChange={chosen} />
      <p className={styles.privacy}>{copy.privacy}</p>
      {phase.kind === "reading" && (
        <p className={styles.status} role="status">
          {copy.reading}
        </p>
      )}
      {phase.kind === "failed" && (
        <p className={styles.error} role="alert">
          {phase.message}
        </p>
      )}
      {phase.kind === "done" && <ExtractedNumbers result={phase.result} />}
    </div>
  );
}
