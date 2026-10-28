from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_settings
from app.config import Settings
from app.meta import Meta, build_meta
from app.sentinel.notify import email_configured

router = APIRouter(tags=["meta"])


@router.get("/api/meta")
def get_meta(settings: Annotated[Settings, Depends(get_settings)]) -> Meta:
    """The score scale, band edges and pillar weights, so no client hard-codes them."""
    return build_meta(email_alerts=email_configured(settings))
