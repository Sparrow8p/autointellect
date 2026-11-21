import pytest

from app.services.parts import Offer, normalize_oem, normalize_text, offer_key, parse_vin


def test_normalize_oem_keeps_only_latin_letters_and_digits():
    assert normalize_oem("04152-yzza1 ") == "04152YZZA1"
    assert normalize_oem("04 152.YZZA1") == "04152YZZA1"
    assert normalize_oem("---") == ""


def test_normalize_text_lowercases_cyrillic_and_collapses_spaces():
    assert normalize_text("  Колодки   ТОРМОЗНЫЕ ") == "колодки тормозные"


def test_offer_key_prefers_url():
    with_url = Offer("shop", "Фильтр", "A1", 100, "new", url="https://shop/1")
    without_url = Offer("shop", "Фильтр", "A1", 100, "used", region="Москва")
    assert offer_key(with_url) == "https://shop/1"
    assert offer_key(without_url) == "A1|used|Москва"


def test_vin_brand_by_prefix():
    assert parse_vin("XTA210930Y2765432").brand == "Lada (ВАЗ)"
    assert parse_vin("JTDBT923171000000").brand == "Toyota"  # JT... — любой завод Toyota
    assert parse_vin("WVWZZZ1KZAW000000").brand == "Volkswagen"


def test_vin_is_normalized_to_upper_case():
    info = parse_vin("  jtdbt923171000000 ")
    assert info.vin == "JTDBT923171000000"


def test_vin_with_ambiguous_prefix_has_no_brand():
    # Solaris и Rio российской сборки начинаются одинаково (Z94): марку определить нельзя.
    info = parse_vin("Z94CT41DBGR123456")
    assert info.brand is None


@pytest.mark.parametrize(
    "vin",
    [
        "XTA21093",  # короткий
        "XTA210930Y27654321",  # длинный
        "XTA210930Y276543I",  # буква I
        "XTA210930Y276543O",  # буква O
        "XTA210930Y276543Q",  # буква Q
        "XTA210930Y27654-3",  # лишний символ
        "",
    ],
)
def test_invalid_vin_is_rejected(vin):
    with pytest.raises(ValueError):
        parse_vin(vin)
