"""What every state adapter looks like, and the one record they all produce.

Scoring reads only a ProjectRecord and the national sources, so it works for every state
unchanged. A state adapter's job is to turn that state's public pages into this record, and
to say honestly how much of it could be read.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Protocol

from pydantic import BaseModel

from app.models import Project
from app.tinyfish import WebClient

# full: Fetch and a parser read every field. partial: Fetch reads the page, some fields only.
# search_only: the portal cannot be fetched, so only what Search returns from its own pages.
Coverage = Literal["full", "partial", "search_only"]


class Extension(BaseModel):
    extended_to: date | None = None
    granted_on: date | None = None
    reason: str | None = None


class ProjectRecord(BaseModel):
    """One project as a state RERA shows it. A field the page did not show stays None."""

    state: str
    rera_id: str
    name: str | None = None
    promoter_name: str | None = None
    promoter_id: str | None = None
    district: str | None = None
    registration_date: date | None = None
    promised_completion: date | None = None
    revised_completion: date | None = None
    extensions: list[Extension] = []
    status: str | None = None
    complaints_count: int | None = None
    units: int | None = None
    source_url: str
    read_on: date
    read_at: datetime
    # The exact words each fact came from, for the evidence ledger.
    raw_snippets: list[str] = []
    # "search_snippet" when no page was opened and the facts came from Search result text.
    read_via: Literal["search_snippet"] | None = None

    @property
    def latest_completion(self) -> date | None:
        dates = [d for d in (self.promised_completion, self.revised_completion) if d]
        dates += [e.extended_to for e in self.extensions if e.extended_to]
        return max(dates, default=None)


@dataclass(frozen=True)
class StateSpec:
    """The facts about one state's portal, as recorded in docs/states.md."""

    code: str
    name: str
    rera_name: str
    domains: tuple[str, ...]
    # Unanchored patterns for the registration number; a number matches if one fullmatches it.
    id_patterns: tuple[str, ...]
    coverage: Coverage
    # Real numbers read from the portal, for the search box's try-chips. May be empty.
    examples: tuple[str, ...]
    complaint_url: str
    # Where a buyer reports a project that should be registered and is not; the complaint page
    # when the authority has no separate form.
    unregistered_url: str = ""
    # Where a project's page lives when its address can be built from the number alone.
    details_template: str | None = None
    # The portal's own search page, used when no project page is known.
    search_url: str = ""
    # Names that identify the authority in a search query ("MahaRERA project").
    query_name: str = ""
    # What NeevCheck can and cannot read here, in a sentence, for the coverage page.
    note: str = ""
    # A pattern with named groups (name, promoter, district) for snippets that list values
    # by position instead of by label.
    positional: str | None = None
    # Part of the address of the pages that print values in that order.
    positional_in: str = ""
    # Name of a parser (app.states.lists) for the project list that Fetch can read.
    row_parser: str | None = None
    # More (address part, pattern) pairs for other pages that print values by position.
    extra_positional: tuple[tuple[str, str], ...] = ()
    # How sure a number that fits the pattern is to belong to this state, when formats overlap.
    detect_confidence: float = 0.9
    unverified_format: bool = field(default=False)

    @property
    def patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(p, re.IGNORECASE) for p in self.id_patterns]


class StateAdapter(Protocol):
    code: str
    name: str
    rera_name: str
    domains: tuple[str, ...]
    id_patterns: tuple[str, ...]
    coverage: Coverage
    examples: tuple[str, ...]
    complaint_url: str
    unregistered_url: str
    search_url: str
    note: str
    unverified_format: bool

    def detect(self, query: str) -> float:
        """0 when the text is not this state's number; up to 1 when it surely is."""
        ...

    def canonical_id(self, query: str) -> str | None:
        """The number as the portal prints it, or None when the text is not a number."""
        ...

    def details_url(self, project: Project) -> str:
        """Where the project's page is, or the portal's search page when none is known."""
        ...

    async def resolve(self, query: str, web: WebClient) -> list[Project]: ...

    async def read(self, project: Project, web: WebClient, now: datetime) -> ProjectRecord | None:
        """The project as the portal shows it, or None when no portal page names it."""
        ...
