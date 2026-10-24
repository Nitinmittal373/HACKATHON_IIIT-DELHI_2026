"use client";

import { ArrowUpRight, Bell, BellRing, Check, Columns2, Download, Link2, MessageSquareText, RotateCw, ScrollText } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { use, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  AskPanel, ChecksList, ComplaintPanel, DeliveryTimeline, EvidenceTable, Insights, KpiTiles, NextSteps,
} from "@/components/report-parts";
import { BandBadge, PillarBars, ScoreCalculation, ScoreRing } from "@/components/score";
import { Button } from "@/components/ui/button";
import { Badge, Card, ErrorNote, Eyebrow, Skeleton } from "@/components/ui/primitives";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import type { Report } from "@/lib/types";
import { safeHref, shortDate, titleCase } from "@/lib/utils";
import { useAsync } from "@/lib/use-async";

const FamilyTree = dynamic(() => import("@/components/family-tree").then((m) => m.FamilyTree), {
  ssr: false,
  loading: () => <Skeleton className="h-[360px]" />,
});

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: r, error, loading } = useAsync(() => api.report(id), [id]);
  const [tab, setTab] = useState("overview");

  if (error) return <div className="p-7"><ErrorNote>{error}</ErrorNote></div>;
  if (loading || !r) return <LoadingDossier />;

  return (
    <>
      <TopBar r={r} />
      <main className="print-full mx-auto max-w-[1320px] px-5 py-6 sm:px-7">
        <Header r={r} />
        <Tabs value={tab} onValueChange={setTab} className="mt-6">
          <TabsList aria-label="Report sections">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="evidence">Evidence ({r.evidence.length})</TabsTrigger>
            <TabsTrigger value="company">Company & family tree</TabsTrigger>
            <TabsTrigger value="ask">Ask NeevCheck</TabsTrigger>
            <TabsTrigger value="complaint">Complaint draft</TabsTrigger>
          </TabsList>
          <div className="mt-5 flex flex-wrap items-start gap-5">
            <div className="min-w-0 flex-[999_1_560px]">
              <TabsContent value="overview" className="mt-0 flex flex-col gap-4">
                <KpiTiles report={r} />
                <DeliveryTimeline report={r} />
                <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] items-start gap-4">
                  <Insights report={r} />
                  <ChecksList report={r} />
                </div>
                <NextSteps report={r} />
              </TabsContent>
              <TabsContent value="evidence" className="mt-0"><EvidenceTable report={r} /></TabsContent>
              <TabsContent value="company" className="mt-0"><CompanyTab r={r} /></TabsContent>
              <TabsContent value="ask" className="mt-0">
                <AskPanel
                  report={r}
                  onCite={(n) => {
                    setTab("evidence");
                    setTimeout(() => document.getElementById(`ev-${n}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 120);
                  }}
                />
              </TabsContent>
              <TabsContent value="complaint" className="mt-0"><ComplaintPanel report={r} /></TabsContent>
            </div>
            <ScoreRail r={r} onTab={setTab} />
          </div>
        </Tabs>
      </main>
    </>
  );
}

function TopBar({ r }: { r: Report }) {
  const [copied, setCopied] = useState(false);
  return (
    <PageHeader
      title={<nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm font-medium"><Link href="/reports" className="text-faint hover:text-fg">Reports</Link><span className="text-faint">/</span><span className="truncate">{titleCase(r.project_name) || r.query}</span></nav>}
      actions={
        <>
          <Badge tone="ok"><span className="size-1.5 rounded-full bg-[#4FC1A6]" aria-hidden />Checked {shortDate(r.created_at)} · {r.lanes.filter((l) => l.ok).length} of 5 sources</Badge>
          <Button asChild variant="outline" size="sm"><Link href={`/check?q=${encodeURIComponent(r.query)}`}><RotateCw /> Re-run</Link></Button>
          <Button variant="outline" size="sm" onClick={() => window.print()}><Download /> PDF</Button>
          <Button variant="outline" size="sm" onClick={() => { navigator.clipboard.writeText(window.location.href); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
            {copied ? <Check /> : <Link2 />} {copied ? "Link copied" : "Share"}
          </Button>
        </>
      }
    />
  );
}

function Header({ r }: { r: Report }) {
  const [watch, setWatch] = useState<"idle" | "busy" | "on" | string>("idle");
  async function startWatch() {
    setWatch("busy");
    try {
      await api.watch(r.id);
      setWatch("on");
    } catch (e) {
      setWatch((e as Error).message);
    }
  }
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-3xl font-extrabold tracking-tight">{titleCase(r.project_name) || r.query}</h1>
        <p className="mt-1.5 text-sm text-muted">
          Uttar Pradesh · Promoter <b className="text-fg">{r.promoter_name ?? "not identified"}</b>
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {r.rera_number && <Badge className="font-mono">{r.rera_number}</Badge>}
          {r.signals.cin && <Badge className="font-mono">CIN {r.signals.cin}</Badge>}
          {r.rera_url && (
            <a href={safeHref(r.rera_url)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 rounded-full border border-line-strong px-2.5 py-0.5 text-xs font-semibold text-accent hover:underline">
              UP-RERA page <ArrowUpRight className="size-3" aria-hidden />
            </a>
          )}
          <Badge tone="info">Formula v{r.score.version} · deterministic</Badge>
          {r.demo_replay && <Badge tone="warn">Replay of a saved run · dates show original retrieval</Badge>}
        </div>
      </div>
      <div className="no-print flex flex-col items-end gap-2">
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline"><Link href={`/compare?a=${r.id}`}><Columns2 /> Compare</Link></Button>
          <Button onClick={startWatch} disabled={watch === "busy" || watch === "on"}>
            {watch === "on" ? <BellRing /> : <Bell />} {watch === "on" ? "Watching daily" : watch === "busy" ? "Starting…" : "Watch this project"}
          </Button>
        </div>
        {!["idle", "busy", "on"].includes(watch) && <p className="max-w-sm text-right text-xs text-high-fg">{watch}</p>}
      </div>
    </div>
  );
}

function ScoreRail({ r, onTab }: { r: Report; onTab: (t: string) => void }) {
  const { t } = useLang();
  const s = r.score;
  return (
    <aside aria-label="NeevScore" className="flex w-full min-w-0 flex-[1_1_300px] flex-col gap-3.5 lg:max-w-[380px]">
      <Card className="p-5">
        <div className="flex items-center justify-between"><Eyebrow>NeevScore</Eyebrow><Badge tone="info" className="font-mono">v{s.version}</Badge></div>
        <div className="mt-3.5 flex items-center gap-4">
          <ScoreRing score={s.score} band={s.band} size={108} />
          <div>
            <BandBadge band={s.band} />
            <div className="mt-2 text-[13px] text-muted">{s.hard_stop ? "Hard stop applied" : "No hard stop"}</div>
            <div className="mt-0.5 text-[13px] text-muted">Confidence <b className="font-mono text-fg">{Math.round(s.confidence * 100)}%</b></div>
          </div>
        </div>
        <h3 className="mt-5 text-sm font-semibold">{t("report.why")}</h3>
        <ul className="mt-2 flex flex-col gap-2">
          {s.reasons.slice(0, 4).map((x) => (
            <li key={x.code} className="flex gap-2.5 text-[13px] leading-snug">
              <span className={`font-mono text-xs ${x.impact >= 70 ? "text-high-fg" : x.impact > 0 ? "text-warn-fg" : "text-faint"}`}>{x.code}</span>
              <span>{x.text}{x.status === "requires_review" && <span className="text-warn-fg"> · review</span>}</span>
            </li>
          ))}
        </ul>
        <div className="mt-5"><PillarBars score={s} /></div>
      </Card>
      <ScoreCalculation score={s} />
      <Card className="no-print flex flex-col gap-2 p-4">
        <Button variant="outline" className="justify-between" onClick={() => onTab("ask")}>Ask about this project <MessageSquareText /></Button>
        <Button variant="outline" className="justify-between" onClick={() => onTab("complaint")}>Draft UP-RERA complaint <ScrollText /></Button>
        <p className="mt-1 text-[11px] leading-relaxed text-faint">{t("disclaimer")}</p>
      </Card>
    </aside>
  );
}

function CompanyTab({ r }: { r: Report }) {
  const s = r.signals;
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3">
        <Card className="p-4"><Eyebrow>Company</Eyebrow><div className="mt-2 font-semibold">{r.promoter_name ?? "Not identified"}</div>{s.cin && <div className="mt-1 font-mono text-xs text-muted">CIN {s.cin}</div>}</Card>
        <Card className="p-4"><Eyebrow>Status</Eyebrow><div className="mt-2 font-semibold">{s.company_status ?? "Not read"}</div></Card>
        <Card className="p-4"><Eyebrow>Directors</Eyebrow><div className="mt-2 text-2xl font-bold">{s.directors ?? "–"}</div></Card>
        <Card className="p-4"><Eyebrow>Open charges</Eyebrow><div className="mt-2 text-2xl font-bold">{s.open_charges ?? "–"}</div><div className="text-xs text-faint">A charge is a secured loan, not a default</div></Card>
      </div>
      <Card className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-[17px] font-semibold">Builder family tree</h2>
          <span className="text-xs text-faint">Solid: official record · Dashed: name match only, verify</span>
        </div>
        <div className="mt-4"><FamilyTree nodes={r.graph.nodes ?? []} edges={r.graph.edges ?? []} /></div>
        <p className="mt-3 text-xs text-faint">A shared name or director is a lead to check, not proof of wrongdoing.</p>
      </Card>
    </div>
  );
}

function LoadingDossier() {
  return (
    <main className="mx-auto max-w-[1320px] px-7 py-8" aria-busy>
      <Skeleton className="h-9 w-2/3" />
      <Skeleton className="mt-3 h-4 w-1/3" />
      <div className="mt-8 grid grid-cols-4 gap-3">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      <Skeleton className="mt-4 h-48" />
    </main>
  );
}
