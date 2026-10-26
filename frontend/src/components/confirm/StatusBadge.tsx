import type { Strings } from "@/lib/i18n";
import type { CandidateStatus } from "@/lib/types";
import styles from "./StatusBadge.module.css";

/** How sure we are that the number exists: orange only for what a state portal itself printed. */
export function StatusBadge({ status, t }: { status: CandidateStatus; t: Strings }) {
  return (
    <span
      className={`${styles.badge} ${status === "confirmed" ? styles.confirmed : ""}`}
      title={t.find.statusHelp[status]}
    >
      {t.find.status[status]}
    </span>
  );
}
