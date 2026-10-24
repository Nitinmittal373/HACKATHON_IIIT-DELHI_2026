"""NeevScore: a deterministic, explainable 300-900 builder/project risk score.

The LLM never decides the score. This file does, so judges can read exactly why.

Formula:  NeevScore = 900 - 6 * sum(weight_i * penalty_i), clipped to 300..900
          where each pillar penalty_i is 0..100.
Pillars mirror how credit-rating agencies split developer risk
(regulatory, track record, legal, financial, approvals, sentiment).
Weights are transparent expert priors, not yet calibrated on data. Say so in the pitch.
"""
from __future__ import annotations

from .models import Signals

WEIGHTS = {
    "P1_regulatory": 0.30,
    "P2_track_record": 0.20,
    "P3_legal_insolvency": 0.25,
    "P4_corporate_health": 0.15,
    "P5_land_authority": 0.05,
    "P6_sentiment": 0.05,
}

REASON_TEXT = {
    "R01": "RERA registration lapsed or revoked",
    "R02": "Completion date extended {n} time(s)",
    "R03": "Running {n} months behind the promised completion date",
    "R04": "{n} of the last 4 quarterly progress reports (QPRs) not filed",
    "R05": "{n} RERA complaint(s) / penalty order(s) found",
    "R06": "Promoter or a sister company is in insolvency (CIRP)",
    "R07": "Company or a director is linked to struck-off entities",
    "R08": "Listed as a defaulter by the land development authority",
    "R09": "Lender action (SARFAESI) or recent new charges on assets",
    "R10": "{n} pending court case(s) found",
    "R11": "{n} news report(s) of delays or buyer protests (check dates in the evidence)",
    "R12": "Some sources could not be checked: confidence reduced",
}

BANDS = [(750, "Low risk"), (600, "Watch"), (450, "Elevated"), (300, "High risk")]


def _cap(x: float) -> float:
    return max(0.0, min(100.0, x))


def score(s: Signals) -> dict:
    reasons: list[tuple[str, float, str]] = []   # (code, penalty impact, text)
    pillars: dict[str, float] = {}
    hard_stop = False

    def add(code: str, impact: float, **fmt):
        reasons.append((code, impact, REASON_TEXT[code].format(**fmt)))

    # P1 Regulatory compliance (RERA)
    p = 0.0
    if s.registration_status and s.registration_status.lower() in {"lapsed", "revoked", "expired", "cancelled"}:
        p = 100; hard_stop = True; add("R01", 100)
    else:
        if s.extensions_count:
            v = 30 + 20 * (s.extensions_count - 1); p += v; add("R02", v, n=s.extensions_count)
        if s.delay_months and s.delay_months > 12:
            v = 70 if s.delay_months > 24 else 40; p += v; add("R03", v, n=s.delay_months)
        if s.qprs_missed_last4:
            v = 15 * s.qprs_missed_last4; p += v; add("R04", v, n=s.qprs_missed_last4)
        n_orders = (s.rera_penalty_orders or 0) + (s.rera_complaints or 0)
        if n_orders:
            v = min(40, 20 * (s.rera_penalty_orders or 0) + 4 * (s.rera_complaints or 0))
            p += v; add("R05", v, n=n_orders)
    pillars["P1_regulatory"] = _cap(p)

    # P2 Delivery track record of the promoter group
    p = 0.0
    if s.group_projects_total:
        p += 100 * (s.group_projects_delayed or 0) / s.group_projects_total
    if s.group_project_lapsed:
        p += 40
    pillars["P2_track_record"] = _cap(p)

    # P3 Legal & insolvency
    p = 0.0
    if s.promoter_in_cirp:
        p = 100; hard_stop = True; add("R06", 100)
    elif s.sister_company_in_cirp:
        p += 50; add("R06", 50)
    if s.pending_cases:
        v = min(40, 5 * s.pending_cases); p += v; add("R10", v, n=s.pending_cases)
    pillars["P3_legal_insolvency"] = _cap(p)

    # P4 Corporate / financial health
    p = 0.0
    if s.company_or_director_struck_off:
        p += 40; add("R07", 40)
    if s.sarfaesi_notice or s.recent_charge_creation:
        v = (60 if s.sarfaesi_notice else 0) + (20 if s.recent_charge_creation else 0)
        p += v; add("R09", v)
    pillars["P4_corporate_health"] = _cap(p)

    # P5 Land authority & approvals
    p = 0.0
    if s.authority_defaulter:
        p += 70; add("R08", 70)
    if s.no_oc_past_due:
        p += 30
    pillars["P5_land_authority"] = _cap(p)

    # P6 Sentiment / news
    p = 0.0
    if s.adverse_news_count:
        p = min(60, 10 * s.adverse_news_count); add("R11", p, n=s.adverse_news_count)
    pillars["P6_sentiment"] = _cap(p)

    weighted = sum(WEIGHTS[k] * pillars[k] for k in WEIGHTS)
    value = int(round(max(300, min(900, 900 - 6 * weighted))))
    band = next(name for floor, name in BANDS if value >= floor)
    if hard_stop:
        value, band = min(value, 449), "High risk"

    # Confidence = share of key signals we actually managed to check
    key_fields = ["registration_status", "delay_months", "qprs_missed_last4",
                  "promoter_in_cirp", "company_or_director_struck_off",
                  "authority_defaulter", "adverse_news_count"]
    checked = sum(getattr(s, f) is not None for f in key_fields)
    confidence = round(checked / len(key_fields), 2)
    if confidence < 1:
        reasons.append(("R12", 0, REASON_TEXT["R12"]))
    # Never show a reassuring score when the key sources were not checked
    if not hard_stop:
        if s.registration_status is None or confidence < 0.5:
            band = "Not enough data"
        elif confidence < 0.8 and band == "Low risk":
            band = "Provisional: no red flags yet"

    reasons.sort(key=lambda r: r[1], reverse=True)
    return {
        "score": value,
        "band": band,
        "hard_stop": hard_stop,
        "confidence": confidence,
        "pillars": {k: round(v, 1) for k, v in pillars.items()},
        "reasons": [{"code": c, "impact": round(i, 1), "text": t} for c, i, t in reasons],
    }
