"""UP-RERA, the primary source: TinyFish Fetch plus a deterministic parser.

Pages are read with Fetch and parsed in Python. Only the sections we use
are requested, which keeps pages small and leaves out bank accounts and
phone numbers that NeevCheck has no reason to store.

Old-format projects have two pages: the details page (dates, documents) and
a Projectsummary page (complaint counts) that only search can find.
"""

from collections.abc import AsyncIterator
from datetime import date, datetime

from app.models import Area, CheckKey, Finding, Project, Verdict
from app.parsers.uprera_page import ParseError, UpreraRecord, parse_uprera_page
from app.sources.base import (
    ChecksRead,
    FoundFinding,
    Progress,
    ProjectDetails,
    SourceContext,
    SourceError,
    SourceEvent,
)
from app.sources.findings import build_finding
from app.tinyfish import WebClient, WebError
from app.uprera_links import find_summary_url, summary_url

ID = "#ctl00_ContentPlaceHolder1_"
DETAILS_SELECTORS = [
    ID + name
    for name in (
        "lblProjectNameHeading",
        "lblProjectNameWithID",
        "lblregisdate",
        "lblPromoterNameHeading",
        "lblPromoterNameWithID",
        "PanelBasicDetails",
        "txtrevised_end_date",
        "grdPermitDetails",
        "grvdocumentdetails",
    )
]
SUMMARY_SELECTORS = [
    ID + name
    for name in (
        "lblprojectname",
        "lblregno",
        "prjregdate",
        "prj_type",
        "Lblproposedenddt",
        "lbldistrict",
        "Lblpromotername",
        "lbltotalcomplaint",
        "lblprojectwisecomplaint",
        "grd_extension",
        "lblDateOfUploadingCC",
        "grvdocumentdetails",
    )
]
PURPOSE = "Read a UP-RERA project page to record its registration, dates and documents"


def selectors_for(url: str) -> list[str]:
    return SUMMARY_SELECTORS if summary_url(url) else DETAILS_SELECTORS


async def read_record(url: str, web: WebClient) -> UpreraRecord:
    page = await web.fetch_html(url, selectors=selectors_for(url), purpose=PURPOSE)
    return parse_uprera_page(page.html)


async def describe_project(project: Project, web: WebClient) -> Project | None:
    """Fill a candidate from its page, or None when the page shows no such project."""
    try:
        record = await read_record(project.details_url, web)
    except ParseError:
        return None
    if record.rera_id != project.rera_id:
        return None
    return with_record(project, record)


def with_record(project: Project, record: UpreraRecord) -> Project:
    return project.model_copy(
        update={
            "name": record.name or project.name,
            "promoter": record.promoter or project.promoter,
            "registered_on": record.registered_on or project.registered_on,
            "district": record.district or project.district,
        }
    )


class UpreraSource:
    name = "uprera"
    checks: tuple[CheckKey, ...] = ("registration", "completion_date", "extensions")

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        project = ctx.project
        yield Progress("Opening the UP-RERA project page")
        try:
            record = await read_record(project.details_url, ctx.web)
        except ParseError as error:
            raise SourceError(str(error)) from None
        if record.rera_id != project.rera_id:
            raise SourceError(f"The UP-RERA page shows {record.rera_id}, not {project.rera_id}")

        yield Progress("Reading registration, completion dates and documents")
        yield ProjectDetails(with_record(project, record))
        for finding in findings_from_record(record, project.details_url, ctx.today, ctx.now):
            yield FoundFinding(finding)

        yield Progress("Reading complaint counts on the UP-RERA summary page")
        summary, url = await self._summary(project, record, ctx.web)
        extensions_read = False
        if summary and url:
            for finding in extension_findings(summary, url, ctx.today, ctx.now):
                yield FoundFinding(finding)
            for finding in complaint_findings(summary, url, ctx.today, ctx.now):
                yield FoundFinding(finding)
            extensions_read = True
        else:
            yield Progress("The UP-RERA summary page was not found, so complaints were not read")

        read: list[CheckKey] = ["registration"]
        if record.latest_end_date:
            read.append("completion_date")
        if extensions_read:
            read.append("extensions")
        yield ChecksRead(tuple(read))

    async def _summary(
        self, project: Project, record: UpreraRecord, web: WebClient
    ) -> tuple[UpreraRecord | None, str | None]:
        """The Projectsummary record: the page already read, or the one search finds."""
        if summary_url(project.details_url):
            return record, project.details_url
        try:
            url = await find_summary_url(project.rera_id, web)
            summary = await read_record(url, web) if url else None
        except (WebError, ParseError):
            return None, None
        if summary is None or summary.rera_id != project.rera_id:
            return None, None
        return summary, url


def findings_from_record(
    record: UpreraRecord, url: str, today: date, now: datetime
) -> list[Finding]:
    """Registration, completion date or delay, and a completion certificate if one is on record."""
    registered = f" on {_day(record.registered_on)}" if record.registered_on else ""
    findings = [
        _finding(
            "registration",
            "rera",
            f"Registered on UP-RERA{registered}",
            "ok",
            url,
            today,
            now,
            occurred_on=record.registered_on,
        )
    ]

    certificate = record.completion_certificate
    if record.completion_uploaded_on and not certificate:
        findings.append(
            _finding(
                "completion_certificate",
                "execution",
                f"Completion certificate uploaded on {_day(record.completion_uploaded_on)}. "
                "Verify possession status",
                "review",
                url,
                today,
                now,
                occurred_on=record.completion_uploaded_on,
            )
        )
    if certificate:
        uploaded = f", uploaded {_day(certificate.uploaded_on)}" if certificate.uploaded_on else ""
        findings.append(
            _finding(
                "completion_certificate",
                "execution",
                f"Completion certificate on record{uploaded}. Verify possession status",
                "review",
                url,
                today,
                now,
                occurred_on=certificate.uploaded_on,
            )
        )

    latest = record.latest_end_date
    if latest is None:
        return findings
    months = months_between(latest, today)
    if months > 0 and not record.is_completed and not certificate:
        findings.append(
            _finding(
                "past_end_date",
                "execution",
                f"Completion date on record ({_day(latest)}) passed {months} months ago; "
                f"project still listed as {record.project_type or 'not completed'}",
                "fail" if months > 12 else "review",
                url,
                today,
                now,
                occurred_on=latest,
                months=months,
            )
        )
    else:
        findings.append(
            _finding(
                "completion_date",
                "execution",
                f"Completion date on record: {_day(latest)}",
                "context",
                url,
                today,
                now,
                occurred_on=latest,
            )
        )
    return findings


def extension_findings(
    summary: UpreraRecord, url: str, today: date, now: datetime
) -> list[Finding]:
    """Extensions the authority granted, without the COVID-19 ones given to every project."""
    own = [e for e in summary.extensions if not e.is_covid]
    if not own:
        return []
    latest = max((e.extended_to for e in own if e.extended_to), default=None)
    until = f", most recently to {_day(latest)}" if latest else ""
    times = "once" if len(own) == 1 else f"{len(own)} times"
    return [
        _finding(
            "completion_extended",
            "execution",
            f"Completion date extended {times} by UP-RERA{until}",
            "fail",
            url,
            today,
            now,
            occurred_on=latest,
            count=len(own),
        )
    ]


def complaint_findings(
    summary: UpreraRecord, url: str, today: date, now: datetime
) -> list[Finding]:
    """Complaint counts from the Projectsummary page, for the promoter and for this project."""
    findings = []
    if summary.promoter_complaints is not None:
        count = summary.promoter_complaints
        findings.append(
            _finding(
                "promoter_complaints",
                "builder_history",
                f"{count} complaints on UP-RERA against the promoter, across all its projects",
                "review" if count else "ok",
                url,
                today,
                now,
                count=count,
            )
        )
    if summary.project_complaints is not None:
        count = summary.project_complaints
        findings.append(
            _finding(
                "project_complaints",
                "legal",
                f"{count} complaints on UP-RERA about this project",
                "review" if count else "ok",
                url,
                today,
                now,
                count=count,
            )
        )
    return findings


def _finding(
    kind: str,
    area: Area,
    title: str,
    verdict: Verdict,
    url: str,
    today: date,
    now: datetime,
    **facts: object,
) -> Finding:
    return build_finding(
        source="uprera",
        reliability="primary",
        kind=kind,
        area=area,
        title=title,
        verdict=verdict,
        url=url,
        today=today,
        now=now,
        **facts,
    )


def months_between(start: date, end: date) -> int:
    """Whole months from start to end; negative when end is earlier."""
    months = (end.year - start.year) * 12 + end.month - start.month
    return months - 1 if end.day < start.day else months


def _day(value: date) -> str:
    return value.strftime("%d %b %Y")
