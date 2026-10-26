"""The adapter for every state whose portal Fetch cannot read well.

It finds a project with TinyFish Search limited to the state's own domains and reads the
facts the portal's pages show in their search snippets (and, for a "partial" state, the page
itself). Whatever a snippet does not show stays None, so a thin read lowers confidence
instead of inventing a fact.
"""

import asyncio
import re
from dataclasses import dataclass, fields
from datetime import date, datetime
from urllib.parse import quote, urlsplit

from app.models import Project
from app.states.base import ProjectRecord, StateSpec
from app.states.lists import ROW_PARSERS
from app.states.text import (
    DISTRICT_LABELS,
    IST,
    NAME_LABELS,
    PROMISED_LABELS,
    PROMOTER_LABELS,
    REGISTERED_LABELS,
    REVISED_LABELS,
    STATUS_LABELS,
    clean,
    id_segments,
    labelled_date,
    labelled_text,
    rank,
    squash,
)
from app.tinyfish import SearchHit, WebClient, WebError

MAX_CANDIDATES = 8
SEARCH_PURPOSE = "Find a housing project on a state RERA portal for a homebuyer who named it"


@dataclass(frozen=True)
class Facts:
    name: str | None = None
    promoter: str | None = None
    district: str | None = None
    registered_on: date | None = None
    promised: date | None = None
    revised: date | None = None
    status: str | None = None

    def count(self) -> int:
        return sum(getattr(self, f.name) is not None for f in fields(self))

    def fill_gaps_from(self, other: "Facts") -> "Facts":
        merged = {f.name: getattr(self, f.name) or getattr(other, f.name) for f in fields(self)}
        return Facts(**merged)


class SearchStateAdapter:
    def __init__(self, spec: StateSpec) -> None:
        self.spec = spec
        self.code = spec.code
        self.name = spec.name
        self.rera_name = spec.rera_name
        self.domains = spec.domains
        self.id_patterns = spec.id_patterns
        self.coverage = spec.coverage
        self.examples = spec.examples
        self.complaint_url = spec.complaint_url
        self.search_url = spec.search_url
        self.note = spec.note
        self._patterns = spec.patterns

    def detect(self, query: str) -> float:
        return self.spec.detect_confidence if self.canonical_id(query) else 0.0

    def canonical_id(self, query: str) -> str | None:
        text = re.sub(r"\s+", " ", clean(query)).upper()
        for candidate in (text, text.replace(" ", "")):
            if any(pattern.fullmatch(candidate) for pattern in self._patterns):
                return candidate
        return None

    def details_url(self, project: Project) -> str:
        return self._page_for(project.rera_id, project.details_url or self.spec.search_url)

    async def resolve(self, query: str, web: WebClient) -> list[Project]:
        rera_id = self.canonical_id(query)
        hits = await self._search(f"{rera_id or query} {self.spec.query_name} project", web)
        candidates = self.candidates_from_hits(hits)
        if rera_id:
            return [p for p in candidates if squash(p.rera_id) == squash(rera_id)][:1]
        return rank(candidates, query)[:MAX_CANDIDATES]

    async def read(self, project: Project, web: WebClient, now: datetime) -> ProjectRecord | None:
        wanted = squash(project.rera_id)
        # Search shows the passages that match the words asked: the bare number finds the
        # portal's page for it, the other wordings bring up dates and the promoter.
        queries = [
            project.rera_id,
            f"{project.rera_id} {self.spec.query_name} project",
            f"{project.rera_id} promoter completion date status",
        ]
        found = await asyncio.gather(*(self._search(q, web) for q in queries))
        hits = [hit for group in found for hit in group]
        evidence = [
            (h.url, clean(f"{h.title}. {h.snippet}")) for h in hits if self._names(h, wanted)
        ]
        opened = await self._fetched_page(project, evidence, web)
        evidence += opened
        if not evidence:
            return None
        facts = Facts()
        best_url, best_count = evidence[0][0], -1
        raw: list[str] = []
        for url, text in evidence:
            segment = self._segment_for(text, wanted)
            found = self._facts(segment, url)
            if found.count() > best_count:
                best_url, best_count = url, found.count()
            facts = facts.fill_gaps_from(found)
            raw.append(segment[:300])
        return ProjectRecord(
            state=self.code,
            rera_id=project.rera_id,
            name=facts.name,
            promoter_name=facts.promoter,
            district=facts.district,
            registration_date=facts.registered_on,
            promised_completion=facts.promised,
            revised_completion=facts.revised,
            status=facts.status,
            source_url=best_url,
            read_on=now.astimezone(IST).date(),
            read_at=now,
            raw_snippets=raw[:3],
            read_via=None if opened else "search_snippet",
        )

    async def _search(self, query: str, web: WebClient) -> list[SearchHit]:
        return await web.search(
            query, purpose=SEARCH_PURPOSE, include_domains=",".join(self.domains)
        )

    async def _fetched_page(
        self, project: Project, evidence: list[tuple[str, str]], web: WebClient
    ) -> list[tuple[str, str]]:
        """The project's own page, or its row in a list page, for states Fetch can read."""
        if self.spec.row_parser:
            return await self._list_row(project, web)
        if self.coverage == "search_only" or not evidence:
            return []
        url = evidence[0][0]
        try:
            page = await web.fetch_text(url, purpose="Read a state RERA project page")
        except WebError:
            return []
        text = clean(page.text)
        return [(url, text)] if squash(project.rera_id) in squash(text) else []

    async def _list_row(self, project: Project, web: WebClient) -> list[tuple[str, str]]:
        url = self.spec.search_url
        try:
            page = await web.fetch_text(url, purpose="Read a state RERA list of projects")
        except WebError:
            return []
        row = ROW_PARSERS[self.spec.row_parser or ""](page.text, project.rera_id)
        return [(url, row)] if row else []

    def _on_portal(self, url: str) -> bool:
        host = urlsplit(url).hostname or ""
        return any(host == d or host.endswith("." + d) for d in self.domains)

    def _names(self, hit: SearchHit, wanted: str) -> bool:
        text = squash(f"{hit.title} {hit.snippet} {hit.url}")
        return self._on_portal(hit.url) and wanted in text

    def _segment_for(self, text: str, wanted: str) -> str:
        """The longest stretch of text after this project's number (a title may repeat it)."""
        mine = [s for rera_id, s in id_segments(text, self._patterns) if squash(rera_id) == wanted]
        return max(mine, key=len, default=text)

    def _facts(self, text: str, url: str) -> Facts:
        by_position = self._positional(text, url)
        return Facts(
            name=by_position.name or labelled_text(text, NAME_LABELS),
            promoter=by_position.promoter or labelled_text(text, PROMOTER_LABELS),
            district=by_position.district or labelled_text(text, DISTRICT_LABELS),
            registered_on=labelled_date(text, REGISTERED_LABELS),
            promised=labelled_date(text, PROMISED_LABELS),
            revised=labelled_date(text, REVISED_LABELS),
            status=labelled_text(text, STATUS_LABELS),
        )

    def _positional(self, text: str, url: str) -> Facts:
        # Orders and lists print the same values in other orders, so only the portal's own
        # project pages are read by position.
        on_project_page = self.spec.positional_in in url
        found = re.search(self.spec.positional, text) if self.spec.positional else None
        found = found if on_project_page else None
        if found is None:
            return Facts()
        groups = found.groupdict()
        return Facts(
            name=groups.get("name"),
            promoter=groups.get("promoter"),
            district=groups.get("district"),
        )

    def candidates_from_hits(self, hits: list[SearchHit]) -> list[Project]:
        by_id: dict[str, Project] = {}
        for hit in hits:
            if not self._on_portal(hit.url) or hit.url.lower().endswith(".pdf"):
                continue
            text = clean(f"{hit.title}. {hit.snippet}")
            for rera_id, segment in id_segments(text, self._patterns):
                facts = self._facts(segment, hit.url)
                candidate = Project(
                    state=self.code,
                    rera_id=rera_id,
                    name=facts.name,
                    promoter=facts.promoter,
                    district=facts.district,
                    registered_on=facts.registered_on,
                    details_url=self._page_for(rera_id, hit.url),
                )
                known = by_id.get(rera_id)
                by_id[rera_id] = _merged(known, candidate) if known else candidate
        return list(by_id.values())

    def _page_for(self, rera_id: str, fallback: str) -> str:
        template = self.spec.details_template
        return template.format(id=quote(rera_id, safe="/")) if template else fallback


def _merged(known: Project, other: Project) -> Project:
    gaps = {k: v for k, v in other.model_dump().items() if getattr(known, k) is None}
    return known.model_copy(update=gaps)
