"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { NeevScore } from "@/components/NeevScore";
import { Skeleton } from "@/components/Skeleton";
import { promoterProjects } from "@/lib/api";
import { formatDay } from "@/lib/format";
import { relabel } from "@/lib/i18n/relabel";
import { useLang } from "@/lib/LangProvider";
import type { TrackedProject } from "@/lib/types";
import styles from "./TrackRecord.module.css";

type Loaded = { status: "loading" } | { status: "ready"; projects: TrackedProject[] } | { status: "failed" };

/** The promoter's other projects in the same state, each one a click away from its own live check. */
export function TrackRecord({
  promoter,
  reraId,
  state,
  rera,
}: {
  promoter: string;
  reraId: string;
  state: string;
  rera: string;
}) {
  const { lang, t: base } = useLang();
  const t = relabel(base, rera);
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    promoterProjects(promoter, reraId, state).then(
      (record) => !cancelled && setLoaded({ status: "ready", projects: record.projects }),
      () => !cancelled && setLoaded({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, [promoter, reraId, state]);

  return (
    <section className={`card ${styles.card} noPrint`} aria-labelledby="track-title" aria-busy={loaded.status === "loading"}>
      <h2 id="track-title" className={styles.title}>
        {t.insights.track.title(promoter)}
      </h2>
      <p className={styles.note}>{t.insights.track.note}</p>
      {loaded.status === "loading" && (
        <div className={styles.loading}>
          <span className="sr" role="status">
            {t.insights.track.loading}
          </span>
          <Skeleton height={44} />
          <Skeleton height={44} />
        </div>
      )}
      {loaded.status === "failed" && <p className={styles.empty}>{t.insights.track.failed}</p>}
      {loaded.status === "ready" && loaded.projects.length === 0 && (
        <p className={styles.empty}>{t.insights.track.none}</p>
      )}
      {loaded.status === "ready" && loaded.projects.length > 0 && (
        <ul className={styles.list}>
          {loaded.projects.map((project) => {
            const name = project.name ?? t.insights.track.unnamed;
            return (
              <li key={project.rera_id} className={styles.item}>
                <div className={styles.text}>
                  <span className={styles.name}>{name}</span>
                  <span className={`mono ${styles.meta}`}>
                    {project.rera_id}
                    {project.registered_on &&
                      ` · ${t.insights.track.registered(formatDay(project.registered_on, lang))}`}
                  </span>
                </div>
                {project.display_score && (
                  <NeevScore score={project.display_score} variant="chip" />
                )}
                <Link
                  href={`/check?q=${encodeURIComponent(project.rera_id)}`}
                  className="btn2"
                  aria-label={t.insights.track.checkLabel(project.name ?? project.rera_id)}
                >
                  {t.insights.track.check}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
