"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { LimitNote } from "@/components/confirm/LimitNote";
import { ProjectRow } from "@/components/confirm/ProjectRow";
import { useAccount } from "@/lib/account";
import { ApiError } from "@/lib/api";
import { describeApiError } from "@/lib/apiMessages";
import { startCheck } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import { useLimits } from "@/lib/useLimits";
import type { Project } from "@/lib/types";
import styles from "./ConfirmPicker.module.css";

/** The matching phases as radio rows, and the sticky "is this the one?" question. */
export function ConfirmPicker({ projects }: { projects: Project[] }) {
  const router = useRouter();
  const { lang, t } = useLang();
  const account = useAccount();
  const limits = useLimits();
  const groupName = useId();
  const [selectedId, setSelectedId] = useState<string | null>(projects[0]?.rera_id ?? null);
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const selected = projects.find((project) => project.rera_id === selectedId) ?? null;
  // Signed out, a new live check needs a sign-in; a recent report still opens without one.
  const needsSignIn = account.status !== "in" && limits?.require_signin === true;

  async function start() {
    if (!selected || starting) return;
    setStarting(true);
    setProblem(null);
    try {
      const check = await startCheck(selected);
      // A recent report of this project is shown instead of starting another check.
      router.push(check.reused ? `/report/${check.id}` : `/check/${check.id}`);
    } catch (error) {
      if (error instanceof ApiError && error.code === "signin_required") {
        const here = `${window.location.pathname}${window.location.search}`;
        router.push(`/login?next=${encodeURIComponent(here)}`);
        return;
      }
      setProblem(describeApiError(error, t, lang));
      setStarting(false);
    }
  }

  return (
    <>
      <div className={`card ${styles.table}`} role="radiogroup" aria-label={t.confirm.tableLabel}>
        <div className={`mono ${styles.head}`} aria-hidden="true">
          <span />
          <span>{t.confirm.colProject.toUpperCase()}</span>
          <span>{t.confirm.colNumber.toUpperCase()}</span>
          <span>{t.confirm.colRegistered.toUpperCase()}</span>
          <span />
        </div>
        {projects.map((project) => (
          <ProjectRow
            key={project.rera_id}
            project={project}
            selected={project.rera_id === selectedId}
            best={project.rera_id === projects[0]?.rera_id}
            groupName={groupName}
            onSelect={() => setSelectedId(project.rera_id)}
            t={t}
            lang={lang}
          />
        ))}
      </div>

      <div className={`card ${styles.bar}`}>
        <div>
          <div className={styles.found}>
            {selected ? (
              <>
                {t.confirm.weFound} <b>{selected.name ?? t.confirm.unnamed}</b> ·{" "}
                <span className="mono">{selected.rera_id}</span>
              </>
            ) : (
              t.confirm.pickOne
            )}
          </div>
          <div className={styles.question}>{t.confirm.question}</div>
          <LimitNote limits={limits} needsSignIn={needsSignIn} t={t} />
        </div>
        <div className={styles.actions}>
          <button type="button" className="btn" onClick={start} disabled={!selected || starting}>
            {starting ? t.confirm.starting : needsSignIn ? t.confirm.signInToRun : t.confirm.yes}
          </button>
          {projects.length > 1 ? (
            <button type="button" className="btn2" onClick={() => setSelectedId(null)}>
              {t.confirm.no}
            </button>
          ) : (
            <Link href="/check" className="btn2">
              {t.confirm.no}
            </Link>
          )}
        </div>
      </div>

      {problem && (
        <PageMessage title={t.confirm.startFailedTitle} alert>
          {problem}
        </PageMessage>
      )}
    </>
  );
}
