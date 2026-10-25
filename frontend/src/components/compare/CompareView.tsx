"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AddProject } from "@/components/compare/AddProject";
import { CompareCards } from "@/components/compare/CompareCards";
import { CompareTable } from "@/components/compare/CompareTable";
import { compareRows } from "@/components/compare/compareRows";
import { BestSummary } from "@/components/compare/BestSummary";
import { PageMessage } from "@/components/PageMessage";
import { Skeleton } from "@/components/Skeleton";
import { compareChecks } from "@/lib/api";
import { addToCompare, removeFromCompare, useCompareTray } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { Comparison } from "@/lib/types";

type Loaded = { status: "loading" } | { status: "ready"; comparison: Comparison } | { status: "failed" };

const MAX_COMPARED = 3;

/** The ids come from the address (shareable); without any, from the picks saved in this browser. */
export function CompareView({ fromUrl }: { fromUrl: string[] }) {
  const router = useRouter();
  const { lang, t } = useLang();
  const tray = useCompareTray();
  const ids = fromUrl.length > 0 ? fromUrl : [...(tray ?? [])].reverse();
  const key = ids.join(",");
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });

  useEffect(() => {
    if (key.split(",").filter(Boolean).length < 2) return;
    let cancelled = false;
    setLoaded({ status: "loading" });
    compareChecks(key.split(",")).then(
      (comparison) => !cancelled && setLoaded({ status: "ready", comparison }),
      () => !cancelled && setLoaded({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, [key]);

  function show(next: string[]) {
    router.replace(next.length > 0 ? `/compare?ids=${next.join(",")}` : "/compare", { scroll: false });
  }

  function remove(checkId: string) {
    removeFromCompare([checkId]);
    show(ids.filter((id) => id !== checkId));
  }

  function add(checkId: string) {
    addToCompare(checkId);
    show([...ids, checkId]);
  }

  const header = (
    <>
      <h1 className="h2 pageTitle">{t.compare.title}</h1>
      <p className="pageLead">{t.compare.lead}</p>
    </>
  );
  const adder = ids.length < MAX_COMPARED && <AddProject current={ids} onAdd={add} />;

  if (ids.length < 2) {
    return (
      <>
        {header}
        <PageMessage
          title={t.compare.pickTitle}
          actions={
            <Link href="/reports" className="btn">
              {t.compare.openReports}
            </Link>
          }
        >
          {t.compare.pickBody(ids.length)}
        </PageMessage>
        {adder}
      </>
    );
  }

  if (loaded.status === "failed") {
    return (
      <>
        {header}
        <PageMessage alert title={t.compare.failedTitle} actions={<Link href="/reports" className="btn">{t.compare.openReports}</Link>}>
          {t.compare.missing}
        </PageMessage>
      </>
    );
  }

  if (loaded.status === "loading") {
    return (
      <>
        {header}
        <div aria-busy="true" style={{ marginTop: 26 }}>
          <span className="sr" role="status">
            {t.compare.loading}
          </span>
          <Skeleton height={420} />
        </div>
      </>
    );
  }

  const { comparison } = loaded;
  const rows = compareRows(comparison, t, lang);
  return (
    <>
      {header}
      <BestSummary comparison={comparison} t={t} />
      <CompareTable projects={comparison.projects} rows={rows} onRemove={remove} t={t} />
      <CompareCards projects={comparison.projects} rows={rows} onRemove={remove} t={t} />
      {adder}
    </>
  );
}
