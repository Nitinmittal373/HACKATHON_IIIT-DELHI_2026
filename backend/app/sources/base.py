"""What every source looks like to the orchestrator.

A source reads one kind of public record and yields small events. It never
touches the database or the event stream; the orchestrator does that, so a
source is easy to test with a fake WebClient.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from app.models import CheckKey, Finding, Project, SourceName
from app.tinyfish import WebClient


class SourceError(RuntimeError):
    """The source could not be read. The message is shown to the buyer."""


class SourceUnavailable(SourceError):
    """The source is not connected yet; its checks stay unread."""


@dataclass(frozen=True)
class SourceContext:
    project: Project
    web: WebClient
    today: date
    now: datetime
    check_id: str = ""
    # Where raw agent answers are saved for debugging; None keeps nothing on disk.
    cache_dir: Path | None = None


@dataclass(frozen=True)
class Progress:
    text: str


@dataclass(frozen=True)
class LiveUrl:
    url: str


@dataclass(frozen=True)
class FoundFinding:
    finding: Finding


@dataclass(frozen=True)
class Blocked:
    reason: str


@dataclass(frozen=True)
class ChecksRead:
    checks: tuple[CheckKey, ...]


@dataclass(frozen=True)
class ProjectDetails:
    """The source learned more about the project (name, promoter, district)."""

    project: Project


SourceEvent = Progress | LiveUrl | FoundFinding | Blocked | ChecksRead | ProjectDetails


class Source(Protocol):
    name: SourceName
    # The key checks this source can read; any it does not confirm stay unread.
    checks: tuple[CheckKey, ...]

    def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]: ...
