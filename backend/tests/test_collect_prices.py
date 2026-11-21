"""Скрипт сбора цен: проверяем, что он останавливается на капче и не трогает сеть по-настоящему."""

from argparse import Namespace

import pytest
from sqlalchemy import select

from app.models import MarketPrice
from scripts import collect_prices

ROBOTS_OK = "User-agent: *\nAllow: /\n"


class FakeResponse:
    def __init__(self, text="", status_code=200, url="https://auto.drom.ru/x"):
        self.text, self.status_code, self.url = text, status_code, url


class FakeSession:
    """Вместо requests.Session: отвечает заранее заданными страницами и запоминает запросы."""

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


def card(year, mileage, price):
    return (
        f'<a><span data-ftid="bull_title">Lada Granta, {year}</span><div>{mileage} км</div>'
        f'<span data-ftid="bull_price">{price}</span></a>'
    )


def listing_page(*cards):
    return f"<html><body>{''.join(cards)}</body></html>"


@pytest.fixture()
def fake_site(monkeypatch):
    sleeps = []
    FakeSession.requested = []
    FakeSession.robots = ROBOTS_OK
    monkeypatch.setattr(collect_prices.requests, "Session", FakeSession)
    monkeypatch.setattr(collect_prices.time, "sleep", sleeps.append)
    return sleeps


def args(**extra):
    base = {"delay": 4.0, "pages": 1, "from_year": 2020, "to_year": 2020, "dry_run": True}
    return Namespace(**{**base, **extra})


def page_requests():
    return [u for u in FakeSession.requested if not u.endswith("/robots.txt")]


def test_stops_on_captcha_page(fake_site):
    FakeSession.pages = lambda url: FakeResponse(
        "<html>Подтвердите, что вы не робот. SmartCaptcha</html>"
    )
    assert collect_prices.collect(args()) == 2
    assert len(page_requests()) == 1  # после капчи больше ни одного запроса


@pytest.mark.parametrize("status", [403, 429, 503, 500])
def test_stops_on_blocking_status(fake_site, status):
    FakeSession.pages = lambda url: FakeResponse("", status_code=status)
    assert collect_prices.collect(args()) == 2
    assert len(page_requests()) == 1


def test_stops_when_redirected_to_another_site(fake_site):
    FakeSession.pages = lambda url: FakeResponse("ok", url="https://example.com/check")
    assert collect_prices.collect(args()) == 2
    assert len(page_requests()) == 1


def test_stops_when_robots_txt_forbids(fake_site):
    FakeSession.robots = "User-agent: *\nDisallow: /\n"
    FakeSession.pages = lambda url: FakeResponse(listing_page(card(2020, 10_000, 600_000)))
    assert collect_prices.collect(args()) == 2
    assert page_requests() == []


def test_pause_is_never_shorter_than_minimum(fake_site):
    FakeSession.pages = lambda url: FakeResponse("", status_code=404)
    collect_prices.collect(args(delay=0.1))
    assert fake_site and min(fake_site) >= collect_prices.MIN_DELAY


def test_dry_run_does_not_write_to_database(fake_site, session_factory, monkeypatch):
    monkeypatch.setattr(collect_prices, "SessionLocal", session_factory)
    FakeSession.pages = lambda url: FakeResponse(
        listing_page(*[card(2020, 60_000 + i, 600_000 + i) for i in range(3)])
    )
    assert collect_prices.collect(args(dry_run=True)) == 0
    with session_factory() as db:
        assert db.scalars(select(MarketPrice)).all() == []


def test_saves_median_and_keeps_only_requested_year(fake_site, session_factory, monkeypatch):
    monkeypatch.setattr(collect_prices, "SessionLocal", session_factory)
    first_car_url = collect_prices.build_url(collect_prices.CARS[0], 2020)

    def pages(url):
        if url != first_car_url:
            return FakeResponse("", status_code=404)  # остальные модели: объявлений нет
        cards = [card(2020, 60_000, p) for p in (500_000, 600_000, 900_000)]
        cards.append(card(2019, 60_000, 100_000))  # чужой год не должен попасть
        return FakeResponse(listing_page(*cards))

    FakeSession.pages = pages
    assert collect_prices.collect(args(dry_run=False)) == 0
    with session_factory() as db:
        rows = db.scalars(select(MarketPrice)).all()
    assert len(rows) == 1
    row = rows[0]
    assert (row.brand, row.model, row.year, row.mileage_band) == (
        "Lada (ВАЗ)",
        "Granta",
        2020,
        50_000,
    )
    assert (int(row.price), row.samples, row.source) == (600_000, 3, "drom")


def test_import_csv(tmp_path, session_factory, monkeypatch):
    monkeypatch.setattr(collect_prices, "SessionLocal", session_factory)
    path = tmp_path / "prices.csv"
    path.write_text(
        "brand,model,year,mileage_band,price,samples\nKia,Rio,2019,50000,900000,5\n",
        encoding="utf-8",
    )
    assert collect_prices.import_csv(path) == 1
    with session_factory() as db:
        row = db.scalar(select(MarketPrice))
    assert (row.brand, row.model, int(row.price), row.source) == ("Kia", "Rio", 900_000, "manual")


@pytest.mark.parametrize(
    "line",
    [
        "Kia,Rio,2019,55000,900000,5",  # корзина не кратна 50 000
        "Kia,Rio,2019,50000,0,5",  # нулевая цена
        "Kia,Rio,abc,50000,900000,5",  # год не число
        ",Rio,2019,50000,900000,5",  # пустая марка
    ],
)
def test_import_csv_rejects_bad_rows(tmp_path, session_factory, monkeypatch, line):
    monkeypatch.setattr(collect_prices, "SessionLocal", session_factory)
    path = tmp_path / "prices.csv"
    path.write_text("brand,model,year,mileage_band,price,samples\n" + line + "\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        collect_prices.import_csv(path)
