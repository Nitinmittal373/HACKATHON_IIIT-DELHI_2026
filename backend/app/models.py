"""Shared data shapes.

Rule 1: no source, no claim. Every finding is `Evidence` with a source URL and the time it was retrieved.
Rule 2: "not found in checked records" is not "does not exist". What we looked for is kept in `checks`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


Lane = Literal["rera", "mca", "ibbi", "authority", "news"]
EvidenceStatus = Literal["verified", "partially_verified", "requires_review"]
SourceType = Literal["official", "registry_mirror", "news", "other"]
CheckOutcome = Literal["found", "not_found", "unavailable", "captcha", "skipped"]
CirpScope = Literal["company", "this_project", "other_project"]


class Evidence(BaseModel):
    n: int = 0                       # citation number shown in the report, set when the report is built
    lane: Lane
    claim: str                       # plain factual sentence shown to the user
    source_url: str
    source_type: SourceType = "other"
    status: EvidenceStatus = "requires_review"
    snippet: str = ""                # verbatim text or extracted fields backing the claim
    fetched_at: str = Field(default_factory=now_iso)   # original retrieval time, kept on cache replay


class Check(BaseModel):
    """One thing we looked for, and what happened. Shown so users see gaps, not just findings."""
    lane: Lane
    what: str
    outcome: CheckOutcome
    detail: str = ""


class Signals(BaseModel):
    """Facts extracted from all lanes. None means 'not checked / unavailable', never 'clean'."""
    # P1 Regulatory (RERA)
    registration_status: str | None = None          # e.g. "registered", "lapsed", "revoked"
    extensions_count: int | None = None
    force_majeure_extensions: int | None = None     # blanket COVID-era extensions: not counted against the builder
    delay_months: int | None = None                 # revised completion minus promised completion
    qprs_missed_last4: int | None = None
    rera_penalty_orders: int | None = None
    rera_complaints: int | None = None
    total_units: int | None = None
    promised_completion: str | None = None
    revised_completion: str | None = None
    # P2 Track record
    group_projects_total: int | None = None
    group_projects_delayed: int | None = None
    group_project_lapsed: bool | None = None
    # P3 Legal & insolvency
    promoter_in_cirp: bool | None = None            # official record names the promoter's exact legal name
    cirp_scope: CirpScope | None = None             # what the proceeding covers, when promoter_in_cirp
    sister_company_in_cirp: bool | None = None      # official record, verified group company
    insolvency_case_found: bool | None = None       # NCLT record names the promoter; stage not confirmed
    insolvency_reported_in_news: bool | None = None # news only: requires review, no penalty by itself
    pending_cases: int | None = None
    # P4 Corporate health
    company_status: str | None = None
    company_or_director_struck_off: bool | None = None
    recent_charge_creation: bool | None = None
    open_charges: int | None = None
    directors: int | None = None
    cin: str | None = None
    sarfaesi_notice: bool | None = None
    # P5 Land authority
    authority_defaulter: bool | None = None
    no_oc_past_due: bool | None = None
    # P6 Sentiment
    adverse_news_count: int | None = None


class LaneStatus(BaseModel):
    lane: Lane
    ok: bool
    message: str = ""


class Report(BaseModel):
    id: str
    query: str
    project_name: str | None = None
    rera_number: str | None = None
    promoter_name: str | None = None
    rera_url: str | None = None
    photo_url: str | None = None     # project photo shown on the UP-RERA page, if any
    signals: Signals
    evidence: list[Evidence]
    checks: list[Check] = []
    lanes: list[LaneStatus]
    score: dict[str, Any]
    graph: dict[str, Any] = {}       # builder family tree: nodes + edges, each edge verified or "verify"
    demo_replay: bool = False       # True when served from cached runs (DEMO_MODE)
    created_at: str = Field(default_factory=now_iso)


class ReportSummary(BaseModel):
    id: str
    query: str
    project_name: str | None
    promoter_name: str | None
    score: int
    band: str
    confidence: float
    hard_stop: bool
    created_at: str
    watching: bool = False
