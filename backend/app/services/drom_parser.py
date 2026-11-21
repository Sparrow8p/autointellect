"""Разбор страницы списка объявлений auto.drom.ru (чистая логика, без сети).

ВАЖНО: вёрстка Дрома не проверялась на живом сайте из рабочей среды разработки. Классы в ней
случайные (css-1ctbluq и т.п.), поэтому разбор опирается на стабильные атрибуты `data-ftid`
(`bull_title`, `bull_price`) и на текст объявления. Если Дром поменяет вёрстку, парсер вернёт
пустой список, а не неверные данные.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag

from app.services.market_prices import Listing

BASE_URL = "https://auto.drom.ru"

# Разумные границы: отсекают опечатки в объявлениях и «цену за месяц аренды».
MIN_PRICE = 30_000
MAX_PRICE = 50_000_000
MAX_MILEAGE = 1_000_000

_TITLE_YEAR = re.compile(r",\s*(\d{4})\s*$")
_MILEAGE = re.compile(r"(\d{1,3}(?:\s\d{3})+|\d+)\s*км\b")
_CAPTCHA_MARKERS = ("captcha", "капч", "вы не робот", "подозрительн")


@dataclass(frozen=True)
class CarSlug:
    """Как марка и модель выглядят в адресе Дрома: auto.drom.ru/toyota/camry/."""

    brand: str  # название марки в нашей базе, например «Lada (ВАЗ)»
    model: str  # название модели в нашей базе
    brand_slug: str
    model_slug: str


def build_url(car: CarSlug, year: int, page: int = 1) -> str:
    """Адрес списка объявлений: марка/модель, один год выпуска, страница."""
    path = f"{BASE_URL}/{car.brand_slug}/{car.model_slug}/"
    if page > 1:
        path += f"page{page}/"
    return f"{path}?{urlencode({'minyear': year, 'maxyear': year})}"


def looks_like_captcha(html: str) -> bool:
    text = html.lower()
    return any(marker in text for marker in _CAPTCHA_MARKERS)


def describe_page(html: str) -> str:
    """Короткое описание страницы для диагностики: что на ней нашлось из ожидаемой разметки."""
    titles = html.count('data-ftid="bull_title"')
    prices = html.count('data-ftid="bull_price"')
    return f"размер {len(html) // 1024} КБ, bull_title: {titles}, bull_price: {prices}"


def _digits(text: str) -> int | None:
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def _item_container(title: Tag) -> Tag | None:
    """Ближайший родитель заголовка, внутри которого есть цена: это карточка объявления."""
    container = title.find_parent(lambda tag: tag.find(attrs={"data-ftid": "bull_price"}))
    if container is None:
        return None
    # Слишком широкий родитель (весь список) — значит, структура не та, что ожидали.
    if len(container.find_all(attrs={"data-ftid": "bull_title"})) != 1:
        return None
    return container


def parse_listings(html: str) -> list[Listing]:
    """Объявления со страницы: цена, пробег, год. Без пробега или цены — пропускаем."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for title in soup.find_all(attrs={"data-ftid": "bull_title"}):
        container = _item_container(title)
        if container is None:
            continue

        year_match = _TITLE_YEAR.search(title.get_text(" ", strip=True))
        price_tag = container.find(attrs={"data-ftid": "bull_price"})
        price = _digits(price_tag.get_text()) if price_tag else None
        # Неразрывные пробелы в «150 000 км» приводим к обычным.
        text = container.get_text(" ", strip=True).replace("\xa0", " ")
        mileage_match = _MILEAGE.search(text)
        if not (year_match and price and mileage_match):
            continue

        mileage = int(re.sub(r"\s", "", mileage_match.group(1)))
        if MIN_PRICE <= price <= MAX_PRICE and mileage <= MAX_MILEAGE:
            listings.append(Listing(price=price, mileage=mileage, year=int(year_match.group(1))))
    return listings
