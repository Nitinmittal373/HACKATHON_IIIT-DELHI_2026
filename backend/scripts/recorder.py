"""Wrap a WebClient and remember every answer, so one live check can become a test fixture.

Only what the agent sources need is kept: search results, document text and
agent runs. UP-RERA pages are stored by the page-fixture part of
capture_fixtures.py. Everything is scrubbed before it is written.
"""

import re
from collections.abc import AsyncIterator
from typing import Any

from app.tinyfish import (
    AgentDone,
    AgentEvent,
    AgentLiveUrl,
    AgentProgress,
    FetchedPage,
    FetchedText,
    SearchHit,
    WebClient,
    WebError,
)

# Search snippets sometimes break an address as "name @host.com", so allow a space around the @.
EMAIL = re.compile(r"[\w.+-]+\s?@\s?[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
# The live browser address can carry a session token, so only its host is kept.
LIVE_URL_PLACEHOLDER = "https://live.tinyfish.example/session"


def scrub(text: str) -> str:
    return PHONE.sub("[phone]", EMAIL.sub("[email]", text))


class RecordingWebClient:
    def __init__(self, inner: WebClient) -> None:
        self._inner = inner
        self.searches: list[dict[str, Any]] = []
        self.texts: dict[str, str] = {}
        # UP-RERA pages read by group projects, which no fixture file holds beforehand.
        self.pages: dict[str, str] = {}
        self.unreadable: list[str] = []
        self.agents: list[dict[str, Any]] = []

    async def search(
        self,
        query: str,
        *,
        purpose: str,
        domain_type: str | None = None,
        include_domains: str | None = None,
    ) -> list[SearchHit]:
        hits = await self._inner.search(
            query, purpose=purpose, domain_type=domain_type, include_domains=include_domains
        )
        self.searches.append(
            {
                "query": query,
                "domain_type": domain_type,
                "include_domains": include_domains,
                "results": [hit.model_dump(exclude_none=True) for hit in hits],
            }
        )
        return hits

    async def fetch_html(self, url: str, *, selectors: list[str], purpose: str) -> FetchedPage:
        page = await self._inner.fetch_html(url, selectors=selectors, purpose=purpose)
        self.pages[url] = page.html
        return page

    async def fetch_text(self, url: str, *, purpose: str) -> FetchedText:
        try:
            page = await self._inner.fetch_text(url, purpose=purpose)
        except WebError:
            self.unreadable.append(url)
            raise
        self.texts[url] = page.text
        return page

    async def run_agent(
        self, *, url: str, goal: str, output_schema: dict[str, Any], max_steps: int
    ) -> AsyncIterator[AgentEvent]:
        events: list[dict[str, Any]] = []
        self.agents.append({"url": url, "events": events})
        async for event in self._inner.run_agent(
            url=url, goal=goal, output_schema=output_schema, max_steps=max_steps
        ):
            events.append(describe_event(event))
            yield event

    async def aclose(self) -> None:
        await self._inner.aclose()

    def recording(self) -> dict[str, Any]:
        return {
            "searches": self.searches,
            "texts": self.texts,
            "pages": self.pages,
            "unreadable": self.unreadable,
            "agents": self.agents,
        }


def describe_event(event: AgentEvent) -> dict[str, Any]:
    if isinstance(event, AgentLiveUrl):
        return {"type": "live_url", "url": LIVE_URL_PLACEHOLDER}
    if isinstance(event, AgentProgress):
        return {"type": "progress", "text": event.text}
    assert isinstance(event, AgentDone)
    return {"type": "done", "status": event.status, "result": event.result, "error": event.error}
