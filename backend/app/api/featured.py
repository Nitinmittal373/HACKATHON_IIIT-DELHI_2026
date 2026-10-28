from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_settings, get_store
from app.config import Settings
from app.models import FeaturedProject
from app.store import Store

router = APIRouter(tags=["checks"])


@router.get("/api/featured")
def get_featured(
    store: Annotated[Store, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[FeaturedProject]:
    """The saved checks of the projects listed in FEATURED_RERA_IDS, in that order.

    A number nobody has checked yet is left out; no card is ever made up.
    """
    featured = []
    for rera_id in settings.featured_ids:
        check = store.latest_completed_check(rera_id)
        project = store.get_project(rera_id)
        if check is None or project is None or check.display_score is None:
            continue
        featured.append(
            FeaturedProject(
                rera_id=rera_id,
                check_id=check.id,
                name=project.name,
                promoter=project.promoter,
                display_score=check.display_score,
                read_at=check.completed_at or check.started_at,
            )
        )
    return featured
