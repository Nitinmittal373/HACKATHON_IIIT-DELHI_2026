"""A WebClient that replays responses recorded by scripts/capture_fixtures.py."""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.tinyfish import (
    AgentDone,
    AgentEvent,
    AgentLiveUrl,
    AgentProgress,
    FetchedPage,
    FetchedText,
    SearchHit,
    WebError,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_search(name: str) -> list[SearchHit]:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [SearchHit.model_validate(hit) for hit in payload["results"]]


def load_page(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def load_recording(name: str) -> dict[str, Any]:
    """A live check recorded by scripts/capture_fixtures.py."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def agent_event(raw: dict[str, Any]) -> AgentEvent:
    match raw["type"]:
        case "live_url":
            return AgentLiveUrl(raw["url"])
        case "progress":
            return AgentProgress(raw["text"])
        case _:
            return AgentDone(raw["status"], raw["result"], raw["error"])


class FakeWebClient:
    def __init__(
        self,
        searches: dict[str, list[SearchHit]] | None = None,
        pages: dict[str, str] | None = None,
        agent_runs: dict[str, list[AgentEvent]] | None = None,
        texts: dict[str, str] | None = None,
    ) -> None:
        self.searches = searches or {}
        self.pages = pages or {}
        self.texts = texts or {}
        self.agent_runs = agent_runs or {}
        self.calls: list[tuple[str, str]] = []
        self.agent_requests: list[dict[str, Any]] = []

    async def search(
        self, query: str, *, purpose: str, domain_type: str | None = None
    ) -> list[SearchHit]:
        self.calls.append(("search", query))
        return self.searches.get(query, [])

    async def fetch_html(self, url: str, *, selectors: list[str], purpose: str) -> FetchedPage:
        self.calls.append(("fetch", url))
        if url not in self.pages:
            raise WebError("Fetch failed: the page could not be read")
        return FetchedPage(url=url, final_url=url, html=self.pages[url])

    async def fetch_text(self, url: str, *, purpose: str) -> FetchedText:
        self.calls.append(("fetch_text", url))
        if url not in self.texts:
            raise WebError("Fetch failed: the page could not be read")
        return FetchedText(url=url, final_url=url, text=self.texts[url])

    def replay(self, recording: dict[str, Any]) -> "FakeWebClient":
        """Add the searches, documents and agent runs of a recorded live check."""
        for search in recording["searches"]:
            hits = [SearchHit.model_validate(raw) for raw in search["results"]]
            self.searches.setdefault(search["query"], hits)
        self.texts |= recording["texts"]
        for run in recording["agents"]:
            self.agent_runs[run["url"]] = [agent_event(raw) for raw in run["events"]]
        return self

    async def run_agent(
        self, *, url: str, goal: str, output_schema: dict[str, Any], max_steps: int
    ) -> AsyncIterator[AgentEvent]:
        self.calls.append(("agent", url))
        self.agent_requests.append({"url": url, "goal": goal, "output_schema": output_schema})
        for event in self.agent_runs.get(url, []):
            yield event

    async def aclose(self) -> None:
        return None
