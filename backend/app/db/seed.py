"""Начальные данные: работы (нормо-часы), ключевые слова, регионы, марки и модели.

Загрузка идемпотентна и только ДОБАВЛЯЕТ недостающие строки: существующие не
перезаписываются, поэтому правки в базе (например, коэффициент региона)
переживают перезапуск приложения. Источник данных — файлы в app/db/seed_data/.
"""

import csv
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Brand, CarModel, Region, Work, WorkKeyword

SEED_DIR = Path(__file__).parent / "seed_data"


def _read_csv(name: str) -> list[dict[str, str]]:
    with open(SEED_DIR / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _seed_works(db: Session) -> None:
    existing = set(db.scalars(select(Work.id)))
    for row in _read_csv("works.csv"):
        work_id = int(row["id"])
        if work_id in existing:
            continue
        db.add(
            Work(
                id=work_id,
                name=row["name"],
                hours=Decimal(row["hours"]),
                part_price=Decimal(row["part_price"]),
                category=row["category"],
            )
        )
    db.flush()


def _seed_keywords(db: Session) -> None:
    existing = {
        tuple(r)
        for r in db.execute(select(WorkKeyword.keyword, WorkKeyword.work_id, WorkKeyword.category))
    }
    for row in _read_csv("work_keywords.csv"):
        key = (
            row["keyword"],
            int(row["work_id"]) if row["work_id"] else None,
            row["category"] or None,
        )
        if key not in existing:
            db.add(WorkKeyword(keyword=key[0], work_id=key[1], category=key[2]))
            existing.add(key)


def _seed_regions(db: Session) -> None:
    existing = set(db.scalars(select(Region.name)))
    for row in _read_csv("regions.csv"):
        if row["name"] not in existing:
            db.add(Region(name=row["name"], coefficient=Decimal(row["coefficient"])))


def _seed_brands(db: Session) -> None:
    data: dict[str, list[str]] = json.loads((SEED_DIR / "brands.json").read_text(encoding="utf-8"))
    brands = {b.name: b for b in db.scalars(select(Brand))}
    for brand_name in data:
        if brand_name not in brands:
            brands[brand_name] = Brand(name=brand_name)
            db.add(brands[brand_name])
    db.flush()

    existing = {tuple(r) for r in db.execute(select(CarModel.brand_id, CarModel.name))}
    for brand_name, models in data.items():
        brand_id = brands[brand_name].id
        for model_name in models:
            if (brand_id, model_name) not in existing:
                db.add(CarModel(brand_id=brand_id, name=model_name))


def seed_reference_data(db: Session) -> None:
    _seed_works(db)
    _seed_keywords(db)
    _seed_regions(db)
    _seed_brands(db)
    db.commit()
