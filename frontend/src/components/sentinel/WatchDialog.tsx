"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { ApiError, createWatch } from "@/lib/api";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";
import styles from "./WatchDialog.module.css";

interface Props {
  project: Pick<Project, "rera_id" | "details_url">;
  open: boolean;
  onClose: () => void;
}

type Phase = { name: "form" } | { name: "saving" } | { name: "done"; email: string };

/** Email and language, then "Watching this project". A native dialog gives focus handling and Esc. */
export function WatchDialog({ project, open, onClose }: Props) {
  const { lang, t } = useLang();
  const dialog = useRef<HTMLDialogElement>(null);
  const emailId = useId();
  const languageId = useId();
  const [phase, setPhase] = useState<Phase>({ name: "form" });
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const language = form.get("language") === "hi" ? "hi" : "en";
    setPhase({ name: "saving" });
    setProblem(null);
    try {
      await createWatch(project, email, language);
      setPhase({ name: "done", email });
    } catch (error) {
      setProblem(messageFor(error, t.sentinel));
      setPhase({ name: "form" });
    }
  }

  return (
    <dialog ref={dialog} className={styles.dialog} onClose={onClose} aria-labelledby={`${emailId}-title`}>
      {phase.name === "done" ? (
        <div className={styles.body}>
          <h2 id={`${emailId}-title`} className={styles.title}>
            {t.sentinel.doneTitle}
          </h2>
          <p className={styles.lead}>{t.sentinel.doneBody}</p>
          <div className={styles.actions}>
            <Link href={`/alerts?email=${encodeURIComponent(phase.email)}`} className="btn">
              {t.sentinel.seeAlerts}
            </Link>
            <button type="button" className="btn2" onClick={onClose}>
              {t.sentinel.close}
            </button>
          </div>
        </div>
      ) : (
        <form className={styles.body} onSubmit={submit}>
          <h2 id={`${emailId}-title`} className={styles.title}>
            {t.sentinel.title}
          </h2>
          <p className={styles.lead}>{t.sentinel.lead}</p>
          <label htmlFor={emailId} className={styles.label}>
            {t.sentinel.email}
          </label>
          <input
            id={emailId}
            name="email"
            type="email"
            className={styles.input}
            placeholder={t.sentinel.emailPlaceholder}
            autoComplete="email"
            maxLength={254}
            required
          />
          <label htmlFor={languageId} className={styles.label}>
            {t.sentinel.language}
          </label>
          <select id={languageId} name="language" className={styles.input} defaultValue={lang}>
            <option value="en">{t.sentinel.english}</option>
            <option value="hi">{t.sentinel.hindi}</option>
          </select>
          <p className={styles.consent}>{t.legal.consent}</p>
          {problem && (
            <p className={styles.problem} role="alert">
              {problem}
            </p>
          )}
          <div className={styles.actions}>
            <button type="submit" className="btn" disabled={phase.name === "saving"}>
              {phase.name === "saving" ? t.sentinel.saving : t.sentinel.submit}
            </button>
            <button type="button" className="btn2" onClick={onClose}>
              {t.sentinel.cancel}
            </button>
          </div>
        </form>
      )}
    </dialog>
  );
}

function messageFor(error: unknown, s: { limit: string; invalidEmail: string; failed: string }): string {
  if (error instanceof ApiError) {
    if (error.code === "watch_limit") return s.limit;
    if (error.status === 422) return s.invalidEmail;
  }
  return s.failed;
}
