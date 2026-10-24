from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_web
from app.models import SearchResponse
from app.resolve import resolve
from app.tinyfish import WebClient, WebError

router = APIRouter(tags=["projects"])


@router.get("/api/projects/search")
async def search_projects(
    q: Annotated[str, Query(min_length=2, max_length=120, description="RERA number or name")],
    web: Annotated[WebClient, Depends(get_web)],
) -> SearchResponse:
    try:
        candidates = await resolve(q, web)
    except WebError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    return SearchResponse(query=q, candidates=candidates)
