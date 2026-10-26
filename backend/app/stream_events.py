"""The Server-Sent Events a check streams, one model per event type.

Event itself (app.models) is the loose envelope the hub carries. These models say exactly
what each event holds, so the OpenAPI contract gives the browser real types for the stream.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models import Band, CheckKey, DisplayScore, Finding, RunStatus, SourceName


class _Event(BaseModel):
    check_id: str
    ts: datetime


class NoData(BaseModel):
    pass


class LiveUrlData(BaseModel):
    url: str


class ProgressData(BaseModel):
    text: str


class FindingData(BaseModel):
    finding: Finding


class BlockedData(BaseModel):
    reason: str


class SourceCompletedData(BaseModel):
    status: RunStatus
    message: str | None = None
    checks_read: list[CheckKey] = []


class ScoreSummary(BaseModel):
    """The classic 0-100 summary sent with check.completed, kept for older clients."""

    value: int
    band: Band
    band_label: str
    confidence: float
    provisional: bool
    hard_stop: bool


class CheckCompletedData(BaseModel):
    status: Literal["completed", "failed"]
    # Why a check failed, in words a visitor can read.
    message: str | None = None
    score: ScoreSummary | None = None
    display_score: DisplayScore | None = None


class SourceStartedEvent(_Event):
    type: Literal["source.started"]
    source: SourceName
    data: NoData


class SourceLiveUrlEvent(_Event):
    type: Literal["source.live_url"]
    source: SourceName
    data: LiveUrlData


class SourceProgressEvent(_Event):
    type: Literal["source.progress"]
    source: SourceName
    data: ProgressData


class FindingAddedEvent(_Event):
    type: Literal["finding.added"]
    source: SourceName
    data: FindingData


class SourceBlockedEvent(_Event):
    type: Literal["source.blocked"]
    source: SourceName
    data: BlockedData


class SourceCompletedEvent(_Event):
    type: Literal["source.completed"]
    source: SourceName
    data: SourceCompletedData


class CheckCompletedEvent(_Event):
    type: Literal["check.completed"]
    source: Literal["check"]
    data: CheckCompletedData


StreamEvent = Annotated[
    SourceStartedEvent
    | SourceLiveUrlEvent
    | SourceProgressEvent
    | FindingAddedEvent
    | SourceBlockedEvent
    | SourceCompletedEvent
    | CheckCompletedEvent,
    Field(discriminator="type"),
]
