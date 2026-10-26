"""Rows of the project lists that Fetch can read (Bihar and Jharkhand).

Each parser looks for one registration number in the page text and returns the row as
labelled text ("Project Name: ...; Promoter Name: ..."), which the shared label parser reads
like any other portal text. They return None when the number is not on that page.
"""

import re
from collections.abc import Callable

from app.states.text import squash

DATE_DMY = re.compile(r"\d{2}/\d{2}/\d{4}")
DATE_DMONY = re.compile(r"^\d{1,2} [A-Z][a-z]{2} \d{4}$")


def jharkhand_row(text: str, rera_id: str) -> str | None:
    """A table row: | Sl | Reg No. & Date | Project Name & Address | Developer Name & Address |."""
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and squash(rera_id) in squash(cells[1]):
            registered = DATE_DMY.search(cells[1])
            parts = [
                f"{rera_id}",
                f"Project Name: {cells[2].split(',')[0].strip()}",
                f"Promoter Name: {cells[3].split(',')[0].strip()}",
            ]
            if registered:
                parts.append(f"Date of Registration: {registered.group(0)}")
            return "; ".join(parts)
    return None


def bihar_row(text: str, rera_id: str) -> str | None:
    """Lines in order: project name, registration number, promoter, [address], date."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if squash(line) != squash(rera_id) or index == 0 or index + 1 >= len(lines):
            continue
        parts = [rera_id, f"Project Name: {lines[index - 1]}", f"Promoter Name: {lines[index + 1]}"]
        for later in lines[index + 2 : index + 4]:
            if DATE_DMONY.match(later):
                parts.append(f"Date of Registration: {later}")
        return "; ".join(parts)
    return None


ROW_PARSERS: dict[str, Callable[[str, str], str | None]] = {
    "jharkhand": jharkhand_row,
    "bihar": bihar_row,
}
