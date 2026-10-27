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

/** The lanes of this check, reading two at a time. Opening one puts its source in the big view. */
export function WarRoom({ state, shown, onOpen, t }: Props) {
  const views = LANES.map((lane) => ({ lane, view: laneView(state, lane) }));
  const ran = views.filter(({ view }) => view.status !== "skipped").length;
  // A lane that never started says why: the check stopped early, or it predates that source.
  const skippedWhy = state.outcome?.status === "failed" ? t.cam.laneSkippedFailed : t.cam.laneSkippedOld;
  return (
    <section className={styles.room} aria-label={t.cam.warRoom}>
      <div className={styles.head}>
        <h2 className={`h3 ${styles.title}`}>{t.cam.warRoom}</h2>
        <p className={styles.hint}>{t.cam.warRoomHint(ran)}</p>
      </div>
      <ul className={styles.grid}>
        {views.map(({ lane, view }) => (
          <Lane
            key={lane.id}
            lane={view}
            open={lane.sources.includes(shown)}
            onOpen={() => onOpen(view.focus)}
            skippedWhy={skippedWhy}
            t={t}
          />
        ))}
      </ul>
    </section>
  );
}
