from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_store
from app.api.projects import search_error
from app.models import normalize_rera_id
from app.store import Store
from app.tinyfish import WebError
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
    exclude: Annotated[str | None, Query(max_length=40, description="RERA no. to skip")] = None,
) -> TrackRecord:
    """Up to 10 other UP-RERA projects of a promoter, from Search on up-rera.in; cached a day."""
    try:
        record = await records.find(name.strip(), normalize_rera_id(exclude or ""))
    except WebError as error:
        raise search_error(error) from None
    return record.model_copy(update={"projects": [with_score(p, store) for p in record.projects]})


def with_score(project: TrackedProject, store: Store) -> TrackedProject:
    """The latest finished check NeevCheck holds for the project, if any."""
    check = store.latest_completed_check(project.rera_id)
    if check is None:
        return project
    return project.model_copy(update={"check_id": check.id, "display_score": check.display_score})
