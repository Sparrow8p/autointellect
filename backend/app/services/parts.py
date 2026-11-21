"""Запчасти: нормализация номеров и названий, разбор VIN (чистая логика, без базы и сети)."""

import re
from dataclasses import dataclass

CONDITIONS = ("new", "used")
MAX_PRICE = 10_000_000

_VIN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")  # в VIN не бывает букв I, O, Q

# Первые символы VIN (код производителя, WMI) -> марка из нашего справочника.
# Только однозначные случаи. Например, Hyundai Solaris и Kia Rio российской сборки имеют
# одинаковое начало Z94, поэтому по нему марку определить нельзя, и его здесь нет.
# Сначала проверяются три символа, потом два.
_WMI_BRANDS = {
    "XTA": "Lada (ВАЗ)",
    "XTT": "UAZ",
    "JT": "Toyota",
    "SB1": "Toyota",
    "XW7": "Toyota",
    "JN": "Nissan",
    "Z8N": "Nissan",
    "KMH": "Hyundai",
    "KNA": "Kia",
    "KND": "Kia",
    "KNE": "Kia",
    "WV": "Volkswagen",
    "TMB": "Skoda",
    "VF1": "Renault",
    "X7L": "Renault",
    "WBA": "BMW",
    "WBS": "BMW",
    "WBY": "BMW",
    "WDB": "Mercedes-Benz",
    "WDC": "Mercedes-Benz",
    "WDD": "Mercedes-Benz",
    "WAU": "Audi",
    "TRU": "Audi",
    "JMZ": "Mazda",
    "JM1": "Mazda",
    "JMB": "Mitsubishi",
    "JA3": "Mitsubishi",
    "JA4": "Mitsubishi",
    "WF0": "Ford",
    "X9F": "Ford",
    "1FA": "Ford",
    "1G1": "Chevrolet",
    "KL1": "Chevrolet",
    "L6T": "Geely",
    "LVV": "Chery",
}


@dataclass(frozen=True)
class VinInfo:
    vin: str  # в верхнем регистре
    brand: str | None  # None — по этому VIN марку определить нельзя


@dataclass(frozen=True)
class Offer:
    """Одно предложение запчасти от магазина (то, что парсер или CSV отдают для сохранения)."""

    shop: str
    name: str
    oem: str
    price: int  # ₽
    condition: str  # new / used
    brand: str | None = None
    manufacturer: str | None = None
    region: str | None = None
    url: str | None = None


def normalize_oem(value: str) -> str:
    """'04152-yzza1 ' -> '04152YZZA1': убираем всё, кроме латиницы и цифр."""
    return re.sub(r"[^0-9A-Za-z]", "", value).upper()


def normalize_text(value: str) -> str:
    """Нижний регистр и одиночные пробелы: для поиска по названию."""
    return " ".join(value.lower().split())


def offer_key(offer: Offer) -> str:
    """Ключ предложения внутри магазина: ссылка, а без неё номер + состояние + регион."""
    return offer.url or f"{normalize_oem(offer.oem)}|{offer.condition}|{offer.region or ''}"


def parse_vin(vin: str) -> VinInfo:
    """Проверяет формат VIN (17 символов, без I, O, Q) и определяет марку по его началу."""
    normalized = vin.strip().upper()
    if not _VIN.fullmatch(normalized):
        raise ValueError("VIN must be 17 characters: digits and letters except I, O, Q")
    brand = _WMI_BRANDS.get(normalized[:3]) or _WMI_BRANDS.get(normalized[:2])
    return VinInfo(vin=normalized, brand=brand)
