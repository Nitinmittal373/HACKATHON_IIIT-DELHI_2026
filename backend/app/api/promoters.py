from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.projects import search_error
from app.models import normalize_rera_id
from app.tinyfish import WebError
from app.track_record import TrackRecord, TrackRecords

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
    exclude: Annotated[str | None, Query(max_length=40, description="RERA no. to skip")] = None,
) -> TrackRecord:
    """Up to 10 other UP-RERA projects of a promoter, from Search on up-rera.in; cached a day."""
    try:
        return await records.find(name.strip(), normalize_rera_id(exclude or ""))
    except WebError as error:
        raise search_error(error) from None
