"""Запись предложений запчастей в базу: обновляет существующее или добавляет новое."""

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Part
from app.services.parts import Offer, normalize_oem, normalize_text, offer_key


def upsert_parts(db: Session, offers: Iterable[Offer]) -> int:
    """Сохраняет предложения; возвращает их количество. Предложение узнаётся по магазину и ключу."""
    count = 0
    for offer in offers:
        key = offer_key(offer)
        existing = db.scalar(select(Part).where(Part.shop == offer.shop, Part.offer_key == key))
        if existing is None:
            existing = Part(shop=offer.shop, offer_key=key)
            db.add(existing)
        else:
            existing.collected_at = datetime.now(UTC)
        existing.brand = offer.brand
        existing.name = offer.name
        existing.name_lower = normalize_text(offer.name)
        existing.oem = normalize_oem(offer.oem)  # поиск идёт по нормализованному номеру
        existing.manufacturer = offer.manufacturer
        existing.price = Decimal(offer.price)
        existing.condition = offer.condition
        existing.region = offer.region
        existing.url = offer.url
        count += 1
    db.commit()
    return count
