# Module Boundaries

## Backend

### Канонический шаблон модуля

Каждый доменный модуль в `apps/backend/app/modules/<name>/` имеет ровно пять файлов:

```
<name>/
├── __init__.py     # re-export моделей и схем (опционально)
├── models.py       # SQLAlchemy ORM-модели
├── schemas.py      # Pydantic-схемы (request/response)
├── repository.py   # Только SQLAlchemy-запросы
├── service.py      # Use-case логика
└── router.py       # Тонкий: request → service → response
```

Минимум для обязательных модулей: `catalog`, `users`, `favorites`, `orders`, `promos`, `support`, `settings`, `notifications`, `admin`, `admin_api`.

### Что где живёт

| Слой | Что может содержать | Что запрещено |
|------|---------------------|---------------|
| `core/` | config, database engine, security (initData, JWT), exceptions, redis_client | доменная логика |
| `modules/<name>/models.py` | `class X(Base): __tablename__ = ...` | методы с бизнес-логикой, расчёты |
| `modules/<name>/schemas.py` | `class XIn(BaseModel)`, `class XOut(BaseModel)` | обращения к БД, SQL |
| `modules/<name>/repository.py` | `class XRepository` с методами, делающими `select`, `update`, `delete`, `db.add` | HTTP-вызовы, расчёты, бизнес-правила |
| `modules/<name>/service.py` | `class XService` с методами-use-case, вызывающими repository и integrations | `select` напрямую (только через repository), HTTP к внутренним сервисам |
| `modules/<name>/router.py` | `APIRouter`, `Depends`, парсинг, вызов service, формирование response | SQL, `db.add/commit`, бизнес-логика, HTTP-вызовы |

### Исключения и нюансы

- **auth.py** (корневой `app/auth.py`) — допустимо иметь `Depends(get_current_user)` и `Depends(get_current_admin)`, которые делают SQL для резолва Telegram-initData/JWT. Но бизнес-логика `get_or_create` должна быть в `users/service.py`.
- **admin_api** — на верхнем уровне имеет `deps.py` (re-export admin-dep) и `filters.py` (общие pagination/sort/search хелперы). Подмодули (`admin_api/products/`, `admin_api/orders/` и т.д.) следуют каноническому шаблону.
- **internal_api** — особый модуль. Не подчиняется общему шаблону (нет models/repository). Содержит: `deps.py` (verify_internal_secret), `schemas.py`, `router.py` (агрегатор), `telegram.py`, `support.py`, `notifications.py`, `bot_delivery.py`.
- **admin** (модели `Admin`, `AdminLog`, `LinkDeliveryLog`, `GoogleDriveToken`, `Setting`) — содержит models и schemas, но router/service/repository не нужны (используется только через admin_api).

### Forbidden patterns

- ❌ `select(...)`, `db.add(...)`, `db.commit()` в `router.py` любого модуля.
- ❌ Бизнес-логика (расчёты, валидации, формирование payload) в `repository.py`.
- ❌ HTTP-вызовы к внешним API в `router.py` или `repository.py`.
- ❌ Прямой доступ к `engine` или `Session` из bot.
- ❌ Импорт `from app.models` в новом коде (только для Alembic).
- ❌ `try: import Service; ... except ImportError: raise HTTPException(501)` — заглушки, маскирующие отсутствующую реализацию.

## Bot

### Что бот делает

```
Telegram update
  → handler (парсинг event)
  → api_client.<method>(...)        # HTTP к backend internal API
  → bot.send_message / send_photo   # транспорт
```

### Что бот НЕ делает

- ❌ Прямой доступ к PostgreSQL/Redis.
- ❌ Расчёт скидок / цены / валидация заказов.
- ❌ Изменение статусов `order`, `payment`, `support_ticket`.
- ❌ Формирование текста доставки со ссылками Google Drive.
- ❌ Создание таблиц в БД.

### Структура

```
apps/bot/
├── main.py           # Dispatcher, startup/shutdown, init http_client
├── config.py         # BOT_TOKEN, INTERNAL_API_URL, INTERNAL_API_SECRET
├── http_client.py    # class InternalAPIClient с методами для каждого endpoint
├── handlers/         # router per concern
│   ├── start.py            # /start, /terms, /support, /paysupport
│   ├── pre_checkout.py     # @router.pre_checkout_query()
│   ├── successful_payment.py
│   └── admin_reply.py      # @router.message(F.reply_to_message)
└── workers/          # фоновые polling-задачи
    ├── ticket_notifications.py
    └── notification_dispatch.py
```

### Forbidden imports в bot

```python
# ❌ ЗАПРЕЩЕНО
import asyncpg
from sqlalchemy import select
import redis.asyncio as redis

# ✅ Разрешено
import httpx
from aiogram import Bot, Dispatcher, Router
```

## Frontend Mini App (FSD)

### Layer rules

| Layer | May import from |
|-------|-----------------|
| app | any layer |
| pages | widgets, features, entities, shared |
| widgets | features, entities, shared |
| features | entities, shared |
| entities | shared |
| shared | nothing below it |

### Forbidden patterns

- Entities importing from features/pages.
- Shared importing from business layers.
- Business logic in pages/screens.
- Прямые HTTP-вызовы к internal API (только через backend public API).

## Frontend Admin

- Использует только `react-admin` data provider → public API backend.
- Никаких прямых вызовов internal API.
- Никакой бизнес-логики в resources.

## Проверка границ

Перед коммитом:

```bash
# 0 SQL в bot
grep -R "asyncpg\|select\|db\." apps/bot/ --include="*.py"  # должно быть пусто

# SQL только в repository.py и Alembic
grep -R "select\|db\.add\|db\.commit" apps/backend/app/modules/ --include="*.py" \
  | grep -v "repository.py\|alembic/"

# Каждый модуль имеет полный набор файлов
for m in catalog users favorites orders promos support settings notifications admin admin_api; do
  for f in models.py schemas.py repository.py service.py router.py; do
    [ -f "apps/backend/app/modules/$m/$f" ] || echo "MISSING: $m/$f"
  done
done
```
