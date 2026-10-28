"""Database tables. They mirror the data model in docs/architecture.md.

SQLite locally, Postgres when DATABASE_URL points at one.
"""

from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Dialect,
    Float,
    ForeignKey,
    Integer,
    String,
    TypeDecorator,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class UTCDateTime(TypeDecorator[datetime]):
    """Stores UTC and always returns aware datetimes (SQLite drops the zone otherwise)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return value.astimezone(UTC) if value else None

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"

    rera_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(300))
    promoter: Mapped[str | None] = mapped_column(String(300))
    district: Mapped[str | None] = mapped_column(String(100))
    registered_on: Mapped[date | None] = mapped_column(Date)
    details_url: Mapped[str] = mapped_column(String(500))


class CheckRow(Base):
    __tablename__ = "checks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rera_id: Mapped[str] = mapped_column(ForeignKey("projects.rera_id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    # The signed-in account that started the check; None for Sentinel's own re-checks.
    started_by: Mapped[str | None] = mapped_column(String(64), index=True)
    # TinyFish calls the check made: {"search": n, "fetch": n, "agent": n}.
    usage: Mapped[dict[str, int] | None] = mapped_column(JSON)


class SourceRunRow(Base):
    __tablename__ = "source_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_id: Mapped[str] = mapped_column(ForeignKey("checks.id"), index=True)
    source: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    live_url: Mapped[str | None] = mapped_column(String(1000))
    message: Mapped[str | None] = mapped_column(String(500))
    checks_read: Mapped[list[str]] = mapped_column(JSON, default=list)
    manual_url: Mapped[str | None] = mapped_column(String(500))


class FindingRow(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    check_id: Mapped[str] = mapped_column(ForeignKey("checks.id"), index=True)
    source: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    area: Mapped[str | None] = mapped_column(String(20))
    verdict: Mapped[str] = mapped_column(String(20))
    reliability: Mapped[str] = mapped_column(String(20))
    source_url: Mapped[str] = mapped_column(String(1000))
    read_on: Mapped[date] = mapped_column(Date)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    occurred_on: Mapped[date | None] = mapped_column(Date)
    count: Mapped[int | None] = mapped_column(Integer)
    months: Mapped[int | None] = mapped_column(Integer)
    scope: Mapped[str | None] = mapped_column(String(20))
    points: Mapped[float | None] = mapped_column(Float)


class SourceCacheRow(Base):
    """One source's result for one entity on one day, kept with the time it was really read."""

    __tablename__ = "source_cache"

    source: Mapped[str] = mapped_column(String(20), primary_key=True)
    entity: Mapped[str] = mapped_column(String(400), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    read_at: Mapped[datetime] = mapped_column(UTCDateTime)
    checks_read: Mapped[list[str]] = mapped_column(JSON, default=list)
    findings: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    # Whatever else the source produced besides findings, such as the group's family tree.
    extras: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class FindingExtraRow(Base):
    """Optional facts of a finding (snippet, totals), kept apart so older databases need no
    column added to the findings table."""

    __tablename__ = "finding_extras"

    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), primary_key=True)
    data: Mapped[dict[str, object]] = mapped_column(JSON)


class ScoreRow(Base):
    __tablename__ = "scores"

    check_id: Mapped[str] = mapped_column(ForeignKey("checks.id"), primary_key=True)
    value: Mapped[int] = mapped_column(Integer)
    band: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    hard_stop: Mapped[bool]
    # Drivers, areas and unread checks, exactly as the engine returned them.
    detail: Mapped[dict[str, object]] = mapped_column(JSON)


class WatchRow(Base):
    """One person watching one project. The email is only ever used for this watch."""

    __tablename__ = "watches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rera_id: Mapped[str] = mapped_column(ForeignKey("projects.rera_id"), index=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    # The Google account that owns the watch. None for watches made before accounts existed;
    # those keep emailing, and are linked to an account that signs in with the same email.
    user_id: Mapped[str | None] = mapped_column(String(255), index=True)
    language: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    # The check later re-checks are compared against; None until the project has a finished one.
    baseline_check_id: Mapped[str | None] = mapped_column(String(32))


class UnsubscribeTokenRow(Base):
    """A link in an alert email that stops one watch. Only the hash is kept, never the token."""

    __tablename__ = "unsubscribe_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    watch_id: Mapped[str] = mapped_column(ForeignKey("watches.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class MonitorRow(Base):
    """A TinyFish monitor created for a watch; cancelled when the watch is removed."""

    __tablename__ = "monitors"

    monitor_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    watch_id: Mapped[str] = mapped_column(ForeignKey("watches.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))


class WebhookReceiptRow(Base):
    """A webhook delivery already handled, so a repeated delivery changes nothing."""

    __tablename__ = "webhook_receipts"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime)


class CorrectionRow(Base):
    """A reader's request to correct a report, kept for the operator to review."""

    __tablename__ = "corrections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    report_id: Mapped[str] = mapped_column(String(32), index=True)
    finding_id: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(String(2000))
    contact: Mapped[str | None] = mapped_column(String(254))


class UserReportRow(Base):
    """A check saved to a signed-in account (the account is the Google id, nothing else)."""

    __tablename__ = "user_reports"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    check_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(UTCDateTime)


class SearchCacheRow(Base):
    """A search answer kept for SEARCH_CACHE_DAYS, so the same query never calls Search twice."""

    __tablename__ = "search_cache"

    key: Mapped[str] = mapped_column(String(500), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)


class AlertRow(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    watch_id: Mapped[str] = mapped_column(ForeignKey("watches.id"), index=True)
    check_id: Mapped[str] = mapped_column(ForeignKey("checks.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    old_score: Mapped[int | None] = mapped_column(Integer)
    new_score: Mapped[int | None] = mapped_column(Integer)
    # {"added": [...], "removed": [...], "changed": [...]}, each entry a title and a source link.
    diff: Mapped[dict[str, object]] = mapped_column(JSON)
    emailed: Mapped[bool] = mapped_column(default=False)


def normalize_database_url(database_url: str) -> str:
    """Hosts give postgres:// or postgresql:// links; SQLAlchemy needs the driver named."""
    for prefix in ("postgres://", "postgresql://"):
        if database_url.startswith(prefix):
            return "postgresql+psycopg://" + database_url.removeprefix(prefix)
    return database_url


# Columns added after the first release; create_all never alters an existing table.
ADDED_COLUMNS = (
    ("watches", "user_id", "VARCHAR(255)", True),
    ("checks", "started_by", "VARCHAR(64)", True),
    ("checks", "usage", "JSON", False),
    ("source_runs", "manual_url", "VARCHAR(500)", False),
)


def add_missing_columns(engine: Engine) -> None:
    """Bring a database made by an older version up to date by adding the columns it lacks."""
    for table, column, kind, indexed in ADDED_COLUMNS:
        if column in {c["name"] for c in inspect(engine).get_columns(table)}:
            continue
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {kind}"))
            if indexed:
                connection.execute(text(f"CREATE INDEX ix_{table}_{column} ON {table} ({column})"))


def make_engine(database_url: str) -> Engine:
    url = make_url(normalize_database_url(database_url))
    if url.get_backend_name() == "sqlite":
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        # The orchestrator writes from the event loop thread and requests read from others.
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    add_missing_columns(engine)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False)
