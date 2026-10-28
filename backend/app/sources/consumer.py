"""Consumer cases: e-Jagriti, the national consumer-commission portal.

The case search always asks for a CAPTCHA, which NeevCheck never bypasses. Sending a browser
agent there only spent credit to reach the same wall, so the lane no longer runs one: it is
shown as not checked automatically, with a link for the buyer to search by hand. It counts as
unread, so it lowers confidence and never changes the score.
"""

from collections.abc import AsyncIterator

from app.models import CheckKey
from app.sources.base import Blocked, Progress, SourceContext, SourceEvent

MANUAL_URL = "https://e-jagriti.gov.in/advance-case-search"
NOT_CHECKED = "Not checked automatically: the site needs a CAPTCHA"


class ConsumerSource:
    name = "consumer"
    checks: tuple[CheckKey, ...] = ("consumer_cases",)
    # Where the buyer can search the promoter's name themselves.
    manual_url = MANUAL_URL

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        yield Progress(NOT_CHECKED)
        yield Blocked(NOT_CHECKED)
