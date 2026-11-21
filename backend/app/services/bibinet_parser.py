"""Разбор страницы результатов поиска по OEM на bibinet.ru (чистая логика, без сети).

Страница Бибинета содержит готовые данные в JSON: в скрипте объявлено `window.page_data={...}`,
внутри `result_search.data` лежит список предложений (цена, состояние, ссылка), а в
`result_search.company` — магазины с городами. Поэтому разбирается JSON, а не вёрстка: он устойчивее
к изменению оформления. Если структура изменится, парсер выбросит PageFormatError, а не вернёт
мусор.
"""

import json

from app.services.parts import MAX_PRICE, Offer, normalize_oem

BASE_URL = "https://bibinet.ru"
SHOP = "bibinet"

_MARKER = "window.page_data="
_CONDITIONS = {"new_part": "new", "used_part": "used"}  # part_class -> наше состояние


class PageFormatError(Exception):
    """На странице нет данных в ожидаемом виде: изменилась структура или это не список."""


def build_url(oem: str) -> str:
    return f"{BASE_URL}/part/all/all/all/all/oem/{normalize_oem(oem)}/"


def extract_page_data(html: str) -> dict:
    start = html.find(_MARKER)
    if start == -1:
        raise PageFormatError("в странице нет window.page_data")
    try:
        data, _ = json.JSONDecoder().raw_decode(html[start + len(_MARKER) :])
    except ValueError as error:
        raise PageFormatError("window.page_data не разобрался как JSON") from error
    if not isinstance(data, dict) or not isinstance(data.get("result_search"), dict):
        raise PageFormatError("в page_data нет result_search")
    return data


def _price(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    price = round(value)
    return price if 0 < price <= MAX_PRICE else None


def _city(company: object) -> str | None:
    if not isinstance(company, dict):
        return None
    city = company.get("city")
    name = city.get("name") if isinstance(city, dict) else None
    return name[:100] if isinstance(name, str) and name else None


def parse_offers(html: str, oem: str) -> list[Offer]:
    """Предложения со страницы поиска по номеру `oem`.

    Сохраняется номер, по которому искали: на странице есть и аналоги других производителей,
    но все они показаны как подходящие к этому номеру. Предложения без цены, без ссылки или
    с неизвестным состоянием пропускаются.
    """
    result = extract_page_data(html)["result_search"]
    items = result.get("data")
    if not isinstance(items, list):
        raise PageFormatError("result_search.data — не список")
    companies = result.get("company")
    companies = companies if isinstance(companies, dict) else {}
    searched_oem = normalize_oem(oem)

    offers = []
    for item in items:
        if not isinstance(item, dict):
            continue
        condition = _CONDITIONS.get(item.get("part_class"))
        price = _price(item.get("price"))
        link, title = item.get("url_part"), item.get("part_title")
        if not (condition and price and isinstance(link, str) and link.startswith("/")):
            continue
        if not (isinstance(title, str) and title.strip()):
            continue
        maker, brand = item.get("sp_name"), item.get("sma_name")
        offers.append(
            Offer(
                shop=SHOP,
                name=title.strip()[:300],
                oem=searched_oem,
                price=price,
                condition=condition,
                brand=brand[:100] if isinstance(brand, str) and brand else None,
                manufacturer=maker[:100] if isinstance(maker, str) and maker else None,
                region=_city(companies.get(str(item.get("branch_id")))),
                url=BASE_URL + link,
            )
        )
    return offers
