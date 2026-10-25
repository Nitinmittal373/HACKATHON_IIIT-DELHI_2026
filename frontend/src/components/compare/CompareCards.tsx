import Link from "next/link";

import type { CompareRow } from "@/components/compare/compareRows";
import type { Strings } from "@/lib/i18n";
import type { ComparedProject } from "@/lib/types";
import styles from "./Compare.module.css";

interface Props {
  projects: ComparedProject[];
  rows: CompareRow[];
  onRemove: (checkId: string) => void;
  t: Strings;
}

/** Phones: one card per project under a sticky switcher that jumps between them. */
export function CompareCards({ projects, rows, onRemove, t }: Props) {
  return (
    <div className={styles.cards}>
      <nav className={styles.switcher} aria-label={t.compare.switcher}>
        {projects.map((project) => (
          <a key={project.check_id} href={`#project-${project.check_id}`}>
            {project.project.name ?? project.project.rera_id}
          </a>
        ))}
      </nav>
      {projects.map((project, column) => {
        const name = project.project.name ?? project.project.rera_id;
        return (
          <section
            key={project.check_id}
            id={`project-${project.check_id}`}
            className={`card ${styles.projectCard}`}
            aria-label={name}
          >
            <header className={styles.cardHead}>
              <Link href={`/report/${project.check_id}`} className={styles.headName}>
                {name}
              </Link>
              <button
                type="button"
                className={styles.remove}
                onClick={() => onRemove(project.check_id)}
                aria-label={t.compare.removeLabel(name)}
              >
                {t.compare.remove}
              </button>
            </header>
            <dl className={styles.facts}>
              {rows.map((row) => (
                <div key={row.key} className={column === row.best ? styles.better : undefined}>
                  <dt>{row.group ? `${row.group}: ${row.label}` : row.label}</dt>
                  <dd>
                    {row.cells[column]}
                    {column === row.best && <span className="sr"> ({t.compare.better})</span>}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        );
      })}
    </div>
  );
}
