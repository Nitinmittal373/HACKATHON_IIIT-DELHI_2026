"""Shared runner for sources read by a TinyFish browser agent.

A subclass says where to start, what to look for and how to turn the
agent's JSON into findings. This class handles the rest the same way for
every source:

- the live browser URL and each step are streamed to the Agent Cam
- a CAPTCHA or bot check stops the run and marks the source blocked
- a run that fails, or completes with nothing in it, leaves the source
  unread (lower confidence) instead of being treated as a clean record
- a run that runs out of time is marked blocked as "timeout" and never retried
- the raw answer is saved under data/cache/{check_id}/ so a surprising
  finding can be traced back to what the agent actually returned
"""

import json
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
CAPTCHA_REASON = "This page asks for a CAPTCHA. We never bypass one"
MAX_PROGRESS_CHARS = 140
TIMEOUT_REASON = "timeout"
TIMEOUT_HINTS = ("timeout", "timed out", "time limit", "max duration", "duration")
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

    # Shown in the Agent Cam when task() finds no page worth opening.
    no_task_message = "No matching page was found, so this source stays unread"

    @abstractmethod
    async def task(self, ctx: SourceContext) -> AgentTask | None:
        """Where the agent starts (a deep page, never a big homepage) and what it returns.

        None means no trustworthy start page was found; the source then stays unread.
        """

    @abstractmethod
    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        """Turn the agent's JSON into findings; every one needs its own source URL."""

    async def read_directly(self, task: AgentTask, ctx: SourceContext) -> dict[str, Any] | None:
        """Read the page without a browser when plain Fetch is enough (free and repeatable).

        Return the same shape the agent would, or None to let the agent do it.
        """
        return None

    def checks_read(self, result: dict[str, Any], ctx: SourceContext) -> tuple[CheckKey, ...]:
        """The key checks this answer actually settles; the default is all of them."""
        return self.checks

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        task = await self.task(ctx)
        if task is None:
            yield Progress(self.no_task_message)
            return
        yield Progress(f"Opening {urlsplit(task.url).hostname}")
        direct = await self.read_directly(task, ctx)
        done: AgentDone | None = None
        if direct is not None:
            yield Progress("Read the page directly, no browser needed")
            done = AgentDone(status="COMPLETED", result=direct)
        else:
            async for event in ctx.web.run_agent(
                url=task.url,
                goal=task.goal + CAPTCHA_RULE,
                output_schema=with_captcha_field(task.output_schema),
                max_steps=task.max_steps,
            ):
                if isinstance(event, AgentLiveUrl):
                    yield LiveUrl(event.url)
                elif isinstance(event, AgentProgress):
                    yield Progress(short(event.text))
                else:
                    done = event

        if done is None:
            raise SourceError("The agent stopped without an answer")
        if done.status != "COMPLETED":
            if ran_out_of_time(done.error):
                yield Blocked(TIMEOUT_REASON)
                return
            reason = f": {done.error}" if done.error else ""
            raise SourceError(f"The agent run ended as {done.status.lower()}{reason}")
        result = done.result or {}
        save_raw(ctx, self.name, task.url, result)
        if result.get(CAPTCHA_FIELD):
            yield Blocked(CAPTCHA_REASON)
            return
        if is_empty(result):
            yield Progress("The agent found nothing it could read, so this source stays unread")
            return
        for finding in self.to_findings(result, ctx, task):
            yield FoundFinding(finding)
        yield ChecksRead(self.checks_read(result, ctx))


def short(text: str) -> str:
    """One calm line for the Agent Cam, however long the agent's note was."""
    line = " ".join(text.split())
    return line if len(line) <= MAX_PROGRESS_CHARS else line[: MAX_PROGRESS_CHARS - 1] + "…"


def ran_out_of_time(error: str | None) -> bool:
    return any(hint in (error or "").lower() for hint in TIMEOUT_HINTS)


def save_raw(ctx: SourceContext, source: str, start_url: str, result: dict[str, Any]) -> None:
    if ctx.cache_dir is None or not ctx.check_id:
        return
    folder = ctx.cache_dir / ctx.check_id
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"source": source, "start_url": start_url, "result": result}
    (folder / f"{source}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def with_captcha_field(schema: dict[str, Any]) -> dict[str, Any]:
    properties = {**schema.get("properties", {}), CAPTCHA_FIELD: {"type": "boolean"}}
    required = [*schema.get("required", []), CAPTCHA_FIELD]
    return {**schema, "type": "object", "properties": properties, "required": required}


def is_empty(result: dict[str, Any]) -> bool:
    """A blocked or confused run often 'completes' with every field null or empty."""
    values = [value for key, value in result.items() if key != CAPTCHA_FIELD]
    return all(value in (None, "", [], {}) for value in values)
