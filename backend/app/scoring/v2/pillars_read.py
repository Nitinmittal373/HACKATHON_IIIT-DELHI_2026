"""Which pillars had at least one source read, for the v2 confidence meter."""

from collections.abc import Iterable

from app.models import CheckKey, SourceName
from app.scoring.v2.models import PillarId

# A pillar counts as read when any of its key checks was read or any of its sources finished.
PILLAR_CHECKS: dict[PillarId, tuple[CheckKey, ...]] = {
    "P1": ("registration",),
    # The complaint counts on UP-RERA's own summary page speak for the promoter (P2) and for
    # this project (P3), so reading them is a real, if partial, read of both pillars.
    "P2": ("rera_complaints",),
    "P3": ("insolvency", "consumer_cases", "rera_complaints"),
    "P4": ("company_status",),
    "P5": ("land_dues",),
}
PILLAR_SOURCES: dict[PillarId, tuple[SourceName, ...]] = {
    "P2": ("group",),
    "P6": ("news",),
}
# What the UP-RERA complaint counts alone can say about a pillar, when nothing else was read.
COMPLAINTS_ONLY: dict[PillarId, str] = {"P2": "UP-RERA complaints", "P3": "UP-RERA complaints"}


def pillars_read(
    checks_read: Iterable[CheckKey], completed_sources: Iterable[SourceName]
) -> list[PillarId]:
    checks, sources = set(checks_read), set(completed_sources)
    by_checks = [p for p, keys in PILLAR_CHECKS.items() if checks & set(keys)]
    by_sources = [p for p, names in PILLAR_SOURCES.items() if sources & set(names)]
    return sorted({*by_checks, *by_sources})


def partly_read(
    checks_read: Iterable[CheckKey], completed_sources: Iterable[SourceName]
) -> dict[PillarId, str]:
    """Pillars read only through the UP-RERA complaint counts, and what that covered."""
    checks, sources = set(checks_read), set(completed_sources)
    partly: dict[PillarId, str] = {}
    for pillar, covered in COMPLAINTS_ONLY.items():
        others = set(PILLAR_CHECKS[pillar]) - {"rera_complaints"}
        elsewhere = checks & others or sources & set(PILLAR_SOURCES.get(pillar, ()))
        if "rera_complaints" in checks and not elsewhere:
            partly[pillar] = covered
    return partly
