"""Диагностика парсера: ОДИН запрос к странице Дрома, HTML сохраняется в файл.

Запуск (из папки backend):

    python -m scripts.debug_drom                 # Hyundai Solaris 2020
    python -m scripts.debug_drom --year 2018
    python -m scripts.debug_drom --url "https://auto.drom.ru/toyota/camry/"

Выводит код ответа, адрес после переходов и то, что нашлось в разметке, и сохраняет страницу в
`drom_debug.html`. Этот файл (или первые строки вывода) нужны, чтобы поправить разбор страницы.
Правила те же, что у основного скрипта: честный User-Agent, проверка robots.txt, один запрос.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.services.drom_parser import (
    _MILEAGE,
    _TITLE_YEAR,
    _digits,
    _item_container,
    build_url,
    describe_page,
    looks_like_captcha,
    parse_listings,
)
from scripts.collect_prices import CARS, USER_AGENT, Stopped, load_robots

OUTPUT = Path("drom_debug.html")
CARD_OUTPUT = Path("drom_debug_card.html")


def explain_first_card(html: str) -> None:
    """Показывает, на каком поле первая карточка не разбирается, и сохраняет её разметку."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find(attrs={"data-ftid": "bull_title"})
    if title is None:
        print("\nКарточки: bull_title на странице не найден")
        return
    container = _item_container(title)
    print("\n--- Первая карточка ---")
    if container is None:
        print("Карточка: родитель с ценой не найден или в нём несколько заголовков")
        container = title.find_parent(attrs={"data-ftid": "bulls-list_bull"}) or title.parent

    title_text = title.get_text(" ", strip=True)
    price_tag = container.find(attrs={"data-ftid": "bull_price"})
    price_text = price_tag.get_text(" ", strip=True) if price_tag else None
    text = container.get_text(" ", strip=True).replace("\xa0", " ")
    mileage = _MILEAGE.search(text)
    print(f"Заголовок: {title_text!r}  -> год найден: {bool(_TITLE_YEAR.search(title_text))}")
    print(f"Цена:      {price_text!r}  -> число: {_digits(price_text) if price_text else None}")
    print(f"Пробег:    найден: {mileage.group(0) if mileage else 'нет'}")
    print(f"Текст карточки: {text[:400]!r}")

    # Разметка карточки без картинок и скриптов: компактно и без лишнего.
    clean = BeautifulSoup(str(container), "html.parser")
    for tag in clean(["img", "source", "svg", "script", "style", "noscript", "picture"]):
        tag.decompose()
    CARD_OUTPUT.write_text(clean.prettify(), encoding="utf-8")
    print(f"Разметка первой карточки сохранена в {CARD_OUTPUT.resolve()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument(
        "--url", help="адрес страницы целиком (по умолчанию Solaris с фильтром года)"
    )
    args = parser.parse_args()

    url = args.url or build_url(CARS[2], args.year)  # CARS[2] — Hyundai Solaris
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    try:
        robots = load_robots(session)
        if not robots.can_fetch(USER_AGENT, url):
            print(f"robots.txt не разрешает заходить на {url}")
            return 2
        response = session.get(url, timeout=20)
    except (Stopped, requests.RequestException) as error:
        print(f"Не удалось выполнить запрос: {error}")
        return 1

    html = response.text
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Запрошено:   {url}")
    print(f"Ответ:       {response.status_code}, после переходов: {response.url}")
    print(f"Страница:    {describe_page(html)}")
    print(f"Слова про капчу на странице: {'да' if looks_like_captcha(html) else 'нет'}")
    print(f"Разобрано объявлений: {len(parse_listings(html))}")
    attributes = Counter(re.findall(r'data-ftid="([^"]+)"', html))
    print("Самые частые data-ftid:", dict(attributes.most_common(15)) or "нет ни одного")
    print(f"HTML сохранён в {OUTPUT.resolve()}")
    explain_first_card(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
