import { Lane } from "@/components/cam/Lane";
import type { CamState } from "@/lib/checkState";
import type { Strings } from "@/lib/i18n";
import { LANES, laneView } from "@/lib/lanes";
import type { SourceName } from "@/lib/types";
import styles from "./WarRoom.module.css";

interface Props {
  state: CamState;
  /** The source shown in the big browser view below. */
  shown: SourceName;
  onOpen: (source: SourceName) => void;
  t: Strings;
}

/** Six lanes reading in parallel. Opening a lane puts its source in the big browser view. */
export function WarRoom({ state, shown, onOpen, t }: Props) {
  return (
    <section className={styles.room} aria-label={t.cam.warRoom}>
      <div className={styles.head}>
        <h2 className={`h3 ${styles.title}`}>{t.cam.warRoom}</h2>
        <p className={styles.hint}>{t.cam.warRoomHint}</p>
      </div>
      <ul className={styles.grid}>
        {LANES.map((lane) => {
          const view = laneView(state, lane);
          return (
            <Lane
              key={lane.id}
              lane={view}
              open={lane.sources.includes(shown)}
              onOpen={() => onOpen(view.focus)}
              t={t}
            />
          );
        })}
      </ul>
    </section>
  );
}
