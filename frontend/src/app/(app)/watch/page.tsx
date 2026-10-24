"use client";

import { AlertTriangle, BellRing, Clock, FileWarning, Radar } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { BandBadge } from "@/components/score";
import { Badge, Card, EmptyState, ErrorNote, Eyebrow, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { shortDate, titleCase } from "@/lib/utils";
import { useAsync } from "@/lib/use-async";

const ALERT_TYPES = [
  { icon: AlertTriangle, tone: "text-high-fg bg-high-bg", h: "New court order names your builder", p: "A new NCLT or IBBI record mentions the promoter's exact name." },
  { icon: Clock, tone: "text-warn-fg bg-warn-bg", h: "Completion date moved", p: "The revised date on UP-RERA changed. Your NeevScore is recalculated." },
  { icon: FileWarning, tone: "text-info-fg bg-info-bg", h: "Progress report not filed", p: "The latest quarterly progress report is missing on UP-RERA." },
];

export default function WatchPage() {
  const reports = useAsync(() => api.reports());
  const alerts = useAsync(() => api.alerts());
  const health = useAsync(() => api.health());
  const watched = (reports.data ?? []).filter((r) => r.watching);
  return (
    <>
      <PageHeader title="Watch & alerts" sub="TinyFish Monitor rechecks your projects every morning" />
      <main className="mx-auto max-w-[1180px] px-5 py-7 sm:px-7">
        {health.data && !health.data.watch_ready && (
          <div className="mb-5 rounded-xl border border-warn-line bg-warn-soft px-4 py-3 text-sm text-warn-fg">
            Watch mode needs a public address for alerts. Set <code className="font-mono">PUBLIC_BASE_URL</code> in the backend <code className="font-mono">.env</code> (for example an ngrok https URL).
          </div>
        )}
        {(reports.error || alerts.error) && <ErrorNote>{reports.error || alerts.error}</ErrorNote>}
        <div className="flex flex-wrap items-start gap-5">
          <section aria-label="Watched projects" className="flex min-w-0 flex-[999_1_560px] flex-col gap-3.5">
            <h2 className="text-base font-semibold">Watched projects</h2>
            {reports.loading ? <Skeleton className="h-24" /> : watched.length ? watched.map((r) => (
              <Card key={r.id} className="flex flex-wrap items-center gap-5 p-5 transition-colors hover:border-line-strong">
                <div className="flex size-16 items-center justify-center rounded-2xl bg-surface-2 text-xl font-extrabold">{r.band === "Not enough data" ? "–" : r.score}</div>
                <div className="min-w-0 flex-[1_1_220px]">
                  <Link href={`/reports/${r.id}`} className="font-semibold hover:underline">{titleCase(r.project_name) || r.query}</Link>
                  <div className="mt-1 flex items-center gap-2 text-xs text-faint">{r.promoter_name} <BandBadge band={r.band} /></div>
                </div>
                <div className="text-[13px]"><Eyebrow>Next check</Eyebrow><div className="mt-1 font-mono">Daily · 06:00</div></div>
                <Badge tone="ok"><span className="size-1.5 animate-pulse rounded-full bg-[#4FC1A6]" />Watching</Badge>
              </Card>
            )) : (
              <EmptyState icon={<Radar />} title="Nothing watched yet">
                Open any report and press <b>Watch this project</b>.
              </EmptyState>
            )}

            <h2 className="mt-4 text-base font-semibold">Alerts received</h2>
            {alerts.loading ? <Skeleton className="h-24" /> : alerts.data?.length ? (
              <Card className="divide-y divide-line">
                {alerts.data.map((a) => (
                  <div key={a.id} className="flex gap-4 px-5 py-4">
                    <BellRing className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium">Change detected {a.report_id && <Link href={`/reports/${a.report_id}`} className="text-accent hover:underline">· open report</Link>}</div>
                      <pre className="mt-1 max-h-24 overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-faint">{JSON.stringify(a.payload, null, 1).slice(0, 600)}</pre>
                    </div>
                    <span className="shrink-0 text-xs text-faint">{shortDate(a.received_at)}</span>
                  </div>
                ))}
              </Card>
            ) : (
              <Card className="p-5 text-sm text-muted">No alerts yet. When a watched record changes, it shows up here.</Card>
            )}
          </section>

          <aside className="flex w-full min-w-0 flex-[1_1_320px] flex-col gap-3.5 lg:max-w-[380px]">
            <Card className="p-5">
              <h2 className="text-base font-semibold">What Watch mode looks for</h2>
              <div className="mt-4 flex flex-col gap-4">
                {ALERT_TYPES.map(({ icon: Icon, tone, h, p }) => (
                  <div key={h} className="flex gap-3">
                    <span className={`flex size-9 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon className="size-4" aria-hidden /></span>
                    <div><div className="text-sm font-semibold">{h}</div><p className="mt-0.5 text-[13px] text-muted">{p}</p></div>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5 text-[13px] leading-relaxed text-muted">
              <Eyebrow>How it works</Eyebrow>
              <p className="mt-2">A TinyFish Monitor rereads the UP-RERA page every morning and searches for new court orders and news. When something changes it calls our webhook, which is protected by a shared secret.</p>
              <p className="mt-2">We store only your project list.</p>
            </Card>
          </aside>
        </div>
      </main>
    </>
  );
}
