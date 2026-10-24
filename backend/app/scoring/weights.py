"""NeevScore weights, penalties and bands. Keep in sync with docs/scoring.md."""

from app.models import Area, Band, CheckKey

AREA_WEIGHTS: dict[Area, float] = {
    "rera": 0.25,
    "execution": 0.20,
    "legal": 0.15,
    "financial": 0.15,
    "builder_history": 0.15,
    "news": 0.10,
}

AREA_LABELS: dict[Area, str] = {
    "rera": "UP-RERA compliance",
    "execution": "Project execution",
    "legal": "Legal and courts",
    "financial": "Financial and insolvency",
    "builder_history": "Builder history",
    "news": "News",
}

# News is a secondary source, so it can never take a whole area's weight.
AREA_CAPS: dict[Area, int] = {area: 100 for area in AREA_WEIGHTS} | {"news": 60}

# Lower bound of each band, highest first.
BANDS: list[tuple[int, Band]] = [(80, "Low"), (60, "Moderate"), (40, "High"), (0, "Critical")]
HARD_STOP_CAP = 39

KEY_CHECKS: tuple[CheckKey, ...] = (
    "registration",
    "completion_date",
    "extensions",
    "company_status",
    "insolvency",
    "land_dues",
    "consumer_cases",
)

# The area each kind of finding is scored in. Kinds not listed never cost points.
KIND_AREAS: dict[str, Area] = {
    "registration_revoked": "rera",
    "completion_extended": "execution",
    "past_end_date": "execution",
    "insolvency_scope": "financial",
    "land_dues": "financial",
    "news_story": "news",
}

EXTENSION_FIRST = 30
EXTENSION_EACH_MORE = 20
# (more than this many months past the latest approved end date, penalty), largest first.
DELAY_STEPS: list[tuple[int, int]] = [(24, 70), (12, 40)]
INSOLVENCY_OTHER_PROJECT = 60
LAND_DUES = 70
NEWS_PER_STORY = 10
