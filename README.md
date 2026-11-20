# Авто-Интеллект

Платформа помогает автовладельцу решить, что выгоднее: ремонтировать машину после поломки
или продать её. Система оценивает ремонт, ищет запчасти, считает рыночную цену автомобиля
«как есть» и «после ремонта» и выдаёт рекомендацию с расчётами.

**Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL 16, JWT (PyJWT), Argon2 (pwdlib), pytest, ruff.

**Frontend:** React, TypeScript, Vite, React Router, Tailwind CSS. [Запуск и документация фронтенда](frontend/README.md).

> Все команды в этом README — для **bash на Windows (Git Bash)**: он устанавливается вместе с
> [Git for Windows](https://git-scm.com/download/win). Откройте проект и запускайте команды
> в окне *Git Bash* (правый клик в папке → *Open Git Bash here*). Также нужны
> [Python 3.12+](https://www.python.org/downloads/) (при установке отметьте *Add python.exe to PATH*)
> и [Docker Desktop](https://www.docker.com/products/docker-desktop/).

## Структура репозитория

```
backend/    FastAPI + PostgreSQL — API и база данных
frontend/   React + TypeScript — вход, главная и маршруты остальных экранов
.github/    CI (GitHub Actions)
```

Внутри `backend/`:

```
app/
  api/         роутеры (auth, users, cars, reference, calculations) и зависимости
  core/        настройки (env) и безопасность (хеширование, JWT)
  db/          Base, сессия, загрузка справочных данных (seed.py + seed_data/)
  models/      User, Car, Calculation, Work, WorkKeyword, Region, Brand, CarModel
  schemas/     Pydantic-схемы запросов/ответов
  services/    parsing.py (разбор текста проблемы), pricing.py (цена работы),
               estimate.py (расчёт диапазона)
tests/
```

## Быстрый старт (backend)

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt

cp .env.example .env                  # и подставить свой SECRET_KEY: openssl rand -hex 32
docker compose up -d db               # PostgreSQL на localhost:5432
uvicorn app.main:app --reload         # http://localhost:8000/docs
```

Команда `openssl rand -hex 32` печатает случайную строку. Выполните её отдельно, откройте `.env`
и вставьте результат вместо `replace-me-with-output-of-openssl-rand-hex-32` в строке
`SECRET_KEY=...` — этим ключом подписываются токены, держите его в секрете.

Окружение активно, пока в начале строки виден `(.venv)`. В новом окне терминала
`source .venv/Scripts/activate` нужно выполнить заново.

`requirements-dev.txt` уже включает `requirements.txt` (первой строкой `-r requirements.txt`),
поэтому одной команды `pip install -r requirements-dev.txt` достаточно.

> Если `python` открывает Microsoft Store или не находится, переустановите Python с python.org
> с галочкой *Add to PATH* или используйте `py -m venv .venv`.

### База данных

Таблицы (`users`, `cars`, `calculations`, `works`, `work_keywords`, `regions`, `brands`,
`car_models`) создаются **автоматически при запуске приложения** (если их ещё нет). Отдельных
команд не нужно.

**Справочные данные** при каждом запуске догружаются из файлов `backend/app/db/seed_data/`:
`works.csv` (база нормо-часов), `work_keywords.csv` (ключевые слова для разбора текста),
`regions.csv` (регионы и коэффициенты), `brands.json` (марки и модели). Загрузка только
**добавляет** недостающие строки и ничего не перезаписывает, поэтому значения, исправленные
прямо в базе (например, коэффициент региона), сохраняются. Чтобы добавить новую работу, слово,
регион или марку, допишите строку в нужный файл и перезапустите `uvicorn`.

> ⚠️ Коэффициенты регионов (`1.3` для Москвы и Московской области, `1.2` для Санкт-Петербурга,
> остальным `1.0`) и ставка нормо-часа (`LABOR_RATE_PER_HOUR`, 2000 ₽) — **заглушки**, пока нет
> реальных данных.

**Изменили модели** (добавили колонку, поменяли тип)? Уже существующие таблицы автоматически
не меняются. Пока в базе нет нужных данных, проще всего пересоздать её:

```bash
docker compose down -v        # удаляет контейнер БД вместе с данными (флаг -v)
docker compose up -d db
```

и перезапустить `uvicorn`. Когда в базе появятся данные, которые жалко терять, самое время
подключить миграции (Alembic) — это можно сделать отдельной задачей.

## Тесты и проверка кода

В папке `backend`, с активным окружением:

```bash
ruff check .
pytest -q
```

Тесты используют in-memory SQLite — Postgres и Docker для них не нужны. Это же запускает CI.
Автоформатирование: `ruff format .` (необязательно). Автоисправление простых замечаний
линтера: `ruff check --fix .`

## API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация: `{"email", "password", "phone"?}` → 201 + профиль. 409 — email/телефон заняты |
| POST | `/api/auth/login` | `{"email", "password"}` → `{"access_token", "token_type": "bearer"}`. 401 — неверные данные |
| GET | `/api/users/me` | Профиль по заголовку `Authorization: Bearer <token>`. 401 — токен отсутствует/невалиден/просрочен |
| GET | `/api/cars` | Список авто текущего пользователя (нужен токен) |
| POST | `/api/cars` | Сохранить авто: `{"brand", "model", "year", "mileage", "region"}` → 201. 422 — неизвестный регион или неверные значения |
| DELETE | `/api/cars/{id}` | Удалить своё авто → 204. 404 — нет такого авто или оно чужое |
| GET | `/api/reference/brands` | Список марок `[{"id", "name"}]` (токен не нужен) |
| GET | `/api/reference/models?brand=Hyundai` | Модели марки `[{"id", "name", "brand"}]`; без `brand` — все модели. 404 — неизвестная марка |
| GET | `/api/reference/regions` | Список регионов `[{"id", "name"}]` — из него выбирается `region` авто |
| POST | `/api/calculations/estimate` | Диапазон стоимости ремонта: `{"car_id", "problem_text"}` → `min_price`, `max_price` (₽), список работ. Ничего не сохраняет |
| POST | `/api/calculations/check-estimate` | Сверка сметы СТО с расчётом: `{"car_id", "problem_text", "sto_amount"}` → `verdict` («В диапазоне» / «Завышено» / «Занижено»), `verdict_code` (`in_range` / `overpriced` / `underpriced`), `difference` (₽ за границей диапазона), `min_price`, `max_price`, работы. Границы входят в диапазон. Ничего не сохраняет |
| POST | `/api/calculations/scenarios` | Цена после ремонта, 3 сценария и рекомендация: `{"car_id", "problem_text", "car_price", "years"?}`. Ничего не сохраняет |
| POST | `/api/calculations/price-after-repair` | Цена авто после ремонта: `{"car_price", "repair_cost"}` → цена после ремонта, рост в ₽ и %. Формула без базы |
| GET | `/api/history` | История расчётов пользователя (`limit`, `offset`), новые сверху |
| POST | `/api/history/save` | Сохранить расчёт: `{"car_id", "problem_text", "car_price"}` → 201. Считается заново на сервере |
| POST | `/api/service-records` | Запись журнала обслуживания: `{"car_id", "service_date", "mileage"?, "sto_name"?, "note"?, "works": [{"name", "price"}]}` → 201. Сумма (`total`) считается на сервере |
| GET | `/api/service-records?car_id=1` | Журнал авто, новые сверху (`limit` 1–100, `offset`) |
| GET | `/api/service-records/{id}` | Одна запись. 404 — нет такой или чужая |
| DELETE | `/api/service-records/{id}` | Удалить запись вместе с файлом чека → 204 |
| PUT | `/api/service-records/{id}/receipt` | Загрузить/заменить чек (форма, поле `file`; JPEG, PNG или PDF, до 5 МБ). 413 — большой файл, 415 — другой тип |
| GET | `/api/service-records/{id}/receipt` | Скачать чек. 404 — чека нет |
| GET | `/api/service-records/report?car_id=1` | PDF «История обслуживания» для покупателя. 404 — записей нет |
| GET | `/health` | Проверка живости сервиса |

Правила: пароль 8–128 символов; телефон необязателен, формат `+79991234567`; email приводится
к нижнему регистру; токен действует 60 минут (`ACCESS_TOKEN_EXPIRE_MINUTES`).

```bash
curl -X POST localhost:8000/api/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"dmitry@example.com","password":"correct-horse-battery"}'
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"dmitry@example.com","password":"correct-horse-battery"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl localhost:8000/api/users/me -H "Authorization: Bearer $TOKEN"
```

Пример расчёта (`problem_text` — свободный текст, `car_id` — id сохранённого авто):

```bash
curl -X POST localhost:8000/api/calculations/estimate -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"car_id": 1, "problem_text": "Стучит подвеска"}'
```

Ответ (авто в Московской области):

```json
{
  "recognized": true,
  "min_price": 16000,
  "max_price": 20600,
  "region_coefficient": 1.3,
  "matched_keywords": ["подвеск", "стуч"],
  "works": [
    {"id": 16, "name": "Замена стойки стабилизатора", "category": "Подвеска", "hours": 0.8, "min_price": 3580, "max_price": 4580},
    {"id": 17, "name": "Замена амортизатора (1 шт)", "category": "Подвеска", "hours": 1.5, "min_price": 7500, "max_price": 9900},
    {"id": 20, "name": "Замена шаровой опоры", "category": "Подвеска", "hours": 1.2, "min_price": 4920, "max_price": 6120}
  ]
}
```

Как считается: текст разбирается по ключевым словам из таблицы `work_keywords` (по основе слова:
«подвеск» найдёт «подвеска», «подвески»…; «стучит» указывает на конкретные детали подвески, а
не на всю подвеску целиком). Для каждой работы: `работа = часы × ставка × коэффициент региона`,
`min = работа + 60% цены запчасти` (б/у, аналог), `max = работа + 100%` (новая). Запчасти на
региональный коэффициент не умножаются. Итог — сумма по работам, в целых рублях. Если ничего
не распознано, `recognized` равно `false`, а в расчёте только «Компьютерная диагностика».
Отрицания («не стучит») и опечатки пока не учитываются.

### Сценарии и рекомендация

`POST /api/calculations/scenarios` принимает `car_id`, `problem_text`, **`car_price`** (текущая
цена авто, ₽, вводит пользователь) и необязательный `years` (1–3, по умолчанию 1):

```bash
curl -X POST localhost:8000/api/calculations/scenarios -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"car_id": 1, "problem_text": "Стучит подвеска", "car_price": 400000}'
```

Ответ (авто в регионе с коэффициентом 1.0):

```json
{
  "recognized": true,
  "matched_keywords": ["подвеск", "стуч"],
  "region_coefficient": 1.0,
  "works": [ "...как в /estimate..." ],
  "repair": {"min_price": 13900, "max_price": 18500, "repair_cost": 16200},
  "scenarios": {
    "sell_as_is": {"value": 400000, "recommended": false},
    "repair_and_sell": {"repair_cost": 16200, "price_after_repair": 470000,
                        "price_growth_percent": 17.5, "value": 453800, "recommended": true},
    "repair_and_keep": {"repair_cost": 16200, "running_costs": 32000, "years": 1,
                        "value": -48200, "recommended": false}
  },
  "profit": 53800,
  "recommendation": "Ремонт окупится. Выгода: 53 800 ₽"
}
```

Как считается (все суммы — целые рубли):

- **Стоимость ремонта** в сценариях — середина диапазона `min_price`…`max_price` (между б/у и
  новыми запчастями).
- **Цена после ремонта** = цена авто × (1 + рост). Рост зависит от доли ремонта в цене авто:
  ремонт до 30% цены — **+17,5%** (середина вилки 15–20%), от 50% — **+2%** («почти не растёт»),
  между 30% и 50% рост линейно падает с 17,5% до 2%. Пример из проектного документа: авто
  400 000 ₽, ремонт 50 000 ₽ → 470 000 ₽.
- **Сценарий 1** — продажа как есть: цена авто.
- **Сценарий 2** — ремонт и продажа: цена после ремонта − стоимость ремонта.
- **Сценарий 3** — ремонт и эксплуатация: −(стоимость ремонта + расходы на владение). Расходы =
  цена авто × 8% × `years` (`ANNUAL_RUNNING_COSTS_RATE`). Это **затраты**, а не сумма продажи,
  поэтому с сценарием 1 он не сравнивается.
- **Рекомендация:** если сценарий 2 больше сценария 1 — «Ремонт окупится. Выгода: … ₽» (выгода =
  сценарий 2 − сценарий 1), иначе — «Выгоднее продать как есть».

**Какой сценарий рекомендован** показывает поле `recommended` в каждом сценарии: у сценария 2
`true`, если ремонт окупится, иначе `true` у сценария 1. У сценария 3 оно всегда `false` (это
затраты, а не вариант продажи).

**Цена после ремонта отдельно:** `POST /api/calculations/price-after-repair` с телом
`{"car_price": 400000, "repair_cost": 50000}` возвращает `repair_share_percent` (12.5),
`price_growth_percent` (17.5), `price_growth` (70000) и `price_after_repair` (470000). Это та же
формула, но без базы и без текста проблемы: стоимость ремонта передаёт клиент (например, из
`/estimate`). В `/scenarios` эта цена приходит внутри ответа.

Из формулы следует, что ремонт окупается, только пока он дешевле роста цены (примерно до 17%
от цены авто); при более дорогом ремонте ответ будет «продать как есть».

### История расчётов

- `POST /api/history/save` — принимает `{"car_id", "problem_text", "car_price"}`, **пересчитывает
  расчёт на сервере** и сохраняет его в таблицу `calculations` → 201 и сохранённая запись. Готовые
  суммы от клиента не принимаются, чтобы нельзя было сохранить произвольные числа.
- `GET /api/history?limit=20&offset=0` — расчёты текущего пользователя, новые сверху (`limit`
  1–100). В каждой записи: `id`, `created_at`, `car` (`id`, `brand`, `model`, `year`),
  `problem_text`, `repair_min`, `repair_max`, `price_as_is`, `price_after_repair`,
  `recommendation`. Сценарий 3 в истории не хранится (для него нет колонок).

При удалении авто его расчёты из истории тоже удаляются (каскад на уровне базы).

### Журнал обслуживания и PDF

Пользователь записывает обращения в СТО: дата, пробег, название СТО и список работ с ценами (строки
чека). Итоговая сумма записи — это сумма цен работ, её считает сервер. Файл чека (JPEG, PNG или PDF,
до 5 МБ) загружается отдельным запросом `PUT /api/service-records/{id}/receipt`; тип определяется
по содержимому файла, а не по имени. Файлы лежат в папке `UPLOAD_DIR` (по умолчанию `backend/uploads`,
в git не попадает) под случайными именами. Это просто папка на диске: при удалении авто записи в базе
удаляются каскадом, а файлы чеков остаются на диске.

`GET /api/service-records/report?car_id=1` отдаёт PDF для покупателя: данные авто, записи по порядку
дат, суммы и пометка «Чек приложен» (сами чеки в PDF не вставляются). Email и другие данные владельца
в отчёт не попадают. PDF строится библиотекой `reportlab`; шрифт DejaVu лежит в
`backend/app/assets/fonts/` (в стандартных шрифтах PDF нет кириллицы).

Для загрузки файлов в `requirements.txt` добавлены `reportlab` и `python-multipart`: после обновления
выполните `pip install -r requirements-dev.txt` в `backend`.

В Swagger (`/docs`) то же самое проще: выполните `/api/auth/login`, нажмите **Authorize** и вставьте
`access_token`.

## Работа с git

Ветки:

- `main` — стабильная версия;
- `dev` — основная ветка разработки;
- `feature/название` — одна задача, создаётся от `dev` (`feature/auth`, `feature/cars-crud`).

Порядок: взяли задачу → создали ветку от `dev` → сделали → `git push` → открыли
Pull Request (PR) на GitHub в `dev` → дождались зелёной галочки CI → влили. В `main` вливаем `dev`, когда всё работает.

Новая задача:

```bash
git switch dev && git pull
git switch -c feature/cars-crud
```

## CI

`.github/workflows/ci.yml` — автоматическая проверка кода на GitHub. Запускается на push в
`main`, `dev`, `feature/**` и на каждый PR в `main`/`dev`: ставит зависимости, запускает
`ruff check` и `pytest`. Результат — зелёная галочка или красный крестик возле коммита или PR.
Если красный — нажмите *Details* и посмотрите, какая проверка упала (то же самое можно
повторить у себя командами из раздела «Тесты и проверка кода»).
