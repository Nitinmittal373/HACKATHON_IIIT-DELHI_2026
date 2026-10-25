import Link from "next/link";
import { Fragment } from "react";

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

/** Wide screens: one column per project, one row per question; the better value is tinted. */
export function CompareTable({ projects, rows, onRemove, t }: Props) {
  return (
    <div className={`card ${styles.tableWrap}`}>
      <table className={styles.table}>
        <caption className="sr">{t.compare.tableLabel}</caption>
        <thead>
          <tr>
            <td />
            {projects.map((project) => {
              const name = project.project.name ?? project.project.rera_id;
              return (
                <th key={project.check_id} scope="col" className={styles.head}>
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
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <Fragment key={row.key}>
              {row.group && rows[index - 1]?.group !== row.group && (
                <tr className={styles.groupRow}>
                  <th scope="rowgroup" colSpan={projects.length + 1}>
                    {row.group}
                  </th>
                </tr>
              )}
              <tr>
                <th scope="row" className={row.group ? styles.indented : undefined}>
                  {row.label}
                </th>
                {row.cells.map((cell, column) => (
                  <td key={projects[column]?.check_id} className={column === row.best ? styles.better : undefined}>
                    {cell}
                    {column === row.best && <span className="sr"> ({t.compare.better})</span>}
                  </td>
                ))}
              </tr>
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
