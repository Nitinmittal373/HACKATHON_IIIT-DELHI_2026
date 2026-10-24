"""Persistence. SQLite through the standard library: zero setup for a 24-hour build.

Every function takes plain JSON, so swapping to PostgreSQL later only changes this file.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

from . import config
from .models import Report, ReportSummary, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    query TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS watches (
    report_id TEXT PRIMARY KEY REFERENCES reports(id),
    created_at TEXT NOT NULL,
    monitors TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT,
    received_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


@contextmanager
def _db():
    con = sqlite3.connect(config.DATABASE_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init() -> None:
    with _db() as con:
        con.executescript(SCHEMA)


def save_report(r: Report) -> None:
    with _db() as con:
        con.execute("INSERT OR REPLACE INTO reports (id, created_at, query, body) VALUES (?, ?, ?, ?)",
                    (r.id, r.created_at, r.query, r.model_dump_json()))


def get_report(report_id: str) -> Report | None:
    with _db() as con:
        row = con.execute("SELECT body FROM reports WHERE id = ?", (report_id,)).fetchone()
    return Report.model_validate_json(row["body"]) if row else None


def list_reports(limit: int = 50) -> list[ReportSummary]:
    with _db() as con:
        rows = con.execute("SELECT r.body, w.report_id IS NOT NULL AS watching FROM reports r "
                           "LEFT JOIN watches w ON w.report_id = r.id ORDER BY r.created_at DESC LIMIT ?",
                           (limit,)).fetchall()
    out = []
    for row in rows:
        r = Report.model_validate_json(row["body"])
        out.append(ReportSummary(id=r.id, query=r.query, project_name=r.project_name,
                                 promoter_name=r.promoter_name, score=r.score["score"], band=r.score["band"],
                                 confidence=r.score["confidence"], hard_stop=r.score["hard_stop"],
                                 created_at=r.created_at, watching=bool(row["watching"])))
    return out


def save_watch(report_id: str, monitors: list[dict]) -> None:
    with _db() as con:
        con.execute("INSERT OR REPLACE INTO watches (report_id, created_at, monitors) VALUES (?, ?, ?)",
                    (report_id, now_iso(), json.dumps(monitors, default=str)))


def list_watches() -> list[dict]:
    with _db() as con:
        rows = con.execute("SELECT report_id, created_at, monitors FROM watches ORDER BY created_at DESC").fetchall()
    return [{"report_id": r["report_id"], "created_at": r["created_at"], "monitors": json.loads(r["monitors"])}
            for r in rows]


def add_alert(report_id: str | None, payload: dict) -> None:
    with _db() as con:
        con.execute("INSERT INTO alerts (report_id, received_at, payload) VALUES (?, ?, ?)",
                    (report_id, now_iso(), json.dumps(payload, default=str)[:20000]))


def list_alerts(limit: int = 50) -> list[dict]:
    with _db() as con:
        rows = con.execute("SELECT id, report_id, received_at, payload FROM alerts ORDER BY id DESC LIMIT ?",
                           (limit,)).fetchall()
    return [{"id": r["id"], "report_id": r["report_id"], "received_at": r["received_at"],
             "payload": json.loads(r["payload"])} for r in rows]
