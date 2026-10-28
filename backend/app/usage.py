"""Counts the TinyFish calls one check makes, and stops them when credit runs out.

The counts are saved on the check, so the operator can learn what a check really costs
(GET /api/admin/usage). When a call fails because the account is out of credit or rate
limited, no further call is made for that check: another try would only spend more.
"""

from collections.abc import AsyncIterator
from typing import Any

from app.tinyfish import AgentEvent, FetchedPage, FetchedText, SearchHit, WebClient, WebError

PAUSED_MESSAGE = "Paused: live-check credits are low"
# Failures that mean "stop calling TinyFish", as opposed to one page that could not be read.
CREDIT_CODES = ("wallet_empty", "rate_limited")


class Usage:
    def __init__(self) -> None:
        self.search = 0
        self.fetch = 0
        self.agent = 0
        self.paused: WebError | None = None

    def as_dict(self) -> dict[str, int]:
        return {"search": self.search, "fetch": self.fetch, "agent": self.agent}

    def note(self, error: WebError) -> None:
        if error.code in CREDIT_CODES and self.paused is None:
            self.paused = error

    def check_open(self) -> None:
        """Refuse a call once credit ran out, without touching TinyFish."""
        if self.paused is not None:
            raise WebError(PAUSED_MESSAGE, self.paused.code, self.paused.retry_after)


class MeteredWeb:
    """A WebClient that counts what it forwards to the real one."""

    def __init__(self, web: WebClient, usage: Usage) -> None:
        self._web = web
        self.usage = usage

    async def search(
        self,
        query: str,
        *,
        purpose: str,
        domain_type: str | None = None,
        include_domains: str | None = None,
    ) -> list[SearchHit]:
        self.usage.check_open()
        self.usage.search += 1
        try:
            return await self._web.search(
                query, purpose=purpose, domain_type=domain_type, include_domains=include_domains
            )
        except WebError as error:
            self.usage.note(error)
            raise

    async def fetch_html(self, url: str, *, selectors: list[str], purpose: str) -> FetchedPage:
        self.usage.check_open()
        self.usage.fetch += 1
        try:
            return await self._web.fetch_html(url, selectors=selectors, purpose=purpose)
        except WebError as error:
            self.usage.note(error)
            raise

    async def fetch_text(self, url: str, *, purpose: str) -> FetchedText:
        self.usage.check_open()
        self.usage.fetch += 1
        try:
            return await self._web.fetch_text(url, purpose=purpose)
        except WebError as error:
            self.usage.note(error)
            raise

    async def run_agent(
        self, *, url: str, goal: str, output_schema: dict[str, Any], max_steps: int
    ) -> AsyncIterator[AgentEvent]:
        self.usage.check_open()
        self.usage.agent += 1
        try:
            async for event in self._web.run_agent(
                url=url, goal=goal, output_schema=output_schema, max_steps=max_steps
            ):
                yield event
        except WebError as error:
            self.usage.note(error)
            raise

    async def aclose(self) -> None:
        """The wrapped client is shared and closed by the app, never by one check."""
