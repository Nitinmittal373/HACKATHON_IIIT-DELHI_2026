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

SourceName = Literal[
    "uprera", "registry", "insolvency", "land", "consumer", "news", "group", "sarfaesi"
]
Area = Literal["rera", "execution", "legal", "financial", "builder_history", "news"]
Reliability = Literal["primary", "secondary"]
Verdict = Literal["ok", "fail", "red_flag", "review", "context", "not_found"]
Band = Literal["Low", "Moderate", "High", "Critical", "insufficient_evidence"]
InsolvencyScope = Literal["company", "this_project", "other_project"]
CheckStatus = Literal["queued", "running", "completed", "failed"]
# "partial": the source gave some of what it was asked for before it ran out of time or failed;
# what it reported is kept.
RunStatus = Literal["running", "completed", "partial", "blocked", "failed", "unavailable"]
# The facts a complete check must read. Confidence is the share of these that were read.
CheckKey = Literal[
    "registration",
    "completion_date",
    "extensions",
    "company_status",
    "insolvency",
    "land_dues",
    "consumer_cases",
    "rera_complaints",
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


# "confirmed": an up-rera.in page prints the number. "listings_only": builder and listing sites
# print it but no portal page was read. The last two come from an uploaded file or a public order.
CandidateStatus = Literal["confirmed", "listings_only", "from_document", "from_order"]


class Project(ApiModel):
    rera_id: str
    name: str | None = None
    promoter: str | None = None
    registered_on: date | None = None
    district: str | None = None
    details_url: str
    # None for candidates produced from up-rera.in's own pages.
    status: CandidateStatus | None = None
    # Where the number was seen: site names, or "your document".
    sources: list[str] = []
    # The order that named this project, when that is how it was found.
    found_in: str | None = None


class OrderLead(ApiModel):
    """A builder that a public order names as the respondent in a case about the project."""

    builder: str
    order_title: str
    order_url: str


class SearchResponse(ApiModel):
    query: str
    candidates: list[Project]
    # True when the text is a registration number of another state, or names a place outside
    # Uttar Pradesh; the page then says calmly that NeevCheck does not cover it.
    outside_up: bool = False
    # Builders that public orders name for the project, when nothing else found it.
    order_leads: list[OrderLead] = []


class CheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rera_id: str = Field(max_length=60, examples=["UPRERAPRJ8334"])
    # The page search returned. Required for new-format numbers, whose pages have no stable
    # address; send it for every number, since many later numbers have no stable page either.
    details_url: str | None = Field(default=None, max_length=500)
    # "Re-check now": read the records again instead of reusing a recent report. Allowed once per
    # project in RECHECK_MIN_DAYS, and only for a signed-in account like any new live check.
    fresh: bool = False

    @model_validator(mode="after")
    def valid_number(self) -> "CheckCreate":
        self.rera_id = check_project_number(self.rera_id, self.details_url)
        return self


OUTSIDE_UP_MESSAGE = (
    "NeevCheck covers Uttar Pradesh RERA projects for now. "
    "Check this project on its own state's RERA website."
)
# The shapes other states' registration numbers take ("P51800000937", "PRM/KA/RERA/1251/...",
# "RC/REP/HARERA/..."). Used only to answer calmly; nothing is looked up for them.
OTHER_STATE_NUMBER = re.compile(
    r"^(?!UPRERA)(?:P\d{11}|[A-Z]{1,8}RERA[A-Z0-9/\-]*\d[A-Z0-9/\-]*"
    r"|[A-Z]{2,5}/[A-Z0-9 /\-]*\d[A-Z0-9 /\-]*"
    r"|[A-Z]{2,6}-[A-Z0-9\-]*\d{3,}[A-Z0-9\-]*|\d{1,5}\s?OF\s?\d{4})$"
)


def is_other_state_number(text: str) -> bool:
    """Whether the text looks like a registration number of another state's RERA."""
    candidate = re.sub(r"\s+", " ", text.strip().upper())
    return normalize_rera_id(candidate) is None and bool(OTHER_STATE_NUMBER.match(candidate))


def check_project_number(rera_id: str, details_url: str | None) -> str:
    """The canonical number a visitor sent, or a ValueError saying what is wrong.

    A link is accepted only on up-rera.in, so a check never reads a page we did not choose.
    """
    canonical = normalize_rera_id(rera_id)
    if canonical is None:
        if is_other_state_number(rera_id):
            raise ValueError(OUTSIDE_UP_MESSAGE)
        raise ValueError("must be a UP-RERA project number, e.g. UPRERAPRJ8334")
    if details_url is not None and not is_uprera_url(details_url):
        raise ValueError("must be an https link on up-rera.in")
    if is_new_format(canonical) and not details_url:
        raise ValueError("new-format numbers need the details_url returned by search")
    return canonical


class SourceRun(ApiModel):
    source: SourceName
    status: RunStatus
    live_url: str | None = None
    message: str | None = None
    checks_read: list[CheckKey] = []
    # Where a visitor can look the record up themselves when it is not checked automatically.
    manual_url: str | None = None


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
    # Set when only part of the pillar was read, naming what was ("UP-RERA complaints").
    partly_read: str | None = None


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


class Check(ApiModel):
    id: str
    rera_id: str
    details_url: str
    status: CheckStatus
    started_at: datetime
    completed_at: datetime | None = None
    sources: list[SourceRun] = []
    # True when an earlier finished check of the same project was returned instead of a new one.
    reused: bool = False
    # When "Re-check now" opens again for this project; None when it is open now.
    next_recheck_at: datetime | None = None
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


class CheckSummary(ApiModel):
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
    """A check with the facts the home page card shows: public records, never who asked."""

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


class Report(ApiModel):
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
    # Where the UP-RERA portal is, and where a complaint is filed.
    portal_url: str = "https://www.up-rera.in/"
    complaint_url: str = "https://www.up-rera.in/ComplaintHome"


class FeaturedProject(ApiModel):
    """A well-known project NeevCheck has already checked, for the home page gallery.

    Built from the saved check only: it never says who ran it.
    """

    rera_id: str
    check_id: str
    name: str | None
    promoter: str | None
    display_score: DisplayScore
    read_at: datetime


class Event(BaseModel):
    type: EventType
    check_id: str
    source: SourceName | Literal["check"]
    ts: datetime
    data: dict[str, Any] = {}
