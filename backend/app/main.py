"""FastAPI app factory. Run with: uvicorn app.main:app --reload"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import checks, events, health, projects, reports
from app.config import BACKEND_DIR, Settings, load_settings
from app.db import make_engine, make_session_factory
from app.events import EventHub
from app.orchestrator import Orchestrator, utc_now
from app.ratelimit import RateLimiter
from app.security import add_security_headers
from app.store import Store
from app.tinyfish import LiveWebClient, WebClient

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
        app.state.hub = EventHub()
        app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
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
        try:
            yield
        finally:
            await app.state.orchestrator.shutdown()
            await app.state.web.aclose()
            engine.dispose()

    app = FastAPI(title="NeevCheck API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings

    app.middleware("http")(add_security_headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    for module in (health, projects, checks, events, reports):
        app.include_router(module.router)
    return app


app = create_app()
