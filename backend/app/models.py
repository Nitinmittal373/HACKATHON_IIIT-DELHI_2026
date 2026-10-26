"""Data shapes shared by the API, the sources and the scoring engine.

Honesty rules live in these types: every Finding carries its source URL and
the day it was read, and a check that could not be read is recorded as
unread instead of being treated as clean.
"""

import re
from datetime import date, datetime
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api_model import ApiModel
from app.states.names import DEFAULT_STATE, state_name

CoverageLevel = Literal["full", "partial", "search_only"]
SourceName = Literal[
    "uprera", "registry", "insolvency", "land", "consumer", "news", "group", "sarfaesi"
]
Area = Literal["rera", "execution", "legal", "financial", "builder_history", "news"]
Reliability = Literal["primary", "secondary"]
Verdict = Literal["ok", "fail", "red_flag", "review", "context", "not_found"]
Band = Literal["Low", "Moderate", "High", "Critical", "insufficient_evidence"]
InsolvencyScope = Literal["company", "this_project", "other_project"]
CheckStatus = Literal["queued", "running", "completed", "failed"]
RunStatus = Literal["running", "completed", "blocked", "failed", "unavailable"]
# The facts a complete check must read. Confidence is the share of these that were read.
CheckKey = Literal[
    "registration",
    "completion_date",
    "extensions",
    "company_status",
    "insolvency",
    "land_dues",
    "consumer_cases",
]
EventType = Literal[
    "source.started",
    "source.live_url",
    "source.progress",
    "finding.added",
    "source.blocked",
    "source.completed",
    "check.completed",
]

RERA_ID_PATTERN = re.compile(r"^UPRERAPRJ\d{1,7}(/\d{2}/\d{4})?$")
UPRERA_HOSTS = {"up-rera.in", "www.up-rera.in"}


def normalize_rera_id(text: str) -> str | None:
    """' uprera prj-8334 ' -> 'UPRERAPRJ8334'; anything that is not a RERA number -> None."""
    # People copy numbers from PDFs and brochures with spaces, hyphens or dots in them.
    candidate = re.sub(r"[\s.\-_]+", "", text).upper()
    return candidate if RERA_ID_PATTERN.match(candidate) else None


def is_new_format(rera_id: str) -> bool:
    return "/" in rera_id


def is_uprera_url(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname in UPRERA_HOSTS


class StateTagged(ApiModel):
    """A record that belongs to one state's RERA. Records made before all-India support are UP."""

    state: str = DEFAULT_STATE
    state_name: str = state_name(DEFAULT_STATE)
    # The state's authority as its own pages call it, such as "MahaRERA".
    rera_name: str = "UP-RERA"

    @model_validator(mode="before")
    @classmethod
    def name_the_state(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Imported here: the state registry imports these models.
        from app.states.registry import BY_CODE

        code = data.get("state", DEFAULT_STATE)
        adapter = BY_CODE.get(code)
        filled = {
            "state_name": state_name(code),
            "rera_name": adapter.rera_name if adapter else "RERA",
        }
        return {**filled, **data}


# "confirmed": a state portal page prints the number. "listings_only": builder and listing sites
# print it but no portal page was read. The last two come from an uploaded file or a public order.
CandidateStatus = Literal["confirmed", "listings_only", "from_document", "from_order"]


class Project(StateTagged):
    rera_id: str
    name: str | None = None
    promoter: str | None = None
    registered_on: date | None = None
    district: str | None = None
    details_url: str
    # None for candidates a state adapter produced from its own portal pages.
    status: CandidateStatus | None = None
    # Where the number was seen: site names, or "your document".
    sources: list[str] = []


class PreReraNote(ApiModel):
    """A project that public pages say was finished before RERA, so it has no number to find."""

    name: str
    # The words of the page that say so, and the page.
    statement: str
    source_url: str


class SearchResponse(ApiModel):
    query: str
    candidates: list[Project]
    # The state the number's format pointed at; None for a name or a number of no known state.
    detected_state: str | None = None
    # The states whose portals were searched, so the page can say where it looked.
    searched_states: list[str] = []
    # Projects public pages say are older than RERA; they get a builder-only check.
    pre_rera: list[PreReraNote] = []


class StateInfo(ApiModel):
    """One state's RERA portal and how much of it NeevCheck reads."""

    code: str
    name: str
    rera_name: str
    coverage: CoverageLevel
    # Real registration numbers read from the portal, for the search box's try-chips.
    examples: list[str]
    # What is read there, in a sentence.
    note: str
    portal_url: str
    complaint_url: str
    # Patterns the registration numbers of this state match, so a page can pick the state while
    # a visitor types. Written for Python, and valid in JavaScript with the "i" flag.
    id_patterns: list[str]
    # False while no real number of this state has been read from its portal.
    format_verified: bool


class CheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rera_id: str = Field(max_length=60, examples=["UPRERAPRJ8334", "P51800000937"])
    # Which state's RERA the number belongs to. Optional: the number's format tells, and
    # UP numbers, the only ones before all-India support, default to "UP".
    state: str | None = Field(default=None, max_length=2, examples=["UP", "MH"])
    # The page search returned. Required for new-format UP numbers, whose pages have no stable
    # address; send it for every number, since many later numbers have no stable page either.
    details_url: str | None = Field(default=None, max_length=500)
    # Skip the 24-hour reuse of a recent check ("Re-check now"). The daily cap still applies.
    fresh: bool = False

    @model_validator(mode="after")
    def valid_for_its_state(self) -> "CheckCreate":
        self.state, self.rera_id = check_project_number(self.rera_id, self.state, self.details_url)
        return self


def check_project_number(
    rera_id: str, state: str | None, details_url: str | None
) -> tuple[str, str]:
    """(state, canonical number) of a number a visitor sent, or a ValueError saying what is wrong.

    The state is the one named, else the one whose number format matches. A link is accepted
    only on that state's own RERA site, so a check never reads a page we did not choose.
    """
    # Imported here: the state registry imports these models.
    from app.states.registry import BY_CODE, detect_state

    found = detect_state(rera_id)
    adapter = BY_CODE.get(state or (found[0].code if found else ""))
    canonical = adapter.canonical_id(rera_id) if adapter else None
    if adapter is None or canonical is None:
        raise ValueError("must be a RERA project number of a supported state, e.g. UPRERAPRJ8334")
    if details_url is not None and not _on_portal(details_url, adapter.domains):
        raise ValueError(f"must be an https link on {adapter.rera_name}'s own site")
    if adapter.code == DEFAULT_STATE and is_new_format(canonical) and not details_url:
        raise ValueError("new-format numbers need the details_url returned by search")
    return adapter.code, canonical


def _on_portal(url: str, domains: tuple[str, ...]) -> bool:
    parts = urlsplit(url)
    host = parts.hostname or ""
    return parts.scheme == "https" and any(host == d or host.endswith("." + d) for d in domains)


class SourceRun(ApiModel):
    source: SourceName
    status: RunStatus
    live_url: str | None = None
    message: str | None = None
    checks_read: list[CheckKey] = []


PillarId = Literal["P1", "P2", "P3", "P4", "P5", "P6"]
BandV2 = Literal["Low", "Watch", "Elevated", "High", "insufficient_evidence"]


class Pillar(ApiModel):
    id: PillarId
    name: str
    weight: float
    # 0-100, after the pillar's cap.
    penalty: int
    # Points lost on the 300-900 scale, negative like the v1 drivers.
    points: float


class DriverV2(ApiModel):
    """One finding's share of the score, so the evidence ledger can show it."""

    finding_id: str
    pillar: PillarId
    code: str
    penalty: int
    points: float


class ReasonCode(ApiModel):
    code: str
    label: str
    finding_ids: list[str]
    points: float


class ScoreV2(ApiModel):
    value: int
    band: BandV2
    band_label: str
    # True when too few pillars were read to rate the project; the value is shown but not banded.
    provisional: bool
    hard_stop: bool
    hard_stop_reason: str | None = None
    # Share of the six pillars with at least one source read.
    confidence: float
    pillars: list[Pillar]
    reason_codes: list[ReasonCode]
    drivers: list[DriverV2]
    pillars_unread: list[PillarId]


class DisplayScore(ApiModel):
    """The score every screen shows: NeevScore v2 on the 300-900 scale, without the detail.

    When too little was read to rate the project (band insufficient_evidence) there is no number
    to show: `value` is null, and the computed one is kept as `provisional_value` for the
    method section only. A number nobody can stand behind is worse than none.
    """

    value: int | None
    # The computed number of an unrated project; shown nowhere but the method section.
    provisional_value: int | None = None
    band: BandV2
    hard_stop: bool
    confidence: float
    # True when too little was read to rate the project.
    provisional: bool
    # How many of the six record types (pillars) were read.
    records_read: int = 0
    records_total: int = 6

    @model_validator(mode="before")
    @classmethod
    def hide_an_unrated_number(cls, data: Any) -> Any:
        """Also applies to scores stored before this rule, so no old answer shows a number."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        total = data.setdefault("records_total", 6)
        data.setdefault("records_read", round(float(data.get("confidence", 0)) * total))
        if data.get("band") == "insufficient_evidence":
            data["provisional_value"] = data.get("provisional_value", data.get("value"))
            data["value"] = None
            data["provisional"] = True
        return data

    @classmethod
    def of(cls, score: ScoreV2) -> "DisplayScore":
        return cls.model_validate(
            {
                "value": score.value,
                "band": score.band,
                "hard_stop": score.hard_stop,
                "confidence": score.confidence,
                "provisional": score.provisional,
                "records_read": len(score.pillars) - len(score.pillars_unread),
                "records_total": len(score.pillars),
            }
        )


class Check(StateTagged):
    id: str
    rera_id: str
    details_url: str
    status: CheckStatus
    started_at: datetime
    completed_at: datetime | None = None
    sources: list[SourceRun] = []
    # True when an earlier finished check of the same project was returned instead of a new one.
    reused: bool = False
    # Set once the check has a score.
    display_score: DisplayScore | None = None


class Finding(ApiModel):
    id: str
    source: SourceName
    kind: str
    title: str
    area: Area | None = None
    verdict: Verdict
    reliability: Reliability
    # No source, no claim: a finding without a web address cannot exist.
    source_url: str = Field(pattern=r"^https?://\S+$")
    read_on: date
    read_at: datetime | None = None
    occurred_on: date | None = None
    # Parsed facts the scoring rules read; which ones are set depends on `kind`.
    count: int | None = None
    months: int | None = None
    scope: InsolvencyScope | None = None
    # Out of how many, for share-style facts such as "3 of 5 group projects delayed".
    total: int | None = None
    # The exact words on the page behind the claim, for the evidence ledger.
    snippet: str | None = Field(default=None, max_length=300)
    # Set when the fact was read from a Search result's text, not from the opened page.
    via: Literal["search_snippet"] | None = None


class Driver(ApiModel):
    finding_id: str
    title: str
    area: Area
    penalty: int
    points: float


class AreaScore(ApiModel):
    area: Area
    label: str
    weight: float
    penalty: int


class Score(ApiModel):
    value: int
    band: Band
    band_label: str
    confidence: float
    # True when too little was read to rate the project; the value is shown but not banded.
    provisional: bool
    hard_stop: bool
    hard_stop_reason: str | None = None
    drivers: list[Driver]
    areas: list[AreaScore]
    checks_unread: list[CheckKey]


class CheckSummary(StateTagged):
    """One line of a visitor's history: enough to list a check without loading its report."""

    id: str
    rera_id: str
    # The page the check read, so "Re-check" can start the same check again.
    details_url: str
    project: str | None
    promoter: str | None
    status: CheckStatus
    # The classic 0-100 score, kept for older clients; screens show display_score.
    score: int | None = None
    band: Band | None = None
    confidence: float | None = None
    display_score: DisplayScore | None = None
    created_at: datetime
    completed_at: datetime | None = None


class RecentCheck(CheckSummary):
    """A finished check shown on the home page. Only public-record facts, never who asked."""

    registered_on: date | None = None
    sources_read: int = 0
    drivers: list[Driver] = []
    # The biggest reasons behind the 300-900 score, with the points each one cost.
    reasons: list[ReasonCode] = []


FamilyFlag = Literal["cirp", "struck_off"]
FamilyProjectState = Literal["ok", "delayed", "lapsed", "unread"]


class FamilyDirector(ApiModel):
    """A director by name and DIN only: nothing else about a person is kept (DPDP)."""

    name: str
    din: str


class FamilyProject(ApiModel):
    rera_id: str
    name: str | None = None
    details_url: str
    state: FamilyProjectState


class FamilyCompany(ApiModel):
    name: str
    # The registry status as a page shows it; None when no page naming this company was read.
    status: str | None = None
    status_url: str | None = None
    flag: FamilyFlag | None = None
    projects: list[FamilyProject] = []


class FamilyTree(ApiModel):
    """The promoter, its directors, related companies and their UP-RERA projects."""

    promoter: str
    source_url: str
    directors: list[FamilyDirector]
    promoter_projects: list[FamilyProject] = []
    companies: list[FamilyCompany] = []


class Report(StateTagged):
    check: Check
    project: Project
    # The classic 0-100 score, shown only as a transparency line in the method section.
    score: Score
    findings: list[Finding]
    timeline: list[Finding]
    # The score screens show. Checks made before v2 are re-scored from their stored findings.
    display_score: DisplayScore
    score_v2: ScoreV2
    # Directors, related companies and their projects; None unless the group source ran.
    family: FamilyTree | None = None
    # Where this state's portal is, how much of it is read, and where a complaint is filed.
    coverage: CoverageLevel = "full"
    portal_url: str = "https://www.up-rera.in/"
    complaint_url: str = "https://www.up-rera.in/ComplaintHome"


class Event(BaseModel):
    type: EventType
    check_id: str
    source: SourceName | Literal["check"]
    ts: datetime
    data: dict[str, Any] = {}
