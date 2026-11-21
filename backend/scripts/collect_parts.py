"""Сбор предложений запчастей с bibinet.ru по списку номеров (OEM) и загрузка в таблицу parts.

Запуск (из папки backend, с активным venv и запущенной базой):

    python -m scripts.collect_parts 04465-02220            # один номер
    python -m scripts.collect_parts 04465-02220 90915-YZZE1  # несколько номеров
    python -m scripts.collect_parts --file oems.txt        # номера из файла, по одному в строке
    python -m scripts.collect_parts --dry-run 04465-02220  # только показать, в базу не писать

С одной страницы берётся до 50 предложений (новые и б/у, разные города). Номера для поиска
нужно подобрать самим, например, найдя нужные детали на сайте.
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Part  # noqa: F401  (регистрирует таблицу для create_all)
from app.services.bibinet_parser import BASE_URL, PageFormatError, build_url, parse_offers
from app.services.part_store import upsert_parts
from app.services.parts import normalize_oem

# Название на ASCII: заголовки HTTP не принимают кириллицу.
USER_AGENT = "AutoIntellectStudentProject/1.0 (student project; average car prices)"
MIN_DELAY = 3.0


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


def fetch(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=20)
    host = urlparse(response.url).hostname or ""
    if not host.endswith("bibinet.ru"):
        raise Stopped(f"сайт перенаправил на другой адрес ({host}) — похоже на проверку")
    if response.status_code != 200:
        raise Stopped(f"сайт ответил {response.status_code}")
    return response.text


def read_oem_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def collect(oems: list[str], delay: float, dry_run: bool) -> int:
    delay = max(delay, MIN_DELAY)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    saved = found = 0
    try:
        robots = load_robots(session)
        for raw in oems:
            oem = normalize_oem(raw)
            if not oem:
                print(f"{raw!r}: в номере нет букв и цифр, пропускаю")
                continue
            url = build_url(oem)
            if not robots.can_fetch(USER_AGENT, url):
                raise Stopped(f"robots.txt не разрешает заходить на {url}")
            time.sleep(delay)
            try:
                offers = parse_offers(fetch(session, url), oem)
            except PageFormatError as error:
                raise Stopped(f"страница не похожа на список предложений ({error})") from error
            kinds = Counter(offer.condition for offer in offers)
            print(f"{oem}: предложений {len(offers)} (новых {kinds['new']}, б/у {kinds['used']})")
            found += len(offers)
            if offers and not dry_run:
                with SessionLocal() as db:
                    saved += upsert_parts(db, offers)
    except Stopped as stop:
        print(f"\nОСТАНОВЛЕНО: {stop}. Обход защиты не выполняется. Сохранено: {saved}.")
        return 2
    except requests.RequestException as error:
        print(f"\nОшибка сети: {error}. Сохранено: {saved}.")
        return 1
    print(f"\nГотово. Найдено предложений: {found}, сохранено: {saved}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("oems", nargs="*", help="номера деталей (OEM)")
    parser.add_argument("--file", type=Path, help="файл с номерами, по одному в строке")
    parser.add_argument("--delay", type=float, default=4.0, help=f"пауза, не меньше {MIN_DELAY} с")
    parser.add_argument("--dry-run", action="store_true", help="ничего не писать в базу")
    args = parser.parse_args()

    oems = list(args.oems) + (read_oem_file(args.file) if args.file else [])
    if not oems:
        parser.error("укажите номера деталей или --file")
    Base.metadata.create_all(bind=engine)
    return collect(oems, args.delay, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
