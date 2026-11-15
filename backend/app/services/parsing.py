"""Разбор текста проблемы («Стучит подвеска») по ключевым словам из базы.

Модуль не зависит от БД и фреймворка: правила приходят списком объектов с полями
keyword / work_id / category (в приложении это строки таблицы work_keywords).

Как сопоставляется слово:
- ключевое слово хранится как основа («подвеск»): оно найдёт «подвеска», «подвески»,
  «подвеску» и т. д. — совпадает начало любого слова из текста;
- основы длиной до 3 букв («грм», «акб») должны совпасть со словом целиком,
  иначе они ловят лишнее;
- ключевое слово из нескольких основ («передн бампер») срабатывает, если в тексте
  есть слова на каждую из основ, в любом порядке;
- если сработало более конкретное ключевое слово («передн бампер»), более общее
  («бампер») отбрасывается;
- конкретная работа вытесняет целую категорию (см. select_works).

Ограничения: отрицания («не стучит») не учитываются, опечатки не исправляются.
"""

import re
from collections.abc import Iterable
from typing import NamedTuple, Protocol

_TOKEN_RE = re.compile(r"[a-zа-я0-9]+")
_EXACT_MATCH_MAX_LEN = 3


class KeywordRule(Protocol):
    keyword: str
    work_id: int | None
    category: str | None


class WorkLike(Protocol):
    id: int
    category: str


class ParseResult(NamedTuple):
    keywords: list[str]  # сработавшие ключевые слова (после отбрасывания общих)
    work_ids: set[int]  # конкретные работы
    categories: set[str]  # категории целиком


def normalize(text: str) -> str:
    return text.lower().replace("ё", "е")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize(text))


def _stem_in_tokens(stem: str, tokens: list[str]) -> bool:
    if len(stem) <= _EXACT_MATCH_MAX_LEN:
        return stem in tokens
    return any(token.startswith(stem) for token in tokens)


def _keyword_in_tokens(keyword: str, tokens: list[str]) -> bool:
    stems = keyword.split()
    return bool(stems) and all(_stem_in_tokens(stem, tokens) for stem in stems)


def parse_problem(text: str, rules: Iterable[KeywordRule]) -> ParseResult:
    tokens = tokenize(text)
    rules = list(rules)

    fired = {rule.keyword for rule in rules if _keyword_in_tokens(rule.keyword, tokens)}
    # Более конкретное слово («передн бампер») вытесняет общее («бампер»).
    stem_sets = {keyword: set(keyword.split()) for keyword in fired}
    kept = {
        keyword
        for keyword in fired
        if not any(stem_sets[keyword] < stem_sets[other] for other in fired)
    }

    work_ids: set[int] = set()
    categories: set[str] = set()
    for rule in rules:
        if rule.keyword not in kept:
            continue
        if rule.work_id is not None:
            work_ids.add(rule.work_id)
        if rule.category is not None:
            categories.add(rule.category)
    return ParseResult(sorted(kept), work_ids, categories)


def select_works[W: WorkLike](result: ParseResult, works: Iterable[W]) -> list[W]:
    """Выбирает работы по результату разбора.

    Название категории («подвеска») даёт все работы этой категории — но только
    если текст не назвал в ней ничего конкретнее («стучит» -> стойка, амортизатор,
    шаровая): тогда берутся только конкретные работы.
    """
    works = list(works)
    specific = [work for work in works if work.id in result.work_ids]
    covered = {work.category for work in specific}
    whole_categories = result.categories - covered
    by_category = [work for work in works if work.category in whole_categories]
    unique = {work.id: work for work in (*specific, *by_category)}
    return [unique[work_id] for work_id in sorted(unique)]
