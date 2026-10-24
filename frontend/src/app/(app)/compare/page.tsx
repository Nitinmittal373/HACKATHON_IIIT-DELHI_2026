"use client";

import { Columns2 } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { BandBadge, ScoreRing } from "@/components/score";
import { Card, EmptyState, ErrorNote, Eyebrow, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Report } from "@/lib/types";
import { cn, titleCase } from "@/lib/utils";
import { useAsync } from "@/lib/use-async";

type Flag = "high" | "warn" | "ok" | "none";
const ROWS: { label: string; get: (r: Report) => [string, Flag] }[] = [
  { label: "NeevScore", get: (r) => [r.score.band === "Not enough data" ? "–" : `${r.score.score} · ${r.score.band}`, r.score.band === "High risk" ? "high" : r.score.band === "Low risk" ? "ok" : "warn"] },
  { label: "Confidence", get: (r) => [`${Math.round(r.score.confidence * 100)}%`, r.score.confidence < 0.8 ? "warn" : "ok"] },
  { label: "RERA registration", get: (r) => [r.signals.registration_status ?? "Not read", r.signals.registration_status == null ? "none" : /lapse|revok|expire|cancel/.test(r.signals.registration_status) ? "high" : "ok"] },
  { label: "Date extensions", get: (r) => [r.signals.extensions_count == null ? "Not read" : String(r.signals.extensions_count), r.signals.extensions_count == null ? "none" : r.signals.extensions_count ? "warn" : "ok"] },
  { label: "Months late", get: (r) => [r.signals.delay_months == null ? "Not read" : String(r.signals.delay_months), r.signals.delay_months == null ? "none" : r.signals.delay_months > 12 ? "warn" : "ok"] },
  { label: "Insolvency", get: (r) => { const s = r.signals; if (s.promoter_in_cirp == null) return ["Not read", "none"]; if (s.promoter_in_cirp) return [s.cirp_scope === "other_project" ? "Limited to another project" : "Under CIRP", s.cirp_scope === "other_project" ? "warn" : "high"]; if (s.insolvency_case_found) return ["NCLT case, stage unconfirmed", "warn"]; return [s.insolvency_reported_in_news ? "News only, unverified" : "None found", s.insolvency_reported_in_news ? "warn" : "ok"]; } },
  { label: "Company status", get: (r) => [r.signals.company_status ?? "Not read", r.signals.company_status == null ? "none" : /cirp|insolv|strike|liquid/i.test(r.signals.company_status) ? "high" : "ok"] },
  { label: "Land authority dues", get: (r) => [r.signals.authority_defaulter == null ? "Not read" : r.signals.authority_defaulter ? "Listed" : "None found", r.signals.authority_defaulter == null ? "none" : r.signals.authority_defaulter ? "high" : "ok"] },
  { label: "News stories", get: (r) => [r.signals.adverse_news_count == null ? "Not read" : String(r.signals.adverse_news_count), r.signals.adverse_news_count ? "warn" : r.signals.adverse_news_count == null ? "none" : "ok"] },
  { label: "Evidence links", get: (r) => [String(r.evidence.length), "none"] },
];
const DOT: Record<Flag, string> = { high: "bg-[#EF5A4C]", warn: "bg-[#F2B84B]", ok: "bg-[#4FC1A6]", none: "bg-line-strong" };

export default function ComparePage() {
  return <Suspense><Compare /></Suspense>;
}

function Compare() {
  const params = useSearchParams();
  const router = useRouter();
  const a = params.get("a") ?? "";
  const b = params.get("b") ?? "";
  const list = useAsync(() => api.reports());
  const ra = useAsync(() => (a ? api.report(a) : Promise.resolve(null)), [a]);
  const rb = useAsync(() => (b ? api.report(b) : Promise.resolve(null)), [b]);
  const set = (k: "a" | "b", v: string) => {
    const p = new URLSearchParams(params.toString());
    if (v) p.set(k, v); else p.delete(k);
    router.replace(`/compare?${p.toString()}`, { scroll: false });
  };
  const reports = list.data ?? [];
  return (
    <>
      <PageHeader title="Compare projects" sub="Same formula, same sources, so the comparison is fair" />
      <main className="mx-auto max-w-[1180px] px-5 py-7 sm:px-7">
        {list.error && <ErrorNote>{list.error}</ErrorNote>}
        {list.loading ? <Skeleton className="h-64" /> : reports.length < 2 ? (
          <EmptyState icon={<Columns2 />} title="Check at least two projects to compare them">
            <Link href="/check" className="font-semibold text-accent hover:underline">Run another check</Link>
          </EmptyState>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {(["a", "b"] as const).map((k) => {
                const r = k === "a" ? ra.data : rb.data;
                const val = k === "a" ? a : b;
                return (
                  <Card key={k} className="p-5">
                    <label htmlFor={`pick-${k}`}><Eyebrow>Project {k.toUpperCase()}</Eyebrow></label>
                    <select
                      id={`pick-${k}`} value={val} onChange={(e) => set(k, e.target.value)}
                      className="mt-2 h-11 w-full cursor-pointer rounded-xl border border-line-strong bg-surface-3 px-3 text-sm text-fg"
                    >
                      <option value="">Choose a checked project…</option>
                      {reports.map((x) => <option key={x.id} value={x.id}>{titleCase(x.project_name) || x.query} ({x.band === "Not enough data" ? "no score" : x.score})</option>)}
                    </select>
                    {r && (
                      <div className="mt-4 flex items-center gap-4">
                        <ScoreRing score={r.score.score} band={r.score.band} size={92} stroke={10} />
                        <div className="min-w-0">
                          <Link href={`/reports/${r.id}`} className="block truncate font-semibold hover:underline">{titleCase(r.project_name) || r.query}</Link>
                          <div className="truncate text-xs text-faint">{r.promoter_name}</div>
                          <BandBadge band={r.score.band} className="mt-2" />
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
            <Card className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="text-left font-mono text-[11px] uppercase tracking-wider text-faint">
                    <th className="w-1/3 px-5 py-3 font-medium">Signal</th><th className="px-5 py-3 font-medium">Project A</th><th className="px-5 py-3 font-medium">Project B</th>
                  </tr>
                </thead>
                <tbody>
                  {ROWS.map((row) => (
                    <tr key={row.label} className="border-t border-line hover:bg-surface-2">
                      <td className="px-5 py-3 text-muted">{row.label}</td>
                      {[ra.data, rb.data].map((r, i) => {
                        if (!r) return <td key={i} className="px-5 py-3 text-faint">—</td>;
                        const [v, f] = row.get(r);
                        return <td key={i} className="px-5 py-3"><span className="inline-flex items-center gap-2"><span className={cn("size-2 rounded-full", DOT[f])} aria-hidden />{v}</span></td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
            <p className="mt-3 text-xs text-faint">Red: red flag · Amber: warning or needs review · Green: nothing found in checked records · Grey: not read. Not a recommendation to buy or avoid any project.</p>
          </>
        )}
      </main>
    </>
  );
}
