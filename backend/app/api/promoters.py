import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_store, get_web
from app.api.projects import SEARCH_BUDGET_SECONDS, search_error
from app.states.promoter_search import PromoterSearchResponse, search_promoter
from app.states.registry import adapter_for, known_state
from app.store import Store
from app.tinyfish import WebClient, WebError
from app.track_record import TrackedProject, TrackRecord, TrackRecords

router = APIRouter(tags=["projects"])


def get_track_records(request: Request) -> TrackRecords:
    return request.app.state.track_records


@router.get(
    "/api/promoters/projects",
    responses={502: {"description": "TinyFish failed; `detail.code` says why"}},
)
async def promoter_projects(
    name: Annotated[str, Query(min_length=3, max_length=300, description="Promoter's legal name")],
    records: Annotated[TrackRecords, Depends(get_track_records)],
    store: Annotated[Store, Depends(get_store)],
    exclude: Annotated[str | None, Query(max_length=60, description="RERA no. to skip")] = None,
    state: Annotated[str, Query(max_length=2, description="State code; UP when omitted")] = "UP",
) -> TrackRecord:
    """Up to 10 other projects of a promoter in one state, from Search on its portal."""
    if not known_state(state.upper()):
        raise HTTPException(status_code=422, detail=f"{state} is not a supported state code")
    code = state.upper()
    try:
        skip = adapter_for(code).canonical_id(exclude or "") if exclude else None
        record = await records.find(name.strip(), skip, code)
    except WebError as error:
        raise search_error(error) from None
    return record.model_copy(update={"projects": [with_score(p, store) for p in record.projects]})


def with_score(project: TrackedProject, store: Store) -> TrackedProject:
    """The latest finished check NeevCheck holds for the project, if any."""
    check = store.latest_completed_check(project.rera_id)
    if check is None:
        return project
    return project.model_copy(update={"check_id": check.id, "display_score": check.display_score})


@router.get(
    "/api/promoters/search",
    responses={502: {"description": "TinyFish failed; `detail.code` says why"}},
)
async def search_promoters(
    q: Annotated[str, Query(min_length=3, max_length=120, description="Builder or company name")],
    web: Annotated[WebClient, Depends(get_web)],
    state: Annotated[str | None, Query(max_length=2, description="State code to limit to")] = None,
    city: Annotated[str | None, Query(max_length=80, description="City or locality")] = None,
) -> PromoterSearchResponse:
    """The registered projects and company pages Search finds for a builder's name."""
    if state is not None and not known_state(state.upper()):
        raise HTTPException(status_code=422, detail=f"{state} is not a supported state code")
    try:
        return await asyncio.wait_for(
            search_promoter(q.strip(), web, state.upper() if state else None, city),
            SEARCH_BUDGET_SECONDS,
        )
    except TimeoutError:
        raise search_error(WebError("The RERA portals did not answer in time", "timeout")) from None
    except WebError as error:
        raise search_error(error) from None
