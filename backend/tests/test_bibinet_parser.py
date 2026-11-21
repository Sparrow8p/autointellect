import json

import pytest

from app.services.bibinet_parser import PageFormatError, build_url, parse_offers

COMPANIES = {
    "100": {"name": "Магазин А", "city": {"name": "Красноярск"}},
    "200": {"name": "Магазин Б", "city": {"name": "Омск"}},
}


def item(**extra):
    base = {
        "part_class": "new_part",
        "part_title": "Тормозные колодки SN138 ADVICS",
        "price": 4970,
        "url_part": "/new_part/krasnoyarsk/invnn-1",
        "branch_id": 100,
        "sp_name": "ADVICS",
        "sma_name": None,
    }
    return {**base, **extra}


def page(items, companies=COMPANIES, tail=";"):
    data = {"result_search": {"data": items, "company": companies}}
    return (
        "<html><script>window.is_base_site=true;"
        'window.config_site={"a": {"b": 1}};'
        f"window.page_data={json.dumps(data, ensure_ascii=False)}{tail}"
        "</script></html>"
    )


def test_build_url_normalizes_oem():
    assert build_url("04465-02220") == "https://bibinet.ru/part/all/all/all/all/oem/0446502220/"


def test_parses_new_offer():
    [offer] = parse_offers(page([item()]), "04465-02220")
    assert offer.shop == "bibinet"
    assert offer.oem == "0446502220"  # номер, по которому искали
    assert offer.name == "Тормозные колодки SN138 ADVICS"
    assert (offer.price, offer.condition) == (4970, "new")
    assert offer.manufacturer == "ADVICS"
    assert offer.region == "Красноярск"
    assert offer.url == "https://bibinet.ru/new_part/krasnoyarsk/invnn-1"
    assert offer.brand is None


def test_used_offer_and_brand():
    used = item(part_class="used_part", sma_name="Toyota", sp_name=None, branch_id=200)
    [offer] = parse_offers(page([used]), "0446502220")
    assert (offer.condition, offer.brand, offer.manufacturer, offer.region) == (
        "used",
        "Toyota",
        None,
        "Омск",
    )


def test_skips_offers_that_cannot_be_used():
    items = [
        item(price=None),  # цена не указана
        item(price=0),
        item(price="1000"),  # цена строкой — не доверяем
        item(part_class="service"),  # неизвестное состояние
        item(url_part=None),
        item(url_part="http://evil.example/x"),  # ссылка не с нашего сайта
        item(part_title="  "),
        "не словарь",
        item(),  # единственная нормальная
    ]
    assert len(parse_offers(page(items), "0446502220")) == 1


def test_unknown_shop_gives_no_region():
    [offer] = parse_offers(page([item(branch_id=999)]), "0446502220")
    assert offer.region is None


def test_long_title_is_cut_to_column_size():
    [offer] = parse_offers(page([item(part_title="Д" * 500)]), "0446502220")
    assert len(offer.name) == 300


def test_float_price_is_rounded():
    [offer] = parse_offers(page([item(price=1999.6)]), "0446502220")
    assert offer.price == 2000


def test_no_offers_is_not_an_error():
    assert parse_offers(page([]), "0446502220") == []


def test_page_data_may_be_followed_by_other_statements():
    html = page([item()], tail=';window.later={"x": 1};')
    assert len(parse_offers(html, "0446502220")) == 1


@pytest.mark.parametrize(
    "html",
    [
        "<html><body>Подтвердите, что вы не робот</body></html>",  # нет page_data
        "<script>window.page_data=не json;</script>",
        '<script>window.page_data={"other": 1};</script>',  # нет result_search
        '<script>window.page_data={"result_search": {"data": "x"}};</script>',  # data — не список
        "",
    ],
)
def test_unexpected_page_is_an_error_not_garbage(html):
    with pytest.raises(PageFormatError):
        parse_offers(html, "0446502220")
