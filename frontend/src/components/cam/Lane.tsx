import type { Strings } from "@/lib/i18n";
import type { LaneView } from "@/lib/lanes";
import styles from "./Lane.module.css";

interface Props {
  lane: LaneView;
  /** True while this lane's source is the one in the big browser view. */
  open: boolean;
  onOpen: () => void;
  /** Why a lane that never started did not run; shown instead of a bare "not in this check". */
  skippedWhy: string;
  t: Strings;
}

/** One lane of the War Room: a source group reading in parallel with the others. */
export function Lane({ lane, open, onOpen, skippedWhy, t }: Props) {
  const label = t.cam.lanes[lane.id];
  const status = t.cam.laneStatus[lane.status];
  const ticker = lane.status === "skipped" ? skippedWhy : (lane.ticker ?? t.cam.laneWaitingNote);
  const showLive = lane.status === "running" && lane.liveUrl !== null && !open;

  return (
    <li className={`${styles.lane} ${open ? styles.open : ""}`} data-status={lane.status}>
      <button type="button" className={styles.button} aria-pressed={open} onClick={onOpen}>
        <span className={styles.top}>
          <span className={styles.name}>{label}</span>
          <span className={`mono ${styles.status}`}>
            <i className={`${styles.dot} ${styles[lane.status]}`} aria-hidden="true" />
            {status}
          </span>
        </span>
        <span className={styles.ticker}>{ticker}</span>
        <span className={`mono ${styles.count}`}>{t.cam.laneFindings(lane.findings)}</span>
        <span className={styles.expand}>{open ? t.cam.laneOpen : t.cam.laneExpand}</span>
      </button>
      {showLive && (
        <iframe
          className={styles.live}
          src={lane.liveUrl ?? undefined}
          title={t.cam.liveViewTitle(label)}
          sandbox="allow-scripts allow-same-origin"
          loading="lazy"
          referrerPolicy="no-referrer"
          tabIndex={-1}
        />
      )}
    </li>
  );
}
