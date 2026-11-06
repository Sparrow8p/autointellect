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
