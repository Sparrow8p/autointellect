"""Сбор средних цен авто с auto.drom.ru и загрузка в таблицу market_prices.

Запуск (из папки backend, с активным venv):

    python -m scripts.collect_prices                  # собрать с Дрома и сохранить в базу
    python -m scripts.collect_prices --dry-run        # только показать, в базу не писать
    python -m scripts.collect_prices --csv prices.csv # загрузить готовую таблицу цен вручную

Правила работы парсера:
  * представляется честно (User-Agent с названием проекта), вёрстку браузера не подделывает;
  * читает robots.txt и не заходит туда, куда он не разрешает;
  * между запросами пауза не меньше 3 секунд;
  * при капче, ответе 403/429/503 или переходе на другой сайт сразу ОСТАНАВЛИВАЕТСЯ,
    не пытаясь её обойти. Всё, что собрано до остановки, сохраняется.
"""

import argparse
import csv
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import MarketPrice  # noqa: F401  (регистрирует таблицу для create_all)
from app.services.drom_parser import (
    BASE_URL,
    CarSlug,
    build_url,
    describe_page,
    looks_like_captcha,
    parse_listings,
)
from app.services.market_price_store import upsert_prices
from app.services.market_prices import BAND_SIZE, MAX_BAND, Aggregate, aggregate

# Название на ASCII: заголовки HTTP не принимают кириллицу.
USER_AGENT = "AutoIntellectStudentProject/1.0 (student project; average car prices)"
MIN_DELAY = 3.0
SOURCE = "drom"

# 10 популярных моделей. Названия марки и модели — как в справочнике (brands.json),
# слаги — как в адресе auto.drom.ru.
CARS = [
    CarSlug("Lada (ВАЗ)", "Granta", "lada", "granta"),
    CarSlug("Lada (ВАЗ)", "Vesta", "lada", "vesta"),
    CarSlug("Hyundai", "Solaris", "hyundai", "solaris"),
    CarSlug("Kia", "Rio", "kia", "rio"),
    CarSlug("Volkswagen", "Polo", "volkswagen", "polo"),
    CarSlug("Skoda", "Octavia", "skoda", "octavia"),
    CarSlug("Toyota", "Camry", "toyota", "camry"),
    CarSlug("Toyota", "Corolla", "toyota", "corolla"),
    CarSlug("Renault", "Logan", "renault", "logan"),
    CarSlug("Nissan", "Qashqai", "nissan", "qashqai"),
]


class Stopped(Exception):
    """Сайт не хочет, чтобы мы продолжали: останавливаемся и ничего не обходим."""


def load_robots(session: requests.Session) -> RobotFileParser:
    robots = RobotFileParser()
    response = session.get(f"{BASE_URL}/robots.txt", timeout=20)
    if response.status_code == 200:
        robots.parse(response.text.splitlines())
    elif response.status_code == 404:
        robots.parse([])  # robots.txt нет — ограничений нет
    else:
        raise Stopped(f"не удалось прочитать robots.txt (ответ {response.status_code})")
    return robots


def fetch(session: requests.Session, url: str) -> str | None:
    """HTML страницы; None, если страницы нет (404)."""
    response = session.get(url, timeout=20)
    host = urlparse(response.url).hostname or ""
    if not host.endswith("drom.ru"):
        raise Stopped(f"сайт перенаправил на другой адрес ({host}) — похоже на проверку")
    if response.status_code == 404:
        return None
    if response.status_code in (403, 429, 503):
        raise Stopped(f"сайт отказал в доступе (ответ {response.status_code})")
    if response.status_code != 200:
        raise Stopped(f"неожиданный ответ сайта: {response.status_code}")
    return response.text


def collect(args: argparse.Namespace) -> int:
    delay = max(args.delay, MIN_DELAY)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    saved = 0
    found = 0  # строк цен найдено (в dry-run они не сохраняются)
    try:
        robots = load_robots(session)
        for car in CARS:
            for year in range(args.from_year, args.to_year + 1):
                listings = []
                note = ""  # почему объявлений нет, для диагностики
                for page in range(1, args.pages + 1):
                    url = build_url(car, year, page)
                    if not robots.can_fetch(USER_AGENT, url):
                        raise Stopped(f"robots.txt не разрешает заходить на {url}")
                    time.sleep(delay)
                    html = fetch(session, url)
                    if html is None:
                        note = "страница не найдена (404)"
                        break
                    page_listings = parse_listings(html)
                    if not page_listings:
                        if looks_like_captcha(html):
                            raise Stopped("сайт показал капчу")
                        if page == 1:
                            if 'data-ftid="bull_title"' in html:
                                note = f"карточки есть, но не разобраны! ({describe_page(html)})"
                            else:
                                note = "на странице нет объявлений: таких авто нет в продаже"
                        break  # объявлений больше нет (или вёрстка изменилась)
                    # Только объявления нужного года: так каждая пара (модель, год)
                    # считается по своему запросу.
                    listings += [item for item in page_listings if item.year == year]

                rows = aggregate(listings)
                found += len(rows)
                title = f"{car.brand} {car.model} {year}"
                line = f"{title}: объявлений {len(listings)}, строк цен {len(rows)}"
                print(f"{line} — {note}" if note and not listings else line)
                if rows and not args.dry_run:
                    with SessionLocal() as db:
                        saved += upsert_prices(db, car.brand, car.model, rows, SOURCE)
    except Stopped as stop:
        print(f"\nОСТАНОВЛЕНО: {stop}. Обход защиты не выполняется. Сохранено строк: {saved}.")
        return 2
    except requests.RequestException as error:
        print(f"\nОшибка сети: {error}. Сохранено строк: {saved}.")
        return 1
    print(f"\nГотово. Найдено строк цен: {found}, сохранено: {saved}.")
    if found == 0:
        print(
            "Не найдено ни одной цены, хотя сайт отвечал без ошибок. Возможно, Дром "
            "изменил вёрстку (тогда нужно поправить app/services/drom_parser.py) "
            "или объявлений слишком мало."
        )
    return 0


def import_csv(path: Path) -> int:
    """Загрузка готовой таблицы: brand,model,year,mileage_band,price,samples."""
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as file, SessionLocal() as db:
        for number, row in enumerate(csv.DictReader(file), start=2):
            try:
                brand, model = row["brand"].strip(), row["model"].strip()
                year, band = int(row["year"]), int(row["mileage_band"])
                price, samples = int(row["price"]), int(row["samples"])
            except (KeyError, ValueError, AttributeError) as error:
                raise SystemExit(f"Строка {number}: неверные данные ({error!r})") from error
            if not (brand and model and 1950 <= year <= date.today().year + 1):
                raise SystemExit(f"Строка {number}: пустая марка/модель или странный год")
            if band % BAND_SIZE or not 0 <= band <= MAX_BAND:
                raise SystemExit(
                    f"Строка {number}: mileage_band — кратно {BAND_SIZE}, от 0 до {MAX_BAND}"
                )
            if price <= 0 or samples <= 0:
                raise SystemExit(f"Строка {number}: price и samples должны быть больше 0")
            count += upsert_prices(
                db, brand, model, [Aggregate(year, band, price, samples)], source="manual"
            )
    return count


def main() -> int:
    this_year = date.today().year
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--csv", type=Path, help="загрузить цены из CSV вместо сбора с сайта")
    parser.add_argument("--from-year", type=int, default=this_year - 10)
    parser.add_argument("--to-year", type=int, default=this_year - 1)
    parser.add_argument("--pages", type=int, default=3, help="страниц списка на модель и год")
    parser.add_argument(
        "--delay", type=float, default=4.0, help=f"пауза между запросами, не меньше {MIN_DELAY} с"
    )
    parser.add_argument("--dry-run", action="store_true", help="ничего не писать в базу")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    if args.csv:
        print(f"Загружено строк: {import_csv(args.csv)}")
        return 0
    return collect(args)


if __name__ == "__main__":
    sys.exit(main())
