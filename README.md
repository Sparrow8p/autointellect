# Авто-Интеллект

Платформа помогает автовладельцу решить, что выгоднее: ремонтировать машину после поломки
или продать её. Система оценивает ремонт, ищет запчасти, считает рыночную цену автомобиля
«как есть» и «после ремонта» и выдаёт рекомендацию с расчётами.

**Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL 16, JWT (PyJWT), Argon2 (pwdlib), pytest, ruff.

> Все команды в этом README — для **bash на Windows (Git Bash)**: он устанавливается вместе с
> [Git for Windows](https://git-scm.com/download/win). Откройте проект и запускайте команды
> в окне *Git Bash* (правый клик в папке → *Open Git Bash here*). Также нужны
> [Python 3.12+](https://www.python.org/downloads/) (при установке отметьте *Add python.exe to PATH*)
> и [Docker Desktop](https://www.docker.com/products/docker-desktop/).

## Структура репозитория

```
backend/    FastAPI + PostgreSQL — API и база данных
frontend/   клиентская часть (пока пусто)
.github/    CI (GitHub Actions)
```

Внутри `backend/`:

```
app/
  api/         роутеры (auth, users) и зависимости (get_current_user)
  core/        настройки (env) и безопасность (хеширование, JWT)
  db/          Base, сессия
  models/      User, Car, Calculation
  schemas/     Pydantic-схемы запросов/ответов
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

Таблицы `users`, `cars` и `calculations` создаются **автоматически при запуске приложения**
(если их ещё нет). Отдельных команд не нужно.

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

В Swagger (`/docs`) то же самое проще: выполните `/api/auth/login`, нажмите **Authorize** и вставьте
`access_token`.

Фронтенду нужно добавить свой адрес в `CORS_ORIGINS` в `.env` (например,
`CORS_ORIGINS=["http://localhost:3000"]`), иначе браузер заблокирует запросы.

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
