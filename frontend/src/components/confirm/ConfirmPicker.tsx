"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { ProjectRow } from "@/components/confirm/ProjectRow";
import { describeApiError } from "@/lib/apiMessages";
import { startCheck } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";
import styles from "./ConfirmPicker.module.css";

/** The matching phases as radio rows, and the sticky "is this the one?" question. */
export function ConfirmPicker({ projects }: { projects: Project[] }) {
  const router = useRouter();
  const { lang, t } = useLang();
  const groupName = useId();
  const [selectedId, setSelectedId] = useState<string | null>(projects[0]?.rera_id ?? null);
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const selected = projects.find((project) => project.rera_id === selectedId) ?? null;

  async function start() {
    if (!selected || starting) return;
    setStarting(true);
    setProblem(null);
    try {
      const check = await startCheck(selected);
      // A check of this project from the last 24 hours is shown instead of starting another.
      router.push(check.reused ? `/report/${check.id}` : `/check/${check.id}`);
    } catch (error) {
      setProblem(describeApiError(error, t));
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
        {projects.map((project, index) => (
          <ProjectRow
            key={project.rera_id}
            project={project}
            selected={project.rera_id === selectedId}
            best={index === 0}
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
                {t.confirm.weFound} <b>{selected.name ?? selected.rera_id}</b> ·{" "}
                <span className="mono">{selected.rera_id}</span>
              </>
            ) : (
              t.confirm.pickOne
            )}
          </div>
          <div className={styles.question}>{t.confirm.question}</div>
        </div>
        <div className={styles.actions}>
          <button type="button" className="btn" onClick={start} disabled={!selected || starting}>
            {starting ? t.confirm.starting : t.confirm.yes}
          </button>
          {projects.length > 1 ? (
            <button type="button" className="btn2" onClick={() => setSelectedId(null)}>
              {t.confirm.no}
            </button>
          ) : (
            <Link href="/#search" className="btn2">
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
