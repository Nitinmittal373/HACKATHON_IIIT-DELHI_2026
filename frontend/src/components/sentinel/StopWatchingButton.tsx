"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { removeWatch } from "@/lib/api";
import { useLang } from "@/lib/LangProvider";
import styles from "./AlertCard.module.css";

/** Stops the watch an alert came from; its alerts go with it, so the list is reloaded. */
export function StopWatchingButton({ watchId, project }: { watchId: string; project: string }) {
  const { t } = useLang();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function stop() {
    setBusy(true);
    setFailed(false);
    try {
      await removeWatch(watchId);
      router.refresh();
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
