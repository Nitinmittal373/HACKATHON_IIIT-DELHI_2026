"""FastAPI app factory. Run with: uvicorn app.main:app --reload"""

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import checks, compare, events, health, projects, promoters, reports, sentinel
from app.config import BACKEND_DIR, Settings, load_settings
from app.db import make_engine, make_session_factory
from app.events import EventHub
from app.orchestrator import Orchestrator, utc_now
from app.ratelimit import RateLimiter
from app.security import add_security_headers
from app.sentinel.service import Sentinel
from app.sentinel.store import SentinelStore
from app.store import Store
from app.tinyfish import LiveWebClient, WebClient
from app.track_record import TrackRecords

DEFAULT_CACHE_DIR = BACKEND_DIR / "data" / "cache"
SOURCE_TIMEOUT_GRACE_SECONDS = 30


def create_app(
    settings: Settings | None = None,
    web: WebClient | None = None,
    clock: Callable[[], datetime] = utc_now,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
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
        # A check's agents run inside this process; any it was running before a restart or a
        # redeploy are gone, so those checks can never finish and are failed honestly.
        app.state.store.fail_unfinished_checks(clock())
        app.state.hub = EventHub()
        app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
        app.state.track_records = TrackRecords(app.state.web, clock)
        app.state.orchestrator = Orchestrator(
            app.state.store,
            app.state.hub,
            app.state.web,
            concurrency=settings.agent_concurrency,
            # The agent stops itself at agent_timeout_seconds; this is only the backstop.
            source_timeout=settings.agent_timeout_seconds + SOURCE_TIMEOUT_GRACE_SECONDS,
            clock=clock,
            cache_dir=cache_dir,
        )
        app.state.sentinel_store = SentinelStore(make_session_factory(engine))
        app.state.sentinel = Sentinel(
            app.state.store,
            app.state.sentinel_store,
            app.state.orchestrator,
            settings,
            clock,
        )
        schedule = None
        if settings.sentinel_interval_hours > 0:
            schedule = asyncio.create_task(app.state.sentinel.loop())
        try:
            yield
        finally:
            if schedule:
                schedule.cancel()
            await app.state.orchestrator.shutdown()
            await app.state.web.aclose()
            engine.dispose()

    app = FastAPI(title="NeevCheck API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.clock = clock

    app.middleware("http")(add_security_headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        # Without this the browser hides Retry-After and cannot tell a visitor how long to wait.
        expose_headers=["Retry-After"],
    )
    # compare before checks: /api/checks/compare must not be read as a check id.
    for module in (health, projects, promoters, compare, checks, events, reports, sentinel):
        app.include_router(module.router)
    return app


app = create_app()
