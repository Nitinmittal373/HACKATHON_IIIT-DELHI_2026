import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Project } from "@/lib/types";
import styles from "./ProjectRow.module.css";

interface Props {
  project: Project;
  selected: boolean;
  best: boolean;
  groupName: string;
  onSelect: () => void;
  t: Strings;
  lang: Lang;
}

/** One selectable row: a real radio button, so arrow keys and screen readers just work. */
export function ProjectRow({ project, selected, best, groupName, onSelect, t, lang }: Props) {
  const detail = [project.district, project.promoter].filter(Boolean).join(" · ");
  return (
    <label className={`${styles.row} ${selected ? styles.selected : ""}`}>
      <input
        className={styles.input}
        type="radio"
        name={groupName}
        value={project.rera_id}
        checked={selected}
        onChange={onSelect}
      />
      <span className={styles.radio} aria-hidden="true">
        <span />
      </span>
      <span className={styles.main}>
        <b>{project.name ?? t.confirm.unnamed}</b>
        {detail && <span className={styles.detail}>{detail}</span>}
        <span className={`mono ${styles.mobileNumber}`}>{project.rera_id}</span>
        {best && <i className={`${styles.badge} ${styles.mobileBadge}`}>{t.confirm.bestMatch}</i>}
      </span>
      <span className={`mono ${styles.cell} ${styles.number}`}>{project.rera_id}</span>
      <span className={styles.cell}>
        {project.registered_on ? formatDay(project.registered_on, lang) : ""}
      </span>
      <span className={styles.cell}>
        {best && <i className={styles.badge}>{t.confirm.bestMatch}</i>}
      </span>
    </label>
  );
}
