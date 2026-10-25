"""Where a UP-RERA project lives on up-rera.in.

Numbers registered in 2017-18 (UPRERAPRJ8334) have a stable details page.
Later numbers, with a date suffix or six digits and none (UPRERAPRJ396176),
do not. Every project also has a Projectsummary page (with complaint counts),
but its address carries opaque tokens, so it can only be found through search.
"""

import re
from urllib.parse import urlsplit

from app.models import is_new_format, is_uprera_url
from app.tinyfish import SearchHit, WebClient

DETAILS_URL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id={digits}"
RERA_IN_TEXT = re.compile(r"UPRERAPRJ\d{1,7}(?:/\d{2}/\d{4})?", re.IGNORECASE)
SUMMARY_PURPOSE = "Find the UP-RERA project summary page for one registration number"
# Search limited to the register itself: without it, news and mirror sites crowd out its pages.
UPRERA_DOMAIN = "up-rera.in"


def details_url_for(rera_id: str) -> str | None:
    """Where the stable details page would be. Only numbers without a date suffix can have
    one, and later six-digit numbers do not, so callers must confirm the page exists."""
    if is_new_format(rera_id):
        return None
    return DETAILS_URL.format(digits=rera_id.removeprefix("UPRERAPRJ"))


def summary_url(url: str) -> str | None:
    """The link as https if it is a Projectsummary page on up-rera.in, else None."""
    url = https(url)
    if not is_uprera_url(url) or urlsplit(url).path.lower() != "/projectsummary":
        return None
    return url


def rera_ids_in(hit: SearchHit) -> list[str]:
    return [found.upper() for found in RERA_IN_TEXT.findall(f"{hit.title} {hit.snippet}")]


async def find_summary_url(rera_id: str, web: WebClient) -> str | None:
    """The Projectsummary link search returns for exactly this number, if any."""
    hits = await web.search(
        f"{rera_id} UP RERA project", purpose=SUMMARY_PURPOSE, include_domains=UPRERA_DOMAIN
    )
    for hit in hits:
        url = summary_url(hit.url)
        if url and rera_id in rera_ids_in(hit):
            return url
    return None


def https(url: str) -> str:
    return re.sub(r"^http://", "https://", url.strip())
