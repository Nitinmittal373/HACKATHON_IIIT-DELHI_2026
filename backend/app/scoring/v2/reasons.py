"""Reason codes: the credit-report style explanation of why a score is what it is.

R12 never costs points. It says which records could not be read, because a missing record
must not look like a clean one. R13 and R14 are additions to the planned R01-R12 list: R13 is
the builder's own record (complaints across its projects, delays elsewhere in the group) and
R14 late registry filings, which have no other code.
"""

from collections.abc import Callable

from app.models import Finding
from app.scoring.v2.models import PillarId, ReasonCode

DATA_UNAVAILABLE = "R12"


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _count(findings: list[Finding]) -> int:
    return sum(f.count or 0 for f in findings)


def _extended(fs: list[Finding]) -> str:
    return f"Completion extended {_plural(max(f.count or 0 for f in fs), 'time', 'times')}"


def _delay(fs: list[Finding]) -> str:
    return f"Revised completion date {max(f.months or 0 for f in fs)} months after the promised one"


def _complaints_or_orders(fs: list[Finding]) -> str:
    orders = _count([f for f in fs if f.kind == "rera_penalty_order"])
    complaints = _count([f for f in fs if f.kind == "project_complaints"])
    parts = []
    if complaints:
        parts.append(_plural(complaints, "RERA complaint", "RERA complaints"))
    if orders:
        parts.append(_plural(orders, "penalty order", "penalty orders"))
    text = " and ".join(parts)
    return text[:1].upper() + text[1:]


def _builder_record(fs: list[Finding]) -> str:
    parts = []
    if any(f.kind == "promoter_complaints" for f in fs):
        parts.append("Builder complaint record")
    if any(f.kind.startswith("group_") for f in fs):
        parts.append("Other projects of the same group delayed or lapsed")
    return "; ".join(parts)


LABELS: dict[str, Callable[[list[Finding]], str]] = {
    "R01": lambda fs: "UP-RERA registration lapsed or revoked",
    "R02": _extended,
    "R03": _delay,
    "R04": lambda fs: f"QPRs missed ({_count(fs)} of the last 4 quarters)",
    "R05": _complaints_or_orders,
    "R06": lambda fs: "Promoter or sister company in insolvency (CIRP or liquidation)",
    "R07": lambda fs: "Director linked to struck-off, disqualified or insolvent companies",
    "R08": lambda fs: "Land authority dues or approvals default",
    "R09": lambda fs: "Charges or SARFAESI action on the builder's assets",
    "R10": lambda fs: f"Pending litigation ({_plural(_count(fs), 'case', 'cases')})",
    "R11": lambda fs: f"Adverse news or protests ({_plural(len(fs), 'article', 'articles')})",
    "R13": _builder_record,
    "R14": lambda fs: "Late filings with the company registry",
}


def label_for(code: str, findings: list[Finding]) -> str:
    return LABELS[code](findings)


def unavailable(unread: list[PillarId], names: dict[PillarId, str]) -> ReasonCode | None:
    """R12 for the pillars with no source read; None when everything was read."""
    if not unread:
        return None
    label = "Data unavailable: " + ", ".join(names[p] for p in unread)
    return ReasonCode(code=DATA_UNAVAILABLE, label=label, finding_ids=[], points=0.0)
