"""Corrections readers send about a report, and where they are kept."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db import CorrectionRow

CHECK_ID_PATTERN = r"^[0-9a-f]{32}$"


class CorrectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(pattern=CHECK_ID_PATTERN)
    finding_id: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=5, max_length=2000)
    # Optional, only so we can reply; never shown on the report.
    contact: str | None = Field(default=None, max_length=254)


class Correction(CorrectionCreate):
    id: str
    created_at: datetime


class CorrectionStore:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def add(self, body: CorrectionCreate, created_at: datetime) -> Correction:
        row = CorrectionRow(
            id=uuid.uuid4().hex,
            created_at=created_at,
            report_id=body.report_id,
            finding_id=body.finding_id,
            message=body.message,
            contact=body.contact,
        )
        with self._sessions.begin() as session:
            session.add(row)
        return _correction(row)

    def latest(self, limit: int = 200) -> list[Correction]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CorrectionRow).order_by(CorrectionRow.created_at.desc()).limit(limit)
            )
            return [_correction(row) for row in rows]


def _correction(row: CorrectionRow) -> Correction:
    return Correction(
        id=row.id,
        created_at=row.created_at,
        report_id=row.report_id,
        finding_id=row.finding_id,
        message=row.message,
        contact=row.contact,
    )
