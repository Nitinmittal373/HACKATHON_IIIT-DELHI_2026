"""TinyFish Monitors for a watched project: a page monitor on its UP-RERA page and a topic
monitor on news about the builder. Each calls our webhook, which re-checks the project."""

import logging
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import SecretStr
from tinyfish import APIError, AsyncTinyFish

logger = logging.getLogger(__name__)

MonitorKind = Literal["page", "topic"]
# Once a day: the shortest interval TinyFish allows is 30 minutes, but every check is billed.
DAILY_CRON = "0 3 * * *"
PAGE_PURPOSE = (
    "Alert if the completion date changes, a new extension or penalty order appears, "
    "or the registration status changes"
)
TOPIC_PURPOSE = "Alert if a new homebuyer protest or NCLT insolvency story appears"


@dataclass(frozen=True)
class CreatedMonitor:
    monitor_id: str
    kind: MonitorKind


class MonitorGateway(Protocol):
    async def create_page_monitor(self, url: str, webhook_url: str) -> CreatedMonitor: ...

    async def create_topic_monitor(self, builder: str, webhook_url: str) -> CreatedMonitor: ...

    async def cancel(self, monitor_id: str) -> None: ...

    async def aclose(self) -> None: ...


class MonitorError(RuntimeError):
    """A monitor call failed. The message is safe to log and never holds the key."""


class TinyFishMonitors:
    def __init__(self, api_key: SecretStr, *, timeout: float) -> None:
        self._sdk = AsyncTinyFish(api_key=api_key.get_secret_value(), timeout=timeout)

    def __repr__(self) -> str:
        return "TinyFishMonitors()"

    async def create_page_monitor(self, url: str, webhook_url: str) -> CreatedMonitor:
        return await self._create(
            "fetch", {"url": url, "format": "markdown"}, PAGE_PURPOSE, webhook_url, "page"
        )

    async def create_topic_monitor(self, builder: str, webhook_url: str) -> CreatedMonitor:
        query = f'"{builder}" homebuyers protest OR NCLT'
        return await self._create(
            "search", {"query": query, "recency_minutes": 1440}, TOPIC_PURPOSE, webhook_url, "topic"
        )

    async def _create(
        self,
        kind: Literal["fetch", "search"],
        config: dict[str, object],
        purpose: str,
        webhook_url: str,
        label: MonitorKind,
    ) -> CreatedMonitor:
        try:
            created = await self._sdk.monitors.create(
                kind,
                config,
                DAILY_CRON,
                name=f"NeevCheck {label}",
                webhook_url=webhook_url,
                purpose=purpose,
            )
        except APIError as error:
            raise MonitorError(f"Monitor not created ({type(error).__name__})") from None
        return CreatedMonitor(created.monitor.id, label)

    async def cancel(self, monitor_id: str) -> None:
        try:
            await self._sdk.monitors.cancel(monitor_id)
        except APIError as error:
            raise MonitorError(f"Monitor not cancelled ({type(error).__name__})") from None

    async def aclose(self) -> None:
        await self._sdk.close()
