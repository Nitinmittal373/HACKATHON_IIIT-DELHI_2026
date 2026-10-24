"""UP-RERA, the primary source: TinyFish Fetch plus a deterministic parser.

The page is read with Fetch and parsed in Python. Only the sections we use
are requested, which keeps the page small and leaves out bank accounts and
phone numbers that NeevCheck has no reason to store.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime
from urllib.parse import urlsplit

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
from app.tinyfish import WebClient

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
        "grvdocumentdetails",
    )
]
PURPOSE = "Read a UP-RERA project page to record its registration, dates and documents"


def selectors_for(url: str) -> list[str]:
    is_summary = urlsplit(url).path.lower() == "/projectsummary"
    return SUMMARY_SELECTORS if is_summary else DETAILS_SELECTORS


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
    # Extension orders are not listed on these pages, so "extensions" stays unread for now.
    checks: tuple[CheckKey, ...] = ("registration", "completion_date", "extensions")

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        yield Progress("Opening the UP-RERA project page")
        try:
            record = await read_record(ctx.project.details_url, ctx.web)
        except ParseError as error:
            raise SourceError(str(error)) from None
        if record.rera_id != ctx.project.rera_id:
            raise SourceError(f"The UP-RERA page shows {record.rera_id}, not {ctx.project.rera_id}")

        yield Progress("Reading registration, completion dates and documents")
        yield ProjectDetails(with_record(ctx.project, record))
        for finding in findings_from_record(record, ctx.project.details_url, ctx.today, ctx.now):
            yield FoundFinding(finding)
        read: list[CheckKey] = ["registration"]
        if record.latest_end_date:
            read.append("completion_date")
        yield ChecksRead(tuple(read))


def findings_from_record(
    record: UpreraRecord, url: str, today: date, now: datetime
) -> list[Finding]:
    def finding(kind: str, area: Area, title: str, verdict: Verdict, **facts: object) -> Finding:
        return Finding.model_validate(
            {
                "id": uuid.uuid4().hex,
                "source": "uprera",
                "kind": kind,
                "title": title,
                "area": area,
                "verdict": verdict,
                "reliability": "primary",
                "source_url": url,
                "read_on": today,
                "read_at": now,
                **facts,
            }
        )

    registered = f" on {_day(record.registered_on)}" if record.registered_on else ""
    findings = [
        finding(
            "registration",
            "rera",
            f"Registered on UP-RERA{registered}",
            "ok",
            occurred_on=record.registered_on,
        )
    ]

    if record.project_complaints is not None:
        findings.append(
            finding(
                "rera_complaints",
                "rera",
                f"{record.project_complaints} complaints on UP-RERA about this project",
                "review" if record.project_complaints else "ok",
                count=record.project_complaints,
            )
        )
    latest = record.latest_end_date
    if latest is None:
        return findings
    findings.append(
        finding(
            "completion_date",
            "execution",
            f"Completion date on record: {_day(latest)}",
            "context",
            occurred_on=latest,
        )
    )

    months = months_between(latest, today)
    # The certificate only matters once the project is late: it is why the delay is not
    # counted. Every new project uploads the blank proforma, so before then it says nothing.
    certificate = record.completion_certificate if months > 0 else None
    if months > 0:
        findings.append(
            finding(
                "past_end_date",
                "execution",
                f"{months} months past the latest approved end date ({_day(latest)})",
                "review" if certificate or months <= 12 else "red_flag",
                months=months,
            )
        )
    if certificate:
        proforma = "proforma" in certificate.name.lower()
        what = "a completion certificate proforma" if proforma else "a completion certificate"
        findings.append(
            finding(
                "completion_certificate",
                "execution",
                f"Promoter uploaded {what}. Verify possession status",
                "review",
                occurred_on=certificate.uploaded_on,
            )
        )

    return findings


def months_between(start: date, end: date) -> int:
    """Whole months from start to end; negative when end is earlier."""
    months = (end.year - start.year) * 12 + end.month - start.month
    return months - 1 if end.day < start.day else months


def _day(value: date) -> str:
    return value.strftime("%d %b %Y")
