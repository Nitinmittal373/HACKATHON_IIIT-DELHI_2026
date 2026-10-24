"use client";

import { ArrowUpRight, Check, Copy, Loader2, Send } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge, Card, ErrorNote, Eyebrow, Input } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import type { AskAnswer, EvidenceStatus, Report } from "@/lib/types";
import {
  LANE_LABEL, LANE_METHOD, OUTCOME_LABEL, OUTCOME_TONE, SOURCE_LABEL, STATUS_LABEL, STATUS_TONE,
  cn, domainOf, safeHref, shortDate, type Tone,
} from "@/lib/utils";

/* ---------------- data tiles ---------------- */
interface Tile { label: string; value: string; note: string; tone?: Tone; dashed?: boolean }

export function buildTiles(r: Report): Tile[] {
  const s = r.signals;
  const ev = r.evidence;
  const nclt = ev.filter((e) => e.lane === "ibbi" && e.source_type === "official").length;
  const insolvency: Tile =
    s.promoter_in_cirp == null
      ? { label: "Insolvency", value: "Not read", note: "Check unavailable", dashed: true }
      : s.promoter_in_cirp && s.cirp_scope === "other_project"
        ? { label: "Insolvency", value: "Other project", note: "Limited to another project · review", tone: "warn" }
        : s.promoter_in_cirp
          ? { label: "Insolvency", value: "Under CIRP", note: `${nclt} official record(s)`, tone: "high" }
          : s.insolvency_case_found
            ? { label: "Insolvency", value: "Case found", note: "Admission not confirmed · review", tone: "warn" }
          : s.insolvency_reported_in_news
            ? { label: "Insolvency", value: "News only", note: "No official match · review", tone: "warn" }
            : { label: "Insolvency", value: "None found", note: "In checked records", tone: "ok" };
  return [
    s.extensions_count == null
      ? { label: "Date extensions", value: "Not read", note: "UP-RERA", dashed: true }
      : { label: "Date extensions", value: String(s.extensions_count), note: s.force_majeure_extensions ? `${s.force_majeure_extensions} COVID-era, not counted` : "UP-RERA record", tone: s.extensions_count ? "warn" : "ok" },
    s.delay_months == null
      ? { label: "Months late", value: "Not read", note: "Lowers confidence", dashed: true }
      : { label: "Months late", value: String(s.delay_months), note: "Revised vs original date", tone: s.delay_months > 12 ? "warn" : "ok" },
    insolvency,
    { label: "Company status", value: s.company_status ?? "Not read", note: s.cin ? `CIN ${s.cin}` : "Company registry", tone: s.company_status && /cirp|insolv|strike|liquid/i.test(s.company_status) ? "high" : undefined, dashed: !s.company_status },
    { label: "Open charges", value: s.open_charges == null ? "Not read" : String(s.open_charges), note: "Secured loans, not default", dashed: s.open_charges == null },
    { label: "Directors", value: s.directors == null ? "Not read" : String(s.directors), note: "Company registry", dashed: s.directors == null },
    s.authority_defaulter == null
      ? { label: "Land authority", value: "Not read", note: "Noida · GNIDA · YEIDA", dashed: true }
      : { label: "Land authority", value: s.authority_defaulter ? "Dues listed" : "None found", note: s.authority_defaulter ? "Attributable record" : "Name must match", tone: s.authority_defaulter ? "high" : "ok" },
    { label: "News stories", value: s.adverse_news_count == null ? "Not read" : String(s.adverse_news_count), note: "Distinct · marked review", dashed: s.adverse_news_count == null },
  ];
}

const TILE_TEXT: Record<Tone, string> = { high: "text-high-fg", warn: "text-warn-fg", ok: "text-ok-fg", info: "text-info-fg", neutral: "text-fg" };

export function KpiTiles({ report }: { report: Report }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(165px,1fr))] gap-3">
      {buildTiles(report).map((t) => (
        <Card
          key={t.label}
          className={cn("p-4 transition-all hover:-translate-y-0.5 hover:border-line-strong", t.dashed && "border-dashed", t.tone === "high" && "border-high-line")}
        >
          <Eyebrow>{t.label}</Eyebrow>
          <div className={cn("mt-2 font-extrabold leading-tight tracking-tight", t.value.length > 9 ? "text-xl" : "text-2xl", t.dashed ? "text-faint" : TILE_TEXT[t.tone ?? "neutral"])}>{t.value}</div>
          <div className="mt-1 truncate text-xs text-faint">{t.note}</div>
        </Card>
      ))}
    </div>
  );
}

/* ---------------- delivery timeline ---------------- */
export function DeliveryTimeline({ report }: { report: Report }) {
  const s = report.signals;
  const start = s.promised_completion ? new Date(s.promised_completion) : null;
  const end = s.revised_completion ? new Date(s.revised_completion) : null;
  const ok = start && end && !Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime());
  const today = new Date();
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-[17px] font-semibold">Delivery timeline</h2>
        <div className="flex gap-4 text-xs text-muted">
          <span className="flex items-center gap-1.5"><span className="size-3 rounded-sm bg-plan" />Original plan</span>
          <span className="flex items-center gap-1.5"><span className="size-3 rounded-sm bg-[#F2B84B]" />Extended</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-0.5 bg-accent" />Today</span>
        </div>
      </div>
      {ok ? (
        (() => {
          const t0 = new Date(start!.getFullYear() - 3, start!.getMonth()).getTime();
          const t1 = Math.max(end!.getTime(), today.getTime()) + 1000 * 3600 * 24 * 120;
          const pos = (d: Date) => ((d.getTime() - t0) / (t1 - t0)) * 100;
          return (
            <div className="mt-6">
              <div className="relative h-24">
                <div className="absolute inset-x-0 top-2 h-4 rounded-md bg-track" />
                <div className="absolute top-2 h-4 rounded-md bg-plan" style={{ left: 0, width: `${pos(start!)}%` }} />
                <div className="absolute top-9 h-4 rounded-md bg-[#F2B84B]" style={{ left: `${pos(start!)}%`, width: `${Math.max(1, pos(end!) - pos(start!))}%` }} />
                <div className="absolute top-0 h-16 w-0.5 bg-accent" style={{ left: `${pos(today)}%` }} aria-hidden />
                <div className="absolute top-[68px] font-mono text-[11px] text-faint" style={{ left: `${pos(start!)}%`, transform: "translateX(-50%)" }}>Promised {shortDate(s.promised_completion!)}</div>
                <div className="absolute top-[84px] font-mono text-[11px] text-faint" style={{ left: `${pos(end!)}%`, transform: "translateX(-60%)" }}>Revised {shortDate(s.revised_completion!)}</div>
              </div>
              <p className="mt-3 text-sm text-muted">
                {s.delay_months ? `${s.delay_months} months after the original date` : "No change between the dates"}
                {s.extensions_count ? ` · ${s.extensions_count} extension(s) on record` : ""}.
              </p>
            </div>
          );
        })()
      ) : (
        <div className="mt-5 rounded-xl border border-dashed border-line-strong bg-bg-2 p-5 text-sm text-muted">
          The completion dates could not be read from UP-RERA in this run
          {s.extensions_count ? `, but the record shows ${s.extensions_count} extension(s)` : ""}. We treat this as a gap, not as on time.
        </div>
      )}
    </Card>
  );
}

/* ---------------- insights from reason codes ---------------- */
const SIGNAL_LABEL: Record<string, string> = {
  registration_status: "registration status",
  delay_months: "months of delay",
  qprs_missed_last4: "missed progress reports",
  promoter_in_cirp: "insolvency records",
  company_or_director_struck_off: "company status",
  authority_defaulter: "land-authority dues",
  adverse_news_count: "news",
};

export function Insights({ report }: { report: Report }) {
  const items = report.score.reasons.filter((r) => r.impact > 0 || r.status === "requires_review").slice(0, 3);
  const gap = report.score.signals_missing;
  return (
    <section aria-label="Insights" className="flex flex-col gap-3">
      <h2 className="text-[17px] font-semibold">Insights</h2>
      {items.map((r) => {
        const critical = r.code === "R06" || r.code === "R01";   // only verified hard stops are "critical"
        return (
          <div
            key={r.code}
            className={cn(
              "rounded-2xl p-4",
              critical ? "bg-[#3A1714] text-[#FFE4DF]" : r.status === "requires_review" ? "border border-warn-line bg-warn-soft" : "border border-line bg-surface",
            )}
          >
            <div className={cn("font-mono text-[11px] tracking-[0.08em]", critical ? "text-[#FF9C90]" : "text-warn-fg")}>
              {critical ? "CRITICAL" : r.status === "requires_review" ? "REVIEW" : "WARNING"} · {r.code}
            </div>
            <div className="mt-1.5 font-medium leading-snug">{r.text}</div>
          </div>
        );
      })}
      {gap.length > 0 && (
        <div className="rounded-2xl border border-line bg-surface p-4">
          <div className="font-mono text-[11px] tracking-[0.08em] text-faint">GAP · R12</div>
          <div className="mt-1.5 font-medium leading-snug">
            Not read: {gap.map((g) => SIGNAL_LABEL[g] ?? g.replace(/_/g, " ")).join(", ")}. We don&apos;t count these as clean.
          </div>
        </div>
      )}
      {items.length === 0 && gap.length === 0 && (
        <div className="rounded-2xl border border-ok-line bg-ok-bg p-4 text-ok-fg">No red flags in the records checked. That is not a guarantee.</div>
      )}
    </section>
  );
}

/* ---------------- what we checked (including what we did not find) ---------------- */
export function ChecksList({ report }: { report: Report }) {
  const { t } = useLang();
  return (
    <Card className="p-5">
      <h2 className="text-[17px] font-semibold">{t("report.checked")}</h2>
      <ul className="mt-2 divide-y divide-line text-sm">
        {report.checks.map((c, i) => (
          <li key={i} className="py-3">
            <div className="flex items-start justify-between gap-3">
              <span className="min-w-0">{c.what}</span>
              <span className="shrink-0 pt-0.5 font-mono text-[11px] uppercase text-faint">{LANE_METHOD[c.lane]}</span>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <Badge tone={OUTCOME_TONE[c.outcome]}>{OUTCOME_LABEL[c.outcome]}</Badge>
              {c.detail && <span className="text-xs text-faint">{c.detail}</span>}
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function NextSteps({ report }: { report: Report }) {
  const { t } = useLang();
  const s = report.signals;
  const steps = [
    { h: "Not booked yet?", p: "Hold the booking amount until you have read every record marked “requires review”." },
    s.promoter_in_cirp
      ? { h: "Already a buyer?", p: "Homebuyers can file a claim with the insolvency professional. Check the public announcement for the deadline." }
      : { h: "Already a buyer?", p: "Turn on Watch mode. We recheck every morning and tell you when the record changes." },
    { h: "Get advice", p: "Share this report with a RERA lawyer. Every fact links to its source and retrieval date." },
  ];
  return (
    <section aria-label={t("report.next")} className="rounded-2xl border border-line-strong bg-bg-2 p-5">
      <h2 className="text-[17px] font-semibold">{t("report.next")}</h2>
      <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
        {steps.map((x, i) => (
          <div key={x.h} className="flex gap-3">
            <span className="font-mono font-semibold text-accent">{i + 1}</span>
            <div>
              <div className="font-semibold">{x.h}</div>
              <p className="mt-1 text-sm leading-relaxed text-muted">{x.p}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------- evidence ledger ---------------- */
export function EvidenceTable({ report }: { report: Report }) {
  const [filter, setFilter] = useState<EvidenceStatus | "all">("all");
  const rows = useMemo(() => report.evidence.filter((e) => filter === "all" || e.status === filter), [report, filter]);
  const counts = (s: EvidenceStatus) => report.evidence.filter((e) => e.status === s).length;
  return (
    <div className="flex flex-col gap-4">
      <div className="no-print flex flex-wrap gap-2" role="group" aria-label="Filter evidence">
        {(["all", "verified", "partially_verified", "requires_review"] as const).map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={cn(
              "cursor-pointer rounded-full border px-3 py-1.5 text-[13px] font-medium transition-colors",
              filter === f ? "border-fg bg-fg text-bg" : "border-line-strong text-muted hover:text-fg",
            )}
          >
            {f === "all" ? `All ${report.evidence.length}` : `${STATUS_LABEL[f]} ${counts(f)}`}
          </button>
        ))}
      </div>
      <Card className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-sm">
          <thead>
            <tr className="text-left font-mono text-[11px] uppercase tracking-wider text-faint">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Claim</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Retrieved</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.n} id={`ev-${e.n}`} className="border-t border-line align-top transition-colors hover:bg-surface-2">
                <td className="px-4 py-3 font-mono text-faint">{e.n}</td>
                <td className="px-4 py-3">
                  {e.claim}
                  {e.snippet && <details className="mt-1 text-xs text-faint"><summary className="cursor-pointer">Extract</summary><p className="mt-1 whitespace-pre-wrap break-words">{e.snippet}</p></details>}
                </td>
                <td className="px-4 py-3"><Badge tone={STATUS_TONE[e.status]}>{STATUS_LABEL[e.status]}</Badge></td>
                <td className="px-4 py-3">
                  <a href={safeHref(e.source_url)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-medium text-accent hover:underline">
                    {domainOf(e.source_url)} <ArrowUpRight className="size-3.5" aria-hidden />
                  </a>
                  <div className="text-xs text-faint">{SOURCE_LABEL[e.source_type]} · {LANE_LABEL[e.lane]}</div>
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-faint">{shortDate(e.fetched_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

/* ---------------- grounded Q&A ---------------- */
const SUGGESTED = ["Is my builder in insolvency?", "Has the project been delayed?", "Why this score?", "What should I do next?"];

export function AskPanel({ report, onCite }: { report: Report; onCite?: (n: number) => void }) {
  const [q, setQ] = useState("");
  const [log, setLog] = useState<{ q: string; a?: AskAnswer; err?: string }[]>([]);
  const [busy, setBusy] = useState(false);
  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setBusy(true);
    setQ("");
    setLog((l) => [...l, { q: question }]);
    try {
      const a = await api.ask(report.id, question);
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, a } : x)));
    } catch (e) {
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, err: (e as Error).message } : x)));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-[17px] font-semibold">Ask about this project</h2>
        <span className="text-xs text-faint">Answers are built only from the evidence in this report, with citations</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {SUGGESTED.map((s) => (
          <button key={s} type="button" onClick={() => ask(s)} className="cursor-pointer rounded-full border border-line-strong px-3.5 py-2 text-sm transition-colors hover:border-accent">
            {s}
          </button>
        ))}
      </div>
      <div className="mt-5 flex flex-col gap-3" aria-live="polite">
        {log.map((m, i) => (
          <div key={i} className="flex flex-col gap-3">
            <div className="max-w-[80%] self-end rounded-2xl rounded-br-sm bg-brand px-4 py-2.5 text-[#FFF8F0]">{m.q}</div>
            <div className="max-w-[90%] self-start rounded-2xl rounded-bl-sm border border-line bg-surface-2 px-4 py-3 leading-relaxed">
              {m.err ? <span className="text-high-fg">{m.err}</span> : m.a ? (
                <>
                  {m.a.answer}{" "}
                  {m.a.citations.map((n) => (
                    <button key={n} type="button" onClick={() => onCite?.(n)} aria-label={`Show evidence ${n}`} className="cursor-pointer font-mono text-xs text-accent hover:underline">[{n}]</button>
                  ))}
                </>
              ) : <Loader2 className="size-4 animate-spin text-faint" aria-label="Thinking" />}
            </div>
          </div>
        ))}
      </div>
      <form
        className="mt-5 flex items-center gap-2 rounded-xl border border-line-strong bg-surface-3 py-1.5 pl-4 pr-1.5"
        onSubmit={(e) => { e.preventDefault(); ask(q); }}
      >
        <label htmlFor="ask" className="sr-only">Ask a question about this project</label>
        <Input id="ask" value={q} onChange={(e) => setQ(e.target.value)} maxLength={300} placeholder="Ask anything about this project" className="h-10 text-[15px]" />
        <Button type="submit" size="icon" aria-label="Send question" disabled={busy}><Send /></Button>
      </form>
    </Card>
  );
}

/* ---------------- complaint draft ---------------- */
export function ComplaintPanel({ report }: { report: Report }) {
  const [text, setText] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  async function load() {
    try {
      setErr(null);
      setText((await api.complaint(report.id)).text);
    } catch (e) {
      setErr((e as Error).message);
    }
  }
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-[17px] font-semibold">Draft complaint to UP-RERA</h2>
          <p className="mt-1 text-sm text-muted">Uses verified facts only. Items that still need checking are listed separately.</p>
        </div>
        {text ? (
          <Button variant="outline" size="sm" onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
            {copied ? <Check /> : <Copy />} {copied ? "Copied" : "Copy text"}
          </Button>
        ) : (
          <Button size="sm" onClick={load}>Create draft</Button>
        )}
      </div>
      {err && <div className="mt-4"><ErrorNote>{err}</ErrorNote></div>}
      {text && (
        <pre className="mt-4 max-h-[520px] overflow-auto whitespace-pre-wrap rounded-xl border border-line bg-surface-3 p-5 font-mono text-[13px] leading-7 text-fg-2">{text}</pre>
      )}
      <p className="mt-3 text-xs text-faint">A starting draft for you to edit and file yourself. Review it with a lawyer.</p>
    </Card>
  );
}
