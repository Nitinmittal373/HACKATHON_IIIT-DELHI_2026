"""Reads and writes for watches and alerts."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import AlertRow, ProjectRow, WatchRow
from app.sentinel.models import Alert, Diff, FindingChange, Language, Watch


class SentinelStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def count_watches(self, email: str) -> int:
        with self._sessions() as session:
            query = select(func.count()).select_from(WatchRow).where(WatchRow.email == email)
            return session.scalar(query) or 0

    def find_watch(self, email: str, rera_id: str) -> Watch | None:
        with self._sessions() as session:
            row = session.scalar(
                select(WatchRow).where(WatchRow.email == email, WatchRow.rera_id == rera_id)
            )
            return _watch(row) if row else None

    def add_watch(
        self,
        *,
        email: str,
        rera_id: str,
        language: Language,
        created_at: datetime,
        baseline_check_id: str | None,
    ) -> Watch:
        row = WatchRow(
            id=uuid.uuid4().hex,
            rera_id=rera_id,
            email=email,
            language=language,
            created_at=created_at,
            baseline_check_id=baseline_check_id,
        )
        with self._sessions.begin() as session:
            session.add(row)
        return _watch(row)

    def watches_for_project(self, rera_id: str) -> list[Watch]:
        with self._sessions() as session:
            rows = session.scalars(select(WatchRow).where(WatchRow.rera_id == rera_id))
            return [_watch(row) for row in rows]

    def watched_projects(self) -> list[str]:
        with self._sessions() as session:
            query = select(WatchRow.rera_id).distinct().order_by(WatchRow.rera_id)
            return list(session.scalars(query))

    def set_baseline(self, watch_id: str, check_id: str) -> None:
        with self._sessions.begin() as session:
            session.get_one(WatchRow, watch_id).baseline_check_id = check_id

    def add_alert(
        self,
        *,
        watch: Watch,
        check_id: str,
        created_at: datetime,
        old_score: int | None,
        new_score: int | None,
        diff: Diff,
    ) -> str:
        alert_id = uuid.uuid4().hex
        with self._sessions.begin() as session:
            session.add(
                AlertRow(
                    id=alert_id,
                    watch_id=watch.id,
                    check_id=check_id,
                    created_at=created_at,
                    old_score=old_score,
                    new_score=new_score,
                    diff=diff.model_dump(mode="json"),
                )
            )
        return alert_id

    def mark_emailed(self, alert_id: str) -> None:
        with self._sessions.begin() as session:
            session.get_one(AlertRow, alert_id).emailed = True

    def alerts_for_email(self, email: str, limit: int = 50) -> list[Alert]:
        with self._sessions() as session:
            rows = session.execute(
                select(AlertRow, WatchRow, ProjectRow)
                .join(WatchRow, AlertRow.watch_id == WatchRow.id)
                .join(ProjectRow, WatchRow.rera_id == ProjectRow.rera_id)
                .where(WatchRow.email == email)
                .order_by(AlertRow.created_at.desc())
                .limit(limit)
            )
            return [_alert(alert, watch, project) for alert, watch, project in rows]


def _watch(row: WatchRow) -> Watch:
    return Watch.model_validate(
        {
            "id": row.id,
            "rera_id": row.rera_id,
            "email": row.email,
            "language": row.language,
            "created_at": row.created_at,
            "baseline_check_id": row.baseline_check_id,
        }
    )


def _changes(items: object) -> list[FindingChange]:
    return [FindingChange.model_validate(item) for item in items or []]  # type: ignore[attr-defined]


def _alert(alert: AlertRow, watch: WatchRow, project: ProjectRow) -> Alert:
    return Alert(
        id=alert.id,
        watch_id=alert.watch_id,
        rera_id=watch.rera_id,
        project_name=project.name,
        check_id=alert.check_id,
        created_at=alert.created_at,
        old_score=alert.old_score,
        new_score=alert.new_score,
        added=_changes(alert.diff.get("added")),
        removed=_changes(alert.diff.get("removed")),
        changed=_changes(alert.diff.get("changed")),
    )
