"use client";

import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Check as CheckIcon, Eye, Loader2, MousePointer2, Play, Search, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useReducer, useRef, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { BandBadge } from "@/components/score";
import { Button } from "@/components/ui/button";
import { Badge, Card, ErrorNote, Eyebrow, Input } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Lane, LiveEvent } from "@/lib/types";
import { LANE_LABEL, LANE_METHOD, cn } from "@/lib/utils";

const ORDER: Lane[] = ["rera", "news", "mca", "ibbi", "authority"];
const WAITING: Record<Lane, string> = {
  rera: "Starts first",
  news: "Starts first",
  mca: "Waits for the builder name from UP-RERA",
  ibbi: "Waits for the builder name from UP-RERA",
  authority: "Waits for the builder name from UP-RERA",
};

type LaneState = { status: "queued" | "running" | "done" | "error"; steps: string[]; liveUrl?: string; error?: string };
type State = { lanes: Record<Lane, LaneState>; result?: { id: string; score: number; band: string }; failed?: string };

const fresh = (): State => ({
  lanes: Object.fromEntries(ORDER.map((l) => [l, { status: "queued", steps: [] } as LaneState])) as Record<Lane, LaneState>,
});

function reducer(s: State, e: LiveEvent | { type: "reset" }): State {
  if (e.type === "reset") return fresh();
  if (e.lane === "score") {
    if (e.type === "report") return { ...s, result: { id: e.message, score: e.score ?? 0, band: e.band ?? "" } };
    if (e.type === "error") return { ...s, failed: e.message };
    return s;
  }
  const cur = s.lanes[e.lane];
  if (!cur) return s;
  const next: LaneState = { ...cur };
  if (e.type === "started") next.status = "running";
  if (e.type === "progress") next.steps = [...cur.steps, e.message].slice(-30);
  if (e.type === "streaming_url") next.liveUrl = e.message;
  if (e.type === "done") next.status = "done";
  if (e.type === "error") { next.status = "error"; next.error = e.message; }
  return { ...s, lanes: { ...s.lanes, [e.lane]: next } };
}

export default function CheckPage() {
  return (
    <Suspense>
      <WarRoom />
    </Suspense>
  );
}

function WarRoom() {
  const params = useSearchParams();
  const router = useRouter();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [state, dispatch] = useReducer(reducer, undefined, fresh);
  const [runId, setRunId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [focus, setFocus] = useState<Lane | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const autoStarted = useRef(false);

  const running = !!runId && !state.result && !state.failed;

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const finishedRef = useRef(false);

  const stopAll = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  }, []);

  // Live stream. The server replays every event from the start, so a reconnect rebuilds the lanes exactly.
  const connect = useCallback((id: string, attempt = 0) => {
    esRef.current?.close();
    dispatch({ type: "reset" });
    const es = new EventSource(api.eventsUrl(id));
    esRef.current = es;
    es.onmessage = (m) => {
      const ev = JSON.parse(m.data) as LiveEvent;
      if (ev.lane === "score" && (ev.type === "report" || ev.type === "error")) finishedRef.current = true;
      dispatch(ev);
    };
    es.addEventListener("end", () => { finishedRef.current = true; es.close(); });
    es.onerror = () => {
      es.close();
      if (!finishedRef.current && attempt < 5 && esRef.current === es) {
        setTimeout(() => connect(id, attempt + 1), 1500 * (attempt + 1));
      }
    };
  }, []);

  // Safety net: even if the stream is blocked (proxy, VPN, antivirus), poll the status and finish cleanly.
  const startPolling = useCallback((id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      if (finishedRef.current) { if (pollRef.current) clearInterval(pollRef.current); return; }
      try {
        const s = await api.investigation(id);
        if (s.status === "done" && s.report_id) {
          const r = await api.report(s.report_id);
          finishedRef.current = true;
          dispatch({ lane: "score", type: "report", message: r.id, score: r.score.score, band: r.score.band, ts: "" });
        } else if (s.status === "failed") {
          finishedRef.current = true;
          dispatch({ lane: "score", type: "error", message: "Investigation failed. Check the backend terminal for details.", ts: "" });
        }
      } catch {
        /* backend busy or restarting: try again on the next tick */
      }
    }, 4000);
  }, []);

  const start = useCallback(async (q: string) => {
    autoStarted.current = true;   // the URL update below must not trigger a second run
    if (q.trim().length < 3) { setErr("Enter at least 3 characters: a project name, UP-RERA number or builder."); return; }
    setErr(null);
    stopAll();
    finishedRef.current = false;
    dispatch({ type: "reset" });
    try {
      const { id } = await api.startInvestigation(q.trim());
      setRunId(id);
      setStartedAt(Date.now());
      if (new URLSearchParams(window.location.search).get("q") !== q.trim()) {
        router.replace(`/check?q=${encodeURIComponent(q.trim())}`, { scroll: false });
      }
      connect(id);
      startPolling(id);
    } catch (e) {
      setErr((e as Error).message);
    }
  }, [router, stopAll, connect, startPolling]);

  // Auto-start once when opened with ?q=... (from the landing page or dashboard search)
  useEffect(() => {
    const q = params.get("q");
    if (q && !autoStarted.current) start(q);
  }, [params, start]);

  // Close the stream only when leaving the page, never when the URL changes
  useEffect(() => stopAll, [stopAll]);

  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [running]);

  const done = ORDER.filter((l) => ["done", "error"].includes(state.lanes[l].status)).length;
  const live = focus ?? ORDER.find((l) => state.lanes[l].status === "running" && state.lanes[l].liveUrl) ?? ORDER.find((l) => state.lanes[l].status === "running") ?? null;
  const liveLane = live ? state.lanes[live] : null;
  const secs = startedAt ? Math.floor(((state.result || state.failed ? now : Date.now()) - startedAt) / 1000) : 0;

  return (
    <>
      <PageHeader
        title="War Room"
        sub="Five agents read public records live. Nothing is guessed."
        actions={<span className="rounded-lg border border-line px-2.5 py-1.5 font-mono text-xs text-muted">Max 2 web agents at once · Search runs in parallel</span>}
      />
      <main className="mx-auto max-w-[1240px] px-5 py-7 sm:px-7">
        <form onSubmit={(e) => { e.preventDefault(); start(query); }} className="flex flex-wrap gap-3">
          <div className="flex min-w-0 flex-[1_1_420px] items-center gap-3 rounded-2xl border border-line-strong bg-surface px-4 shadow-sm">
            <Search className="size-5 text-faint" aria-hidden />
            <label htmlFor="wr-q" className="sr-only">Project to check</label>
            <Input id="wr-q" value={query} onChange={(e) => setQuery(e.target.value)} maxLength={160} placeholder="Project name, UP-RERA number or builder" className="h-14 text-base" />
          </div>
          <Button type="submit" size="lg" className="h-14" disabled={running}>
            {running ? <Loader2 className="animate-spin" /> : <Play />} {running ? "Investigating…" : runId ? "Run again" : "Start check"}
          </Button>
        </form>
        {err && <div className="mt-4"><ErrorNote>{err}</ErrorNote></div>}

        {runId && (
          <>
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 text-[15px] font-semibold">
                <span className={cn("size-2.5 rounded-full", state.result ? "bg-[#4FC1A6]" : state.failed ? "bg-[#EF5A4C]" : "animate-pulse bg-[#F2B84B]")} aria-hidden />
                {state.result ? "Investigation complete" : state.failed ? "Investigation stopped" : `Investigating “${query}”`}
              </div>
              <span className="font-mono text-xs text-faint" aria-live="polite">
                {done} of 5 lanes · {Math.floor(secs / 60)}m {String(secs % 60).padStart(2, "0")}s
              </span>
            </div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-track">
              <motion.div className="h-full rounded-full bg-accent" animate={{ width: `${(done / 5) * 100}%` }} transition={{ duration: 0.6 }} />
            </div>

            <div className="mt-6 flex flex-wrap items-start gap-5">
              <div className="grid min-w-0 flex-[999_1_560px] grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-3.5">
                {ORDER.map((l) => <LaneCard key={l} lane={l} s={state.lanes[l]} onWatch={() => setFocus(l)} active={live === l} />)}
              </div>
              <LiveBrowser lane={live} s={liveLane} onClear={() => setFocus(null)} pinned={!!focus} />
            </div>

            <AnimatePresence>
              {state.result && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
                  <Card className="flex flex-wrap items-center justify-between gap-4 border-line-strong bg-bg-2 p-5">
                    <div className="flex items-center gap-4">
                      <div className="text-4xl font-extrabold tracking-tight">{state.result.band === "Not enough data" ? "–" : state.result.score}</div>
                      <div>
                        <div className="flex items-center gap-2 font-semibold">Report ready <BandBadge band={state.result.band} /></div>
                        <div className="text-sm text-faint">Every finding is saved with its source and retrieval time.</div>
                      </div>
                    </div>
                    <Button asChild size="lg"><Link href={`/reports/${state.result.id}`}>Open the dossier <ArrowRight /></Link></Button>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
            {state.failed && <div className="mt-6"><ErrorNote>{state.failed}</ErrorNote></div>}
          </>
        )}

        {!runId && (
          <Card className="mt-8 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-5 p-6">
            {ORDER.map((l) => (
              <div key={l}>
                <Eyebrow>{LANE_METHOD[l]}</Eyebrow>
                <div className="mt-1.5 font-semibold">{LANE_LABEL[l]}</div>
                <p className="mt-1 text-sm text-muted">{WAITING[l]}</p>
              </div>
            ))}
          </Card>
        )}
      </main>
    </>
  );
}

function LaneCard({ lane, s, onWatch, active }: { lane: Lane; s: LaneState; onWatch: () => void; active: boolean }) {
  const pill = {
    queued: "bg-surface-2 text-faint",
    running: "bg-warn-bg text-warn-fg",
    done: "bg-ok-bg text-ok-fg",
    error: "bg-high-bg text-high-fg",
  }[s.status];
  return (
    <section className={cn("min-h-[230px] rounded-2xl border bg-surface p-4 transition-colors", active ? "border-warn-line" : "border-line")} aria-label={LANE_LABEL[lane]}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <Eyebrow>{LANE_METHOD[lane]}</Eyebrow>
          <h2 className="mt-1 text-[16px] font-semibold">{LANE_LABEL[lane]}</h2>
        </div>
        <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold", pill)}>{s.status === "error" ? "unavailable" : s.status}</span>
      </div>
      {s.liveUrl && s.status === "running" && (
        <button type="button" onClick={onWatch} className="mt-2.5 inline-flex cursor-pointer items-center gap-1.5 text-[13px] font-medium text-accent hover:underline">
          <Eye className="size-3.5" aria-hidden /> Watch this agent&apos;s browser
        </button>
      )}
      <ol className="mt-3 flex max-h-40 flex-col gap-1.5 overflow-y-auto text-[13px] leading-snug" aria-live="polite">
        {s.steps.length === 0 && <li className="text-faint">{s.status === "queued" ? WAITING[lane] : "Starting…"}</li>}
        {s.steps.map((step, i) => {
          const last = i === s.steps.length - 1 && s.status === "running";
          return (
            <motion.li key={i} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="flex gap-2 text-fg-2">
              {last ? <Loader2 className="mt-0.5 size-3.5 shrink-0 animate-spin text-warn-fg" aria-hidden /> : <CheckIcon className="mt-0.5 size-3.5 shrink-0 text-ok-fg" aria-hidden />}
              <span>{step}</span>
            </motion.li>
          );
        })}
        {s.error && <li className="flex gap-2 text-high-fg"><X className="mt-0.5 size-3.5 shrink-0" aria-hidden />{s.error}</li>}
      </ol>
    </section>
  );
}

function LiveBrowser({ lane, s, onClear, pinned }: { lane: Lane | null; s: LaneState | null; onClear: () => void; pinned: boolean }) {
  return (
    <aside aria-label="Live agent browser" className="w-full min-w-0 flex-[1_1_380px] overflow-hidden rounded-2xl border border-line-strong bg-surface lg:sticky lg:top-6">
      <div className="flex items-center gap-2 border-b border-line px-3.5 py-3">
        <span className="size-2.5 rounded-full bg-line-strong" /><span className="size-2.5 rounded-full bg-line-strong" /><span className="size-2.5 rounded-full bg-line-strong" />
        <div className="ml-2 min-w-0 flex-1 truncate rounded-lg border border-line bg-surface-3 px-2.5 py-1.5 font-mono text-xs text-muted">
          {s?.liveUrl ? `TinyFish agent · ${lane ? LANE_LABEL[lane] : ""}` : lane ? `${LANE_LABEL[lane]} · ${LANE_METHOD[lane]}` : "Waiting for an agent"}
        </div>
        {s?.status === "running" && <Badge tone="high" className="gap-1"><span className="size-1.5 animate-pulse rounded-full bg-[#EF5A4C]" />LIVE</Badge>}
        {pinned && <button type="button" onClick={onClear} aria-label="Follow the active agent" className="cursor-pointer text-faint hover:text-fg"><X className="size-4" /></button>}
      </div>
      <div className="relative h-[340px] bg-surface-3">
        {s?.liveUrl ? (
          <iframe
            key={s.liveUrl}
            src={s.liveUrl}
            title={`Live browser for ${lane ? LANE_LABEL[lane] : "agent"}`}
            className="size-full"
            sandbox="allow-scripts allow-same-origin"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="relative size-full overflow-hidden p-5">
            {s?.status === "running" && <div className="absolute inset-x-0 h-0.5 animate-[scan_2.6s_ease-in-out_infinite] bg-accent/60" />}
            <div className="shimmer h-5 w-2/3 rounded" />
            <div className="shimmer mt-5 h-3 w-11/12 rounded" />
            <div className="shimmer mt-2.5 h-3 w-4/5 rounded" />
            <div className="shimmer mt-2.5 h-3 w-5/6 rounded" />
            <div className="mt-6 grid grid-cols-3 gap-2.5"><div className="shimmer h-14 rounded-lg" /><div className="shimmer h-14 rounded-lg" /><div className="shimmer h-14 rounded-lg" /></div>
            <div className="absolute inset-x-5 bottom-5 flex items-center gap-2.5 rounded-xl border border-line-strong bg-surface px-3.5 py-3 text-[13px] text-fg-2">
              <MousePointer2 className="size-4 shrink-0 text-accent" aria-hidden />
              <span className="truncate">{s?.steps.at(-1) ?? "The live browser appears here when a web agent starts."}</span>
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-3 text-xs text-faint">
        <span>Streamed from the agent&apos;s real browser. CAPTCHAs are never solved automatically.</span>
        {s?.liveUrl && <a href={s.liveUrl} target="_blank" rel="noopener noreferrer" className="shrink-0 font-semibold text-accent hover:underline">Open</a>}
      </div>
    </aside>
  );
}
