"""NeevCheck API.

POST /api/investigate            {"query": "..."}  -> {"job_id"}
GET  /api/investigate/{id}/events  Server-Sent Events for the War Room
GET  /api/report/{id}              Final report (signals, evidence, NeevScore)
GET  /api/report/{id}/complaint    UP-RERA complaint draft built only from evidence
POST /api/watch/{id}               Start Watch mode (TinyFish Monitor -> webhook)
POST /api/webhooks/tinyfish        Monitor webhook receiver
GET  /api/alerts                   Alerts received from monitors
Run:  uvicorn app.main:app --reload --port 8000   (from the backend folder)
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from . import config, sources, tf
from .models import LaneStatus, Report, Signals, now_iso
from .scoring import score

app = FastAPI(title="NeevCheck API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

JOBS: dict[str, dict] = {}     # in-memory is enough for a 24h demo; swap for a DB later
ALERTS: list[dict] = []
LANES = ["rera", "mca", "ibbi", "authority", "news"]


class InvestigateIn(BaseModel):
    query: str


@app.get("/api/health")
def health():
    return {"ok": True, "demo_mode": config.DEMO_MODE, "key_loaded": bool(config.TINYFISH_API_KEY)}


@app.post("/api/investigate")
async def investigate(body: InvestigateIn):
    q = body.query.strip()
    if len(q) < 3:
        raise HTTPException(400, "Enter a project name, RERA number or builder name")
    job_id = uuid.uuid4().hex[:10]
    JOBS[job_id] = {"query": q, "events": [], "done": False, "report": None, "cond": asyncio.Condition()}
    asyncio.create_task(_run(job_id))
    return {"job_id": job_id}


async def _run(job_id: str) -> None:
    job = JOBS[job_id]
    q = job["query"]
    sig, ev, ctx, lanes = Signals(), [], {}, {}

    async def emit(e: dict):
        e["ts"] = now_iso()
        async with job["cond"]:
            job["events"].append(e)
            job["cond"].notify_all()

    async def run_lane(name: str, fn):
        await emit({"lane": name, "type": "started", "message": "started"})
        try:
            await fn(q, sig, ev, ctx, emit)
            lanes[name] = LaneStatus(lane=name, ok=True, message="done")
            await emit({"lane": name, "type": "done", "message": "done"})
        except Exception as e:
            lanes[name] = LaneStatus(lane=name, ok=False, message=str(e))
            await emit({"lane": name, "type": "error", "message": str(e)})

    # Phase 1: RERA tells us the promoter; news can start right away on the query
    await asyncio.gather(run_lane("rera", sources.rera_lane), run_lane("news", sources.news_lane))
    # Phase 2: everything keyed on the promoter company, in parallel (agents still capped at 2)
    await asyncio.gather(run_lane("mca", sources.mca_lane), run_lane("ibbi", sources.ibbi_lane),
                         run_lane("authority", sources.authority_lane))

    result = score(sig)
    job["report"] = Report(query=q, project_name=ctx.get("project_name"), rera_number=ctx.get("rera_number"),
                           promoter_name=ctx.get("promoter_name"), rera_url=ctx.get("rera_url"),
                           signals=sig, evidence=ev, lanes=list(lanes.values()), score=result)
    await emit({"lane": "score", "type": "report", "message": json.dumps(result)})
    job["done"] = True
    async with job["cond"]:
        job["cond"].notify_all()


@app.get("/api/investigate/{job_id}/events")
async def events(job_id: str):
    job = JOBS.get(job_id) or _404()

    async def stream():
        i = 0
        while True:
            async with job["cond"]:
                while i >= len(job["events"]) and not job["done"]:
                    try:
                        await asyncio.wait_for(job["cond"].wait(), timeout=15)
                    except asyncio.TimeoutError:
                        break
            while i < len(job["events"]):
                yield f"data: {json.dumps(job['events'][i], ensure_ascii=False)}\n\n"
                i += 1
            if job["done"] and i >= len(job["events"]):
                yield "event: end\ndata: {}\n\n"
                return
            yield ": keep-alive\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/report/{job_id}")
def report(job_id: str):
    job = JOBS.get(job_id) or _404()
    if not job["report"]:
        raise HTTPException(202, "Still investigating")
    return job["report"]


@app.get("/api/report/{job_id}/complaint", response_class=PlainTextResponse)
def complaint(job_id: str):
    """Draft for the buyer to review and file themselves. Facts come only from cited evidence."""
    job = JOBS.get(job_id) or _404()
    r: Report | None = job["report"]
    if not r:
        raise HTTPException(202, "Still investigating")
    facts = "\n".join(f"{i}. {e.claim} (Source: {e.source_url}, checked {e.fetched_at[:10]})"
                      for i, e in enumerate(r.evidence, 1)) or "No adverse facts were found."
    return (
        "DRAFT: FOR THE ALLOTTEE TO REVIEW, EDIT AND FILE. NOT LEGAL ADVICE.\n\n"
        "To: Uttar Pradesh Real Estate Regulatory Authority (UP-RERA)\n"
        f"Subject: Complaint under the RERA Act, 2016 regarding project '{r.project_name or r.query}'"
        f" (Registration No. {r.rera_number or '[enter]'})\n\n"
        "Complainant: [Your name], Allottee of Unit [number], [contact details]\n"
        f"Respondent: {r.promoter_name or '[Promoter name]'}\n\n"
        "Facts found in public records:\n" + facts + "\n\n"
        "Relief sought: [e.g. possession with delay interest under Section 18 / refund with interest / "
        "direction to file pending quarterly progress reports]\n\n"
        "Annexures: copies of the above source pages, allotment letter, payment receipts.\n"
    )


# ---------------- Watch mode (TinyFish Monitor) ----------------
@app.post("/api/watch/{job_id}")
async def watch(job_id: str):
    job = JOBS.get(job_id) or _404()
    r: Report | None = job["report"]
    if not r:
        raise HTTPException(409, "Finish the investigation first")
    if not config.PUBLIC_BASE_URL:
        raise HTTPException(400, "Set PUBLIC_BASE_URL in .env (an https URL that TinyFish can reach)")
    hook = f"{config.PUBLIC_BASE_URL}/api/webhooks/tinyfish?job={job_id}"
    created = []
    if r.rera_url:
        m = await tf.client().monitors.create(
            "fetch", {"url": r.rera_url}, "0 6 * * *", name=f"NeevCheck RERA {r.rera_number or job_id}",
            webhook_url=hook,
            purpose="Alert if completion date changes, a new extension or penalty order appears, "
                    "or the registration status changes.")
        created.append(m.model_dump())
    who = r.promoter_name or r.project_name or r.query
    m = await tf.client().monitors.create(
        "search", {"query": f"{who} homebuyers protest OR NCLT OR insolvency OR delay"}, "0 7 * * *",
        name=f"NeevCheck news {who}"[:80], webhook_url=hook,
        purpose="Alert on new news about delays, buyer protests, insolvency or lender action.")
    created.append(m.model_dump())
    return {"watching": True, "monitors": created}


@app.post("/api/webhooks/tinyfish")
async def tinyfish_webhook(request: Request, job: str | None = None):
    payload = await request.json()
    ALERTS.append({"job_id": job, "received_at": now_iso(), "payload": payload})
    return {"ok": True}


@app.get("/api/alerts")
def alerts():
    return ALERTS[-50:]


# ---------------- simple War Room page (frontend team can replace with Next.js) ----------------
FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@app.get("/")
def index():
    return FileResponse(FRONTEND)


def _404():
    raise HTTPException(404, "Unknown job")
