"""NeevCheck API (FastAPI).

Investigations
  POST /api/investigations                  {"query": "..."} -> {"id"}
  GET  /api/investigations/{id}             status: running | done | failed
  GET  /api/investigations/{id}/events      Server-Sent Events for the War Room
Reports
  GET  /api/reports                         summaries, newest first
  GET  /api/reports/{id}                    full report: signals, evidence, checks, NeevScore, family tree
  POST /api/reports/{id}/ask                {"question": "..."} -> answer built only from cited evidence
  POST /api/reports/{id}/complaint-draft    UP-RERA complaint draft from verified evidence
Projects / Watch mode
  GET  /api/projects/{id}/evidence          evidence ledger for one checked project
  POST /api/projects/{id}/watch             TinyFish Monitors -> our webhook
  GET  /api/watches                         watched projects
  POST /api/webhooks/tinyfish               Monitor webhook receiver (shared secret)
  GET  /api/alerts                          alerts received
  GET  /api/health
Run from the backend folder:  uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import hmac
import json
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import config, insights, sources, store, tf
from .models import Check, Evidence, LaneStatus, Report, Signals, now_iso
from .scoring import score

LANES = ["rera", "mca", "ibbi", "authority", "news"]
JOBS: dict[str, dict] = {}                     # live investigations; finished reports go to the database
_hits: dict[str, deque] = defaultdict(deque)   # simple per-IP rate limit for new investigations


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    yield


app = FastAPI(title="NeevCheck API", version="1.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.FRONTEND_ORIGINS,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


class InvestigateIn(BaseModel):
    query: str = Field(min_length=3, max_length=160)


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=300)


@app.get("/api/health")
def health():
    return {"ok": True, "demo_mode": config.DEMO_MODE, "key_loaded": bool(config.TINYFISH_API_KEY),
            "watch_ready": bool(config.PUBLIC_BASE_URL)}


# ---------------- investigations ----------------
def _rate_limit(ip: str) -> None:
    q, now = _hits[ip], time.monotonic()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(429, "Too many checks from this address. Try again in a minute.")
    q.append(now)


@app.post("/api/investigations")
async def start_investigation(body: InvestigateIn, request: Request):
    _rate_limit(request.client.host if request.client else "unknown")
    q = " ".join(body.query.split())
    inv_id = uuid.uuid4().hex[:12]
    JOBS[inv_id] = {"query": q, "events": [], "status": "running", "cond": asyncio.Condition()}
    asyncio.create_task(_run(inv_id))
    return {"id": inv_id}


async def _run(inv_id: str) -> None:
    job = JOBS[inv_id]
    q = job["query"]
    sig, ev, checks, ctx, lanes = Signals(), [], [], {}, {}

    async def emit(e: dict):
        e["ts"] = now_iso()
        async with job["cond"]:
            job["events"].append(e)
            job["cond"].notify_all()

    async def run_lane(name: str, fn):
        await emit({"lane": name, "type": "started", "message": "started"})
        try:
            await fn(q, sig, ev, checks, ctx, emit)
            lanes[name] = LaneStatus(lane=name, ok=True, message="done")
            await emit({"lane": name, "type": "done", "message": "done"})
        except Exception as e:  # one failed source must never stop the others
            lanes[name] = LaneStatus(lane=name, ok=False, message=str(e))
            await emit({"lane": name, "type": "error", "message": str(e)})

    try:
        # Phase 1: UP-RERA gives the promoter's exact name; news can start on the query right away
        await asyncio.gather(run_lane("rera", sources.rera_lane), run_lane("news", sources.news_lane))
        # Phase 2: everything keyed on the promoter, in parallel (agents still capped at 2)
        await asyncio.gather(run_lane("mca", sources.mca_lane), run_lane("ibbi", sources.ibbi_lane),
                             run_lane("authority", sources.authority_lane))
        # The company registry saying "Under CIRP" confirms admission, even if no IBBI page was found
        if ctx.get("registry_says_cirp") and not sig.promoter_in_cirp:
            sig.promoter_in_cirp = True
            sig.insolvency_case_found = None
        for i, e in enumerate(ev, 1):
            e.n = i
        report = Report(
            id=inv_id, query=q, project_name=ctx.get("project_name"), rera_number=ctx.get("rera_number"),
            promoter_name=ctx.get("promoter_name"), rera_url=ctx.get("rera_url"),
            photo_url=ctx.get("photo_url"), signals=sig, evidence=ev,
            checks=checks, lanes=[lanes[n] for n in LANES if n in lanes], score=score(sig),
            graph=insights.build_graph(ctx.get("project_name"), ctx.get("promoter_name"), sig,
                                       ctx.get("group_names", [])),
            demo_replay=config.DEMO_MODE)
        store.save_report(report)
        job["status"] = "done"
        await emit({"lane": "score", "type": "report", "message": inv_id,
                    "score": report.score["score"], "band": report.score["band"]})
    except Exception as e:
        job["status"] = "failed"
        await emit({"lane": "score", "type": "error", "message": f"Investigation failed: {e}"})
    finally:
        async with job["cond"]:
            job["cond"].notify_all()


@app.get("/api/investigations/{inv_id}")
def investigation(inv_id: str):
    job = JOBS.get(inv_id)
    if job:
        return {"id": inv_id, "query": job["query"], "status": job["status"],
                "report_id": inv_id if job["status"] == "done" else None}
    if store.get_report(inv_id):
        return {"id": inv_id, "status": "done", "report_id": inv_id}
    raise HTTPException(404, "Unknown investigation")


@app.get("/api/investigations/{inv_id}/events")
async def events(inv_id: str):
    job = JOBS.get(inv_id)
    if not job:
        raise HTTPException(404, "Unknown investigation")

    async def stream():
        i = 0
        while True:
            async with job["cond"]:
                while i >= len(job["events"]) and job["status"] == "running":
                    try:
                        await asyncio.wait_for(job["cond"].wait(), timeout=15)
                    except asyncio.TimeoutError:
                        break
            while i < len(job["events"]):
                yield f"data: {json.dumps(job['events'][i], ensure_ascii=False)}\n\n"
                i += 1
            if job["status"] != "running" and i >= len(job["events"]):
                yield f"event: end\ndata: {json.dumps({'status': job['status']})}\n\n"
                return
            yield ": keep-alive\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------- reports ----------------
def _report(report_id: str) -> Report:
    r = store.get_report(report_id)
    if not r:
        raise HTTPException(404, "Unknown report")
    return r


@app.get("/api/reports")
def reports():
    return store.list_reports()


@app.get("/api/reports/{report_id}")
def report(report_id: str):
    return _report(report_id)


@app.post("/api/reports/{report_id}/ask")
def ask(report_id: str, body: AskIn):
    return insights.answer(_report(report_id), body.question)


@app.post("/api/reports/{report_id}/complaint-draft")
def complaint_draft(report_id: str):
    return {"text": insights.complaint(_report(report_id))}


@app.get("/api/projects/{report_id}/evidence")
def evidence(report_id: str) -> list[Evidence]:
    return _report(report_id).evidence


# ---------------- Watch mode (TinyFish Monitor) ----------------
@app.post("/api/projects/{report_id}/watch")
async def watch(report_id: str):
    r = _report(report_id)
    if not config.PUBLIC_BASE_URL:
        raise HTTPException(400, "Watch mode needs PUBLIC_BASE_URL in .env (an https address TinyFish can reach)")
    hook = f"{config.PUBLIC_BASE_URL}/api/webhooks/tinyfish?report={report_id}"
    if config.WEBHOOK_SECRET:
        hook += f"&token={config.WEBHOOK_SECRET}"
    created = []
    if r.rera_url:
        m = await tf.client().monitors.create(
            "fetch", {"url": r.rera_url}, "0 6 * * *", name=f"NeevCheck RERA {r.rera_number or report_id}"[:80],
            webhook_url=hook,
            purpose="Alert if the completion date changes, a new extension or penalty order appears, "
                    "or the registration status changes.")
        created.append(m.model_dump())
    who = r.promoter_name or r.project_name or r.query
    m = await tf.client().monitors.create(
        "search", {"query": f"{who} homebuyers protest OR NCLT OR insolvency OR delay"}, "0 7 * * *",
        name=f"NeevCheck news {who}"[:80], webhook_url=hook,
        purpose="Alert on new news about delays, buyer protests, insolvency or lender action.")
    created.append(m.model_dump())
    store.save_watch(report_id, created)
    return {"watching": True, "monitors": len(created)}


@app.get("/api/watches")
def watches():
    return store.list_watches()


@app.post("/api/webhooks/tinyfish")
async def tinyfish_webhook(request: Request, report: str | None = None, token: str = ""):
    if config.WEBHOOK_SECRET and not hmac.compare_digest(token, config.WEBHOOK_SECRET):
        raise HTTPException(401, "Bad webhook token")
    payload = await request.json()
    store.add_alert(report, payload)
    return {"ok": True}


@app.get("/api/alerts")
def alerts():
    return store.list_alerts()


# Re-exported for tests
__all__ = ["app", "Check"]
