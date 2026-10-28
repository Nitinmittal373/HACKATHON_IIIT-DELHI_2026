"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AgentCam } from "@/components/cam/AgentCam";
import { PageMessage } from "@/components/PageMessage";
import { Skeleton } from "@/components/Skeleton";
import { ApiError, getCheck, wakeServer } from "@/lib/api";
import { describeApiError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import type { Check } from "@/lib/types";

type Loaded = { status: "loading" } | { status: "ready"; check: Check } | { status: "missing" } | { status: "failed"; error: unknown };

/**
 * Opens a check where it stands, so a refresh or a reopened tab picks up the run: the event
 * stream replays everything so far and then continues. A finished check goes to its report.
 * Fetched in the browser, so a sleeping server can take its minute to wake.
 */
export function ResumeCheck({ checkId }: { checkId: string }) {
  const router = useRouter();
  const { t } = useLang();
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      await wakeServer();
      try {
        const check = await getCheck(checkId);
        if (cancelled) return;
        if (check.status === "completed") router.replace(`/report/${checkId}`);
        else setLoaded({ status: "ready", check });
      } catch (error) {
        if (cancelled) return;
        const missing = error instanceof ApiError && error.status === 404;
        setLoaded(missing ? { status: "missing" } : { status: "failed", error });
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [checkId, attempt, router]);

  if (loaded.status === "missing") {
    return (
      <PageMessage title={t.errors.notFoundTitle} actions={<Link href="/check" className="btn">{t.hero.submit}</Link>}>
        {t.errors.notFoundBody}
      </PageMessage>
    );
  }
  if (loaded.status === "failed") {
    return (
      <PageMessage
        alert
        title={t.errors.somethingTitle}
        actions={
          <button type="button" className="btn" onClick={() => setAttempt((n) => n + 1)}>
            {t.common.tryAgain}
          </button>
        }
      >
        {describeApiError(loaded.error, t)}
      </PageMessage>
    );
  }
  if (loaded.status === "loading") {
    return (
      <div aria-busy="true">
        <Skeleton width={180} height={14} />
        <Skeleton width="55%" height={36} style={{ marginTop: 14 }} />
        <Skeleton height={520} style={{ marginTop: 22 }} />
      </div>
    );
  }
  const { check } = loaded;
  return (
    <AgentCam
      checkId={check.id}
      reraId={check.rera_id}
      detailsUrl={check.details_url}
    />
  );
}
