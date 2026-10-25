"""Which pillars had at least one source read, for the v2 confidence meter."""

from collections.abc import Iterable

from app.models import CheckKey, SourceName
from app.scoring.v2.models import PillarId

# A pillar counts as read when any of its key checks was read or any of its sources finished.
PILLAR_CHECKS: dict[PillarId, tuple[CheckKey, ...]] = {
    "P1": ("registration",),
    "P3": ("insolvency", "consumer_cases"),
    "P4": ("company_status",),
    "P5": ("land_dues",),
}
PILLAR_SOURCES: dict[PillarId, tuple[SourceName, ...]] = {
    "P2": ("group",),
    "P6": ("news",),
}


def pillars_read(
    checks_read: Iterable[CheckKey], completed_sources: Iterable[SourceName]
) -> list[PillarId]:
    checks, sources = set(checks_read), set(completed_sources)
    by_checks = [p for p, keys in PILLAR_CHECKS.items() if checks & set(keys)]
    by_sources = [p for p, names in PILLAR_SOURCES.items() if sources & set(names)]
    return sorted([*by_checks, *by_sources])
