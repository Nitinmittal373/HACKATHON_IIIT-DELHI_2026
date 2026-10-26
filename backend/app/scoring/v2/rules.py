"""What each kind of finding costs in NeevScore v2, and which reason code explains it.

A kind that is not listed here never costs points; it still shows in the evidence list.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models import Finding
from app.scoring.v2 import weights as w
from app.scoring.v2.models import PillarId


@dataclass(frozen=True)
class Rule:
    pillar: PillarId
    code: str
    penalty: Callable[[Finding], int]


def _extensions(f: Finding) -> int:
    count = f.count or 0
    return w.EXTENSION_FIRST + w.EXTENSION_EACH_MORE * (count - 1) if count > 0 else 0


def _delay(f: Finding) -> int:
    months = f.months or 0
    return next((penalty for limit, penalty in w.DELAY_STEPS if months > limit), 0)


def _per(each: int, cap: int = 100) -> Callable[[Finding], int]:
    return lambda f: min(cap, each * (f.count or 0))


def _flat(penalty: int) -> Callable[[Finding], int]:
    return lambda _: penalty


def _group_delay_share(f: Finding) -> int:
    """Share of the group's projects delayed more than 12 months, 0-100."""
    if not f.count or not f.total:
        return 0
    return min(100, round(100 * f.count / f.total))


def _recent_news(f: Finding) -> int:
    """Only an article known to be from the last 12 months counts; an undated one is not proved."""
    if f.occurred_on is None or not 0 <= (f.read_on - f.occurred_on).days <= w.NEWS_WINDOW_DAYS:
        return 0
    return w.NEWS_PER_ARTICLE


def _insolvency(f: Finding) -> int:
    if f.scope in ("company", "this_project") and f.reliability == "primary":
        return 100
    # Anything weaker, or limited to another project, is a sister-company signal.
    return w.SISTER_COMPANY_INSOLVENT


RULES: dict[str, Rule] = {
    "registration_revoked": Rule("P1", "R01", _flat(100)),
    "completion_extended": Rule("P1", "R02", _extensions),
    "delay_vs_promised": Rule("P1", "R03", _delay),
    "qpr_missed": Rule("P1", "R04", _per(w.QPR_MISSED_EACH, w.QPR_MISSED_CAP)),
    "rera_penalty_order": Rule("P1", "R05", _per(w.PENALTY_ORDER_EACH)),
    "group_delay_share": Rule("P2", "R13", _group_delay_share),
    "group_project_lapsed": Rule("P2", "R13", _flat(w.GROUP_PROJECT_LAPSED)),
    "insolvency_scope": Rule("P3", "R06", _insolvency),
    "group_company_insolvent": Rule("P3", "R06", _flat(w.SISTER_COMPANY_INSOLVENT)),
    "project_complaints": Rule("P3", "R05", _per(w.COMPLAINT_EACH)),
    "consumer_cases": Rule("P3", "R10", _per(w.CASE_EACH, w.CASE_CAP)),
    "company_struck_off": Rule("P4", "R07", _flat(w.STRUCK_OFF_OR_DISQUALIFIED)),
    "director_struck_off": Rule("P4", "R07", _flat(w.STRUCK_OFF_OR_DISQUALIFIED)),
    "director_disqualified": Rule("P4", "R07", _flat(w.STRUCK_OFF_OR_DISQUALIFIED)),
    "charge_created": Rule("P4", "R09", _flat(w.CHARGE_RECENT)),
    "mca_late_filing": Rule("P4", "R14", _flat(w.LATE_FILINGS)),
    "sarfaesi_notice": Rule("P4", "R09", _flat(w.SARFAESI_NOTICE)),
    "land_dues": Rule("P5", "R08", _flat(w.LAND_DEFAULTER)),
    "land_package_default": Rule("P5", "R08", _flat(w.LAND_PACKAGE_DEPOSIT_FAILED)),
    "oc_cc_past_due": Rule("P5", "R08", _flat(w.OC_CC_PAST_DUE)),
    "news_story": Rule("P6", "R11", _recent_news),
}


def hard_stop_reason(finding: Finding) -> str | None:
    """Only an official page can stop a project outright."""
    if finding.kind == "registration_revoked":
        return "UP-RERA registration lapsed or revoked"
    if (
        finding.kind == "insolvency_scope"
        and finding.reliability == "primary"
        and finding.scope in ("company", "this_project")
    ):
        covered = "the promoter company" if finding.scope == "company" else "this project"
        return f"Insolvency (CIRP) covers {covered}, per an official page"
    return None
