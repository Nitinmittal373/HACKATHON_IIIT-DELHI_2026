"""NeevScore: a deterministic, explainable 300-900 builder/project risk score.

The LLM never decides the score. This file does, so anyone can reproduce a score from the evidence.
Full rules, weights and limitations: docs/METHODOLOGY.md (keep the two in sync).

    P         = sum(weight_i * penalty_i)          penalty_i in 0..100 per pillar
    formula   = clip(900 - 6 * P, 300, 900)
    hard stop = verified serious event (lapsed/revoked registration, or insolvency covering this project)
                -> score capped at 449 and band "High risk"

Weights are initial design priors, not statistically validated. Say so when asked.
"""
from __future__ import annotations

from .models import Signals

VERSION = "1.1"
WEIGHTS = {
    "P1_regulatory": 0.30,
    "P2_track_record": 0.20,
    "P3_legal_insolvency": 0.25,
    "P4_corporate_health": 0.15,
    "P5_land_authority": 0.05,
    "P6_sentiment": 0.05,
}
PILLAR_NAMES = {
    "P1_regulatory": "Regulatory compliance (RERA)",
    "P2_track_record": "Delivery track record",
    "P3_legal_insolvency": "Legal & insolvency",
    "P4_corporate_health": "Company & financial health",
    "P5_land_authority": "Land authority & approvals",
    "P6_sentiment": "News & buyer sentiment",
}
REASON_TEXT = {
    "R01": "RERA registration lapsed or revoked",
    "R02": "Completion date extended {n} time(s), not counting blanket COVID-era extensions",
    "R03": "Running {n} months behind the original completion date",
    "R04": "{n} of the last 4 quarterly progress reports not filed",
    "R05": "{n} RERA complaint(s) or penalty order(s) found",
    "R06": "Promoter is in insolvency proceedings (CIRP) that cover this project or the whole company",
    "R06S": "Promoter has insolvency proceedings limited to a different project: requires review",
    "R06G": "A verified group company is in insolvency proceedings",
    "R06P": "An NCLT insolvency case names the promoter; whether it was admitted is not confirmed: requires review",
    "R06N": "News reports insolvency proceedings; no official record matched yet: requires review",
    "R07": "Company or a director is linked to struck-off or liquidated entities",
    "R08": "Listed as a defaulter by the land development authority",
    "R09": "Lender action (SARFAESI) or a new charge on company assets in the last 12 months",
    "R10": "{n} pending court case(s) found",
    "R11": "{n} distinct news report(s) of delays or buyer protests",
    "R12": "Some sources could not be checked: confidence reduced, score not lowered",
}
BANDS = [(750, "Low risk"), (600, "Watch"), (450, "Elevated"), (300, "High risk")]
HARD_STOP_CAP = 449
KEY_SIGNALS = ["registration_status", "delay_months", "qprs_missed_last4", "promoter_in_cirp",
               "company_or_director_struck_off", "authority_defaulter", "adverse_news_count"]
REVOKED = {"lapsed", "revoked", "expired", "cancelled", "deregistered"}


def _cap(x: float) -> float:
    return max(0.0, min(100.0, x))


def score(s: Signals) -> dict:
    reasons: list[dict] = []
    pillars: dict[str, float] = {}
    hard_stop: str | None = None

    def add(code: str, impact: float, pillar: str | None, review: bool = False, **fmt):
        reasons.append({"code": code, "impact": round(impact, 1), "pillar": pillar,
                        "text": REASON_TEXT[code].format(**fmt),
                        "status": "requires_review" if review else "verified"})

    # P1 Regulatory compliance (RERA)
    p = 0.0
    if s.registration_status and any(w in s.registration_status.lower() for w in REVOKED):
        p = 100
        hard_stop = "R01"
        add("R01", 100, "P1_regulatory")
    else:
        counted = max(0, (s.extensions_count or 0) - (s.force_majeure_extensions or 0))
        if counted:
            v = 30 + 20 * (counted - 1)
            p += v
            add("R02", v, "P1_regulatory", n=counted)
        if s.delay_months and s.delay_months > 12:
            v = 70 if s.delay_months > 24 else 40
            p += v
            add("R03", v, "P1_regulatory", n=s.delay_months)
        if s.qprs_missed_last4:
            v = 15 * s.qprs_missed_last4
            p += v
            add("R04", v, "P1_regulatory", n=s.qprs_missed_last4)
        n_orders = (s.rera_penalty_orders or 0) + (s.rera_complaints or 0)
        if n_orders:
            v = min(40, 20 * (s.rera_penalty_orders or 0) + 4 * (s.rera_complaints or 0))
            p += v
            add("R05", v, "P1_regulatory", n=n_orders)
    pillars["P1_regulatory"] = _cap(p)

    # P2 Delivery track record of the promoter group
    p = 0.0
    if s.group_projects_total:
        p += 100 * (s.group_projects_delayed or 0) / s.group_projects_total
    if s.group_project_lapsed:
        p += 40
    pillars["P2_track_record"] = _cap(p)

    # P3 Legal & insolvency. Precedence: official+in scope > official other project > group > news only
    p = 0.0
    if s.promoter_in_cirp and s.cirp_scope in (None, "company", "this_project"):
        p = 100
        hard_stop = hard_stop or "R06"
        add("R06", 100, "P3_legal_insolvency")
    elif s.promoter_in_cirp and s.cirp_scope == "other_project":
        p += 60
        add("R06S", 60, "P3_legal_insolvency", review=True)
    elif s.sister_company_in_cirp:
        p += 50
        add("R06G", 50, "P3_legal_insolvency")
    elif s.insolvency_case_found:
        p += 30
        add("R06P", 30, "P3_legal_insolvency", review=True)
    elif s.insolvency_reported_in_news:
        add("R06N", 0, "P3_legal_insolvency", review=True)
    if s.pending_cases:
        v = min(40, 5 * s.pending_cases)
        p += v
        add("R10", v, "P3_legal_insolvency", n=s.pending_cases)
    pillars["P3_legal_insolvency"] = _cap(p)

    # P4 Corporate / financial health. A charge alone is not default, so it weighs little.
    p = 0.0
    if s.company_or_director_struck_off:
        p += 40
        add("R07", 40, "P4_corporate_health")
    if s.sarfaesi_notice or s.recent_charge_creation:
        v = (60 if s.sarfaesi_notice else 0) + (10 if s.recent_charge_creation else 0)
        p += v
        add("R09", v, "P4_corporate_health")
    pillars["P4_corporate_health"] = _cap(p)

    # P5 Land authority & approvals (needs an attributable record naming the builder)
    p = 0.0
    if s.authority_defaulter:
        p += 70
        add("R08", 70, "P5_land_authority")
    if s.no_oc_past_due:
        p += 30
    pillars["P5_land_authority"] = _cap(p)

    # P6 Sentiment / news (count is of distinct stories, de-duplicated upstream)
    p = 0.0
    if s.adverse_news_count:
        p = min(60, 10 * s.adverse_news_count)
        add("R11", p, "P6_sentiment", review=True, n=s.adverse_news_count)
    pillars["P6_sentiment"] = _cap(p)

    weighted = sum(WEIGHTS[k] * pillars[k] for k in WEIGHTS)
    formula = int(round(max(300, min(900, 900 - 6 * weighted))))
    value = min(formula, HARD_STOP_CAP) if hard_stop else formula
    band = next(name for floor, name in BANDS if value >= floor)

    checked = [f for f in KEY_SIGNALS if getattr(s, f) is not None]
    confidence = round(len(checked) / len(KEY_SIGNALS), 2)
    if confidence < 1:
        reasons.append({"code": "R12", "impact": 0, "pillar": None, "text": REASON_TEXT["R12"],
                        "status": "verified"})

    # Never show a reassuring band when the key sources were not checked
    if not hard_stop:
        if s.registration_status is None or confidence < 0.5:
            band = "Not enough data"
        elif confidence < 0.8 and band == "Low risk":
            band = "Provisional: no red flags yet"

    reasons.sort(key=lambda r: r["impact"], reverse=True)
    return {
        "version": VERSION,
        "score": value,
        "band": band,
        "hard_stop": bool(hard_stop),
        "hard_stop_code": hard_stop,
        "formula_score": formula,
        "weighted_penalty": round(weighted, 2),
        "confidence": confidence,
        "signals_checked": checked,
        "signals_missing": [f for f in KEY_SIGNALS if f not in checked],
        "pillars": {k: {"name": PILLAR_NAMES[k], "weight": WEIGHTS[k], "penalty": round(v, 1),
                        "checked": _pillar_checked(k, s)} for k, v in pillars.items()},
        "reasons": reasons,
    }


def _pillar_checked(k: str, s: Signals) -> bool:
    fields = {
        "P1_regulatory": ["registration_status"],
        "P2_track_record": ["group_projects_total"],
        "P3_legal_insolvency": ["promoter_in_cirp"],
        "P4_corporate_health": ["company_or_director_struck_off"],
        "P5_land_authority": ["authority_defaulter"],
        "P6_sentiment": ["adverse_news_count"],
    }[k]
    return any(getattr(s, f) is not None for f in fields)
