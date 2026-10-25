"""Shared objects the routes need, read from app.state (set up in app.main)."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import HTTPException, Path, Request

from app.config import Settings
from app.events import EventHub
from app.models import Check
from app.orchestrator import Orchestrator
from app.ratelimit import RateLimiter
from app.sentinel.service import Sentinel
from app.sentinel.store import SentinelStore
from app.store import Store
from app.tinyfish import WebClient

CheckId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$", description="Check id")]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_web(request: Request) -> WebClient:
    return request.app.state.web


def get_store(request: Request) -> Store:
    return request.app.state.store


def get_hub(request: Request) -> EventHub:
    return request.app.state.hub


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


def get_sentinel(request: Request) -> Sentinel:
    return request.app.state.sentinel


def get_sentinel_store(request: Request) -> SentinelStore:
    return request.app.state.sentinel_store


def get_clock(request: Request) -> Callable[[], datetime]:
    return request.app.state.clock


def get_limiter(request: Request) -> RateLimiter:
    return request.app.state.limiter


def client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def find_check(store: Store, check_id: str) -> Check:
    check = store.get_check(check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="No check with this id")
    return check
