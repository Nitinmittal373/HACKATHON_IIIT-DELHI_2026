"""Placeholders for sources that are not connected yet.

They let a check run end to end today: each one reports itself as
unavailable, so its checks stay unread and confidence shows the gap.
"""

from collections.abc import AsyncIterator

from app.models import CheckKey, SourceName
from app.sources.base import SourceContext, SourceEvent, SourceUnavailable


class NotConnected:
    def __init__(self, name: SourceName, checks: tuple[CheckKey, ...]) -> None:
        self.name = name
        self.checks = checks

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        raise SourceUnavailable("Not connected yet, so this source was not read")
        yield  # makes this an async generator, like every other source
