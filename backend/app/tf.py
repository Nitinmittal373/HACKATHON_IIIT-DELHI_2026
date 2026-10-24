"""All TinyFish calls go through here.

Follows the organisers' radar.py pattern (AsyncTinyFish, agent + output_schema,
Search finds pages, agents work them) with additions for NeevCheck:
  1. Streaming: agent.stream() so the War Room shows each step live.
  2. A semaphore so at most AGENT_CONCURRENCY agents run at once (pay-as-you-go limit = 2).
  3. A per-day cache + DEMO_MODE replay, so the stage demo never waits on a slow site.
     Cached results keep their ORIGINAL retrieval time, which the report shows.
Search and Fetch are free, so lanes use them first and the Agent only when a page needs clicking.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import date
from typing import Any, Awaitable, Callable

from tinyfish import (AgentConfig, AsyncTinyFish, BrowserProfile, CompleteEvent,
                      ProgressEvent, ProxyConfig, RunStatus, StreamingUrlEvent)

from . import config
from .models import now_iso

Emit = Callable[[dict], Awaitable[None]]

_client: AsyncTinyFish | None = None
_agent_slots = asyncio.Semaphore(config.AGENT_CONCURRENCY)
replayed = False          # set when any result came from cache in DEMO_MODE


def client() -> AsyncTinyFish:
    global _client
    if _client is None:
        _client = AsyncTinyFish()          # reads TINYFISH_API_KEY loaded from .env
    return _client


# ---------- cache ----------
def _key_hash(kind: str, key: str) -> str:
    return hashlib.sha1(f"{kind}|{key}".encode()).hexdigest()[:16]


def _cache_path(kind: str, key: str):
    stamp = "any" if config.DEMO_MODE else date.today().isoformat()
    return config.CACHE_DIR / f"{kind}_{_key_hash(kind, key)}_{stamp}.json"


def _cache_get(kind: str, key: str) -> dict | None:
    global replayed
    p = _cache_path(kind, key)
    if not p.exists() and config.DEMO_MODE:   # in demo mode accept any older cached copy
        older = sorted(config.CACHE_DIR.glob(f"{kind}_{_key_hash(kind, key)}_*.json"))
        p = older[-1] if older else p
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):                # cache written by an older version
        data = {"at": None, "value": data}
    if config.DEMO_MODE:
        replayed = True
    return data


def _cache_put(kind: str, key: str, value: Any, at: str) -> None:
    _cache_path(kind, key).write_text(json.dumps({"at": at, "value": value}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")


# ---------- free tools ----------
async def search(query: str, *, include_domains: str | None = None,
                 exclude_domains: str | None = None,
                 recency_minutes: int | None = None, news: bool = False,
                 limit: int = 5) -> list[dict]:
    """Rows: title, url, snippet, date, fetched_at (original retrieval time)."""
    key = f"{query}|{include_domains}|{exclude_domains}|{recency_minutes}|{news}"
    cached = _cache_get("search", key)
    if cached is not None:
        rows = cached["value"]
        for r in rows:
            r.setdefault("fetched_at", cached.get("at") or now_iso())
        return rows[:limit]
    at = now_iso()
    resp = await client().search.query(query, include_domains=include_domains,
                                       exclude_domains=exclude_domains,
                                       recency_minutes=recency_minutes,
                                       domain_type="news" if news else None)
    rows = [{"title": r.title or "", "url": r.url, "snippet": r.snippet or "", "date": r.date,
             "fetched_at": at} for r in resp.results]
    _cache_put("search", key, rows, at)
    return rows[:limit]


async def fetch(urls: list[str], *, highlight: str | None = None) -> list[dict]:
    key = "|".join(urls) + f"|{highlight}"
    cached = _cache_get("fetch", key)
    if cached is not None:
        return cached["value"]
    at = now_iso()
    kwargs: dict[str, Any] = {"format": "markdown"}
    if highlight:
        kwargs["highlights"] = {"query": highlight, "max_snippets": 5, "include_full_page_text": True}
    resp = await client().fetch.get_contents(urls, **kwargs)
    rows = [{"url": r.url, "title": r.title, "text": (r.text or "")[:20000], "fetched_at": at,
             "highlights": [h.text for h in (r.highlights or [])]} for r in resp.results]
    _cache_put("fetch", key, rows, at)
    return rows


# ---------- paid tool: streamed agent ----------
async def agent(lane: str, *, url: str, goal: str, schema: dict, emit: Emit,
                stealth: bool = True, max_seconds: int = 110) -> dict | None:
    """Run one web agent and stream its steps to the War Room.

    Returns the result JSON with an extra '_fetched_at' key, or None if the run failed.
    """
    key = f"{url}|{goal}"
    cached = _cache_get("agent", key)
    if cached is not None:
        value = cached["value"]
        for step in value.get("_steps", [])[:12]:          # replay steps so the demo still looks live
            await emit({"lane": lane, "type": "progress", "message": step})
            await asyncio.sleep(0.35)
        await emit({"lane": lane, "type": "progress",
                    "message": f"Replayed from a saved run of {(cached.get('at') or '')[:10]}"})
        result = dict(value.get("result") or {})
        result["_fetched_at"] = cached.get("at") or now_iso()
        return result

    await emit({"lane": lane, "type": "progress", "message": "Waiting for a free agent slot..."})
    async with _agent_slots:
        steps: list[str] = []
        result = None
        at = now_iso()
        try:
            async with client().agent.stream(
                url=url, goal=goal, output_schema=schema,
                browser_profile=BrowserProfile.STEALTH if stealth else BrowserProfile.LITE,
                proxy_config=ProxyConfig(enabled=True, country_code="IN") if stealth else None,
                agent_config=AgentConfig(max_duration_seconds=max_seconds),
            ) as stream:
                async for ev in stream:
                    if isinstance(ev, StreamingUrlEvent):
                        await emit({"lane": lane, "type": "streaming_url", "message": ev.streaming_url})
                    elif isinstance(ev, ProgressEvent):
                        steps.append(ev.purpose)
                        await emit({"lane": lane, "type": "progress", "message": ev.purpose})
                    elif isinstance(ev, CompleteEvent):
                        if ev.status == RunStatus.COMPLETED:
                            result = ev.result_json
                        else:
                            msg = ev.error.message if ev.error else str(ev.status)
                            await emit({"lane": lane, "type": "progress", "message": f"Agent stopped: {msg}"})
        except Exception as e:  # never let one lane crash the whole investigation
            await emit({"lane": lane, "type": "progress", "message": f"Agent error: {e}"})
            return None
    if result is None:
        return None
    _cache_put("agent", key, {"result": result, "_steps": steps}, at)
    out = dict(result)
    out["_fetched_at"] = at
    return out
