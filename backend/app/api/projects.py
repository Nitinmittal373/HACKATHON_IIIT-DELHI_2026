import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.auth import MaybeUser
from app.api.deps import client_ip, get_search_gate, get_settings, get_web
from app.config import Settings
from app.models import SearchResponse
from app.search_gate import SearchGate, cache_key
from app.states.resolver import resolve_any
from app.tinyfish import WebClient, WebError

router = APIRouter(tags=["projects"])

# The browser waits up to 120 seconds; answer well before that, even if TinyFish is slow.
SEARCH_BUDGET_SECONDS = 90
ERROR_STATUS = {"timeout": 504, "rate_limited": 429}


@router.get(
    "/api/projects/search",
    responses={
        429: {
            "description": "The daily search limit (`search_limit`) or TinyFish's rate limit; "
            "`Retry-After` says how long to wait"
        },
        502: {"description": "TinyFish failed; `detail.code` says why"},
        504: {"description": "The search took too long"},
    },
)
async def search_projects(
    q: Annotated[
        str, Query(min_length=2, max_length=120, description="UP-RERA number, project or builder")
    ],
    request: Request,
    web: Annotated[WebClient, Depends(get_web)],
    gate: Annotated[SearchGate, Depends(get_search_gate)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: MaybeUser,
    locality: Annotated[
        str | None,
        Query(max_length=80, description="City or locality such as 'Sector 43 Noida'"),
    ] = None,
) -> SearchResponse:
    async def search() -> SearchResponse:
        try:
            found = await asyncio.wait_for(resolve_any(q, web, locality), SEARCH_BUDGET_SECONDS)
        except TimeoutError:
            error = WebError("The RERA portals did not answer in time", "timeout")
            raise search_error(error) from None
        except WebError as error:
            raise search_error(error) from None
        return SearchResponse(
            query=q,
            candidates=found.candidates,
            outside_up=found.outside_up,
            order_leads=found.order_leads,
        )

    return await gate.serve(
        cache_key("projects", q, locality),
        client_ip(request, settings),
        user is not None,
        SearchResponse,
        search,
        keep=lambda found: bool(found.candidates or found.order_leads or found.outside_up),
    )


def search_error(error: WebError) -> HTTPException:
    """A 4xx/5xx whose detail carries a code, so the app can name the reason to the visitor."""
    headers = {"Retry-After": str(error.retry_after)} if error.retry_after else None
    return HTTPException(
        status_code=ERROR_STATUS.get(error.code, 502),
        detail={"code": error.code, "message": str(error)},
        headers=headers,
    )
