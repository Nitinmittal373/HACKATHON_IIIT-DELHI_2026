import { WatchButton } from "@/components/sentinel/WatchButton";
import type { Strings } from "@/lib/i18n";
import type { Project } from "@/lib/types";
import styles from "./SentinelCard.module.css";

export function SentinelCard({ project, t }: { project: Project; t: Strings }) {
  return (
    <section className={`card ${styles.card}`} aria-labelledby="sentinel-title">
      <h2 id="sentinel-title" className={styles.title}>
        {t.report.sentinelTitle}
      </h2>
      <p className={styles.body}>{t.sentinel.card}</p>
      <WatchButton project={project} look="card" />
    </section>
  );
}
