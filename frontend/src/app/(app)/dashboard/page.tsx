"use client";

import { ArrowRight, Bell, FolderSearch, Plus, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ProjectPhoto } from "@/components/illustration";
import { PageHeader } from "@/components/page-header";
import { BandBadge, ScoreRing } from "@/components/score";
import { Button } from "@/components/ui/button";
import { Badge, Card, EmptyState, ErrorNote, Eyebrow, Input, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import type { Alert, Report, ReportSummary } from "@/lib/types";
import { shortDate, titleCase } from "@/lib/utils";
import { useAsync } from "@/lib/use-async";

export default function DashboardPage() {
  const { t } = useLang();
  const router = useRouter();
  const [q, setQ] = useState("");
  const list = useAsync(() => api.reports());
  const alerts = useAsync(() => api.alerts().catch(() => [] as Alert[]));
  const latestId = list.data?.[0]?.id;
  const latest = useAsync(() => (latestId ? api.report(latestId) : Promise.resolve(null)), [latestId]);

  const reports = list.data ?? [];
  const high = reports.filter((r) => r.band === "High risk").length;
  const watching = reports.filter((r) => r.watching).length;

  return (
    <>
      <PageHeader
        title={t("app.projects")}
        sub={new Date().toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" })}
        actions={
          <form
            onSubmit={(e) => { e.preventDefault(); if (q.trim().length >= 3) router.push(`/check?q=${encodeURIComponent(q.trim())}`); }}
            className="flex h-10 w-[min(420px,100%)] items-center gap-2 rounded-xl border border-line bg-surface-3 px-3"
          >
            <Search className="size-4 text-faint" aria-hidden />
            <label htmlFor="dash-q" className="sr-only">Check a project</label>
            <Input id="dash-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Check a project, UP-RERA number or builder" className="text-sm" />
          </form>
        }
      />
      <main className="mx-auto max-w-[1180px] px-5 py-7 sm:px-7">
        {list.error && <ErrorNote>{list.error}</ErrorNote>}

        <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3.5">
          <Kpi label="Projects checked" value={list.loading ? null : String(reports.length)} note="Saved reports" />
          <Kpi label="High risk" value={list.loading ? null : String(high)} note={high ? "Needs attention" : "None flagged"} tone={high ? "high" : undefined} />
          <Kpi label="Watching" value={list.loading ? null : String(watching)} note="Rechecked every morning" />
          <Kpi label="Alerts received" value={alerts.loading ? null : String(alerts.data?.length ?? 0)} note="From TinyFish Monitor" />
        </div>

        {list.loading ? (
          <Skeleton className="mt-7 h-72" />
        ) : !reports.length ? (
          <div className="mt-7">
            <EmptyState icon={<FolderSearch />} title="No projects checked yet">
              Run your first check. Five agents read the public records and build a report you can verify.
              <div className="mt-5"><Button asChild><Link href="/check"><Plus /> {t("app.newcheck")}</Link></Button></div>
            </EmptyState>
          </div>
        ) : (
          latest.data && <ProjectRow r={latest.data} />
        )}

        {reports.length > 0 && (
          <div className="mt-7 grid grid-cols-1 gap-4 xl:grid-cols-[1fr_340px]">
            <Card className="overflow-x-auto">
              <div className="flex items-center justify-between px-5 pt-5">
                <h2 className="text-base font-semibold">All checks</h2>
                <Link href="/reports" className="text-sm font-semibold text-accent hover:underline">View all</Link>
              </div>
              <table className="mt-3 w-full min-w-[560px] text-sm">
                <tbody>
                  {reports.slice(0, 6).map((r) => <Row key={r.id} r={r} />)}
                </tbody>
              </table>
            </Card>
            <section aria-label="Alerts" className="flex flex-col gap-3">
              <h2 className="flex items-center gap-2 text-base font-semibold"><Sparkles className="size-4 text-accent" aria-hidden /> Latest alerts</h2>
              {alerts.data?.length ? (
                alerts.data.slice(0, 4).map((a) => (
                  <Card key={a.id} className="p-4 text-sm">
                    <Eyebrow>{shortDate(a.received_at)}</Eyebrow>
                    <p className="mt-1.5 line-clamp-3 text-fg-2">{summarizeAlert(a)}</p>
                  </Card>
                ))
              ) : (
                <Card className="p-4 text-sm text-muted">
                  <Bell className="mb-2 size-5 text-faint" aria-hidden />
                  No alerts yet. Turn on Watch mode from a report and we&apos;ll tell you when a record changes.
                </Card>
              )}
            </section>
          </div>
        )}
      </main>
    </>
  );
}

function summarizeAlert(a: Alert): string {
  const p = a.payload as Record<string, unknown>;
  const text = (p.summary ?? p.message ?? p.change ?? p.event ?? "") as string;
  return text ? String(text) : "A watched record changed. Open the report to see what moved.";
}

function Kpi({ label, value, note, tone }: { label: string; value: string | null; note: string; tone?: "high" }) {
  return (
    <Card className="p-4">
      <Eyebrow>{label}</Eyebrow>
      {value === null ? <Skeleton className="mt-3 h-8 w-16" /> : (
        <div className={`mt-2 text-3xl font-extrabold tracking-tight ${tone === "high" ? "text-high-fg" : ""}`}>{value}</div>
      )}
      <div className="mt-1 text-xs text-muted">{note}</div>
    </Card>
  );
}

function Row({ r }: { r: ReportSummary }) {
  return (
    <tr className="border-t border-line transition-colors hover:bg-surface-2">
      <td className="px-5 py-3">
        <Link href={`/reports/${r.id}`} className="font-medium hover:underline">{titleCase(r.project_name) || r.query}</Link>
        <div className="text-xs text-faint">{r.promoter_name ?? "Promoter not identified"}</div>
      </td>
      <td className="px-3 py-3 font-mono tabular">{r.band === "Not enough data" ? "–" : r.score}</td>
      <td className="px-3 py-3"><BandBadge band={r.band} /></td>
      <td className="px-3 py-3 text-xs text-faint">{shortDate(r.created_at)}</td>
      <td className="px-5 py-3 text-right">{r.watching && <Badge tone="ok">Watching</Badge>}</td>
    </tr>
  );
}

function ProjectRow({ r }: { r: Report }) {
  const s = r.signals;
  const groups = [
    { h: "Delivery", rows: [["Date extensions", s.extensions_count], ["Months late", s.delay_months]] },
    { h: "Legal", rows: [["Insolvency", s.promoter_in_cirp == null ? null : s.promoter_in_cirp ? (s.cirp_scope === "other_project" ? "Other project" : "Under CIRP") : "None found"], ["Official records", r.evidence.filter((e) => e.lane === "ibbi" && e.source_type === "official").length]] },
    { h: "Company", rows: [["Status", s.company_status], ["Open charges", s.open_charges]] },
    { h: "Evidence", rows: [["Sources linked", r.evidence.length], ["Confidence", `${Math.round(r.score.confidence * 100)}%`]] },
  ] as const;
  return (
    <section aria-label={r.project_name ?? r.query} className="mt-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <h2 className="text-xl font-bold tracking-tight">{titleCase(r.project_name) || r.query}</h2>
          {r.promoter_name && <Badge>{r.promoter_name}</Badge>}
          {r.demo_replay && <Badge tone="info">Saved run replay</Badge>}
        </div>
        <Link href={`/reports/${r.id}`} className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent hover:underline">
          Open dossier <ArrowRight className="size-4" aria-hidden />
        </Link>
      </div>
      <div className="mt-3.5 flex flex-wrap gap-3.5">
        <Card className="flex flex-[1_1_220px] flex-col items-center gap-2.5 p-5">
          <Eyebrow className="self-start">NeevScore</Eyebrow>
          <ScoreRing score={r.score.score} band={r.score.band} size={130} />
          <BandBadge band={r.score.band} />
          <div className="text-xs text-faint">Checked {shortDate(r.created_at)}</div>
        </Card>
        <ProjectPhoto src={r.photo_url} sourceUrl={r.rera_url} className="min-h-[240px] flex-[2_1_340px]" />
        <div className="grid flex-[2_1_360px] grid-cols-2 gap-3.5">
          {groups.map((g) => (
            <Card key={g.h} className="p-4 transition-colors hover:border-line-strong">
              <div className="text-sm font-semibold">{g.h}</div>
              <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-3 gap-y-2 text-[13px]">
                {g.rows.map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="text-muted">{k}</dt>
                    <dd className={`text-right font-mono ${v == null ? "text-faint" : ""}`}>{v == null ? "Not read" : String(v)}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
