"""Reads and writes for checks, findings and scores.

Each method opens a short session, so callers never hold ORM objects.
"""

import logging
from datetime import datetime

from sqlalchemy import Row, Select, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import CheckRow, FindingExtraRow, FindingRow, ProjectRow, ScoreRow, SourceRunRow
from app.models import (
    Check,
    CheckStatus,
    CheckSummary,
    DisplayScore,
    Driver,
    FamilyTree,
    Finding,
    Project,
    ReasonCode,
    RecentCheck,
    Score,
    ScoreV2,
    SourceRun,
)
from app.scoring.v2.from_runs import score_from_runs
from app.scoring.v2.reasons import DATA_UNAVAILABLE
from app.states.registry import state_of

logger = logging.getLogger(__name__)

# Keys the v1 score detail also holds for the v2 score and the family tree.
EXTRA_DETAIL = ("v2", "family")

# Finding fields stored in finding_extras instead of the findings table.
EXTRA_FIELDS = ("snippet", "total", "via")

# The home page card shows the three biggest reasons behind a score.
# The state is not stored: every number format belongs to exactly one state's RERA.
STATE_FIELDS = {"state", "state_name", "rera_name"}
# What search learned about a candidate; the stored project is the portal-confirmed record.
CANDIDATE_FIELDS = {"status", "sources"}
RECENT_DRIVERS = 3
RECENT_REASONS = 3


class Store:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def save_project(self, project: Project) -> None:
        with self._sessions.begin() as session:
            session.merge(ProjectRow(**project.model_dump(exclude=STATE_FIELDS | CANDIDATE_FIELDS)))

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

    def fail_unfinished_checks(self, now: datetime) -> int:
        """Mark checks left queued or running by a stopped process as failed; returns how many."""
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(CheckRow).where(CheckRow.status.in_(("queued", "running")))
            ).all()
            for row in rows:
                row.status = "failed"
                row.completed_at = now
            return len(rows)

    def get_check(self, check_id: str) -> Check | None:
        check = self._load_check(check_id)
        if check is None:
            return None
        score = self.get_score_v2(check_id, check)
        if score is None:
            return check
        return check.model_copy(update={"display_score": DisplayScore.of(score)})

    def _load_check(self, check_id: str) -> Check | None:
        with self._sessions() as session:
            row = session.get(CheckRow, check_id)
            if row is None:
                return None
            project = session.get_one(ProjectRow, row.rera_id)
            runs = session.scalars(
                select(SourceRunRow)
                .where(SourceRunRow.check_id == check_id)
                .order_by(SourceRunRow.id)
            )
            return Check(
                id=row.id,
                rera_id=row.rera_id,
                state=state_of(row.rera_id),
                details_url=project.details_url,
                status=row.status,  # type: ignore[arg-type]  # written only from CheckStatus
                started_at=row.started_at,
                completed_at=row.completed_at,
                sources=[_source_run(run) for run in runs],
            )

    def count_checks_since(self, since: datetime) -> int:
        """How many checks were started since then; each one costs live agent runs."""
        with self._sessions() as session:
            return (
                session.scalar(
                    select(func.count()).select_from(CheckRow).where(CheckRow.started_at >= since)
                )
                or 0
            )

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
        by_id = {row.CheckRow.id: self._summary(row) for row in rows}
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
        return [self._recent(row, read.get(row.CheckRow.id, 0)) for row in picked]

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
        # No source, no claim: a finding without a link is never stored.
        if not finding.source_url.strip():
            raise ValueError(f"Finding {finding.kind!r} has no source_url")
        fields = finding.model_dump()
        extras = {name: fields.pop(name) for name in EXTRA_FIELDS if fields[name] is not None}
        for name in EXTRA_FIELDS:
            fields.pop(name, None)
        with self._sessions.begin() as session:
            session.add(FindingRow(check_id=check_id, **fields))
            if extras:
                session.add(FindingExtraRow(finding_id=finding.id, data=extras))

    def list_findings(self, check_id: str) -> list[Finding]:
        with self._sessions() as session:
            rows = session.scalars(select(FindingRow).where(FindingRow.check_id == check_id))
            extras = {
                extra.finding_id: extra.data
                for extra in session.scalars(
                    select(FindingExtraRow)
                    .join(FindingRow, FindingRow.id == FindingExtraRow.finding_id)
                    .where(FindingRow.check_id == check_id)
                )
            }
            return [_finding(row, extras.get(row.id, {})) for row in rows]

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

    def save_score_v2(self, check_id: str, score: ScoreV2) -> None:
        """Keep the v2 score inside the stored v1 detail, which has no fixed columns."""
        with self._sessions.begin() as session:
            row = session.get_one(ScoreRow, check_id)
            row.detail = {**row.detail, "v2": score.model_dump(mode="json")}

    def save_family(self, check_id: str, tree: FamilyTree) -> None:
        with self._sessions.begin() as session:
            row = session.get_one(ScoreRow, check_id)
            row.detail = {**row.detail, "family": tree.model_dump(mode="json")}

    def get_family(self, check_id: str) -> FamilyTree | None:
        with self._sessions() as session:
            row = session.get(ScoreRow, check_id)
            stored = row.detail.get("family") if row else None
            return FamilyTree.model_validate(stored) if stored else None

    def get_score_v2(self, check_id: str, check: Check | None = None) -> ScoreV2 | None:
        """The stored v2 score; a finished check made before v2 is re-scored from its findings.

        Scoring is deterministic, so the same findings and source runs always give the same
        number. Nothing is written: the old check is left exactly as it was stored.
        """
        with self._sessions() as session:
            row = session.get(ScoreRow, check_id)
            stored = row.detail.get("v2") if row else None
        if row is None:
            return None
        if stored:
            return ScoreV2.model_validate(stored)
        check = check or self._load_check(check_id)
        if check is None:
            return None
        try:
            return score_from_runs(self.list_findings(check_id), check.sources)
        except Exception:
            logger.exception("v2 re-score failed for check %s", check_id)
            return None

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
                **{k: v for k, v in row.detail.items() if k not in EXTRA_DETAIL},  # type: ignore[arg-type]
            )

    def _summary(self, row: Row[tuple[CheckRow, ProjectRow, ScoreRow]]) -> CheckSummary:
        check, project, score = row.CheckRow, row.ProjectRow, row.ScoreRow
        v2 = self._score_v2_of(row)
        return CheckSummary.model_validate(
            {
                "id": check.id,
                "rera_id": check.rera_id,
                "state": state_of(check.rera_id),
                "details_url": project.details_url,
                "project": project.name,
                "promoter": project.promoter,
                "status": check.status,
                "score": score.value if score else None,
                "band": score.band if score else None,
                "confidence": score.confidence if score else None,
                "display_score": DisplayScore.of(v2) if v2 else None,
                "created_at": check.started_at,
                "completed_at": check.completed_at,
            }
        )

    def _recent(
        self, row: Row[tuple[CheckRow, ProjectRow, ScoreRow]], sources_read: int
    ) -> RecentCheck:
        drivers = row.ScoreRow.detail.get("drivers", []) if row.ScoreRow else []
        v2 = self._score_v2_of(row)
        costing = [r for r in (v2.reason_codes if v2 else []) if r.code != DATA_UNAVAILABLE]
        return RecentCheck(
            **self._summary(row).model_dump(),
            registered_on=row.ProjectRow.registered_on,
            sources_read=sources_read,
            drivers=[Driver.model_validate(driver) for driver in drivers[:RECENT_DRIVERS]],
            reasons=[ReasonCode.model_validate(r) for r in costing[:RECENT_REASONS]],
        )

    def _score_v2_of(self, row: Row[tuple[CheckRow, ProjectRow, ScoreRow]]) -> ScoreV2 | None:
        """The row's own stored v2 score, so listing many checks needs no extra queries."""
        if row.ScoreRow is None:
            return None
        stored = row.ScoreRow.detail.get("v2")
        if stored:
            return ScoreV2.model_validate(stored)
        return self.get_score_v2(row.CheckRow.id)


def _summary_query() -> Select[tuple[CheckRow, ProjectRow, ScoreRow]]:
    return (
        select(CheckRow, ProjectRow, ScoreRow)
        .join(ProjectRow, ProjectRow.rera_id == CheckRow.rera_id)
        .outerjoin(ScoreRow, ScoreRow.check_id == CheckRow.id)
    )


def _project(row: ProjectRow) -> Project:
    return Project(
        rera_id=row.rera_id,
        state=state_of(row.rera_id),
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


def _finding(row: FindingRow, extras: dict[str, object]) -> Finding:
    fields = {name: getattr(row, name) for name in Finding.model_fields if name not in EXTRA_FIELDS}
    return Finding.model_validate({**fields, **extras})
