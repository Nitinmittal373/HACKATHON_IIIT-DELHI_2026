"""The only module that talks to TinyFish.

Sources depend on the small WebClient protocol, so tests can replay recorded
responses through a fake client and never touch the network.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, SecretStr
from tinyfish import (
    AgentConfig,
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncTinyFish,
    AuthenticationError,
    BadRequestError,
    CompleteEvent,
    PaymentRequiredError,
    ProgressEvent,
    RateLimitError,
    StreamingUrlEvent,
)

# The SDK's fetch call does not take selectors yet, so Fetch is called directly.
FETCH_URL = "https://api.fetch.tinyfish.ai/"


class WebError(RuntimeError):
    """A TinyFish call failed. The message is safe to show and never holds the key."""


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str
    site_name: str = ""
    # Publication date as the search engine reports it (news results); free-form text.
    date: str | None = None


class FetchedPage(BaseModel):
    url: str
    final_url: str
    html: str


class FetchedText(BaseModel):
    """A page or PDF turned into plain text by Fetch."""

    url: str
    final_url: str
    text: str


@dataclass(frozen=True)
class AgentLiveUrl:
    url: str


@dataclass(frozen=True)
class AgentProgress:
    text: str


@dataclass(frozen=True)
class AgentDone:
    status: str
    result: dict[str, Any] | None
    error: str | None = None


AgentEvent = AgentLiveUrl | AgentProgress | AgentDone


class WebClient(Protocol):
    async def search(
        self, query: str, *, purpose: str, domain_type: str | None = None
    ) -> list[SearchHit]: ...

    async def fetch_html(self, url: str, *, selectors: list[str], purpose: str) -> FetchedPage: ...

    async def fetch_text(self, url: str, *, purpose: str) -> FetchedText: ...

    def run_agent(
        self, *, url: str, goal: str, output_schema: dict[str, Any], max_steps: int
    ) -> AsyncIterator[AgentEvent]: ...

    async def aclose(self) -> None: ...


class LiveWebClient:
    def __init__(
        self,
        api_key: SecretStr,
        *,
        fetch_timeout: float,
        agent_timeout: float,
        send_max_steps: bool = False,
    ) -> None:
        self._key = api_key
        self._fetch_timeout = fetch_timeout
        self._agent_timeout = agent_timeout
        self._send_max_steps = send_max_steps
        self._sdk = AsyncTinyFish(api_key=api_key.get_secret_value(), timeout=fetch_timeout)
        self._http = httpx.AsyncClient(timeout=fetch_timeout + 15)

    def __repr__(self) -> str:
        # The SDK client's repr shows part of the key; never let it reach a log.
        return "LiveWebClient()"

    async def search(
        self, query: str, *, purpose: str, domain_type: str | None = None
    ) -> list[SearchHit]:
        try:
            response = await self._sdk.search.query(
                query, purpose=purpose, domain_type=domain_type
            )
        except APIError as error:
            raise WebError(f"Search failed: {describe(error)}") from None
        return [SearchHit.model_validate(hit.model_dump()) for hit in response.results]

    async def fetch_html(self, url: str, *, selectors: list[str], purpose: str) -> FetchedPage:
        body = self._fetch_body(url, "html", purpose) | {
            "include_selectors": [",".join(selectors)]
        }
        final_url, html = await self._fetch(body)
        return FetchedPage(url=url, final_url=final_url or url, html=html)

    async def fetch_text(self, url: str, *, purpose: str) -> FetchedText:
        """Plain text of a page or PDF, for lists that are published as documents."""
        final_url, text = await self._fetch(self._fetch_body(url, "markdown", purpose))
        return FetchedText(url=url, final_url=final_url or url, text=text)

    def _fetch_body(self, url: str, fmt: str, purpose: str) -> dict[str, Any]:
        return {
            "urls": [url],
            "format": fmt,
            "ttl": 0,
            "per_url_timeout_ms": int(self._fetch_timeout * 1000),
            "purpose": purpose,
        }

    async def _fetch(self, body: dict[str, Any]) -> tuple[str, str]:
        headers = {"X-API-Key": self._key.get_secret_value()}
        try:
            response = await self._http.post(FETCH_URL, json=body, headers=headers)
        except httpx.TimeoutException:
            raise WebError("Fetch failed: TinyFish did not answer in time") from None
        except httpx.HTTPError:
            raise WebError("Fetch failed: could not reach TinyFish") from None
        if response.status_code != 200:
            raise WebError(f"Fetch failed: TinyFish answered HTTP {response.status_code}")
        payload = response.json()
        results = payload.get("results") or []
        if payload.get("errors") or not results or not results[0].get("text"):
            raise WebError("Fetch failed: the page could not be read")
        return results[0].get("final_url") or "", results[0]["text"]

    async def run_agent(
        self, *, url: str, goal: str, output_schema: dict[str, Any], max_steps: int
    ) -> AsyncIterator[AgentEvent]:
        config = AgentConfig(
            max_steps=max_steps if self._send_max_steps else None,
            max_duration_seconds=int(self._agent_timeout),
        )
        try:
            async with self._sdk.agent.stream(
                goal=goal, url=url, output_schema=output_schema, agent_config=config
            ) as stream:
                async for event in stream:
                    if isinstance(event, StreamingUrlEvent):
                        yield AgentLiveUrl(event.streaming_url)
                    elif isinstance(event, ProgressEvent):
                        yield AgentProgress(event.purpose)
                    elif isinstance(event, CompleteEvent):
                        error = event.error.message if event.error else None
                        yield AgentDone(str(event.status), event.result_json, error)
        except APIError as error:
            raise WebError(f"Agent run failed: {describe(error)}") from None

    async def aclose(self) -> None:
        await self._http.aclose()
        await self._sdk.close()


def describe(error: APIError) -> str:
    if isinstance(error, AuthenticationError):
        return "TinyFish rejected the API key (check TINYFISH_API_KEY)"
    if isinstance(error, PaymentRequiredError):
        return "the TinyFish account has no credit left"
    if isinstance(error, BadRequestError):
        # The reason is about our request (for example the output schema), never the key.
        return f"TinyFish rejected the request: {str(error)[:200]}"
    if isinstance(error, RateLimitError):
        return "TinyFish rate limit reached, try again shortly"
    if isinstance(error, APITimeoutError):
        return "TinyFish did not answer in time"
    if isinstance(error, APIConnectionError):
        return "could not reach TinyFish"
    return f"TinyFish returned an error ({type(error).__name__})"
