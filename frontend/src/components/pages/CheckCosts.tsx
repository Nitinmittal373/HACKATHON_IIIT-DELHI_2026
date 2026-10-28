"use client";

import { useLang } from "@/lib/LangProvider";
import { useLimits } from "@/lib/useLimits";
import styles from "./pages.module.css";

/** What a check costs a visitor, from the live limits; the account's checks left, once signed in. */
export function CheckCosts() {
  const { t } = useLang();
  const copy = t.pages.check;
  const limits = useLimits();

  return (
    <section className={styles.section} aria-labelledby="costs-title">
      <h2 id="costs-title" className={styles.heading}>
        {copy.costTitle}
      </h2>
      <ul className={styles.list}>
        <li>{copy.costFree}</li>
        {limits && <li>{copy.costReuse(limits.reuse_report_days)}</li>}
        {limits?.require_signin && <li>{copy.costSignIn}</li>}
        {limits && <li>{copy.costPerDay(limits.checks_per_account_per_day)}</li>}
        {limits && <li>{copy.costRecheck(limits.recheck_min_days)}</li>}
        <li>{copy.costSearches}</li>
      </ul>
      {limits?.invited === false && <p className={styles.text}>{copy.costInvite}</p>}
      {limits && !limits.live_checks_open && <p className={styles.text}>{copy.costClosed}</p>}
      {limits?.checks_left_today != null && (
        <p className={styles.text}>
          <b>{copy.costLeft(limits.checks_left_today)}</b>
        </p>
      )}
    </section>
  );
}
