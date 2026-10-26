"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";

import { listChecks } from "@/lib/api";
import { useHistory } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { CheckSummary } from "@/lib/types";
import styles from "./Compare.module.css";

interface Props {
  /** Checks already compared; they are not offered again. */
  current: string[];
  onAdd: (checkId: string) => void;
}

/** Adds a finished check from My reports, or points to a new search. */
export function AddProject({ current, onAdd }: Props) {
  const { t } = useLang();
  const selectId = useId();
  const history = useHistory();
  const [finished, setFinished] = useState<CheckSummary[]>([]);
  const [choice, setChoice] = useState("");
  const key = history?.join(",") ?? "";

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    listChecks(key.split(",")).then(
      (checks) => !cancelled && setFinished(checks.filter((check) => check.status === "completed")),
      () => undefined,
    );
    return () => {
      cancelled = true;
    };
  }, [key]);

  const offered = finished.filter((check) => !current.includes(check.id));

  return (
    <section className={`card ${styles.add}`} aria-labelledby={`${selectId}-title`}>
      <h2 id={`${selectId}-title`} className={styles.addTitle}>
        {t.compare.addTitle}
      </h2>
      {offered.length > 0 ? (
        <form
          className={styles.addForm}
          onSubmit={(event) => {
            event.preventDefault();
            if (choice) onAdd(choice);
            setChoice("");
          }}
        >
          <label htmlFor={selectId} className="sr">
            {t.compare.addLabel}
          </label>
          <select id={selectId} value={choice} onChange={(event) => setChoice(event.target.value)}>
            <option value="">{t.compare.addPlaceholder}</option>
            {offered.map((check) => (
              <option key={check.id} value={check.id}>
                {check.project ?? check.rera_id} · {check.display_score?.value}
              </option>
            ))}
          </select>
          <button type="submit" className="btn2" disabled={!choice}>
            {t.compare.addButton}
          </button>
        </form>
      ) : (
        <p className={styles.muted}>{t.compare.addNone}</p>
      )}
      <p className={styles.small}>
        {t.compare.addSearchHint}{" "}
        <Link href="/#search" className={styles.inlineLink}>
          {t.compare.searchNew}
        </Link>
      </p>
    </section>
  );
}
