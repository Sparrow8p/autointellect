"""Скрипт сбора запчастей: останавливается при отказе сайта, сеть в тестах не используется."""

import json

import pytest
from sqlalchemy import select

from app.models import Part
from scripts import collect_parts

ROBOTS_OK = "User-agent: *\nAllow: /\n"


class FakeResponse:
    def __init__(self, text="", status_code=200, url="https://bibinet.ru/x"):
        self.text, self.status_code, self.url = text, status_code, url


class FakeSession:
    pages = None  # функция url -> FakeResponse
    robots = ROBOTS_OK
    requested: list[str] = []

    def __init__(self):
        self.headers = {}

    def get(self, url, timeout=None):
        FakeSession.requested.append(url)
        if url.endswith("/robots.txt"):
            return FakeResponse(FakeSession.robots)
        return FakeSession.pages(url)


def listing_page(*prices):
    items = [
        {
            "part_class": "new_part",
            "part_title": f"Колодки {price}",
            "price": price,
            "url_part": f"/new_part/omsk/invnn-{price}",
            "branch_id": 1,
        }
        for price in prices
    ]
    data = {"result_search": {"data": items, "company": {"1": {"city": {"name": "Омск"}}}}}
    return f"<script>window.page_data={json.dumps(data)};</script>"


@pytest.fixture()
def fake_site(monkeypatch):
    sleeps = []
    FakeSession.requested = []
    FakeSession.robots = ROBOTS_OK
    monkeypatch.setattr(collect_parts.requests, "Session", FakeSession)
    monkeypatch.setattr(collect_parts.time, "sleep", sleeps.append)
    return sleeps


def page_requests():
    return [u for u in FakeSession.requested if not u.endswith("/robots.txt")]


@pytest.mark.parametrize("status", [401, 403, 429, 503, 500])
def test_stops_on_refusal(fake_site, status):
    FakeSession.pages = lambda url: FakeResponse("", status_code=status)
    assert collect_parts.collect(["04465-02220", "90915"], 4.0, dry_run=True) == 2
    assert len(page_requests()) == 1  # после отказа больше ни одного запроса


def test_stops_on_redirect_to_another_site(fake_site):
    FakeSession.pages = lambda url: FakeResponse("ok", url="https://example.com/check")
    assert collect_parts.collect(["04465-02220", "90915"], 4.0, dry_run=True) == 2
    assert len(page_requests()) == 1


def test_stops_on_page_without_expected_data(fake_site):
    FakeSession.pages = lambda url: FakeResponse("<html>Подтвердите, что вы не робот</html>")
    assert collect_parts.collect(["04465-02220", "90915"], 4.0, dry_run=True) == 2
    assert len(page_requests()) == 1


def test_stops_when_robots_txt_forbids(fake_site):
    FakeSession.robots = "User-agent: *\nDisallow: /\n"
    FakeSession.pages = lambda url: FakeResponse(listing_page(100))
    assert collect_parts.collect(["04465-02220"], 4.0, dry_run=True) == 2
    assert page_requests() == []


def test_pause_is_never_shorter_than_minimum(fake_site):
    FakeSession.pages = lambda url: FakeResponse(listing_page())
    collect_parts.collect(["A1", "A2"], 0.1, dry_run=True)
    assert fake_site and min(fake_site) >= collect_parts.MIN_DELAY


def test_empty_oem_is_skipped_without_request(fake_site):
    FakeSession.pages = lambda url: FakeResponse(listing_page(100))
    assert collect_parts.collect(["---"], 4.0, dry_run=True) == 0
    assert page_requests() == []


def test_dry_run_does_not_write_to_database(fake_site, session_factory, monkeypatch):
    monkeypatch.setattr(collect_parts, "SessionLocal", session_factory)
    FakeSession.pages = lambda url: FakeResponse(listing_page(100, 200))
    assert collect_parts.collect(["04465-02220"], 4.0, dry_run=True) == 0
    with session_factory() as db:
        assert db.scalars(select(Part)).all() == []


def test_saves_offers(fake_site, session_factory, monkeypatch):
    monkeypatch.setattr(collect_parts, "SessionLocal", session_factory)
    FakeSession.pages = lambda url: FakeResponse(listing_page(100, 200))
    assert collect_parts.collect(["04465-02220"], 4.0, dry_run=False) == 0
    with session_factory() as db:
        parts = db.scalars(select(Part).order_by(Part.price)).all()
    assert [(p.shop, p.oem, int(p.price), p.region) for p in parts] == [
        ("bibinet", "0446502220", 100, "Омск"),
        ("bibinet", "0446502220", 200, "Омск"),
    ]


def test_rerun_updates_instead_of_duplicating(fake_site, session_factory, monkeypatch):
    monkeypatch.setattr(collect_parts, "SessionLocal", session_factory)
    FakeSession.pages = lambda url: FakeResponse(listing_page(100))
    collect_parts.collect(["04465-02220"], 4.0, dry_run=False)
    collect_parts.collect(["04465-02220"], 4.0, dry_run=False)
    with session_factory() as db:
        assert len(db.scalars(select(Part)).all()) == 1


def test_read_oem_file_ignores_comments_and_blank_lines(tmp_path):
    path = tmp_path / "oems.txt"
    path.write_text("# детали\n04465-02220\n\n  90915-YZZE1  \n", encoding="utf-8")
    assert collect_parts.read_oem_file(path) == ["04465-02220", "90915-YZZE1"]
