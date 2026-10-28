"""FastAPI app factory. Run with: uvicorn app.main:app --reload"""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.accounts import UserReports
from app.api import (
    admin,
    checks,
    compare,
    corrections,
    events,
    extract,
    featured,
    health,
    limits,
    me,
    meta,
    projects,
    promoters,
    reports,
    sentinel,
)
from app.cache import SourceCache
from app.config import BACKEND_DIR, Settings, load_settings
from app.corrections import CorrectionStore
from app.db import make_engine, make_session_factory
from app.events import EventHub
from app.orchestrator import Orchestrator, utc_now
from app.ratelimit import DailyLimiter, RateLimiter
from app.search_gate import SavedSearches, SearchGate
from app.security import add_security_headers
from app.sentinel.monitors import MonitorGateway, TinyFishMonitors
from app.sentinel.service import Sentinel
from app.sentinel.store import SentinelStore
from app.sources import build_sources
from app.store import Store
from app.tinyfish import LiveWebClient, WebClient
from app.track_record import TrackRecords

DEFAULT_CACHE_DIR = BACKEND_DIR / "data" / "cache"
SOURCE_TIMEOUT_GRACE_SECONDS = 30
# Files read per minute from one address; each may be 5 MB and 40 pages.
EXTRACT_PER_MINUTE = 10
# Saved-report calls per minute from one address; each is a small database read or write.
ACCOUNT_PER_MINUTE = 30
UNSUBSCRIBE_PER_MINUTE = 10


async def wake_sentinel(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Every request is a chance to start a due re-check; Sentinel keeps it to once an hour."""
    sentinel = getattr(request.app.state, "sentinel", None)
    if sentinel is not None:
        sentinel.poke()
    return await call_next(request)


def create_app(
    settings: Settings | None = None,
    web: WebClient | None = None,
    clock: Callable[[], datetime] = utc_now,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    monitors: MonitorGateway | None = None,
) -> FastAPI:
    """Build the app. Tests pass a fake `web` client and a fixed clock."""
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.web = web or LiveWebClient(
            settings.tinyfish_api_key,
            fetch_timeout=settings.fetch_timeout_seconds,
            agent_timeout=settings.agent_timeout_seconds,
            send_max_steps=settings.agent_send_max_steps,
        )
        engine = make_engine(settings.database_url)
        app.state.store = Store(make_session_factory(engine))
        source_cache = SourceCache(make_session_factory(engine))
        # A check's agents run inside this process; any it was running before a restart or a
        # redeploy are gone, so those checks can never finish and are failed honestly.
        app.state.store.fail_unfinished_checks(clock())
        # Old reports follow the current rules too, so the home page and My reports never
        # show a number the method section no longer explains.
        app.state.store.rescore_all()
        app.state.hub = EventHub()
        app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
        app.state.search_gate = SearchGate(
            SavedSearches(make_session_factory(engine)), DailyLimiter(), settings, clock
        )
        app.state.extract_limiter = RateLimiter(EXTRACT_PER_MINUTE)
        app.state.account_limiter = RateLimiter(ACCOUNT_PER_MINUTE)
        app.state.unsubscribe_limiter = RateLimiter(UNSUBSCRIBE_PER_MINUTE)
        app.state.user_reports = UserReports(make_session_factory(engine))
        app.state.track_records = TrackRecords(app.state.web, clock)
        app.state.orchestrator = Orchestrator(
            app.state.store,
            app.state.hub,
            app.state.web,
            concurrency=settings.agent_concurrency,
            # The agent stops itself at agent_timeout_seconds; this is only the backstop.
            source_timeout=settings.agent_timeout_seconds + SOURCE_TIMEOUT_GRACE_SECONDS,
            clock=clock,
            sources=build_sources,
            cache_dir=cache_dir,
            source_cache=source_cache,
        )
        app.state.corrections = CorrectionStore(make_session_factory(engine))
        app.state.sentinel_store = SentinelStore(make_session_factory(engine))
        app.state.sentinel = Sentinel(
            app.state.store,
            app.state.sentinel_store,
            app.state.orchestrator,
            settings,
            clock,
        )
        # Monitors bill outside the site budget, so they exist only when SENTINEL_MONITORS is on.
        # Switched off, any that an earlier version made for current watches are cancelled now.
        monitors_on = bool(
            settings.sentinel_monitors and settings.public_base_url and settings.webhook_secret
        )
        leftover = not settings.sentinel_monitors and app.state.sentinel_store.monitor_ids()
        app.state.monitors = monitors or (
            TinyFishMonitors(settings.tinyfish_api_key, timeout=settings.fetch_timeout_seconds)
            if monitors_on or leftover
            else None
        )
        if leftover and app.state.monitors:
            await app.state.sentinel.cancel_monitors(app.state.monitors)
        app.state.sentinel.poke()
        try:
            yield
        finally:
            app.state.sentinel.stop()
            await app.state.orchestrator.shutdown()
            await app.state.web.aclose()
            if app.state.monitors:
                await app.state.monitors.aclose()
            engine.dispose()

    app = FastAPI(title="NeevCheck API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.clock = clock

    app.middleware("http")(add_security_headers)
    app.middleware("http")(wake_sentinel)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        # Without this the browser hides Retry-After and cannot tell a visitor how long to wait.
        expose_headers=["Retry-After"],
    )
    # compare before checks: /api/checks/compare must not be read as a check id.
    for module in (
        health,
        meta,
        projects,
        extract,
        promoters,
        compare,
        checks,
        featured,
        limits,
        admin,
        events,
        reports,
        sentinel,
        corrections,
        me,
    ):
        app.include_router(module.router)
    return app


app = create_app()
