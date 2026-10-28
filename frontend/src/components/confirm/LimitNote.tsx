import type { Strings } from "@/lib/i18n";
import type { Limits } from "@/lib/types";
import styles from "./ConfirmPicker.module.css";

interface Props {
  limits: Limits | null;
  needsSignIn: boolean;
  t: Strings;
}

/** One quiet line under the question: what signing in unlocks, or how many checks are left. */
export function LimitNote({ limits, needsSignIn, t }: Props) {
  if (needsSignIn) {
    return <p className={styles.limit}>{t.confirm.signedOutNote(limits?.reuse_report_days ?? 7)}</p>;
  }
  if (limits?.invited === false) return <p className={styles.limit}>{t.errors.inviteOnly}</p>;
  if (limits?.live_checks_open === false) return <p className={styles.limit}>{t.errors.siteBudget}</p>;
  if (limits?.checks_left_today != null) {
    return <p className={styles.limit}>{t.confirm.liveChecksLeft(limits.checks_left_today)}</p>;
  }
  return null;
}
