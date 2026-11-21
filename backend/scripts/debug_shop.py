"""Диагностика страницы магазина запчастей: ОДИН запрос, HTML сохраняется в файл.

Запуск (из папки backend). Откройте сайт магазина в браузере, найдите любую деталь по номеру
и скопируйте адрес страницы результатов:

    python -m scripts.debug_shop "https://адрес-страницы-результатов"

Скрипт проверяет robots.txt, делает один запрос с честным User-Agent, печатает код ответа и то, что
нашлось в разметке (структурированные данные, атрибуты data-*, цены), и сохраняет страницу в
`shop_debug.html`. По этим данным пишется разбор страницы магазина.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "AutoIntellectStudentProject/1.0 (student project; average car prices)"
OUTPUT = Path("shop_debug.html")
CAPTCHA_MARKERS = ("captcha", "капч", "вы не робот", "подозрительн")

# Признаки, по которым можно разобрать страницу не по вёрстке, а по данным.
HINTS = {
    'itemprop="price"': "микроразметка цены (schema.org)",
    "application/ld+json": "данные JSON-LD",
    "__NEXT_DATA__": "данные Next.js",
    "__INITIAL_STATE__": "начальное состояние приложения",
    "₽": "знак ₽",
    "руб": "слово «руб»",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    url = sys.argv[1]
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        print("Нужен полный адрес, начинающийся с https://")
        return 1

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    try:
        robots = RobotFileParser()
        robots_response = session.get(f"{parts.scheme}://{parts.hostname}/robots.txt", timeout=20)
        if robots_response.status_code == 200:
            robots.parse(robots_response.text.splitlines())
        elif robots_response.status_code == 404:
            robots.parse([])
        else:
            print(f"Не удалось прочитать robots.txt (ответ {robots_response.status_code})")
            return 2
        if not robots.can_fetch(USER_AGENT, url):
            print("robots.txt не разрешает заходить на этот адрес. Останавливаюсь.")
            return 2
        response = session.get(url, timeout=20)
    except requests.RequestException as error:
        print(f"Не удалось выполнить запрос: {error}")
        return 1

    html = response.text
    OUTPUT.write_text(html, encoding="utf-8")
    text = html.lower()
    print(f"Запрошено:   {url}")
    print(f"Ответ:       {response.status_code}, после переходов: {response.url}")
    print(f"Страница:    размер {len(html) // 1024} КБ")
    print(
        f"Слова про капчу на странице: {'да' if any(m in text for m in CAPTCHA_MARKERS) else 'нет'}"
    )
    print("Что найдено:", {label: html.count(key) for key, label in HINTS.items()})
    attributes = Counter(re.findall(r'(data-[\w-]+)="', html))
    print("Самые частые атрибуты data-*:", dict(attributes.most_common(12)) or "нет")
    print(f"HTML сохранён в {OUTPUT.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
