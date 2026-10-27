"use client";

import { useState } from "react";

import { stopWatching } from "@/lib/accountReports";
import { useLang } from "@/lib/LangProvider";
import styles from "./AlertCard.module.css";

interface Props {
  watchId: string;
  project: string;
  onStopped: () => void;
}

/** Stops the watch an alert came from; its alerts go with it, so the list drops them. */
export function StopWatchingButton({ watchId, project, onStopped }: Props) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function stop() {
    setBusy(true);
    setFailed(false);
    try {
      await stopWatching(watchId);
      onStopped();
    } catch {
      setFailed(true);
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className={`btn2 ${styles.stop}`}
        disabled={busy}
        aria-label={t.alerts.stopWatchingLabel(project)}
        onClick={() => void stop()}
      >
        {t.alerts.stopWatching}
      </button>
      {failed && (
        <p className={styles.stopFailed} role="alert">
          {t.alerts.stopFailed}
        </p>
      )}
    </>
  );
}
