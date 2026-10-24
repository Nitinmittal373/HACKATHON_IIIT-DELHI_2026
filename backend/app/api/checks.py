from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import (
    CheckId,
    client_ip,
    find_check,
    get_limiter,
    get_orchestrator,
    get_settings,
    get_store,
)
from app.config import Settings
from app.models import Check, CheckCreate, Project
from app.orchestrator import Orchestrator
from app.ratelimit import RateLimiter
from app.resolve import details_url_for
from app.store import Store

router = APIRouter(tags=["checks"])


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_limiter)],
) -> None:
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many checks from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


@router.post("/api/checks", status_code=202, dependencies=[Depends(rate_limit)])
async def create_check(
    body: CheckCreate,
    response: Response,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
) -> Check:
    # Old-format numbers always use their canonical page, whatever link was sent.
    details_url = details_url_for(body.rera_id) or body.details_url
    assert details_url is not None  # CheckCreate requires a link for new-format numbers
    check = orchestrator.start(Project(rera_id=body.rera_id, details_url=details_url))
    response.headers["Location"] = f"/api/checks/{check.id}"
    return check


@router.get("/api/checks/{check_id}")
def get_check(check_id: CheckId, store: Annotated[Store, Depends(get_store)]) -> Check:
    return find_check(store, check_id)
