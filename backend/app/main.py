"""FastAPI app factory. Run with: uvicorn app.main:app --reload"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, projects
from app.config import Settings, load_settings
from app.security import add_security_headers
from app.tinyfish import LiveWebClient, WebClient


def create_app(settings: Settings | None = None, web: WebClient | None = None) -> FastAPI:
    """Build the app. Tests pass a fake `web` client; otherwise TinyFish is used."""
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.web = web or LiveWebClient(
            settings.tinyfish_api_key,
            fetch_timeout=settings.fetch_timeout_seconds,
            agent_timeout=settings.agent_timeout_seconds,
        )
        try:
            yield
        finally:
            await app.state.web.aclose()

    app = FastAPI(title="NeevCheck API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings

    app.middleware("http")(add_security_headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(projects.router)
    return app


app = create_app()
