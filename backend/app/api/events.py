"""GET /api/checks/{id}/events: the check's progress as Server-Sent Events."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import CheckId, find_check, get_hub, get_store
from app.events import EventHub
from app.models import Check, Event
from app.store import Store

router = APIRouter(tags=["checks"])
HEARTBEAT_SECONDS = 15


@router.get(
    "/api/checks/{check_id}/events",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
def stream_events(
    check_id: CheckId,
    store: Annotated[Store, Depends(get_store)],
    hub: Annotated[EventHub, Depends(get_hub)],
) -> StreamingResponse:
    check = find_check(store, check_id)
    log = hub.get(check_id)
    stream = _follow(log.follow(HEARTBEAT_SECONDS)) if log else _replay_finished(check)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _follow(events: AsyncIterator[Event | None]) -> AsyncIterator[str]:
    number = 0
    async for event in events:
        if event is None:
            yield ": keep-alive\n\n"
            continue
        number += 1
        yield format_event(event, number)


async def _replay_finished(check: Check) -> AsyncIterator[str]:
    """The live log is gone (for example after a restart); send the final state only."""
    event = Event(
        type="check.completed",
        check_id=check.id,
        source="check",
        ts=check.completed_at or datetime.now(UTC),
        data={"status": check.status},
    )
    yield format_event(event, 1)


def format_event(event: Event, number: int) -> str:
    return f"id: {number}\nevent: {event.type}\ndata: {event.model_dump_json()}\n\n"
