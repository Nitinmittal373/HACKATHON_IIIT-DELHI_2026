"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { ProjectRow } from "@/components/confirm/ProjectRow";
import { StateGroupHeader } from "@/components/confirm/StateGroupHeader";
import { describeApiError } from "@/lib/apiMessages";
import { startCheck } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import { useStates } from "@/lib/useStates";
import type { Project } from "@/lib/types";
import styles from "./ConfirmPicker.module.css";

/** The matching phases as radio rows, and the sticky "is this the one?" question. */
export function ConfirmPicker({ projects }: { projects: Project[] }) {
  const router = useRouter();
  const { lang, t } = useLang();
  const groupName = useId();
  const load = useStates();
  const info = load.status === "ready" ? load.states : [];
  const groups = groupByState(projects);
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
      {groups.map((group) => (
        <section key={group.code} aria-label={group.name}>
          <StateGroupHeader
            code={group.code}
            name={group.name}
            rera={group.rera}
            info={info.find((state) => state.code === group.code)}
            t={t}
            lang={lang}
          />
          <div className={`card ${styles.table}`} role="radiogroup" aria-label={t.confirm.tableLabel}>
            <div className={`mono ${styles.head}`} aria-hidden="true">
              <span />
              <span>{t.confirm.colProject.toUpperCase()}</span>
              <span>{t.confirm.colNumber.toUpperCase()}</span>
              <span>{t.confirm.colRegistered.toUpperCase()}</span>
              <span />
            </div>
            {group.projects.map((project) => (
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
        </section>
      ))}

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

interface StateGroup {
  code: string;
  name: string;
  rera: string;
  projects: Project[];
}

/** Results by state, in the order each state first appears (the best match's state first). */
function groupByState(projects: Project[]): StateGroup[] {
  const groups = new Map<string, StateGroup>();
  for (const project of projects) {
    const group = groups.get(project.state) ?? {
      code: project.state,
      name: project.state_name,
      rera: project.rera_name,
      projects: [],
    };
    group.projects.push(project);
    groups.set(project.state, group);
  }
  return [...groups.values()];
}
