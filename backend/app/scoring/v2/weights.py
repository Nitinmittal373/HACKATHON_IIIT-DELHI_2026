"""NeevScore v2 weights, penalties and bands. Keep in sync with docs/scoring.md.

These are transparent expert priors. They are meant to be calibrated on labelled lists of
stalled projects, not read as statistics.
"""

from app.scoring.v2.models import BandV2, PillarId

SCALE_TOP = 900
SCALE_FLOOR = 300
# 100 weighted penalty points use up the whole 600-point range.
POINTS_PER_PENALTY = 6
# A hard stop can never leave a project looking better than the top of the High band.
HARD_STOP_CAP = 449
MIN_CONFIDENCE_FOR_BAND = 0.5

PILLAR_WEIGHTS: dict[PillarId, float] = {
    "P1": 0.30,
    "P2": 0.20,
    "P3": 0.25,
    "P4": 0.15,
    "P5": 0.05,
    "P6": 0.05,
}
PILLAR_NAMES: dict[PillarId, str] = {
    "P1": "Regulatory compliance (RERA)",
    "P2": "Delivery track record",
    "P3": "Legal and insolvency",
    "P4": "Financial and corporate health",
    "P5": "Land authority and approvals",
    "P6": "Sentiment and news",
}
# News is secondary, so it may never take the whole pillar.
PILLAR_CAPS: dict[PillarId, int] = dict.fromkeys(PILLAR_WEIGHTS, 100) | {"P6": 60}

# Lower bound of each band, highest first.
BANDS: list[tuple[int, BandV2]] = [(750, "Low"), (600, "Watch"), (450, "Elevated"), (0, "High")]
BAND_LABELS: dict[BandV2, str] = {
    "Low": "Low risk",
    "Watch": "Watch",
    "Elevated": "Elevated risk",
    "High": "High risk",
    "insufficient_evidence": "Not enough evidence yet",
}

EXTENSION_FIRST = 30
EXTENSION_EACH_MORE = 20
# (more than this many months the revised date is after the promised one, penalty), largest first.
DELAY_STEPS: list[tuple[int, int]] = [(24, 70), (12, 40)]
QPR_MISSED_EACH = 15
QPR_MISSED_CAP = 60
PENALTY_ORDER_EACH = 20
COMPLAINT_EACH = 10
GROUP_PROJECT_LAPSED = 40
SISTER_COMPANY_INSOLVENT = 50
CASE_EACH = 5
CASE_CAP = 40
STRUCK_OFF_OR_DISQUALIFIED = 40
CHARGE_RECENT = 20
LATE_FILINGS = 20
SARFAESI_NOTICE = 60
LAND_DEFAULTER = 70
LAND_PACKAGE_DEPOSIT_FAILED = 50
OC_CC_PAST_DUE = 30
NEWS_PER_ARTICLE = 10
