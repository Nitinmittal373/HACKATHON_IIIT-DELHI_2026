"""In-memory event log per check, read by the Server-Sent Events route.

The log keeps every event, so a browser that connects late (or reconnects)
still sees the whole run from the start.
"""

import asyncio
from collections.abc import AsyncIterator

from app.models import Event

MAX_LOGS = 200


class EventLog:
    def __init__(self) -> None:
        self.events: list[Event] = []
        self._wake = asyncio.Event()

    @property
    def closed(self) -> bool:
        return bool(self.events) and self.events[-1].type == "check.completed"

    def append(self, event: Event) -> None:
        self.events.append(event)
        self._wake.set()
        self._wake = asyncio.Event()

    async def follow(self, heartbeat: float) -> AsyncIterator[Event | None]:
        """Every event from the start, then new ones as they come; None when idle."""
        sent = 0
        while True:
            wake = self._wake
            while sent < len(self.events):
                yield self.events[sent]
                sent += 1
            if self.closed:
                return
            try:
                await asyncio.wait_for(wake.wait(), heartbeat)
            except TimeoutError:
                yield None


class EventHub:
    def __init__(self) -> None:
        self._logs: dict[str, EventLog] = {}

    def open(self, check_id: str) -> EventLog:
        self._forget_old_logs()
        log = self._logs[check_id] = EventLog()
        return log

    def get(self, check_id: str) -> EventLog | None:
        return self._logs.get(check_id)

    def publish(self, event: Event) -> None:
        self._logs[event.check_id].append(event)

    def _forget_old_logs(self) -> None:
        # Finished checks can be rebuilt from the database, so only they are dropped.
        for check_id in [cid for cid, log in self._logs.items() if log.closed]:
            if len(self._logs) < MAX_LOGS:
                return
            del self._logs[check_id]
