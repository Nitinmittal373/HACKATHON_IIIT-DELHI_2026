import { CoverageNote } from "@/components/CoverageNote";
import { StateBadge } from "@/components/StateBadge";
import type { Lang, Strings } from "@/lib/i18n";
import { stateLabel } from "@/lib/states";
import type { StateInfo } from "@/lib/types";
import styles from "./StateGroupHeader.module.css";

interface Props {
  code: string;
  name: string;
  rera: string;
  info: StateInfo | undefined;
  t: Strings;
  lang: Lang;
}

/** Heads the results of one state: its badge, how deeply its portal is read, and the link. */
export function StateGroupHeader({ code, name, rera, info, t, lang }: Props) {
  return (
    <div className={styles.head}>
      <div className={styles.title}>
        <StateBadge code={code} name={name} rera={rera} t={t} lang={lang} />
        <h2>{stateLabel(code, name, lang)}</h2>
        {info && <span className={styles.level}>{t.states.levels[info.coverage]}</span>}
      </div>
      {info && (
        <CoverageNote coverage={info.coverage} rera={info.rera_name} href={info.portal_url} t={t} />
      )}
    </div>
  );
}
