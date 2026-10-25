"""Consumer cases: e-Jagriti, the national consumer-commission portal.

The case search asks for a CAPTCHA, so this source usually ends as blocked
("Unable to verify"). That costs confidence, never score. If a run does get
through, the agent reports what the results table shows and Python counts
only cases whose opposite party carries the promoter's exact legal name.
"""

from typing import Any

from app.matching import legal_name_in, normalize
from app.models import CheckKey, Finding
from app.sources.agent import AgentSource, AgentTask
from app.sources.base import SourceContext
from app.sources.findings import build_finding

START_URL = "https://e-jagriti.gov.in/advance-case-search"
GOAL = (
    "This is the e-Jagriti consumer case search. Search by party name: choose the option to "
    "search by opposite party (respondent) name, type {promoter}, and submit. Do not log in. "
    "Read the first page of results only. total_cases: the number of cases the results "
    "report. cases: up to 10 rows, each with the case number, the commission (forum) and "
    "the opposite party name exactly as shown. Return null for anything not shown."
)
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "total_cases": {"type": ["integer", "null"]},
        "cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "case_number": {"type": ["string", "null"]},
                    "forum": {"type": ["string", "null"]},
                    "opposite_party": {"type": ["string", "null"]},
                },
            },
        },
    },
    "required": ["total_cases", "cases"],
}


class ConsumerSource(AgentSource):
    name = "consumer"
    checks: tuple[CheckKey, ...] = ("consumer_cases",)
    no_task_message = "The promoter's name is not known, so consumer cases were not searched"

    async def task(self, ctx: SourceContext) -> AgentTask | None:
        promoter = ctx.project.promoter
        if not promoter:
            return None
        # A CAPTCHA is expected, so the run is kept short: it is never retried or solved.
        return AgentTask(
            url=START_URL,
            goal=GOAL.format(promoter=promoter),
            output_schema=OUTPUT_SCHEMA,
            max_steps=12,
        )

    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        return to_findings(result, ctx.project.promoter, task.url, ctx)


def to_findings(
    result: dict[str, Any], promoter: str | None, url: str, ctx: SourceContext
) -> list[Finding]:
    rows = [row for row in result.get("cases") or [] if isinstance(row, dict)]
    ours = [row for row in rows if legal_name_in(promoter, normalize(row.get("opposite_party")))]
    if result.get("total_cases") is None and not rows:
        return []
    count = len(ours)
    if count:
        title = f"{count} consumer cases against {promoter} on the first page of e-Jagriti results"
        verdict = "review"
    else:
        title = f"No consumer case naming {promoter} on the first page of e-Jagriti results"
        verdict = "not_found"
    return [
        build_finding(
            source="consumer",
            reliability="primary",
            kind="consumer_cases",
            area="legal",
            title=title,
            verdict=verdict,
            url=url,
            today=ctx.today,
            now=ctx.now,
            count=count,
        )
    ]
