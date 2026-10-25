import asyncio
import uuid
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.models import CheckKey, Finding, Project
from app.sources.agent import CAPTCHA_FIELD, CAPTCHA_RULE, AgentSource, AgentTask, is_empty
from app.sources.base import (
    Blocked,
    ChecksRead,
    FoundFinding,
    LiveUrl,
    Progress,
    SourceContext,
    SourceError,
)
from app.tinyfish import AgentDone, AgentEvent, AgentLiveUrl, AgentProgress
from tests.fakes import FakeWebClient

START_URL = "https://www.zaubacorp.com/SUPERTECH-LIMITED-U74899DL1995PLC074422"
PROJECT = Project(
    rera_id="UPRERAPRJ8334",
    promoter="SUPERTECH LIMITED",
    details_url="https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
)


class CompanyStatusSource(AgentSource):
    """A minimal agent source, only for exercising the shared runner."""

    name = "registry"
    checks: tuple[CheckKey, ...] = ("company_status",)

    async def task(self, ctx: SourceContext) -> AgentTask | None:
        return AgentTask(
            url=START_URL,
            goal=f"Read the company status and CIN of {ctx.project.promoter}.",
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "nullable": True},
                    "cin": {"type": "string", "nullable": True},
                },
                "required": ["status", "cin"],
            },
        )

    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        return [
            Finding(
                id=uuid.uuid4().hex,
                source="registry",
                kind="company_status",
                title=f"Company status: {result['status']}",
                area="financial",
                verdict="review",
                reliability="secondary",
                source_url=START_URL,
                read_on=ctx.today,
                read_at=ctx.now,
            )
        ]


def run(events: list[AgentEvent]) -> tuple[list[object], FakeWebClient]:
    web = FakeWebClient(agent_runs={START_URL: events})
    ctx = SourceContext(
        project=PROJECT, web=web, today=date(2026, 10, 25), now=datetime(2026, 10, 25, tzinfo=UTC)
    )

    async def collect() -> list[object]:
        return [event async for event in CompanyStatusSource().run(ctx)]

    return asyncio.run(collect()), web


def done(result: dict[str, Any] | None, status: str = "COMPLETED") -> AgentDone:
    return AgentDone(status=status, result=result)


def test_live_url_and_steps_reach_the_agent_cam() -> None:
    events, _ = run(
        [
            AgentLiveUrl("wss://live.example/run-1"),
            AgentProgress("Searching for SUPERTECH LIMITED"),
            done({"status": "Under CIRP", "cin": "U74899DL1995PLC074422", CAPTCHA_FIELD: False}),
        ]
    )
    assert events[0] == Progress("Opening www.zaubacorp.com")
    assert LiveUrl("wss://live.example/run-1") in events
    assert Progress("Searching for SUPERTECH LIMITED") in events


def test_a_good_result_becomes_findings_and_reads_the_checks() -> None:
    events, _ = run([done({"status": "Under CIRP", "cin": "U74899DL1995PLC074422"})])
    findings = [e.finding for e in events if isinstance(e, FoundFinding)]
    assert [f.title for f in findings] == ["Company status: Under CIRP"]
    assert events[-1] == ChecksRead(("company_status",))


def test_captcha_marks_the_source_blocked_and_reads_nothing() -> None:
    events, _ = run([done({"status": None, "cin": None, CAPTCHA_FIELD: True})])
    assert any(isinstance(e, Blocked) for e in events)
    assert not any(isinstance(e, ChecksRead | FoundFinding) for e in events)


def test_an_empty_completed_run_leaves_the_source_unread() -> None:
    events, _ = run([done({"status": None, "cin": "", CAPTCHA_FIELD: False})])
    assert not any(isinstance(e, ChecksRead | FoundFinding | Blocked) for e in events)


def test_a_failed_run_is_an_error_with_the_reason() -> None:
    with pytest.raises(SourceError, match="failed: page too large"):
        run([AgentDone(status="FAILED", result=None, error="page too large")])


def test_a_run_without_a_final_event_is_an_error() -> None:
    with pytest.raises(SourceError, match="without an answer"):
        run([AgentProgress("Opening the page")])


def test_every_run_is_told_never_to_bypass_a_captcha() -> None:
    _, web = run([done({"status": "Active", "cin": "U1"})])
    request = web.agent_requests[0]
    assert request["url"] == START_URL
    assert request["goal"].endswith(CAPTCHA_RULE)
    assert CAPTCHA_FIELD in request["output_schema"]["required"]
    assert request["output_schema"]["properties"]["status"] == {"type": "string", "nullable": True}


def test_is_empty() -> None:
    assert is_empty({"a": None, "b": [], CAPTCHA_FIELD: False})
    assert not is_empty({"a": "Active"})
