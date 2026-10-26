"""Group companies: the promoter's directors, charges, related companies and their projects.

Everything here is free Search and Fetch; no browser agent runs. The steps:
1. Read the promoter's public company profile (Tofler) for directors, charges and related companies.
2. Read each related company's registry status (at most MAX_COMPANIES).
3. List the UP-RERA projects of the promoter and of those companies (at most MAX_PROJECTS), read
   each project page, and count the ones delayed more than 12 months or lapsed.

A step that cannot be read leaves its facts out; absence of a record never adds points.
"""

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Iterable
from datetime import date, timedelta

from app.matching import blob, legal_name_in
from app.models import CheckKey, Finding, Project
from app.parsers.uprera_page import ParseError, UpreraRecord
from app.sources.base import (
    FoundFinding,
    Progress,
    SourceContext,
    SourceError,
    SourceEvent,
)
from app.sources.findings import build_finding
from app.sources.mca import CompanyProfile, is_this_company, parse_profile
from app.sources.registry import (
    IN_INSOLVENCY,
    parse_company_table,
    pick_company_page,
    readable_pages,
)
from app.sources.registry import (
    is_this_company as status_is_this_company,
)
from app.sources.uprera import months_between, read_record
from app.tinyfish import SearchHit, WebError
from app.track_record import TrackRecords

MAX_COMPANIES = 10
MAX_PROJECTS = 20
RECENT_CHARGE_DAYS = 365
DELAYED_AFTER_MONTHS = 12
PARALLEL_READS = 4
PROFILE_HOSTS = ("tofler.in",)
STRUCK_OFF = re.compile(r"strike|struck", re.IGNORECASE)
LAPSED = re.compile(r"lapse|revok", re.IGNORECASE)
SEARCH_PURPOSE = "Find a builder's public company profile and its related companies"
FETCH_PURPOSE = (
    "Read a builder's public company profile for directors, charges and related companies"
)


class GroupSource:
    name = "group"
    checks: tuple[CheckKey, ...] = ()

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        promoter = ctx.project.promoter
        if not promoter:
            raise SourceError("The promoter's name is not known, so its group cannot be looked up")

        yield Progress(f"Finding the public company profile of {promoter}")
        found = await self._profile(promoter, ctx)
        if found is None:
            raise SourceError("No public company profile with the promoter's exact name was read")
        profile, url = found

        for finding in profile_findings(profile, url, ctx):
            yield FoundFinding(finding)
        companies = list(profile.related_companies[:MAX_COMPANIES])
        yield Progress(f"Reading the registry status of {len(companies)} related companies")
        statuses = await _gather_limited(self._status(name, ctx) for name in companies)
        for finding in status_findings(statuses, ctx):
            yield FoundFinding(finding)

        yield Progress("Listing the UP-RERA projects of the group")
        projects = await self._group_projects(promoter, companies, ctx)
        yield Progress(f"Reading {len(projects)} group project pages on UP-RERA")
        reads = await _gather_limited(self._read(project, ctx) for project in projects)
        for finding in project_findings([r for r in reads if r], ctx):
            yield FoundFinding(finding)

    async def _profile(
        self, promoter: str, ctx: SourceContext
    ) -> tuple[CompanyProfile, str] | None:
        hits = await ctx.web.search(f"{promoter} tofler directors", purpose=SEARCH_PURPOSE)
        for hit in pages_named(hits, promoter):
            try:
                page = await ctx.web.fetch_text(hit.url, purpose=FETCH_PURPOSE)
            except WebError:
                continue
            profile = parse_profile(page.text)
            if is_this_company(profile, promoter) and profile.directors:
                return profile, hit.url
        return None

    async def _status(self, company: str, ctx: SourceContext) -> tuple[str, str, str] | None:
        """(company, registry status, page) when a page naming exactly this company shows one."""
        try:
            hits = await ctx.web.search(f"{company} company CIN status", purpose=SEARCH_PURPOSE)
            page = pick_company_page(hits, company)
            for url in readable_pages(page.url, company) if page else []:
                text = await ctx.web.fetch_text(url, purpose=FETCH_PURPOSE)
                found = parse_company_table(text.text)
                if found["status"] and status_is_this_company(found, company):
                    return company, found["status"], url
        except WebError:
            return None
        return None

    async def _group_projects(
        self, promoter: str, companies: list[str], ctx: SourceContext
    ) -> list[Project]:
        records = TrackRecords(ctx.web, lambda: ctx.now)
        own = ctx.project.rera_id
        try:
            found = await _gather_limited(
                records.find(name, own) for name in [promoter, *companies]
            )
        except WebError:
            return []
        seen: dict[str, Project] = {}
        for record in found:
            for project in record.projects if record else []:
                seen.setdefault(project.rera_id, project)
        return list(seen.values())[:MAX_PROJECTS]

    async def _read(
        self, project: Project, ctx: SourceContext
    ) -> tuple[Project, UpreraRecord] | None:
        try:
            record = await read_record(project.details_url, ctx.web)
        except (WebError, ParseError):
            return None
        return (project, record) if record.rera_id == project.rera_id else None


def pages_named(hits: list[SearchHit], promoter: str) -> list[SearchHit]:
    """Profile pages on a known mirror whose address or text holds the exact legal name."""
    return [
        hit
        for hit in hits
        if any(host in hit.url for host in PROFILE_HOSTS) and legal_name_in(promoter, blob(hit))
    ]


def profile_findings(profile: CompanyProfile, url: str, ctx: SourceContext) -> list[Finding]:
    """Directors by name and DIN only, and charges registered in the last 12 months."""

    def make(kind: str, title: str, verdict: str, **facts: object) -> Finding:
        return build_finding(
            source="group",
            reliability="secondary",
            kind=kind,
            area="financial",
            title=title,
            verdict=verdict,  # type: ignore[arg-type]
            url=url,
            today=ctx.today,
            now=ctx.now,
            **facts,
        )

    directors = "; ".join(f"{d.name} (DIN {d.din})" for d in profile.directors)
    findings = [
        make(
            "directors",
            f"{len(profile.directors)} directors on record for {profile.legal_name}",
            "context",
            snippet=directors[:300],
        )
    ]
    since = ctx.today - timedelta(days=RECENT_CHARGE_DAYS)
    recent = sorted(d for d in profile.charge_dates if since <= d <= ctx.today)
    if recent:
        times = "once" if len(recent) == 1 else f"{len(recent)} times"
        findings.append(
            make(
                "charge_created",
                f"A charge was registered {times} in the last 12 months; "
                f"latest on {recent[-1]:%d %b %Y}",
                "review",
                count=len(recent),
                occurred_on=recent[-1],
            )
        )
    return findings


def status_findings(
    statuses: list[tuple[str, str, str] | None], ctx: SourceContext
) -> list[Finding]:
    findings = []
    for entry in statuses:
        if entry is None:
            continue
        company, status, url = entry
        if IN_INSOLVENCY.search(status):
            kind, title = "group_company_insolvent", f"Related company {company}: status {status}"
        elif STRUCK_OFF.search(status):
            kind, title = "director_struck_off", f"Related company {company}: status {status}"
        else:
            continue
        findings.append(
            build_finding(
                source="group",
                reliability="secondary",
                kind=kind,
                area="financial",
                title=title,
                verdict="fail",
                url=url,
                today=ctx.today,
                now=ctx.now,
                snippet=f"Status: {status}",
            )
        )
    return findings


def project_findings(
    reads: list[tuple[Project, UpreraRecord]], ctx: SourceContext
) -> list[Finding]:
    """One finding per lapsed or delayed project, then the share of the group's projects delayed."""
    delayed = [(p, r) for p, r in reads if is_delayed(r, ctx.today)]
    lapsed = [(p, r) for p, r in reads if LAPSED.search(r.project_type or "")]
    findings = [
        _project_finding(
            "group_project_lapsed", p, r, f"UP-RERA lists {_name(p)} as '{r.project_type}'", ctx
        )
        for p, r in lapsed
    ]
    findings += [
        _project_finding(
            "group_project_delayed",
            p,
            r,
            f"{_name(p)}: completion date {_day(r.latest_end_date)} passed "
            f"{months_between(r.latest_end_date, ctx.today)} months ago, not completed",  # type: ignore[arg-type]
            ctx,
        )
        for p, r in delayed
    ]
    if reads and delayed:
        first = delayed[0][0]
        numbers = ", ".join(p.rera_id for p, _ in delayed)
        findings.append(
            build_finding(
                source="group",
                reliability="primary",
                kind="group_delay_share",
                area="builder_history",
                title=f"{len(delayed)} of {len(reads)} group projects read on UP-RERA are "
                f"more than {DELAYED_AFTER_MONTHS} months past their completion date",
                verdict="fail",
                url=first.details_url,
                today=ctx.today,
                now=ctx.now,
                count=len(delayed),
                total=len(reads),
                snippet=numbers[:300],
            )
        )
    return findings


def is_delayed(record: UpreraRecord, today: date) -> bool:
    latest = record.latest_end_date
    if latest is None or record.is_completed or record.completion_certificate:
        return False
    return months_between(latest, today) > DELAYED_AFTER_MONTHS


def _project_finding(
    kind: str, project: Project, record: UpreraRecord, title: str, ctx: SourceContext
) -> Finding:
    return build_finding(
        source="group",
        reliability="primary",
        kind=kind,
        area="builder_history",
        title=title,
        verdict="fail",
        url=project.details_url,
        today=ctx.today,
        now=ctx.now,
        occurred_on=record.latest_end_date,
    )


def _name(project: Project) -> str:
    return f"{project.name or 'Project'} ({project.rera_id})"


def _day(value: date | None) -> str:
    return f"{value:%d %b %Y}" if value else "unknown"


async def _gather_limited[T](reads: Iterable[Awaitable[T]]) -> list[T]:
    """Run reads a few at a time so one check does not flood the sites it reads."""
    slots = asyncio.Semaphore(PARALLEL_READS)

    async def limited(read: Awaitable[T]) -> T:
        async with slots:
            return await read

    return list(await asyncio.gather(*(limited(read) for read in reads)))
