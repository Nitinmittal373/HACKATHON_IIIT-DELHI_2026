"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createCheck } from "@/lib/api";
import { describeApiError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";
import styles from "./RecheckNote.module.css";

interface Props {
  hours: number;
  project: Pick<Project, "rera_id" | "details_url">;
}

/** "Checked 3 h ago" with a way to start a fresh check instead of the reused one. */
export function RecheckNote({ hours, project }: Props) {
  const router = useRouter();
  const { t } = useLang();
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function recheck() {
    setStarting(true);
    setProblem(null);
    try {
      const check = await createCheck(project, { fresh: true });
      router.push(`/check/${check.id}`);
    } catch (error) {
      setProblem(describeApiError(error, t));
      setStarting(false);
    }
  }

  return (
    <p className={styles.note}>
      <span>{t.report.checkedAgo(hours)}</span>
      <button type="button" className={styles.button} onClick={recheck} disabled={starting}>
        {t.report.recheck}
      </button>
      {problem && (
        <span className={styles.problem} role="alert">
          {problem}
        </span>
      )}
    </p>
  );
}
