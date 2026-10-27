"""Registration numbers in a document the buyer has: a brochure, an agreement or a QR code.

Nothing here is stored. A PDF is read from memory, its text is searched for numbers in
UP-RERA's format, and only the numbers and the few words around each one go back to the buyer,
with phone numbers, e-mail addresses and identity numbers removed. The file is never written to
disk, so there is nothing to delete afterwards; a photo is never uploaded at all, because its QR
code is decoded in the browser and only the decoded text arrives here.
"""

import re
from io import BytesIO
from urllib.parse import unquote

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.api_model import ApiModel
from app.models import Project
from app.states.openweb import numbers_in, prepare
from app.uprera_links import project_details_url

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 40
MAX_TEXT = 4000
# How much of the line around a number is shown back to the buyer.
LINE_WINDOW = 90
MAX_NUMBERS = 6

# Personal data a brochure or agreement may print beside a number.
PERSONAL = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.-]+"  # e-mail
    r"|(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"  # mobile
    r"|\b[A-Z]{5}\d{4}[A-Z]\b"  # PAN
    r"|(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\d)",  # Aadhaar
    re.IGNORECASE,
)


class ExtractError(ValueError):
    """The file could not be read; the message is safe to show the buyer."""


class ExtractedNumber(ApiModel):
    rera_id: str
    # The words around the number in the buyer's own document, without personal data.
    line: str


class ExtractText(ApiModel):
    """Text decoded in the browser, such as the address a QR code holds."""

    text: str


class ExtractResponse(ApiModel):
    source: str
    numbers: list[ExtractedNumber]
    candidates: list[Project]
    # Said when nothing was found, so the buyer knows what to do next.
    message: str | None = None


def pdf_text(data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ExtractError("This file is larger than 5 MB")
    if not data.startswith(b"%PDF"):
        raise ExtractError("This does not look like a PDF file")
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ExtractError("This PDF is locked with a password, so it cannot be read")
        pages = reader.pages[:MAX_PAGES]
        return "\n".join(page.extract_text() or "" for page in pages)
    except (PyPdfError, ValueError, KeyError, RecursionError):
        raise ExtractError("This PDF could not be read") from None


def numbers_in_document(text: str) -> list[ExtractedNumber]:
    """Each distinct registration number in the text, with the words around its first use."""
    readable = prepare(unquote(text))
    seen: dict[str, ExtractedNumber] = {}
    for rera_id, start, end in numbers_in(readable):
        key = re.sub(r"[^A-Z0-9]", "", rera_id.upper())
        if key not in seen:
            seen[key] = ExtractedNumber(
                rera_id=rera_id, line=line_around(readable, start, end)
            )
    return list(seen.values())[:MAX_NUMBERS]


def line_around(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line = text[line_start : len(text) if line_end < 0 else line_end]
    offset = start - line_start
    near = line[max(0, offset - LINE_WINDOW) : offset + (end - start) + LINE_WINDOW]
    return re.sub(r"\s+", " ", PERSONAL.sub("[removed]", near)).strip()


def candidates_from_document(numbers: list[ExtractedNumber]) -> list[Project]:
    """The numbers as candidates; a portal page may still confirm them."""
    return [
        Project(
            rera_id=number.rera_id,
            details_url=project_details_url(number.rera_id),
            status="from_document",
            sources=["your document"],
        )
        for number in numbers
    ]
