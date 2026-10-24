"""Parse a UP-RERA project page into plain fields. Pure: HTML in, record out.

UP-RERA serves two layouts:
- Frm_View_Project_Details.aspx (old-format numbers): labels and grids by id
- Projectsummary (new-format numbers): a label/value list and a document grid
Both are ASP.NET pages with stable element ids, which is what we key on.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

from bs4 import BeautifulSoup, Tag

ID = "ctl00_ContentPlaceHolder1_"
RERA_IN_TEXT = re.compile(r"UPRERAPRJ\d{1,7}(?:/\d{2}/\d{4})?", re.IGNORECASE)
RERA_PROMOTER = re.compile(r"UPRERAPRM\d+", re.IGNORECASE)
COMPLETION_DOCUMENT = re.compile(r"completion certificate|occupancy", re.IGNORECASE)


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Permit:
    number: str | None
    permit_date: date | None
    valid_upto: date | None
    end_date: date | None


@dataclass(frozen=True)
class Document:
    name: str
    file_name: str | None
    uploaded_on: date | None
    uploaded: bool


@dataclass(frozen=True)
class UpreraRecord:
    rera_id: str
    name: str | None
    promoter: str | None
    promoter_id: str | None
    registered_on: date | None
    project_type: str | None
    district: str | None
    start_date: date | None
    end_date: date | None
    revised_end_date: date | None
    permits: tuple[Permit, ...]
    documents: tuple[Document, ...]
    project_complaints: int | None = None
    promoter_complaints: int | None = None

    @property
    def latest_end_date(self) -> date | None:
        dates = [self.end_date, self.revised_end_date, *(p.end_date for p in self.permits)]
        known = [d for d in dates if d is not None]
        return max(known) if known else None

    @property
    def completion_certificate(self) -> Document | None:
        return next(
            (d for d in self.documents if d.uploaded and COMPLETION_DOCUMENT.search(d.name)),
            None,
        )


def parse_uprera_page(html: str) -> UpreraRecord:
    soup = BeautifulSoup(html, "html.parser")
    if soup.find(id=ID + "lblProjectNameWithID"):
        return _parse_details(soup)
    if soup.find(id=ID + "lblregno"):
        return _parse_summary(soup)
    raise ParseError("The UP-RERA page did not have the expected layout")


def _parse_details(soup: BeautifulSoup) -> UpreraRecord:
    rera_id = _rera_id(_text(soup, "lblProjectNameWithID"))
    return UpreraRecord(
        rera_id=rera_id,
        name=_text(soup, "lblProjectName") or _after_colon(_text(soup, "lblProjectNameHeading")),
        promoter=_after_colon(_text(soup, "lblPromoterNameHeading")),
        promoter_id=_first(RERA_PROMOTER, _text(soup, "lblPromoterNameWithID")),
        registered_on=_date(_after_colon(_text(soup, "lblregisdate"))),
        project_type=_text(soup, "lblProjectType"),
        district=_selected(soup, "ddlDistrict"),
        start_date=_date(_text(soup, "lblStartDate")),
        end_date=_date(_text(soup, "lblEndDate")),
        revised_end_date=_date(_text(soup, "txtrevised_end_date")),
        permits=tuple(_permit(row) for row in _rows(soup, "grdPermitDetails")),
        documents=tuple(_details_document(row) for row in _rows(soup, "grvdocumentdetails")),
    )


def _parse_summary(soup: BeautifulSoup) -> UpreraRecord:
    return UpreraRecord(
        rera_id=_rera_id(_text(soup, "lblregno")),
        name=_text(soup, "lblprojectname"),
        promoter=_text(soup, "Lblpromotername"),
        promoter_id=None,
        registered_on=_date(_text(soup, "prjregdate")),
        project_type=_text(soup, "prj_type"),
        district=_text(soup, "lbldistrict"),
        start_date=None,
        end_date=_date(_text(soup, "Lblproposedenddt")),
        revised_end_date=None,
        permits=(),
        documents=tuple(_summary_document(row) for row in _rows(soup, "grvdocumentdetails")),
        project_complaints=_leading_int(_text(soup, "lblprojectwisecomplaint")),
        promoter_complaints=_leading_int(_text(soup, "lbltotalcomplaint")),
    )


def _permit(row: dict[str, str]) -> Permit:
    return Permit(
        number=row.get("Orignal Permit No") or None,
        permit_date=_date(row.get("Orignal Permit Date")),
        valid_upto=_date(row.get("Valid Upto")),
        end_date=_date(row.get("End Date")),
    )


def _details_document(row: dict[str, str]) -> Document:
    file_name = row.get("Uploaded File Name") or None
    # "Promoter select NA for this document" means nothing was uploaded.
    uploaded = bool(file_name) and not file_name.lower().startswith("promoter select na")
    return Document(
        name=row.get("Document Name", ""),
        file_name=file_name if uploaded else None,
        uploaded_on=_date(row.get("Uploaded Date")),
        uploaded=uploaded,
    )


def _summary_document(row: dict[str, str]) -> Document:
    upload_type = row.get("Upload Type", "")
    return Document(
        name=row.get("Document Name", ""),
        file_name=None,
        uploaded_on=None,
        uploaded=bool(upload_type) and upload_type.upper() != "NA",
    )


def _rows(soup: BeautifulSoup, grid_id: str) -> list[dict[str, str]]:
    """A grid's data rows as {header: cell text}."""
    table = soup.find(id=ID + grid_id)
    if not isinstance(table, Tag):
        return []
    rows = table.find_all("tr")
    if not rows:
        return []
    headers = [_clean(cell.get_text(" ")) for cell in rows[0].find_all(["th", "td"])]
    return [
        dict(zip(headers, (_clean(c.get_text(" ")) for c in row.find_all("td")), strict=False))
        for row in rows[1:]
        if row.find("td")
    ]


def _text(soup: BeautifulSoup, element_id: str) -> str | None:
    """Visible text of a label, or the value of a read-only input (dates are inputs)."""
    element = soup.find(id=ID + element_id)
    if not isinstance(element, Tag):
        return None
    if element.name == "input":
        value = element.get("value")
        return (_clean(value) or None) if isinstance(value, str) else None
    return _clean(element.get_text(" ")) or None


def _selected(soup: BeautifulSoup, select_id: str) -> str | None:
    select = soup.find(id=ID + select_id)
    if not isinstance(select, Tag):
        return None
    option = select.find("option", selected=True)
    text = _clean(option.get_text(" ")) if option else ""
    return text if text and not text.startswith("--") else None


def _rera_id(text: str | None) -> str:
    found = RERA_IN_TEXT.search(text or "")
    if found is None:
        raise ParseError("The UP-RERA page did not show a project number")
    return found.group(0).upper()


def _first(pattern: re.Pattern[str], text: str | None) -> str | None:
    found = pattern.search(text or "")
    return found.group(0).upper() if found else None


def _after_colon(text: str | None) -> str | None:
    if not text:
        return None
    return text.split(":", 1)[-1].strip() or None


def _date(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%d-%m-%Y").date()
    except ValueError:
        return None


def _leading_int(text: str | None) -> int | None:
    found = re.match(r"\s*(\d+)", text or "")
    return int(found.group(1)) if found else None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
