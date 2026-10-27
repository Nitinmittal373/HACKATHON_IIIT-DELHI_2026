"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageMessage } from "@/components/PageMessage";
import { Skeleton } from "@/components/Skeleton";
import { AlertCard } from "@/components/sentinel/AlertCard";
import { SignInForAlerts } from "@/components/sentinel/SignInForAlerts";
import { useAccount } from "@/lib/account";
import { myAlerts } from "@/lib/accountReports";
import { useLang } from "@/lib/LangProvider";
import type { Alert } from "@/lib/types";
import styles from "@/app/(app)/alerts/alerts.module.css";

type Loaded = { status: "loading" } | { status: "ready"; alerts: Alert[] } | { status: "failed" };

/** The signed-in account's alerts. Without a sign-in there is nothing to show, only the reason to sign in. */
export function AccountAlerts() {
  const account = useAccount();
  const { t } = useLang();
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const signedIn = account.status === "in";

  useEffect(() => {
    if (!signedIn) return;
    let cancelled = false;
    myAlerts().then(
      (alerts) => !cancelled && setLoaded({ status: "ready", alerts }),
      () => !cancelled && setLoaded({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, [signedIn, attempt]);

  if (account.status === "loading") return <Skeleton height={120} style={{ marginTop: 28, maxWidth: 760 }} />;
  if (!signedIn) return <SignInForAlerts className={styles.signIn} />;
  if (loaded.status === "loading") return <Skeleton height={160} style={{ marginTop: 28, maxWidth: 760 }} />;
  if (loaded.status === "failed") {
    return (
      <PageMessage
        alert
        title={t.alerts.failedTitle}
        actions={
          <button type="button" className="btn" onClick={() => setAttempt((n) => n + 1)}>
            {t.common.tryAgain}
          </button>
        }
      >
        {t.alerts.failedBody}
      </PageMessage>
    );
  }
  if (loaded.alerts.length === 0) {
    return (
      <PageMessage
        title={t.alerts.empty}
        actions={
          <Link href="/#search" className="btn2">
            {t.nav.check}
          </Link>
        }
      />
    );
  }
  return (
    <ul className={styles.list}>
      {loaded.alerts.map((alert) => (
        <li key={alert.id}>
          <AlertCard
            alert={alert}
            onStopped={() =>
              setLoaded({ status: "ready", alerts: loaded.alerts.filter((a) => a.watch_id !== alert.watch_id) })
            }
          />
        </li>
      ))}
    </ul>
  );
}
