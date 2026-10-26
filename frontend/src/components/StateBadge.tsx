import type { Lang, Strings } from "@/lib/i18n";
import { stateLabel } from "@/lib/states";
import styles from "./StateBadge.module.css";

interface Props {
  code: string;
  name: string;
  rera: string;
  t: Strings;
  lang: Lang;
  /** Show the state's name beside its code. */
  withName?: boolean;
}

/** A small mark of the state a project is registered in, so no result is read as UP by default. */
export function StateBadge({ code, name, rera, t, lang, withName = false }: Props) {
  const label = stateLabel(code, name, lang);
  return (
    <span className={styles.badge} title={t.states.badgeLabel(label, rera)}>
      <b className="mono">{code}</b>
      {withName && <span>{label}</span>}
    </span>
  );
}
