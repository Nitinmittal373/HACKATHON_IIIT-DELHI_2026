"""Right of reply: anyone can tell us a report is wrong; only the operator can read the log."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.checks import rate_limit
from app.api.deps import get_clock, get_correction_store, get_settings, get_store
from app.api.sentinel import require_secret
from app.config import Settings
from app.corrections import Correction, CorrectionCreate, CorrectionStore
from app.store import Store

router = APIRouter(tags=["corrections"])


@router.post("/api/corrections", status_code=201, dependencies=[Depends(rate_limit)])
def create_correction(
    body: CorrectionCreate,
    store: Annotated[Store, Depends(get_store)],
    corrections: Annotated[CorrectionStore, Depends(get_correction_store)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
) -> dict[str, str]:
    if store.get_check(body.report_id) is None:
        raise HTTPException(status_code=404, detail="No report with this id")
    return {"id": corrections.add(body, clock()).id}


@router.get("/api/corrections")
def list_corrections(
    settings: Annotated[Settings, Depends(get_settings)],
    corrections: Annotated[CorrectionStore, Depends(get_correction_store)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> list[Correction]:
    """Admin log, protected by WEBHOOK_SECRET."""
    require_secret(settings, x_webhook_secret)
    return corrections.latest()
