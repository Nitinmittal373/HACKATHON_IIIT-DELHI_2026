from fastapi import APIRouter

from app.models import StateInfo
from app.states.registry import ADAPTERS

router = APIRouter(tags=["states"])


@router.get("/api/states")
def list_states() -> list[StateInfo]:
    """Every state NeevCheck can search, how much of its portal is read, and real examples."""
    return [
        StateInfo(
            code=adapter.code,
            name=adapter.name,
            rera_name=adapter.rera_name,
            coverage=adapter.coverage,
            examples=list(adapter.examples),
            note=adapter.note,
            portal_url=adapter.search_url,
            complaint_url=adapter.complaint_url,
            unregistered_url=adapter.unregistered_url,
            id_patterns=list(adapter.id_patterns),
            format_verified=not adapter.unverified_format,
        )
        for adapter in ADAPTERS
    ]
