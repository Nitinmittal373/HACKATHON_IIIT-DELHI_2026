"use client";

import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { SearchBar } from "@/components/SearchBar";
import { Skeleton } from "@/components/Skeleton";
import { CompareBar } from "@/components/reports/CompareBar";
import { ReportCard } from "@/components/reports/ReportCard";
import { listChecks } from "@/lib/api";
import { AccountReports } from "@/components/reports/AccountReports";
import { useAccount } from "@/lib/account";
import { addToCompare, forgetChecks, removeFromCompare, useCompareTray, useHistory } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { CheckSummary } from "@/lib/types";
import styles from "./MyReports.module.css";

type Loaded = { status: "loading" } | { status: "ready"; checks: CheckSummary[] } | { status: "failed" };

// While a check is running its card refreshes, so "Running" turns into a score by itself.
const REFRESH_WHILE_RUNNING_MS = 10_000;
const MAX_COMPARED = 3;

/** Signed in: the account's saved reports. Otherwise the checks kept in this browser. */
export function MyReports() {
  const account = useAccount();
  return account.status === "in" ? <AccountReports /> : <BrowserReports />;
}

function BrowserReports() {
  const { t } = useLang();
  const ids = useHistory();
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });
  const [pruned, setPruned] = useState(0);
  const picked = useCompareTray() ?? [];
  const [attempt, setAttempt] = useState(0);
  const key = ids?.join(",") ?? "";

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function load() {
      const wanted = key.split(",");
      try {
        const checks = await listChecks(wanted);
        if (cancelled) return;
        // Checks the server no longer has (for example after its database was reset) cannot open.
        const missing = wanted.filter((id) => !checks.some((check) => check.id === id));
        if (missing.length > 0) {
          setPruned((count) => count + missing.length);
          forgetChecks(missing);
        }
        setLoaded({ status: "ready", checks });
        if (checks.some((check) => check.status === "queued" || check.status === "running")) {
          timer = setTimeout(() => void load(), REFRESH_WHILE_RUNNING_MS);
        }
      } catch {
        if (!cancelled) setLoaded({ status: "failed" });
      }
    }

    void load();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [key, attempt]);

  function togglePicked(id: string) {
    if (picked.includes(id)) removeFromCompare([id]);
    else if (picked.length < MAX_COMPARED) addToCompare(id);
  }

  function remove(id: string) {
    removeFromCompare([id]);
    forgetChecks([id]);
  }

  const header = (
    <>
      <h1 className="h2 pageTitle">{t.reports.title}</h1>
      <p className="pageLead">{t.reports.lead}</p>
      {pruned > 0 && <p className={styles.note}>{t.reports.pruned(pruned)}</p>}
    </>
  );

  if (ids !== null && ids.length === 0) {
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

  if (ids === null || loaded.status === "loading") {
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

  // Newest first, as saved; a card disappears at once when it is removed.
  const byId = new Map(loaded.checks.map((check) => [check.id, check]));
  const shown = ids.flatMap((id) => byId.get(id) ?? []);

  return (
    <>
      {header}
      <ul className={styles.list}>
        {shown.map((check) => (
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
