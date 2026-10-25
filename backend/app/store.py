"""Reads and writes for checks, findings and scores.

Each method opens a short session, so callers never hold ORM objects.
"""

from datetime import datetime

from sqlalchemy import Row, Select, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import CheckRow, FindingRow, ProjectRow, ScoreRow, SourceRunRow
from app.models import (
    Check,
    CheckStatus,
    CheckSummary,
    Driver,
    Finding,
    Project,
    RecentCheck,
    Score,
    SourceRun,
)

# The home page card shows the three biggest reasons behind a score.
RECENT_DRIVERS = 3


class Store:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save_project(self, project: Project) -> None:
        with self._sessions.begin() as session:
            session.merge(ProjectRow(**project.model_dump()))

    def get_project(self, rera_id: str) -> Project | None:
        with self._sessions() as session:
            row = session.get(ProjectRow, rera_id)
            return _project(row) if row else None

    def create_check(self, check_id: str, rera_id: str, started_at: datetime) -> None:
        with self._sessions.begin() as session:
            session.add(
                CheckRow(id=check_id, rera_id=rera_id, status="queued", started_at=started_at)
            )

    def set_check_status(
        self, check_id: str, status: CheckStatus, completed_at: datetime | None = None
    ) -> None:
        with self._sessions.begin() as session:
            row = session.get_one(CheckRow, check_id)
            row.status = status
            row.completed_at = completed_at

    def get_check(self, check_id: str) -> Check | None:
        with self._sessions() as session:
            row = session.get(CheckRow, check_id)
            if row is None:
                return None
            project = session.get_one(ProjectRow, row.rera_id)
            runs = session.scalars(
                select(SourceRunRow).where(SourceRunRow.check_id == check_id).order_by(
                    SourceRunRow.id
                )
            )
            return Check(
                id=row.id,
                rera_id=row.rera_id,
                details_url=project.details_url,
                status=row.status,  # type: ignore[arg-type]  # written only from CheckStatus
                started_at=row.started_at,
                completed_at=row.completed_at,
                sources=[_source_run(run) for run in runs],
            )

    def count_checks_since(self, since: datetime) -> int:
        """How many checks were started since then; each one costs live agent runs."""
        with self._sessions() as session:
            return session.scalar(
                select(func.count()).select_from(CheckRow).where(CheckRow.started_at >= since)
            ) or 0

    def latest_completed_check(self, rera_id: str, since: datetime | None = None) -> Check | None:
        """The newest finished check of a project, optionally only if it finished after `since`."""
        with self._sessions() as session:
            query = select(CheckRow.id).where(
                CheckRow.rera_id == rera_id, CheckRow.status == "completed"
            )
            if since is not None:
                query = query.where(CheckRow.completed_at >= since)
            check_id = session.scalar(query.order_by(CheckRow.completed_at.desc()).limit(1))
        return self.get_check(check_id) if check_id else None

    def summaries(self, check_ids: list[str]) -> list[CheckSummary]:
        """The checks among these ids that exist, in the order asked; unknown ids are skipped."""
        with self._sessions() as session:
            rows = session.execute(_summary_query().where(CheckRow.id.in_(check_ids))).all()
        by_id = {row.CheckRow.id: _summary(row) for row in rows}
        return [by_id[check_id] for check_id in check_ids if check_id in by_id]

    def recent_completed(self, limit: int) -> list[RecentCheck]:
        """The newest finished check of each project, newest first."""
        query = _summary_query().where(CheckRow.status == "completed")
        query = query.order_by(CheckRow.completed_at.desc()).limit(limit * 4)
        with self._sessions() as session:
            picked: list[Row[tuple[CheckRow, ProjectRow, ScoreRow]]] = []
            for row in session.execute(query):
                seen = {p.CheckRow.rera_id for p in picked}
                if row.CheckRow.rera_id not in seen and len(picked) < limit:
                    picked.append(row)
            read = self._sources_read(session, [row.CheckRow.id for row in picked])
        return [_recent(row, read.get(row.CheckRow.id, 0)) for row in picked]

    def _sources_read(self, session: Session, check_ids: list[str]) -> dict[str, int]:
        counts = session.execute(
            select(SourceRunRow.check_id, func.count())
            .where(SourceRunRow.check_id.in_(check_ids), SourceRunRow.status == "completed")
            .group_by(SourceRunRow.check_id)
        ).all()
        return {check_id: count for check_id, count in counts}

    def save_source_run(self, check_id: str, run: SourceRun) -> None:
        """Insert the run, or update it if this source already has one for the check."""
        with self._sessions.begin() as session:
            row = session.scalar(
                select(SourceRunRow).where(
                    SourceRunRow.check_id == check_id, SourceRunRow.source == run.source
                )
            )
            if row is None:
                row = SourceRunRow(check_id=check_id, source=run.source)
                session.add(row)
            row.status = run.status
            row.live_url = run.live_url
            row.message = run.message
            row.checks_read = list(run.checks_read)

    def add_finding(self, check_id: str, finding: Finding) -> None:
        with self._sessions.begin() as session:
            session.add(FindingRow(check_id=check_id, **finding.model_dump()))

    def list_findings(self, check_id: str) -> list[Finding]:
        with self._sessions() as session:
            rows = session.scalars(select(FindingRow).where(FindingRow.check_id == check_id))
            return [_finding(row) for row in rows]

    def save_score(self, check_id: str, score: Score) -> None:
        detail = score.model_dump(
            mode="json",
            include={
                "band_label",
                "provisional",
                "hard_stop_reason",
                "drivers",
                "areas",
                "checks_unread",
            },
        )
        points = {driver.finding_id: driver.points for driver in score.drivers}
        with self._sessions.begin() as session:
            session.merge(
                ScoreRow(
                    check_id=check_id,
                    value=score.value,
                    band=score.band,
                    confidence=score.confidence,
                    hard_stop=score.hard_stop,
                    detail=detail,
                )
            )
            for row in session.scalars(select(FindingRow).where(FindingRow.check_id == check_id)):
                row.points = points.get(row.id, 0.0)

    def get_score(self, check_id: str) -> Score | None:
        with self._sessions() as session:
            row = session.get(ScoreRow, check_id)
            if row is None:
                return None
            return Score(
                value=row.value,
                band=row.band,  # type: ignore[arg-type]  # written only from Band
                confidence=row.confidence,
                hard_stop=row.hard_stop,
                **row.detail,  # type: ignore[arg-type]
            )


def _summary_query() -> Select[tuple[CheckRow, ProjectRow, ScoreRow]]:
    return (
        select(CheckRow, ProjectRow, ScoreRow)
        .join(ProjectRow, ProjectRow.rera_id == CheckRow.rera_id)
        .outerjoin(ScoreRow, ScoreRow.check_id == CheckRow.id)
    )


def _summary(row: Row[tuple[CheckRow, ProjectRow, ScoreRow]]) -> CheckSummary:
    check, project, score = row.CheckRow, row.ProjectRow, row.ScoreRow
    return CheckSummary.model_validate(
        {
            "id": check.id,
            "rera_id": check.rera_id,
            "details_url": project.details_url,
            "project": project.name,
            "promoter": project.promoter,
            "status": check.status,
            "score": score.value if score else None,
            "band": score.band if score else None,
            "confidence": score.confidence if score else None,
            "created_at": check.started_at,
            "completed_at": check.completed_at,
        }
    )


def _recent(row: Row[tuple[CheckRow, ProjectRow, ScoreRow]], sources_read: int) -> RecentCheck:
    drivers = row.ScoreRow.detail.get("drivers", []) if row.ScoreRow else []
    return RecentCheck(
        **_summary(row).model_dump(),
        registered_on=row.ProjectRow.registered_on,
        sources_read=sources_read,
        drivers=[Driver.model_validate(driver) for driver in drivers[:RECENT_DRIVERS]],
    )


def _project(row: ProjectRow) -> Project:
    return Project(
        rera_id=row.rera_id,
        name=row.name,
        promoter=row.promoter,
        registered_on=row.registered_on,
        district=row.district,
        details_url=row.details_url,
    )


def _source_run(row: SourceRunRow) -> SourceRun:
    return SourceRun.model_validate(
        {
            "source": row.source,
            "status": row.status,
            "live_url": row.live_url,
            "message": row.message,
            "checks_read": row.checks_read,
        }
    )


def _finding(row: FindingRow) -> Finding:
    fields = {name: getattr(row, name) for name in Finding.model_fields}
    return Finding.model_validate(fields)
