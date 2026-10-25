"""Data shapes shared by the API, the sources and the scoring engine.

Honesty rules live in these types: every Finding carries its source URL and
the day it was read, and a check that could not be read is recorded as
unread instead of being treated as clean.
"""

import re
from datetime import date, datetime
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceName = Literal["uprera", "registry", "insolvency", "land", "consumer", "news"]
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


class Project(BaseModel):
    rera_id: str
    name: str | None = None
    promoter: str | None = None
    registered_on: date | None = None
    district: str | None = None
    details_url: str


class SearchResponse(BaseModel):
    query: str
    candidates: list[Project]


class CheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rera_id: str = Field(max_length=40, examples=["UPRERAPRJ8334"])
    # The page search returned. Required for new-format numbers, whose pages have no stable
    # address; send it for every number, since many later numbers have no stable page either.
    details_url: str | None = Field(default=None, max_length=500)
    # Skip the 24-hour reuse of a recent check ("Re-check now"). The daily cap still applies.
    fresh: bool = False

    @field_validator("rera_id")
    @classmethod
    def valid_rera_id(cls, value: str) -> str:
        normalized = normalize_rera_id(value)
        if normalized is None:
            raise ValueError("must be a UP-RERA project number such as UPRERAPRJ8334")
        return normalized

    @field_validator("details_url")
    @classmethod
    def uprera_url_only(cls, value: str | None) -> str | None:
        if value is not None and not is_uprera_url(value):
            raise ValueError("must be an https link on up-rera.in")
        return value

    @model_validator(mode="after")
    def new_format_needs_url(self) -> "CheckCreate":
        if is_new_format(self.rera_id) and self.details_url is None:
            raise ValueError("new-format numbers need the details_url returned by search")
        return self


class SourceRun(BaseModel):
    source: SourceName
    status: RunStatus
    live_url: str | None = None
    message: str | None = None
    checks_read: list[CheckKey] = []


class Check(BaseModel):
    id: str
    rera_id: str
    details_url: str
    status: CheckStatus
    started_at: datetime
    completed_at: datetime | None = None
    sources: list[SourceRun] = []
    # True when an earlier finished check of the same project was returned instead of a new one.
    reused: bool = False


class Finding(BaseModel):
    id: str
    source: SourceName
    kind: str
    title: str
    area: Area | None = None
    verdict: Verdict
    reliability: Reliability
    source_url: str
    read_on: date
    read_at: datetime | None = None
    occurred_on: date | None = None
    # Parsed facts the scoring rules read; which ones are set depends on `kind`.
    count: int | None = None
    months: int | None = None
    scope: InsolvencyScope | None = None


class Driver(BaseModel):
    finding_id: str
    title: str
    area: Area
    penalty: int
    points: float


class AreaScore(BaseModel):
    area: Area
    label: str
    weight: float
    penalty: int


class Score(BaseModel):
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


class CheckSummary(BaseModel):
    """One line of a visitor's history: enough to list a check without loading its report."""

    id: str
    rera_id: str
    # The page the check read, so "Re-check" can start the same check again.
    details_url: str
    project: str | None
    promoter: str | None
    status: CheckStatus
    score: int | None = None
    band: Band | None = None
    confidence: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class RecentCheck(CheckSummary):
    """A finished check shown on the home page. Only public-record facts, never who asked."""

    registered_on: date | None = None
    sources_read: int = 0
    drivers: list[Driver] = []


class Report(BaseModel):
    check: Check
    project: Project
    score: Score
    findings: list[Finding]
    timeline: list[Finding]


class Event(BaseModel):
    type: EventType
    check_id: str
    source: SourceName | Literal["check"]
    ts: datetime
    data: dict[str, Any] = {}
