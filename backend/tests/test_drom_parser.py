from app.services.drom_parser import CarSlug, build_url, looks_like_captcha, parse_listings
from app.services.market_prices import Listing

CAMRY = CarSlug("Toyota", "Camry", "toyota", "camry")


def card(title: str, description: str, price: str) -> str:
    return (
        f'<a href="/x"><div><span data-ftid="bull_title">{title}</span></div>'
        f"<div>{description}</div>"
        f'<div><span data-ftid="bull_price">{price}</span><span>₽</span></div></a>'
    )


def page(*cards: str) -> str:
    return f'<html><body><div id="list">{"".join(cards)}</div></body></html>'


def test_parses_price_year_and_mileage():
    html = page(
        card("Toyota Camry, 2015", "2.5 л, бензин, АКПП, 150&nbsp;000 км", "1&nbsp;250&nbsp;000")
    )
    assert parse_listings(html) == [Listing(price=1_250_000, mileage=150_000, year=2015)]


def test_title_and_price_may_be_any_tag_not_only_span():
    # На живом Дроме data-ftid="bull_title" стоит не на <span>; разбор не должен зависеть от тега.
    html = (
        '<div data-ftid="bulls-list_bull"><h3 data-ftid="bull_title">Hyundai Solaris, 2020</h3>'
        '<div data-ftid="component_inline-bull-description">'
        '<span data-ftid="bull_description-item">85 000 км</span></div>'
        '<div data-ftid="bull_price">1 150 000</div></div>'
    )
    assert parse_listings(html) == [Listing(price=1_150_000, mileage=85_000, year=2020)]


def test_parses_several_listings_independently():
    html = page(
        card("Toyota Camry, 2015", "98 000 км", "1 400 000"),
        card("Toyota Camry, 2016", "45 000 км", "1 600 000"),
    )
    assert parse_listings(html) == [
        Listing(1_400_000, 98_000, 2015),
        Listing(1_600_000, 45_000, 2016),
    ]


def test_skips_listing_without_mileage_or_price_or_year():
    html = page(
        card("Toyota Camry, 2015", "новый автомобиль", "1 400 000"),  # нет пробега
        card("Toyota Camry, 2015", "98 000 км", ""),  # нет цены
        card("Toyota Camry", "98 000 км", "1 400 000"),  # нет года
    )
    assert parse_listings(html) == []


def test_skips_absurd_values():
    html = page(
        card("Toyota Camry, 2015", "98 000 км", "1 000"),  # цена слишком мала
        card("Toyota Camry, 2015", "9 900 000 км", "1 400 000"),  # пробег нереальный
    )
    assert parse_listings(html) == []


def test_unexpected_markup_gives_empty_result_not_garbage():
    assert parse_listings("<html><body><p>Ничего нет</p></body></html>") == []
    # заголовок и цена вперемешку в одном общем блоке — карточки не различить
    two_titles_one_container = (
        '<div><span data-ftid="bull_title">A, 2015</span>'
        '<span data-ftid="bull_title">B, 2016</span>'
        '<span data-ftid="bull_price">1 000 000</span> 10 000 км</div>'
    )
    assert parse_listings(two_titles_one_container) == []


def test_build_url():
    assert build_url(CAMRY, 2015) == "https://auto.drom.ru/toyota/camry/?minyear=2015&maxyear=2015"
    assert (
        build_url(CAMRY, 2015, page=3)
        == "https://auto.drom.ru/toyota/camry/page3/?minyear=2015&maxyear=2015"
    )


def test_captcha_detection():
    assert looks_like_captcha("<html>Подтвердите, что вы не робот. SmartCaptcha</html>")
    assert looks_like_captcha("<title>Please complete the CAPTCHA</title>")
    assert not looks_like_captcha(page(card("Toyota Camry, 2015", "98 000 км", "1 400 000")))
