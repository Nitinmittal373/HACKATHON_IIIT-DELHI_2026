"""Shared runner for sources read by a TinyFish browser agent.

A subclass says where to start, what to look for and how to turn the
agent's JSON into findings. This class handles the rest the same way for
every source:

- the live browser URL and each step are streamed to the Agent Cam
- a CAPTCHA or bot check stops the run and marks the source blocked
- a run that fails, or completes with nothing in it, leaves the source
  unread (lower confidence) instead of being treated as a clean record
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from app.models import CheckKey, Finding, SourceName
from app.sources.base import (
    Blocked,
    ChecksRead,
    FoundFinding,
    LiveUrl,
    Progress,
    SourceContext,
    SourceError,
    SourceEvent,
)
from app.tinyfish import AgentDone, AgentLiveUrl, AgentProgress

CAPTCHA_FIELD = "captcha_seen"
CAPTCHA_RULE = (
    " If the site shows a CAPTCHA, a login wall or any other bot check, stop at once,"
    f" do not try to solve or get around it, and set {CAPTCHA_FIELD} to true."
)


@dataclass(frozen=True)
class AgentTask:
    url: str
    goal: str
    output_schema: dict[str, Any]
    max_steps: int = 40


class AgentSource(ABC):
    name: SourceName
    checks: tuple[CheckKey, ...]

    @abstractmethod
    def task(self, ctx: SourceContext) -> AgentTask:
        """Where the agent starts (a deep page, never a big homepage) and what it returns."""

    @abstractmethod
    def to_findings(self, result: dict[str, Any], ctx: SourceContext) -> list[Finding]:
        """Turn the agent's JSON into findings; every one needs its own source URL."""

    def checks_read(self, result: dict[str, Any]) -> tuple[CheckKey, ...]:
        return self.checks

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        task = self.task(ctx)
        yield Progress(f"Opening {urlsplit(task.url).hostname}")
        done: AgentDone | None = None
        async for event in ctx.web.run_agent(
            url=task.url,
            goal=task.goal + CAPTCHA_RULE,
            output_schema=with_captcha_field(task.output_schema),
            max_steps=task.max_steps,
        ):
            if isinstance(event, AgentLiveUrl):
                yield LiveUrl(event.url)
            elif isinstance(event, AgentProgress):
                yield Progress(event.text)
            else:
                done = event

        if done is None:
            raise SourceError("The agent stopped without an answer")
        if done.status != "COMPLETED":
            reason = f": {done.error}" if done.error else ""
            raise SourceError(f"The agent run ended as {done.status.lower()}{reason}")
        result = done.result or {}
        if result.get(CAPTCHA_FIELD):
            yield Blocked("The site asked for a CAPTCHA, which NeevCheck never bypasses")
            return
        if is_empty(result):
            yield Progress("The agent found nothing it could read, so this source stays unread")
            return
        for finding in self.to_findings(result, ctx):
            yield FoundFinding(finding)
        yield ChecksRead(self.checks_read(result))


def with_captcha_field(schema: dict[str, Any]) -> dict[str, Any]:
    properties = {**schema.get("properties", {}), CAPTCHA_FIELD: {"type": "boolean"}}
    required = [*schema.get("required", []), CAPTCHA_FIELD]
    return {**schema, "type": "object", "properties": properties, "required": required}


def is_empty(result: dict[str, Any]) -> bool:
    """A blocked or confused run often 'completes' with every field null or empty."""
    values = [value for key, value in result.items() if key != CAPTCHA_FIELD]
    return all(value in (None, "", [], {}) for value in values)
