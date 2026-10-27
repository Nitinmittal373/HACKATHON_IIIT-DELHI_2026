"""Checks saved to a signed-in account. The account is the Google id; nothing else is kept."""

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import UserReportRow

MAX_SAVED = 50


class UserReports:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def ids(self, user_id: str) -> list[str]:
        """The saved check ids, newest first."""
        with self._sessions() as session:
            query = (
                select(UserReportRow.check_id)
                .where(UserReportRow.user_id == user_id)
                .order_by(UserReportRow.saved_at.desc())
                .limit(MAX_SAVED)
            )
            return list(session.scalars(query))

    def add(self, user_id: str, check_ids: list[str], now: datetime) -> None:
        """Saves the ids in the order given (first is newest); one already saved keeps its row."""
        with self._sessions.begin() as session:
            saved = select(UserReportRow.check_id).where(UserReportRow.user_id == user_id)
            known = set(session.scalars(saved))
            for position, check_id in enumerate(reversed(check_ids)):
                if check_id in known:
                    continue
                # Later ids in the list are older, so they get an earlier time.
                saved_at = now + timedelta(microseconds=position)
                session.add(UserReportRow(user_id=user_id, check_id=check_id, saved_at=saved_at))

    def remove(self, user_id: str, check_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(UserReportRow).where(
                    UserReportRow.user_id == user_id, UserReportRow.check_id == check_id
                )
            )
