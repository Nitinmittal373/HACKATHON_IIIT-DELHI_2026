"""Uttar Pradesh: UP-RERA, the one portal NeevCheck reads in full.

The logic is the original UP-RERA code (app.resolve, app.sources.uprera); this adapter only
gives it the same shape as every other state.
"""

from datetime import datetime

from app.models import Project, normalize_rera_id
from app.parsers.uprera_page import ParseError, UpreraRecord
from app.sources.uprera import read_record
from app.states.base import Extension, ProjectRecord
from app.states.text import IST
from app.tinyfish import WebClient, WebError
from app.uprera_links import details_url_for


class UpAdapter:
    code = "UP"
    name = "Uttar Pradesh"
    rera_name = "UP-RERA"
    domains = ("up-rera.in",)
    id_patterns = (r"UPRERAPRJ\d{1,7}(?:/\d{2}/\d{4})?",)
    coverage = "full"
    examples = ("UPRERAPRJ8334", "UPRERAPRJ2634")
    complaint_url = "https://www.up-rera.in/ComplaintHome"
    unregistered_url = "https://www.up-rera.in/NonRegistration"
    search_url = "https://www.up-rera.in/"
    unverified_format = False
    note = (
        "Fetch reads the project page and its summary page: promoter, dates, extensions, "
        "status and complaint counts."
    )

    def detect(self, query: str) -> float:
        return 0.95 if normalize_rera_id(query) else 0.0

    def canonical_id(self, query: str) -> str | None:
        return normalize_rera_id(query)

    def details_url(self, project: Project) -> str:
        return project.details_url or details_url_for(project.rera_id) or "https://www.up-rera.in/"

    async def resolve(self, query: str, web: WebClient) -> list[Project]:
        # Imported here: app.resolve and app.sources import each other, so it must come second.
        from app.resolve import resolve

        return await resolve(query, web)

    async def read(self, project: Project, web: WebClient, now: datetime) -> ProjectRecord | None:
        try:
            record = await read_record(project.details_url, web)
        except (ParseError, WebError):
            return None
        if record.rera_id != project.rera_id:
            return None
        return record_of(record, project.details_url, now)


def record_of(record: UpreraRecord, url: str, now: datetime) -> ProjectRecord:
    return ProjectRecord(
        state="UP",
        rera_id=record.rera_id,
        name=record.name,
        promoter_name=record.promoter,
        promoter_id=record.promoter_id,
        district=record.district,
        registration_date=record.registered_on,
        promised_completion=record.end_date,
        revised_completion=record.revised_end_date,
        extensions=[
            Extension(extended_to=e.extended_to, reason=e.note)
            for e in record.extensions
            if not e.is_covid
        ],
        status=record.project_type,
        complaints_count=record.project_complaints,
        source_url=url,
        read_on=now.astimezone(IST).date(),
        read_at=now,
    )


ADAPTER = UpAdapter()
