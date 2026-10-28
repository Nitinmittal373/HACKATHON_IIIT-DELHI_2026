"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { SignInForAlerts } from "@/components/sentinel/SignInForAlerts";
import { useAccount } from "@/lib/account";
import { watchProject } from "@/lib/accountReports";
import { ApiError } from "@/lib/api";
import { useLang } from "@/lib/LangProvider";
import { useMeta } from "@/lib/MetaProvider";
import type { Project } from "@/lib/types";
import styles from "./WatchDialog.module.css";

interface Props {
  project: Pick<Project, "rera_id" | "details_url">;
  open: boolean;
  onClose: () => void;
  /** Called once the watch is saved, so the page can say it is being watched. */
  onWatched?: () => void;
}

type Phase = "form" | "saving" | "done";

/** Language, then "Watching this project". Needs a signed-in account: the alert goes to its email. */
export function WatchDialog({ project, open, onClose, onWatched }: Props) {
  const { lang, t } = useLang();
  const emailAlerts = useMeta().email_alerts;
  const account = useAccount();
  const pathname = usePathname();
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const languageId = useId();
  const [phase, setPhase] = useState<Phase>("form");
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const language = new FormData(event.currentTarget).get("language") === "hi" ? "hi" : "en";
    setPhase("saving");
    setProblem(null);
    try {
      await watchProject(project, language);
      setPhase("done");
      onWatched?.();
    } catch (error) {
      setProblem(messageFor(error, t.sentinel));
      setPhase("form");
    }
  }

  return (
    <dialog ref={dialog} className={styles.dialog} onClose={onClose} aria-labelledby={`${titleId}-title`}>
      {phase === "done" ? (
        <div className={styles.body}>
          <h2 id={`${titleId}-title`} className={styles.title}>
            {t.sentinel.doneTitle}
          </h2>
          <p className={styles.lead}>{emailAlerts ? t.sentinel.doneBodyEmail : t.sentinel.doneBody}</p>
          <div className={styles.actions}>
            <Link href="/alerts" className="btn">
              {t.sentinel.seeAlerts}
            </Link>
            <button type="button" className="btn2" onClick={onClose}>
              {t.sentinel.close}
            </button>
          </div>
        </div>
      ) : account.status === "in" ? (
        <form className={styles.body} onSubmit={submit}>
          <h2 id={`${titleId}-title`} className={styles.title}>
            {t.sentinel.title}
          </h2>
          <p className={styles.lead}>{emailAlerts ? t.sentinel.lead : t.sentinel.leadInApp}</p>
          {emailAlerts && <p className={styles.lead}>{t.sentinel.sentTo(account.user.email ?? "")}</p>}
          <label htmlFor={languageId} className={styles.label}>
            {t.sentinel.language}
          </label>
          <select id={languageId} name="language" className={styles.input} defaultValue={lang}>
            <option value="en">{t.sentinel.english}</option>
            <option value="hi">{t.sentinel.hindi}</option>
          </select>
          <p className={styles.consent}>{emailAlerts ? t.legal.consent : t.legal.consentInApp}</p>
          {problem && (
            <p className={styles.problem} role="alert">
              {problem}
            </p>
          )}
          <div className={styles.actions}>
            <button type="submit" className="btn" disabled={phase === "saving"}>
              {phase === "saving" ? t.sentinel.saving : t.sentinel.submit}
            </button>
            <button type="button" className="btn2" onClick={onClose}>
              {t.sentinel.cancel}
            </button>
          </div>
        </form>
      ) : (
        <div className={styles.body}>
          <h2 id={`${titleId}-title`} className={styles.title}>
            {t.sentinel.title}
          </h2>
          <SignInForAlerts className={styles.signIn} next={`${pathname}?watch=1`} />
          <div className={styles.actions}>
            <button type="button" className="btn2" onClick={onClose}>
              {t.sentinel.cancel}
            </button>
          </div>
        </div>
      )}
    </dialog>
  );
}

function messageFor(error: unknown, s: { limit: string; signInAgain: string; failed: string }): string {
  if (error instanceof ApiError) {
    if (error.code === "watch_limit") return s.limit;
    if (error.status === 401) return s.signInAgain;
  }
  return s.failed;
}
