import pytest
from sqlalchemy import func, select

from app.models import Part
from app.services.part_store import upsert_parts
from app.services.parts import Offer
from scripts import import_parts

URL = "/api/parts"
LADA_VIN = "XTA210930Y2765432"  # начало XTA — Lada (ВАЗ)
UNKNOWN_VIN = "Z94CT41DBGR123456"  # марку определить нельзя

HEADER = "shop,name,oem,price,condition,brand,manufacturer,region,url\n"


@pytest.fixture()
def parts(session_factory):
    offers = [
        Offer(
            "euroauto",
            "Колодки тормозные передние",
            "04465-02220",
            2_500,
            "new",
            brand="Toyota",
            manufacturer="Toyota",
            region="Москва",
            url="https://shop/1",
        ),
        Offer(
            "euroauto",
            "Колодки тормозные передние",
            "04465-02220",
            1_200,
            "used",
            brand="Toyota",
            region="Свердловская область",
            url="https://shop/2",
        ),
        Offer(
            "bibinet",
            "Масляный фильтр",
            "W 712/75",
            600,
            "new",
            manufacturer="Mann",
            region="Москва",
            url="https://shop/3",
        ),  # универсальный
        Offer(
            "bibinet",
            "Масляный фильтр 2105",
            "2105-1012005",
            300,
            "new",
            brand="Lada (ВАЗ)",
            region="Москва",
            url="https://shop/4",
        ),
        Offer(
            "bibinet",
            "Масло моторное 5W-30, скидка 5%",
            "OIL5W30",
            3_000,
            "new",
            url="https://shop/5",
        ),
    ]
    with session_factory() as db:
        upsert_parts(db, offers)


def search(client, headers, **params):
    response = client.get(URL, params=params, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def names(body):
    return [item["name"] for item in body["items"]]


def test_search_by_oem_ignores_case_and_separators(client, auth_headers, parts):
    for oem in ("04465-02220", "0446502220", "04465 02220"):
        body = search(client, auth_headers, oem=oem)
        assert body["total"] == 2
    assert search(client, auth_headers, oem="w712/75")["total"] == 1


def test_search_by_name_is_case_insensitive_for_cyrillic(client, auth_headers, parts):
    assert search(client, auth_headers, q="КОЛОДКИ")["total"] == 2
    assert search(client, auth_headers, q="фильтр")["total"] == 2
    assert search(client, auth_headers, q="нет такой детали")["total"] == 0


def test_percent_in_query_is_literal(client, auth_headers, parts):
    body = search(client, auth_headers, q="5%")
    assert names(body) == ["Масло моторное 5W-30, скидка 5%"]


def test_price_filter_is_inclusive(client, auth_headers, parts):
    body = search(client, auth_headers, min_price=600, max_price=2_500)
    assert sorted(item["price"] for item in body["items"]) == [600, 1_200, 2_500]


def test_condition_filter(client, auth_headers, parts):
    used = search(client, auth_headers, condition="used")
    assert [item["price"] for item in used["items"]] == [1_200]
    assert search(client, auth_headers, condition="new")["total"] == 4


def test_region_filter(client, auth_headers, parts):
    body = search(client, auth_headers, region="Свердловская область")
    assert [item["price"] for item in body["items"]] == [1_200]
    assert search(client, auth_headers, region="Москва")["total"] == 3


def test_filters_combine(client, auth_headers, parts):
    body = search(client, auth_headers, q="колодки", condition="new", region="Москва")
    assert [item["price"] for item in body["items"]] == [2_500]


def test_vin_filters_by_brand_and_keeps_universal_parts(client, auth_headers, parts):
    body = search(client, auth_headers, vin=LADA_VIN, q="фильтр")
    assert sorted(item["price"] for item in body["items"]) == [300, 600]  # Lada + универсальный
    assert body["vin"] == {"vin": LADA_VIN, "brand": "Lada (ВАЗ)"}
    # детали Toyota под Lada не показываются
    assert search(client, auth_headers, vin=LADA_VIN, q="колодки")["total"] == 0


def test_unknown_vin_brand_does_not_filter(client, auth_headers, parts):
    body = search(client, auth_headers, vin=UNKNOWN_VIN)
    assert body["vin"] == {"vin": UNKNOWN_VIN, "brand": None}
    assert body["total"] == 5


def test_sort_and_pagination(client, auth_headers, parts):
    ascending = search(client, auth_headers, sort="price_asc")
    assert [i["price"] for i in ascending["items"]] == [300, 600, 1_200, 2_500, 3_000]
    descending = search(client, auth_headers, sort="price_desc", limit=2, offset=1)
    assert [i["price"] for i in descending["items"]] == [2_500, 1_200]
    assert descending["total"] == 5  # total не зависит от limit и offset


def test_item_fields(client, auth_headers, parts):
    item = search(client, auth_headers, oem="04465-02220", condition="new")["items"][0]
    assert item["oem"] == "0446502220"
    assert (item["brand"], item["shop"], item["condition"]) == ("Toyota", "euroauto", "new")
    assert (item["region"], item["url"], item["price"]) == ("Москва", "https://shop/1", 2_500)


def test_requires_token(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize(
    "params",
    [
        {"vin": "XTA21093"},  # неверный VIN
        {"vin": "XTA210930Y276543I"},  # буква I
        {"min_price": 100, "max_price": 50},
        {"oem": "---"},  # после очистки пусто
        {"condition": "broken"},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"min_price": -1},
    ],
)
def test_invalid_query_is_rejected(client, auth_headers, params):
    assert client.get(URL, params=params, headers=auth_headers).status_code == 422


# --- сохранение предложений ---


def test_upsert_updates_same_offer(session_factory):
    offer = Offer("shop", "Фильтр", "A1", 100, "new", url="https://shop/1")
    newer = Offer("shop", "Фильтр воздушный", "A1", 90, "new", url="https://shop/1")
    with session_factory() as db:
        upsert_parts(db, [offer])
        upsert_parts(db, [newer])
        assert db.scalar(select(func.count()).select_from(Part)) == 1
        part = db.scalar(select(Part))
        assert (part.name, int(part.price), part.name_lower) == (
            "Фильтр воздушный",
            90,
            "фильтр воздушный",
        )


def test_same_oem_in_different_shops_is_kept_separately(session_factory):
    with session_factory() as db:
        upsert_parts(db, [Offer("a", "Деталь", "X1", 100, "new")])
        upsert_parts(db, [Offer("b", "Деталь", "X1", 110, "new")])
        assert db.scalar(select(func.count()).select_from(Part)) == 2


# --- импорт из CSV ---


def write_csv(tmp_path, *lines):
    path = tmp_path / "parts.csv"
    path.write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_import_reads_valid_rows(tmp_path):
    path = write_csv(
        tmp_path,
        "euroauto,Колодки,04465-02220,2500,NEW,Toyota,Toyota,Москва,https://shop/1",
        "bibinet,Фильтр,W 712/75,600,used,,Mann,,",
    )
    first, second = import_parts.read_offers(path)
    assert (first.oem, first.price, first.condition, first.brand) == (
        "0446502220",
        2500,
        "new",
        "Toyota",
    )
    assert (second.oem, second.brand, second.region, second.url) == ("W71275", None, None, None)


@pytest.mark.parametrize(
    "line",
    [
        "euroauto,Колодки,04465,abc,new,,,,",  # цена не число
        "euroauto,Колодки,04465,0,new,,,,",  # цена ноль
        "euroauto,Колодки,04465,100,broken,,,,",  # неверное состояние
        "euroauto,,04465,100,new,,,,",  # нет названия
        "euroauto,Колодки,---,100,new,,,,",  # номер пуст после очистки
        ",Колодки,04465,100,new,,,,",  # нет магазина
    ],
)
def test_import_rejects_bad_rows(tmp_path, line):
    with pytest.raises(SystemExit):
        import_parts.read_offers(write_csv(tmp_path, line))


def test_import_is_checked_fully_before_saving(tmp_path, session_factory, monkeypatch):
    monkeypatch.setattr(import_parts, "SessionLocal", session_factory)
    path = write_csv(
        tmp_path,
        "euroauto,Колодки,04465,2500,new,,,,",
        "euroauto,Фильтр,A1,abc,new,,,,",  # ошибка во второй строке
    )
    monkeypatch.setattr("sys.argv", ["import_parts", str(path)])
    with pytest.raises(SystemExit):
        import_parts.main()
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Part)) == 0


def test_import_saves_rows(tmp_path, session_factory, monkeypatch):
    monkeypatch.setattr(import_parts, "SessionLocal", session_factory)
    path = write_csv(tmp_path, "euroauto,Колодки,04465-02220,2500,new,Toyota,,Москва,")
    monkeypatch.setattr("sys.argv", ["import_parts", str(path)])
    assert import_parts.main() == 0
    with session_factory() as db:
        part = db.scalar(select(Part))
    assert (part.shop, part.oem, int(part.price), part.region) == (
        "euroauto",
        "0446502220",
        2500,
        "Москва",
    )
