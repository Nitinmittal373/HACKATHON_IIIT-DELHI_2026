"""The state RERA portal, as the primary source of a check for any state but UP.

It turns the adapter's ProjectRecord into the same findings UP-RERA gives, so scoring needs no
state-specific code. The lane keeps the name "uprera" because the API and the stored reports
already use it for "the RERA lane"; the findings and the report name the real authority.
"""

from collections.abc import AsyncIterator, Callable
from datetime import date, datetime

from app.models import Area, CheckKey, Finding, Project, Verdict
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
from app.sources.uprera import REGISTRATION_ENDED, months_between
from app.states.base import ProjectRecord, StateAdapter
from app.states.builder import BuilderIdentity, identify_builder
from app.tinyfish import WebError

COMPLETED_STATUS = ("complet", "possession", "occupancy")


class StateReraSource:
    name = "uprera"
    checks: tuple[CheckKey, ...] = ("registration", "completion_date", "extensions")

    def __init__(self, adapter: StateAdapter) -> None:
        self._adapter = adapter

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        adapter, project = self._adapter, ctx.project
        yield Progress(f"Looking for {project.rera_id} on {adapter.rera_name}")
        record = await adapter.read(project, ctx.web, ctx.now)
        if record is None:
            raise SourceError(
                f"Unable to verify: {adapter.rera_name} pages that Search can read do not show "
                f"{project.rera_id}. Open the portal to check it yourself."
            )

        yield Progress(f"Reading what {adapter.rera_name} shows about the project")
        identity = None
        if not record.promoter_name:
            yield Progress(
                "The portal's page names no promoter; looking for the builder in listings"
            )
            identity = await find_builder(record.rera_id, ctx)
        named = record.model_copy(
            update={"promoter_name": record.promoter_name or (identity.name if identity else None)}
        )
        yield ProjectDetails(with_record(project, named))
        for finding in findings_from_record(record, adapter, ctx.today, ctx.now):
            yield FoundFinding(finding)
        if identity:
            yield FoundFinding(identity_finding(identity, adapter, ctx))

        read: list[CheckKey] = ["registration"]
        if record.latest_completion:
            read.append("completion_date")
        if record.revised_completion or record.extensions:
            read.append("extensions")
        yield ChecksRead(tuple(read))


async def find_builder(rera_id: str, ctx: SourceContext) -> BuilderIdentity | None:
    """A failed lookup only leaves the builder unnamed, as before."""
    try:
        return await identify_builder(rera_id, ctx.web)
    except WebError:
        return None


def identity_finding(
    identity: BuilderIdentity, adapter: StateAdapter, ctx: SourceContext
) -> Finding:
    """Who the builder is, for the reader to verify. It maps to no scoring rule: 0 points."""
    url, near = identity.sources[0]
    return build_finding(
        source="uprera",
        reliability="secondary",
        kind="builder_identity",
        area="builder_history",
        title=(
            f"Builder identified from public listings: {identity.name}. "
            f"Verify on {adapter.rera_name}"
        ),
        verdict="context",
        url=url,
        today=ctx.today,
        now=ctx.now,
        snippet=near,
    )


def with_record(project: Project, record: ProjectRecord) -> Project:
    return project.model_copy(
        update={
            "name": record.name or project.name,
            "promoter": record.promoter_name or project.promoter,
            "district": record.district or project.district,
            "registered_on": record.registration_date or project.registered_on,
        }
    )


def findings_from_record(
    record: ProjectRecord, adapter: StateAdapter, today: date, now: datetime
) -> list[Finding]:
    """Registration, completion date or delay, status and complaints, each with its words."""

    def make(kind: str, area: Area, title: str, verdict: Verdict, **facts: object) -> Finding:
        return build_finding(
            source="uprera",
            reliability="primary",
            kind=kind,
            area=area,
            title=title,
            verdict=verdict,
            url=record.source_url,
            today=today,
            now=now,
            snippet=(record.raw_snippets[0] if record.raw_snippets else None),
            via=record.read_via,
            **facts,
        )

    rera = adapter.rera_name
    since = f" on {_day(record.registration_date)}" if record.registration_date else ""
    findings = [
        make(
            "registration",
            "rera",
            f"Registration number appears on {rera}{since}",
            "ok",
            occurred_on=record.registration_date,
        )
    ]

    status = (record.status or "").strip()
    if REGISTRATION_ENDED.search(status):
        findings.append(
            make(
                "registration_revoked",
                "rera",
                f"{rera} lists the project status as '{status}' as of {_day(today)}",
                "red_flag",
            )
        )

    latest = record.latest_completion
    if latest is not None:
        findings.append(_completion(record, latest, today, make))
    promised, revised = record.promised_completion, latest
    if promised and revised:
        months = months_between(promised, revised)
        if months >= 1:
            findings.append(
                make(
                    "delay_vs_promised",
                    "execution",
                    f"Completion date moved from {_day(promised)} to {_day(revised)}, "
                    f"{months} months later than first promised",
                    "fail" if months > 12 else "review",
                    occurred_on=revised,
                    months=months,
                )
            )
    if record.extensions:
        times = "once" if len(record.extensions) == 1 else f"{len(record.extensions)} times"
        findings.append(
            make(
                "completion_extended",
                "execution",
                f"Completion date extended {times} by {rera}",
                "fail",
                count=len(record.extensions),
            )
        )
    if record.complaints_count is not None:
        count = record.complaints_count
        findings.append(
            make(
                "project_complaints",
                "legal",
                f"{count} complaints on {rera} about this project",
                "review" if count else "ok",
                count=count,
            )
        )
    return findings


def _completion(
    record: ProjectRecord, latest: date, today: date, make: Callable[..., Finding]
) -> Finding:
    status = (record.status or "").lower()
    months = months_between(latest, today)
    if months > 0 and not any(word in status for word in COMPLETED_STATUS):
        shown = record.status or "not completed"
        return make(
            "past_end_date",
            "execution",
            f"Completion date on record ({_day(latest)}) passed {months} months ago; "
            f"project still listed as {shown}",
            "fail" if months > 12 else "review",
            occurred_on=latest,
            months=months,
        )
    return make(
        "completion_date",
        "execution",
        f"Completion date on record: {_day(latest)}",
        "context",
        occurred_on=latest,
    )


def _day(value: date) -> str:
    return value.strftime("%d %b %Y")
