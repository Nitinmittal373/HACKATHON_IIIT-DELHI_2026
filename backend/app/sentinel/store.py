"""Reads and writes for watches and alerts."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.db import (
    AlertRow,
    MonitorRow,
    ProjectRow,
    SentinelStateRow,
    UnsubscribeTokenRow,
    WatchRow,
    WebhookReceiptRow,
)
from app.models import DisplayScore
from app.sentinel.models import Alert, Diff, FindingChange, Language, Watch

TOKEN_BYTES = 32
STATE_ID = 1


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SentinelStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def count_watches(self, user_id: str) -> int:
        with self._sessions() as session:
            query = select(func.count()).select_from(WatchRow).where(WatchRow.user_id == user_id)
            return session.scalar(query) or 0

    def find_watch(self, user_id: str, rera_id: str) -> Watch | None:
        with self._sessions() as session:
            row = session.scalar(
                select(WatchRow).where(WatchRow.user_id == user_id, WatchRow.rera_id == rera_id)
            )
            return _watch(row) if row else None

    def adopt_unowned(self, user_id: str, email: str) -> None:
        """Links watches made before accounts existed to the account with the same email.

        The email comes from a Google-verified sign-in, so only its owner can claim them."""
        with self._sessions.begin() as session:
            session.execute(
                update(WatchRow)
                .where(WatchRow.user_id.is_(None), WatchRow.email == email)
                .values(user_id=user_id)
            )

    def watches_of(self, user_id: str) -> list[Watch]:
        with self._sessions() as session:
            rows = session.scalars(
                select(WatchRow).where(WatchRow.user_id == user_id).order_by(WatchRow.created_at)
            )
            return [_watch(row) for row in rows]

    def watch_ids_of(self, user_id: str) -> list[str]:
        with self._sessions() as session:
            return list(session.scalars(select(WatchRow.id).where(WatchRow.user_id == user_id)))

    def get_owned_watch(self, user_id: str, watch_id: str) -> Watch | None:
        """The watch, only if this account owns it."""
        with self._sessions() as session:
            row = session.scalar(
                select(WatchRow).where(WatchRow.id == watch_id, WatchRow.user_id == user_id)
            )
            return _watch(row) if row else None

    def add_watch(
        self,
        *,
        user_id: str,
        email: str,
        rera_id: str,
        language: Language,
        created_at: datetime,
        baseline_check_id: str | None,
    ) -> Watch:
        row = WatchRow(
            id=uuid.uuid4().hex,
            rera_id=rera_id,
            user_id=user_id,
            email=email,
            language=language,
            created_at=created_at,
            baseline_check_id=baseline_check_id,
        )
        with self._sessions.begin() as session:
            session.add(row)
        return _watch(row)

    def get_watch(self, watch_id: str) -> Watch | None:
        with self._sessions() as session:
            row = session.get(WatchRow, watch_id)
            return _watch(row) if row else None

    def remove_watch(self, watch_id: str) -> list[str]:
        """Delete a watch with its alerts; returns the TinyFish monitors to cancel."""
        with self._sessions.begin() as session:
            monitor_ids = list(
                session.scalars(
                    select(MonitorRow.monitor_id).where(MonitorRow.watch_id == watch_id)
                )
            )
            session.execute(delete(MonitorRow).where(MonitorRow.watch_id == watch_id))
            session.execute(
                delete(UnsubscribeTokenRow).where(UnsubscribeTokenRow.watch_id == watch_id)
            )
            session.execute(delete(AlertRow).where(AlertRow.watch_id == watch_id))
            session.execute(delete(WatchRow).where(WatchRow.id == watch_id))
            return monitor_ids

    def new_unsubscribe_token(self, watch_id: str, created_at: datetime) -> str:
        """A fresh 32-byte token for one alert email. Only its hash is stored, so each email
        gets its own and links in older emails keep working until the watch is gone."""
        token = secrets.token_urlsafe(TOKEN_BYTES)
        with self._sessions.begin() as session:
            session.add(
                UnsubscribeTokenRow(
                    token_hash=hash_token(token), watch_id=watch_id, created_at=created_at
                )
            )
        return token

    def watch_for_token(self, token: str) -> str | None:
        with self._sessions() as session:
            return session.scalar(
                select(UnsubscribeTokenRow.watch_id).where(
                    UnsubscribeTokenRow.token_hash == hash_token(token)
                )
            )

    def add_monitor(self, watch_id: str, monitor_id: str, kind: str) -> None:
        with self._sessions.begin() as session:
            session.add(MonitorRow(monitor_id=monitor_id, watch_id=watch_id, kind=kind))

    def monitor_ids(self) -> list[str]:
        with self._sessions() as session:
            return list(session.scalars(select(MonitorRow.monitor_id)))

    def forget_monitor(self, monitor_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(delete(MonitorRow).where(MonitorRow.monitor_id == monitor_id))

    def claim_run(self, now: datetime, min_gap: timedelta) -> bool:
        """True, and the time is saved, when the last automatic run is at least `min_gap` ago."""
        with self._sessions.begin() as session:
            state = session.get(SentinelStateRow, STATE_ID)
            if state is None:
                session.add(SentinelStateRow(id=STATE_ID, last_run_at=now))
                return True
            if now - state.last_run_at < min_gap:
                return False
            state.last_run_at = now
            return True

    def project_for_monitor(self, monitor_id: str) -> str | None:
        with self._sessions() as session:
            return session.scalar(
                select(WatchRow.rera_id)
                .join(MonitorRow, MonitorRow.watch_id == WatchRow.id)
                .where(MonitorRow.monitor_id == monitor_id)
            )

    def claim_delivery(self, key: str, received_at: datetime) -> bool:
        """True the first time a delivery key is seen, False for every repeat."""
        with self._sessions.begin() as session:
            if session.get(WebhookReceiptRow, key):
                return False
            session.add(WebhookReceiptRow(key=key, received_at=received_at))
            return True

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
        old_display: DisplayScore | None,
        new_display: DisplayScore | None,
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
                    # The 300-900 scores are kept inside the diff, which has no fixed columns.
                    diff={
                        **diff.model_dump(mode="json"),
                        "display": {
                            "old": old_display.model_dump(mode="json") if old_display else None,
                            "new": new_display.model_dump(mode="json") if new_display else None,
                        },
                    },
                )
            )
        return alert_id

    def mark_emailed(self, alert_id: str) -> None:
        with self._sessions.begin() as session:
            session.get_one(AlertRow, alert_id).emailed = True

    def alerts_for_user(self, user_id: str, limit: int = 50) -> list[Alert]:
        return self._alerts(WatchRow.user_id == user_id, limit)

    def get_alert(self, alert_id: str) -> Alert | None:
        found = self._alerts(AlertRow.id == alert_id, 1)
        return found[0] if found else None

    def _alerts(self, condition: ColumnElement[bool], limit: int) -> list[Alert]:
        with self._sessions() as session:
            rows = session.execute(
                select(AlertRow, WatchRow, ProjectRow)
                .join(WatchRow, AlertRow.watch_id == WatchRow.id)
                .join(ProjectRow, WatchRow.rera_id == ProjectRow.rera_id)
                .where(condition)
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


def _display(value: object) -> DisplayScore | None:
    return DisplayScore.model_validate(value) if value else None


def _alert(alert: AlertRow, watch: WatchRow, project: ProjectRow) -> Alert:
    scores = alert.diff.get("display") or {}
    return Alert(
        id=alert.id,
        watch_id=alert.watch_id,
        rera_id=watch.rera_id,
        project_name=project.name,
        check_id=alert.check_id,
        created_at=alert.created_at,
        old_score=alert.old_score,
        new_score=alert.new_score,
        old_display_score=_display(scores.get("old")),  # type: ignore[attr-defined]
        new_display_score=_display(scores.get("new")),  # type: ignore[attr-defined]
        added=_changes(alert.diff.get("added")),
        removed=_changes(alert.diff.get("removed")),
        changed=_changes(alert.diff.get("changed")),
    )
