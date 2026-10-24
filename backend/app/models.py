"""Shared data shapes. Every finding is Evidence with a source URL: no source, no claim."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Evidence(BaseModel):
    lane: str                      # rera | mca | ibbi | authority | news
    claim: str                     # plain factual sentence shown to the user
    source_url: str
    snippet: str = ""              # verbatim text or extracted value backing the claim
    fetched_at: str = Field(default_factory=now_iso)


class Signals(BaseModel):
    """Facts extracted from all lanes. None means 'not checked / unavailable', never 'clean'."""
    # P1 Regulatory (RERA)
    registration_status: str | None = None          # e.g. "registered", "lapsed", "revoked"
    extensions_count: int | None = None
    delay_months: int | None = None                 # revised completion minus promised completion
    qprs_missed_last4: int | None = None
    rera_penalty_orders: int | None = None
    rera_complaints: int | None = None
    total_units: int | None = None
    # P2 Track record
    group_projects_total: int | None = None
    group_projects_delayed: int | None = None
    group_project_lapsed: bool | None = None
    # P3 Legal & insolvency
    promoter_in_cirp: bool | None = None
    sister_company_in_cirp: bool | None = None
    pending_cases: int | None = None
    # P4 Corporate health
    company_or_director_struck_off: bool | None = None
    recent_charge_creation: bool | None = None
    sarfaesi_notice: bool | None = None
    # P5 Land authority
    authority_defaulter: bool | None = None
    no_oc_past_due: bool | None = None
    # P6 Sentiment
    adverse_news_count: int | None = None


class LaneStatus(BaseModel):
    lane: str
    ok: bool
    message: str = ""


class Report(BaseModel):
    query: str
    project_name: str | None = None
    rera_number: str | None = None
    promoter_name: str | None = None
    rera_url: str | None = None
    signals: Signals
    evidence: list[Evidence]
    lanes: list[LaneStatus]
    score: dict[str, Any]
    created_at: str = Field(default_factory=now_iso)
