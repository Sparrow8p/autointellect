"""Загрузка запчастей из CSV в таблицу parts.

Запуск (из папки backend, с активным venv и запущенной базой):

    python -m scripts.import_parts parts.csv

Колонки (шаблон — scripts/parts_template.csv):
    shop          название магазина (обязательно)
    name          название детали (обязательно)
    oem           номер детали (обязательно); дефисы и пробелы будут убраны
    price         цена в рублях, целое число (обязательно)
    condition     new или used (обязательно)
    brand         марка авто, как в справочнике (Toyota, Lada (ВАЗ) ...); пусто — универсальная
    manufacturer  производитель детали
    region        регион магазина или склада
    url           ссылка на предложение

Файл проверяется целиком до записи: при ошибке в любой строке в базу не попадает ничего.
"""

import csv
import sys
from pathlib import Path

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Part  # noqa: F401  (регистрирует таблицу для create_all)
from app.services.part_store import upsert_parts
from app.services.parts import CONDITIONS, MAX_PRICE, Offer, normalize_oem


def read_offers(path: Path) -> list[Offer]:
    """Читает и проверяет CSV; при первой ошибке останавливается с номером строки."""
    offers = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        for number, row in enumerate(csv.DictReader(file), start=2):
            row = {key: (value or "").strip() for key, value in row.items() if key}
            shop, name = row.get("shop", ""), row.get("name", "")
            oem = normalize_oem(row.get("oem", ""))
            condition = row.get("condition", "").lower()
            try:
                price = int(row.get("price", ""))
            except ValueError:
                raise SystemExit(f"Строка {number}: price должна быть целым числом") from None
            if not (shop and name and oem):
                raise SystemExit(f"Строка {number}: shop, name и oem обязательны")
            if condition not in CONDITIONS:
                raise SystemExit(f"Строка {number}: condition — new или used, а не {condition!r}")
            if not 0 < price <= MAX_PRICE:
                raise SystemExit(f"Строка {number}: price должна быть от 1 до {MAX_PRICE}")
            offers.append(
                Offer(
                    shop=shop,
                    name=name,
                    oem=oem,
                    price=price,
                    condition=condition,
                    brand=row.get("brand") or None,
                    manufacturer=row.get("manufacturer") or None,
                    region=row.get("region") or None,
                    url=row.get("url") or None,
                )
            )
    return offers


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    offers = read_offers(Path(sys.argv[1]))
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        count = upsert_parts(db, offers)
    print(f"Загружено предложений: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
