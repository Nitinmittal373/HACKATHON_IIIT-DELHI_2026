"""Source results kept per (source, entity, day), so a second check of the same builder does
not read the same public pages again.

A cached result keeps the time it was really read: the report shows that time, never the time
of the check that reused it. Blocked, failed or empty reads are never kept, so an unreadable
page is retried next time instead of being remembered as a result.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db import SourceCacheRow
from app.matching import normalize
from app.models import CheckKey, FamilyTree, Finding, Project, SourceName

# How many days a result is reused. Company-level group facts change slowly.
TTL_DAYS: dict[SourceName, int] = {
    "registry": 1,
    "insolvency": 1,
    "land": 1,
    "news": 1,
    "group": 7,
    "sarfaesi": 1,
}


@dataclass(frozen=True)
class CachedRead:
    read_at: datetime
    findings: list[Finding]
    checks_read: tuple[CheckKey, ...]
    family: FamilyTree | None = None

    def fresh_copies(self) -> list[Finding]:
        """The findings under new ids, so each check owns its own rows; read times are kept."""
        return [f.model_copy(update={"id": uuid.uuid4().hex}) for f in self.findings]


def entity_for(source: SourceName, project: Project) -> str | None:
    """What a source's answer depends on; None when the source is never cached."""
    promoter = normalize(project.promoter)
    if source not in TTL_DAYS or not promoter:
        return None
    if source in ("insolvency", "news"):
        return f"{promoter}|{project.rera_id}"
    if source == "land":
        return f"{promoter}|{normalize(project.district)}"
    return promoter


class SourceCache:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self, source: SourceName, entity: str, today: date) -> CachedRead | None:
        oldest = today - timedelta(days=TTL_DAYS[source] - 1)
        with self._sessions() as session:
            row = session.scalars(
                select(SourceCacheRow)
                .where(
                    SourceCacheRow.source == source,
                    SourceCacheRow.entity == entity,
                    SourceCacheRow.day >= oldest,
                )
                .order_by(SourceCacheRow.day.desc())
                .limit(1)
            ).first()
            if row is None:
                return None
            family = (row.extras or {}).get("family")
            return CachedRead(
                read_at=row.read_at,
                family=FamilyTree.model_validate(family) if family else None,
                findings=[Finding.model_validate(f) for f in row.findings],
                checks_read=tuple(row.checks_read),  # type: ignore[arg-type]  # saved from CheckKey
            )

    def put(
        self,
        source: SourceName,
        entity: str,
        today: date,
        read_at: datetime,
        findings: list[Finding],
        checks_read: tuple[CheckKey, ...],
        family: FamilyTree | None = None,
    ) -> None:
        extras = {"family": family.model_dump(mode="json")} if family else {}
        with self._sessions.begin() as session:
            session.merge(
                SourceCacheRow(
                    source=source,
                    entity=entity,
                    day=today,
                    read_at=read_at,
                    checks_read=list(checks_read),
                    findings=[f.model_dump(mode="json") for f in findings],
                    extras=extras,
                )
            )
