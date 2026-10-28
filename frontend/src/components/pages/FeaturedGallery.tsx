"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { NeevScore } from "@/components/NeevScore";
import { getFeatured } from "@/lib/api";
import { dayOf } from "@/lib/format";
import { useLang } from "@/lib/LangProvider";
import type { FeaturedProject } from "@/lib/types";
import styles from "./pages.module.css";

/**
 * Saved reports of well-known projects. Each card is a check already in the database; a project
 * nobody has checked is simply absent, and nothing here says who ran a check.
 */
export function FeaturedGallery() {
  const { lang, t } = useLang();
  const copy = t.pages.check;
  const [projects, setProjects] = useState<FeaturedProject[]>([]);

  useEffect(() => {
    let cancelled = false;
    getFeatured().then(
      (found) => !cancelled && setProjects(found),
      () => !cancelled && setProjects([]),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  if (projects.length === 0) return null;
  return (
    <section className={styles.sectionWide} aria-labelledby="gallery-title">
      <h2 id="gallery-title" className={styles.heading}>
        {copy.galleryTitle}
      </h2>
      <p className={styles.text}>{copy.galleryLead}</p>
      <ul className={styles.gallery}>
        {projects.map((project) => (
          <li key={project.check_id}>
            <Link href={`/report/${project.check_id}`} className={`card ${styles.galleryCard}`}>
              <NeevScore score={project.display_score} size={64} delay={0} />
              <span className={styles.galleryName}>{project.name ?? project.rera_id}</span>
              <span className={styles.galleryMeta}>
                {copy.galleryRead(dayOf(project.read_at, lang))}
              </span>
              <span className={styles.galleryOpen}>{copy.galleryOpen}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
