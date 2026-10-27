"use client";

import { useEffect, useId, useRef, useState } from "react";

import { saveToAccount } from "@/lib/accountReports";
import { useLang } from "@/lib/LangProvider";
import { readAnonIds, removeLocalReports, useAnonIds } from "@/lib/localReports";
import { forgetRecentChecks } from "@/lib/recentChecks";
import styles from "./AddBrowserReports.module.css";

/**
 * Right after sign-in, offers to add the reports made in this browser while signed out. They
 * move only if the visitor agrees; "Not now" leaves them here and asks again at the next
 * sign-in. Reports tagged with any account never appear in this count.
 */
export function AddBrowserReports() {
  const { t } = useLang();
  const anon = useAnonIds();
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [dismissed, setDismissed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const count = anon?.length ?? 0;
  const open = count > 0 && !dismissed;

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  async function add() {
    // Read now, not at render: only what is still anonymous at this moment is moved.
    const ids = readAnonIds();
    setSaving(true);
    setFailed(false);
    try {
      await saveToAccount(ids);
    } catch {
      setSaving(false);
      setFailed(true);
      return;
    }
    removeLocalReports(ids);
    forgetRecentChecks();
    setSaving(false);
  }

  const copy = t.account.addBrowser;
  return (
    <dialog
      ref={dialog}
      className={styles.dialog}
      aria-labelledby={titleId}
      onClose={() => setDismissed(true)}
    >
      {open && (
        <div className={styles.body}>
          <h2 id={titleId} className={styles.title}>
            {copy.title(count)}
          </h2>
          <p className={styles.lead}>{copy.lead}</p>
          {failed && (
            <p className={styles.problem} role="alert">
              {copy.failed}
            </p>
          )}
          <div className={styles.actions}>
            <button type="button" className="btn" disabled={saving} onClick={() => void add()}>
              {copy.add}
            </button>
            <button type="button" className="btn2" disabled={saving} onClick={() => setDismissed(true)}>
              {copy.notNow}
            </button>
          </div>
        </div>
      )}
    </dialog>
  );
}
