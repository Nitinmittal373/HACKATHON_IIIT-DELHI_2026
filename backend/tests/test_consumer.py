from app.sources.base import Blocked
from app.sources.consumer import MANUAL_URL, NOT_CHECKED, ConsumerSource
from tests.fakes import FakeWebClient
from tests.sourcekit import context, run_source


def test_the_lane_is_not_checked_automatically_and_spends_no_credit() -> None:
    web = FakeWebClient()

    events = run_source(ConsumerSource(), context(web=web))

    assert Blocked(NOT_CHECKED) in events
    assert web.calls == [] and web.agent_requests == []


def test_it_points_the_buyer_to_the_court_portal() -> None:
    assert ConsumerSource.manual_url == MANUAL_URL
    assert MANUAL_URL.startswith("https://e-jagriti.gov.in/")
    assert NOT_CHECKED == "Not checked automatically: the site needs a CAPTCHA"
