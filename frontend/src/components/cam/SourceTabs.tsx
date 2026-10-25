import type { SourceStatus, SourceView } from "@/lib/checkState";
import type { Strings } from "@/lib/i18n";
import { SOURCE_ORDER } from "@/lib/sources";
import type { SourceName } from "@/lib/types";
import styles from "./SourceTabs.module.css";

interface Props {
  sources: Record<SourceName, SourceView>;
  selected: SourceName;
  onSelect: (name: SourceName) => void;
  t: Strings;
}

/** One pill per source; the dot says waiting, running, done, stopped or not read. */
export function SourceTabs({ sources, selected, onSelect, t }: Props) {
  return (
    <div className={styles.tabs} role="group" aria-label={t.cam.sourceTabs}>
      {SOURCE_ORDER.map((name) => {
        const status: SourceStatus = sources[name].status;
        return (
          <button
            key={name}
            type="button"
            className={`${styles.tab} ${name === selected ? styles.selected : ""}`}
            aria-pressed={name === selected}
            onClick={() => onSelect(name)}
          >
            <span className={`${styles.dot} ${styles[status]}`} aria-hidden="true" />
            {t.cam.sourceLabels[name]}
            <span className="sr">: {t.cam.status[status]}</span>
          </button>
        );
      })}
    </div>
  );
}
