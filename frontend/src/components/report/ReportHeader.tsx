import { ReportActions } from "@/components/report/ReportActions";
import { dayOf } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Report } from "@/lib/types";
import styles from "./ReportHeader.module.css";

interface Props {
  report: Report;
  t: Strings;
  lang: Lang;
}

export function ReportHeader({ report, t, lang }: Props) {
  const { project, check } = report;
  const checkedOn = dayOf(check.completed_at ?? check.started_at, lang);
  const meta = [project.district, project.promoter].filter(Boolean).join(" · ");

  return (
    <header>
      <div className="eyebrow">{t.report.step(checkedOn)}</div>
      <div className={styles.row}>
        <div>
          <h1 className="h2 pageTitle" style={{ marginTop: 10 }}>
            {project.name ?? project.rera_id}
          </h1>
          <p className={styles.meta}>
            {meta && `${meta} · `}
            <span className="mono">{project.rera_id}</span>
          </p>
        </div>
        <ReportActions reportId={check.id} reraId={project.rera_id} />
      </div>
    </header>
  );
}
