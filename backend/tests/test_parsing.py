import csv
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.services.parsing import parse_problem, select_works, tokenize

SEED_DIR = Path(__file__).parent.parent / "app" / "db" / "seed_data"


@dataclass
class Rule:
    keyword: str
    work_id: int | None = None
    category: str | None = None


@dataclass
class Work:
    id: int
    name: str
    category: str


def _read(name: str) -> list[dict[str, str]]:
    with open(SEED_DIR / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def rules() -> list[Rule]:
    return [
        Rule(r["keyword"], int(r["work_id"]) if r["work_id"] else None, r["category"] or None)
        for r in _read("work_keywords.csv")
    ]


@pytest.fixture(scope="module")
def works() -> list[Work]:
    return [Work(int(r["id"]), r["name"], r["category"]) for r in _read("works.csv")]


def found_ids(text, rules, works) -> list[int]:
    return [w.id for w in select_works(parse_problem(text, rules), works)]


def test_tokenize_lowercases_and_replaces_yo():
    assert tokenize("Течёт, ТОСОЛ! Масло-фильтр") == ["течет", "тосол", "масло", "фильтр"]


def test_category_word_gives_all_works_of_category(rules, works):
    # «подвеска» -> все пять работ категории «Подвеска»
    assert found_ids("Подвеска", rules, works) == [16, 17, 18, 19, 20]


def test_specific_symptom_narrows_category(rules, works):
    # «стучит» указывает на три детали и вытесняет всю категорию «Подвеска»
    assert found_ids("Стучит подвеска", rules, works) == [16, 17, 20]


def test_word_forms_are_matched_by_stem(rules, works):
    for text in ["Стучит подвеска", "стук в подвеске", "стучат стойки"]:
        assert set(found_ids(text, rules, works)) >= {16}


def test_phrase_matches_words_in_any_order(rules, works):
    assert found_ids("бампера переднего разбит", rules, works) == [9]
    assert found_ids("Задний бампер", rules, works) == [10]


def test_specific_phrase_beats_generic_word(rules, works):
    assert found_ids("передний бампер", rules, works) == [9]
    # без уточнения — оба бампера
    assert found_ids("разбит бампер", rules, works) == [9, 10]


def test_oil_and_filter_phrase(rules, works):
    assert found_ids("Замените, пожалуйста, масло и фильтр", rules, works) == [1, 2]
    assert found_ids("замена масла", rules, works) == [1]


def test_several_problems_in_one_text(rules, works):
    assert found_ids("передний бампер и фара", rules, works) == [9, 13]


def test_short_stems_require_whole_word(rules, works):
    assert found_ids("ремень ГРМ", rules, works) == [23]
    # «грмотный» не должен срабатывать как «грм»
    assert parse_problem("грмотный текст", rules).keywords == []


def test_case_and_yo_do_not_matter(rules, works):
    assert found_ids("ДВИГАТЕЛЬ ПЕРЕГРЕЛСЯ, ТЁК АНТИФРИЗ", rules, works) == [25, 26, 27]


def test_unknown_text_finds_nothing(rules, works):
    assert found_ids("что-то непонятное", rules, works) == []
    assert found_ids("", rules, works) == []


def test_select_works_has_no_duplicates(rules, works):
    ids = found_ids("стучит подвеска, амортизатор и стойка", rules, works)
    assert ids == sorted(set(ids))


def test_seed_keywords_are_consistent(rules, works):
    work_ids = {w.id for w in works}
    categories = {w.category for w in works}
    for rule in rules:
        # ровно одна цель у каждого правила
        assert (rule.work_id is None) != (rule.category is None), rule
        assert rule.keyword == rule.keyword.lower().replace("ё", "е"), rule
        if rule.work_id is not None:
            assert rule.work_id in work_ids, rule
        if rule.category is not None:
            assert rule.category in categories, rule
