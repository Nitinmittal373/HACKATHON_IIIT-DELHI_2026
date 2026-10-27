"use client";

import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { SearchBar } from "@/components/SearchBar";
import { Skeleton } from "@/components/Skeleton";
import { CompareBar } from "@/components/reports/CompareBar";
import { ReportCard } from "@/components/reports/ReportCard";
import { accountReports, forgetFromAccount } from "@/lib/accountReports";
import { addToCompare, removeFromCompare, useCompareTray } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { CheckSummary } from "@/lib/types";
import styles from "./MyReports.module.css";

type Loaded = { status: "loading" } | { status: "ready"; checks: CheckSummary[] } | { status: "failed" };

const MAX_COMPARED = 3;

/** "My reports" for a signed-in visitor: the checks saved to their account, newest first. */
export function AccountReports() {
  const { t } = useLang();
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const picked = useCompareTray() ?? [];

  useEffect(() => {
    let cancelled = false;
    accountReports().then(
      (checks) => !cancelled && setLoaded({ status: "ready", checks }),
      () => !cancelled && setLoaded({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  function togglePicked(id: string) {
    if (picked.includes(id)) removeFromCompare([id]);
    else if (picked.length < MAX_COMPARED) addToCompare(id);
  }

  function remove(id: string) {
    removeFromCompare([id]);
    setLoaded((current) =>
      current.status === "ready" ? { status: "ready", checks: current.checks.filter((c) => c.id !== id) } : current,
    );
    void forgetFromAccount(id).catch(() => setAttempt((n) => n + 1));
  }

  const header = (
    <>
      <h1 className="h2 pageTitle">{t.reports.title}</h1>
      <p className="pageLead">{t.account.reportsNote}</p>
    </>
  );

  if (loaded.status === "failed") {
    return (
      <>
        {header}
        <PageMessage
          alert
          title={t.reports.loadFailed}
          actions={
            <button type="button" className="btn" onClick={() => setAttempt((n) => n + 1)}>
              {t.common.tryAgain}
            </button>
          }
        >
          {t.errors.unreachableBody}
        </PageMessage>
      </>
    );
  }

  if (loaded.status === "loading") {
    return (
      <>
        {header}
        <div className={styles.list} aria-busy="true">
          <span className="sr" role="status">
            {t.reports.loading}
          </span>
          {[0, 1, 2].map((row) => (
            <Skeleton key={row} height={128} />
          ))}
        </div>
      </>
    );
  }

  if (loaded.checks.length === 0) {
    return (
      <>
        {header}
        <PageMessage title={t.reports.emptyTitle}>
          <p>{t.reports.emptyBody}</p>
          <SearchBar label={t.hero.searchLabel} placeholder={t.hero.placeholder} submitLabel={t.hero.submit} />
        </PageMessage>
      </>
    );
  }

  return (
    <>
      {header}
      <ul className={styles.list}>
        {loaded.checks.map((check) => (
          <li key={check.id}>
            <ReportCard
              check={check}
              picked={picked.includes(check.id)}
              canPick={picked.length < MAX_COMPARED}
              onTogglePicked={() => togglePicked(check.id)}
              onRemove={() => remove(check.id)}
            />
          </li>
        ))}
      </ul>
      <CompareBar picked={picked} max={MAX_COMPARED} />
    </>
  );
}
