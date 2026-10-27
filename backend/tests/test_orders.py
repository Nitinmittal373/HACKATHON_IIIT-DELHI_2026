"""Finding a project through public orders that name it.

find_orders_mywoods.json is the live Search answer of 27 Oct 2026 (scripts/capture_orders.py);
order_sample.txt is a made-up RERA order, so no real party's order is kept in the repository.
"""

import asyncio

from app.states.openweb import SearchCache
from app.states.orders import find_in_orders, is_order
from app.states.resolver import resolve_any
from app.tinyfish import SearchHit
from tests.fakes import FIXTURES, FakeWebClient, load_recording

ORDER_URL = "https://www.up-rera.in/orders/12345-Order.pdf"


def sample_order_web() -> FakeWebClient:
    hit = SearchHit(
        title="Order - Sunrise Heights",
        url=ORDER_URL,
        snippet="Complaint against Sunrise Builders Pvt. Ltd. for Sunrise Heights, Noida.",
    )
    text = (FIXTURES / "order_sample.txt").read_text(encoding="utf-8")
    return FakeWebClient(searches={"Sunrise Heights RERA order": [hit]}, texts={ORDER_URL: text})


def test_an_order_pdf_gives_the_projects_number_and_its_link() -> None:
    found = asyncio.run(find_in_orders("Sunrise Heights", sample_order_web(), SearchCache()))
    [project] = found.projects
    assert project.rera_id == "UPRERAPRJ99999"
    assert project.status == "from_order"
    assert project.found_in == ORDER_URL
    assert project.sources == ["up-rera.in"]


def test_an_unreadable_order_falls_back_to_its_snippet() -> None:
    web = sample_order_web()
    web.texts.clear()
    found = asyncio.run(find_in_orders("Sunrise Heights", web, SearchCache()))
    assert found.projects == []  # the snippet holds no number, and none is invented


def test_a_judgment_names_the_builder_as_a_lead_not_a_project() -> None:
    web = FakeWebClient().replay(load_recording("find_orders_mywoods.json"))
    found = asyncio.run(find_in_orders("Mahagun Mywoods", web, SearchCache()))
    assert found.projects == []
    [lead] = found.leads
    assert lead.builder.startswith("Mahagun India Pvt. Ltd")
    assert lead.order_url == "https://indiankanoon.org/doc/192063939/"


def test_listing_pages_are_not_orders() -> None:
    page = SearchHit(title="Mahagun Mywoods RERA", url="https://upreratracker.com/x", snippet="")
    court = SearchHit(title="Judgment", url="https://indiankanoon.org/doc/1/", snippet="")
    assert not is_order(page) and is_order(court)


def test_orders_are_only_searched_when_nothing_else_found_the_project() -> None:
    web = sample_order_web()
    resolved = asyncio.run(resolve_any("Sunrise Heights", web))
    assert [p.rera_id for p in resolved.candidates] == ["UPRERAPRJ99999"]
    assert resolved.candidates[0].status == "from_order"
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    asyncio.run(resolve_any("Mahagun Mywoods", web))
    assert not any("order" in query for _, query in web.calls)
