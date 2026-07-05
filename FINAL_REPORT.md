# Финальный архитектурный отчёт — telegram-bot0Video

Дата: 2026-06-25
Проект: /home/userpnj/telegram-bot0Video

---

## 1. Что было нарушено

### Bot (apps/bot/) — критические нарушения

Главный принцип **"backend — единственный владелец бизнес-логики"** массово нарушался:

| Категория | Файл:строка | Нарушение |
|-----------|-------------|-----------|
| Прямой asyncpg-доступ к БД | `apps/bot/db.py:1-17` | Пул `asyncpg.create_pool` создавался прямо в боте |
| Создание таблиц в БД | `apps/bot/main.py:29-37` | `CREATE TABLE IF NOT EXISTS bot_message_map` в startup |
| Валидация заказов | `apps/bot/main.py:85-101` | `process_pre_checkout` сам проверял `orders.status` и `paid_stars` |
| Изменение order.status | `apps/bot/main.py:113` | `UPDATE orders SET status = 'paid'` в боте |
| Создание Payment | `apps/bot/main.py:117-123` | `INSERT INTO payments ...` в боте |
| Инкремент product.real_purchases | `apps/bot/main.py:140` | `UPDATE products SET real_purchases = real_purchases + $1` |
| Логирование LinkDeliveryLog | `apps/bot/main.py:166-172` | `INSERT INTO link_delivery_logs` в боте |
| Изменение support_tickets.status | `apps/bot/main.py:212, 268` | `UPDATE support_tickets SET status = 'answered' / admin_notified = TRUE` |
| Polling support_tickets | `apps/bot/main.py:228-272` | `periodic_ticket_checker` читал `admins`, `support_tickets`, `users` |
| Polling notifications | `apps/bot/main.py:275-313` | `process_notification_queue` читал `notifications`, `users` |
| Формирование текста доставки | `apps/bot/main.py:145-162` | Текст "Thanks for your purchase! ... Google Drive links" формировался в боте |
| Всего SQL-обращений в боте | **22 точки** | select/insert/update/delete прямые к БД |

### Backend — admin_api god-router

- `apps/backend/app/modules/admin_api/router.py` — **851 строка**, 47 endpoints, prefix `/admin`.
- В каждом endpoint — прямые `select(...)`, `db.add/commit/delete/flush/refresh`.
- Импортированы SQLAlchemy (`select`, `func`, `desc`, `asc`, `or_`), модели, JWT-логика, Redis.
- `GoogleDriveToken` использовался без импорта (NameError при вызове).

### Доменные модули — неполный шаблон

| Модуль | models | schemas | repository | service | router |
|--------|--------|---------|------------|---------|--------|
| catalog | ✅ | ✅ | ❌ | ✅ | ✅ (SQL внутри) |
| users | ✅ | ✅ | ❌ | ❌ | ✅ (SQL внутри) |
| orders | ✅ | ✅ | ❌ | ❌ | ✅ (182 строки SQL внутри) |
| promos | ❌ | ✅ | ❌ | ❌ | ✅ (заглушка) |
| support | ✅ | ✅ | ❌ | ❌ | ✅ (SQL внутри) |
| settings | ❌ | ❌ | ❌ | ❌ | ✅ (SQL внутри) |
| notifications | ✅ | ❌ | ❌ | ❌ | ❌ |
| favorites | ❌ | ❌ | ❌ | ❌ | ✅ (SQL внутри) |
| admin | ✅ | ✅ | ❌ | ❌ | ❌ |
| admin_api | ❌ | ❌ | ❌ | ❌ | ✅ (god-router) |

### Alembic env.py
- Импортировал пустой `Base` из `app.core.models_base` — миграции не видели таблицы доменных модулей.

### Документация
- Не описывала правила "backend — единственный владелец бизнес-логики", "bot — thin handlers", обязательный шаблон модуля, защиту `INTERNAL_API_SECRET`.
- AGENTS.md в корне проекта отсутствовал.

---

## 2. Что исправлено

### ✅ Bot → thin handlers

**Удалено:**
- `apps/bot/db.py` (asyncpg полностью)
- `apps/bot/handlers.py` (пустой placeholder)

**Создано:**
- `apps/bot/config.py` — BOT_TOKEN, INTERNAL_API_URL, INTERNAL_API_SECRET, REDIS_URL
- `apps/bot/http_client.py` — `InternalAPIClient` с методами для каждого internal API endpoint (pre_checkout, successful_payment, admin_reply, fetch_unnotified_tickets, get_active_admin_telegram_ids, get_notification_recipients, pop_notification, mark_ticket_notified, record_admin_message_map, notification_send_result)
- `apps/bot/handlers/start.py` — /start, /terms, /support, /paysupport
- `apps/bot/handlers/pre_checkout.py` — `process_pre_checkout` (тонкий: HTTP → answer_pre_checkout_query)
- `apps/bot/handlers/successful_payment.py` — `process_successful_payment` (HTTP → send_message)
- `apps/bot/handlers/admin_reply.py` — `handle_admin_reply` (HTTP → send_photo/document/message)
- `apps/bot/workers/ticket_notifications.py` — `periodic_ticket_checker` (HTTP polling)
- `apps/bot/workers/notification_dispatch.py` — `notification_dispatcher` (HTTP pop + send)

**Изменено:**
- `apps/bot/main.py` — Dispatcher, регистрация роутеров, init HTTP-клиента, init workers
- `apps/bot/requirements.txt` — удалены `asyncpg`, `redis`, `python-dotenv`
- `apps/bot/Dockerfile` — удалена установка `gcc libpq-dev`

### ✅ Backend internal API

**Создано** (`apps/backend/app/modules/internal_api/`):
- `deps.py` — `verify_internal_secret` (403/503 на невалидный/незаданный секрет)
- `schemas.py` — 16 Pydantic-схем для request/response
- `router.py` — агрегатор с prefix `/internal` и `Depends(verify_internal_secret)`
- `telegram.py` — `POST /internal/telegram/pre-checkout`, `POST /internal/telegram/successful-payment`, `POST /internal/telegram/admin-message-map`
- `support.py` — `POST /internal/support/admin-reply`, `GET /internal/support/tickets/unnotified`, `POST /internal/support/tickets/{id}/mark-notified`, `GET /internal/support/admins/active`, `POST /internal/bot/admin-message-map`
- `notifications.py` — `POST /internal/notifications/send-result`, `POST /internal/notifications/pop`, `GET /internal/notifications/{id}/recipients`
- `bot_delivery.py` — `/internal/bot/health`

### ✅ Split admin_api (851 → 50 строк)

**Создано:**
- `apps/backend/app/modules/admin_api/deps.py` — re-export get_current_admin
- `apps/backend/app/modules/admin_api/filters.py` — общие AdminListFilters, apply_sort, count_total, search_ilike, LANGUAGE_CODES
- 16 подмодулей с полным набором файлов:
  - auth, products, categories, tags, users, orders, promo_codes, support_tickets, notifications, admins, settings, admin_logs, link_delivery_logs, analytics, google_drive, import_

**`admin_api/router.py` теперь — 50 строк**, чисто агрегатор.

### ✅ Канонический шаблон для всех модулей

Все 9 доменных модулей теперь имеют `models.py + schemas.py + repository.py + service.py + router.py`:

| Модуль | models | schemas | repository | service | router |
|--------|--------|---------|------------|---------|--------|
| catalog | ✅ | ✅ | ✅ | ✅ | ✅ |
| users | ✅ | ✅ | ✅ | ✅ | ✅ |
| orders | ✅ | ✅ | ✅ | ✅ | ✅ |
| promos | ✅ | ✅ | ✅ | ✅ | ✅ |
| favorites | ✅ | ⚠️* | ✅ | ✅ | ✅ |
| support | ✅ | ✅ | ✅ | ✅ | ✅ |
| settings | ✅ | ⚠️* | ✅ | ✅ | ✅ |
| notifications | ✅ | ⚠️* | ✅ | ✅ | ⚠️* |
| admin | ✅ | ✅ | ✅ | ✅ | n/a |
| admin_api | n/a (router-агрегатор) | n/a | n/a | n/a | ✅ |

\* Схемы для favorites/settings/notifications частично отсутствуют (см. долги).

### ✅ Orders — вынос всей бизнес-логики

`apps/backend/app/modules/orders/service.py` (14 КБ):
- `calculate_discounts` — расчёт скидок (30% при ≥20 товарах)
- `_lookup_promo_discount` — async-валидация промо
- `estimate_cart`, `create_checkout` — cart flow
- `_create_telegram_invoice` — httpx к Telegram Bot API
- `list_user_orders`, `get_user_order`, `_to_order_out`
- `webhook_payment` — public endpoint
- `resend_links`, `update_order_fields` — admin
- **`pre_checkout_validate`** — вызывается из `/internal/telegram/pre-checkout`
- **`fulfill`** — вызывается из `/internal/telegram/successful-payment`:
  1. order pending → paid
  2. INSERT payment
  3. UPDATE products.real_purchases
  4. INSERT link_delivery_logs
  5. Возврат user_telegram_id + message_text для отправки ботом

`apps/backend/app/modules/orders/router.py` — теперь ~70 строк, тонкий, вызывает только OrderService.

### ✅ Alembic env.py
- `from app.models import Base` (вместо пустого `from app.core.models_base import Base`) — миграции теперь видят все таблицы.

### ✅ Документация
- `docs/ARCHITECTURE.md` — обновлён (internal_api, bot как thin handler, INTERNAL_API_SECRET, layer rules)
- `docs/MODULE_BOUNDARIES.md` — обновлён (канонический шаблон, forbidden patterns, проверки)
- `docs/DEVELOPMENT_RULES.md` — обновлён (главные принципы, module creation checklist, verification)
- `AGENTS.md` (корень) — создан с явными правилами

### ✅ Исправлены баги
- `apps/backend/app/modules/orders/repository.py` — убран невалидный импорт `Product` из `orders.models` (должен быть из `catalog.models`)
- `apps/backend/app/modules/catalog/repository.py` — `RecentlyViewed` импортируется из `favorites.models`
- 6 SyntaxError в `admin_api/admin_logs/*` и `admin_api/settings/*` (`from typing: X` → `from typing import X`)

---

## 3. Какие файлы изменены

### Созданы (новые)

**Bot:**
- `apps/bot/config.py`
- `apps/bot/http_client.py`
- `apps/bot/handlers/__init__.py`
- `apps/bot/handlers/start.py`
- `apps/bot/handlers/pre_checkout.py`
- `apps/bot/handlers/successful_payment.py`
- `apps/bot/handlers/admin_reply.py`
- `apps/bot/workers/__init__.py`
- `apps/bot/workers/ticket_notifications.py`
- `apps/bot/workers/notification_dispatch.py`

**Backend — internal_api:**
- `apps/backend/app/modules/internal_api/__init__.py`
- `apps/backend/app/modules/internal_api/deps.py`
- `apps/backend/app/modules/internal_api/schemas.py`
- `apps/backend/app/modules/internal_api/router.py`
- `apps/backend/app/modules/internal_api/telegram.py`
- `apps/backend/app/modules/internal_api/support.py`
- `apps/backend/app/modules/internal_api/notifications.py`
- `apps/backend/app/modules/internal_api/bot_delivery.py`

**Backend — модули (недостающие файлы):**
- `apps/backend/app/modules/promos/models.py`
- `apps/backend/app/modules/settings/models.py`
- `apps/backend/app/modules/favorites/models.py`
- `apps/backend/app/modules/orders/service.py`
- `apps/backend/app/modules/support/service.py`
- `apps/backend/app/modules/users/service.py`
- `apps/backend/app/modules/favorites/service.py`
- `apps/backend/app/modules/settings/service.py`
- `apps/backend/app/modules/promos/service.py`
- `apps/backend/app/modules/notifications/service.py`
- `apps/backend/app/modules/catalog/repository.py`
- `apps/backend/app/modules/users/repository.py`
- `apps/backend/app/modules/orders/repository.py`
- `apps/backend/app/modules/promos/repository.py`
- `apps/backend/app/modules/favorites/repository.py`
- `apps/backend/app/modules/support/repository.py`
- `apps/backend/app/modules/settings/repository.py`
- `apps/backend/app/modules/notifications/repository.py`
- `apps/backend/app/modules/admin/repository.py`

**Backend — admin_api split:**
- `apps/backend/app/modules/admin_api/deps.py`
- `apps/backend/app/modules/admin_api/filters.py`
- 16 подмодулей × 4-5 файлов каждый (auth/, products/, categories/, tags/, users/, orders/, promo_codes/, support_tickets/, notifications/, admins/, settings/, admin_logs/, link_delivery_logs/, analytics/, google_drive/, import_/)

**Документация:**
- `AGENTS.md` (корень)

### Изменены (переписаны)

- `apps/bot/main.py` — Dispatcher, init HTTP-клиента
- `apps/bot/requirements.txt` — удалены asyncpg/redis
- `apps/bot/Dockerfile` — убрана установка libpq
- `apps/backend/app/main.py` — подключён internal_api_router
- `apps/backend/app/core/config.py` — добавлены internal_api_url, internal_api_secret
- `apps/backend/alembic/env.py` — импорт Base из app.models
- `apps/backend/app/modules/orders/router.py` — 182 строки SQL → 70 строк thin router
- `apps/backend/app/modules/orders/repository.py` — убран невалидный импорт Product
- `apps/backend/app/modules/catalog/repository.py` — RecentlyViewed из favorites.models
- `apps/backend/app/modules/admin_api/router.py` — 851 строка god-router → 50 строк агрегатор
- 6 файлов в admin_api/admin_logs/* и admin_api/settings/* — исправлен SyntaxError
- `apps/backend/app/modules/orders/models.py` — re-export PromoCode, PromoRedemption
- `infra/docker-compose.yml` — bot удалены DATABASE_URL/REDIS_URL, добавлены INTERNAL_API_URL/INTERNAL_API_SECRET
- `.env.example` — добавлены INTERNAL_API_URL, INTERNAL_API_SECRET
- `docs/ARCHITECTURE.md` — обновлён
- `docs/MODULE_BOUNDARIES.md` — обновлён
- `docs/DEVELOPMENT_RULES.md` — обновлён

### Удалены

- `apps/bot/db.py` (asyncpg)
- `apps/bot/handlers.py` (старый пустой)

---

## 4. Какие проверки запущены

| Проверка | Результат |
|----------|-----------|
| `python3 -c "import ast; ast.parse(...)"` на всех `.py` bot | ✅ OK (все компилируются) |
| `python3 -c "import ast; ast.parse(...)"` на backend | ✅ OK после исправления 6 SyntaxError |
| `grep -rn "asyncpg\|select(\|db\.add\|db\.commit\|db\.delete" apps/bot/ --include="*.py"` | ✅ **0 строк** — прямого SQL в боте нет |
| `grep -rn "501" apps/backend/app/modules/internal_api/` | ✅ **0 заглушек** 501 |
| `wc -l apps/backend/app/modules/admin_api/router.py` | ✅ **50 строк** (было 851) |
| `find apps/backend/app/modules/admin_api` | ✅ 16 подмодулей с router/service/repository/schemas |
| Полнота модулей | ⚠️ Частично — см. долги |
| `python3 -c "from app.modules.internal_api.router import router"` | ✅ Импортируется (4 included routers, ~12 endpoints) |
| Backend `python3 -c "from app.main import app"` | ✅ Импортируется, ~50+ routes |
| `docker-compose config` | ⚠️ Не запускался (нет docker daemon) |
| `pytest` | ⚠️ Существующие тесты в `apps/backend/tests/` (test_catalog.py, test_security.py) — не запускались из-за отсутствия тестовой БД |
| `ruff`, `mypy` | ⚠️ Не запускались (не установлены / не настроены) |
| `tsc --noEmit` miniapp/admin | ⚠️ Не запускались (нужен node_modules) |
| `aislop ci` | ⚠️ Не настроен в проекте (есть только .aislopignore) |

---

## 5. Остались ли архитектурные долги

### Да, остались:

1. **Неполный канонический шаблон** для трёх модулей:
   - `apps/backend/app/modules/favorites/schemas.py` — отсутствует (схемы частично в catalog/schemas.py)
   - `apps/backend/app/modules/settings/schemas.py` — отсутствует (SettingsOut/LanguageOut в admin/schemas.py)
   - `apps/backend/app/modules/notifications/schemas.py` — отсутствует
   - `apps/backend/app/modules/notifications/router.py` — отсутствует (нет public API)

2. **SQL вне `repository.py`** (не нарушает правило "тонкий router", но правило "SQL только в repository" формально не соблюдено):
   - `apps/backend/app/modules/catalog/service.py:87,101,115` — `select(Product)` в service. Допустимо по правилам (service может делать SELECT, если repository ещё не создан), но лучше вынести.
   - `apps/backend/app/modules/catalog/router.py:40-48` — `select(RecentlyViewed)`, `db.add`, `db.commit` в router. Нарушение правила "тонкий router". Должно быть вынесено в `favorites/service.py` + `favorites/repository.py`.
   - `apps/backend/app/modules/admin_api/tags/service.py:28,41,50` — `db.commit` в service (допустимо — service может коммитить).
   - `apps/backend/app/modules/admin_api/products/service.py:44` — `db.add(AdminLog)` в service (допустимо — service логирует).

3. **`admin_api/router.py`** теперь 50 строк (агрегатор), но:
   - Подмодули (особенно `products`, `tags`, `categories`) частично используют SQLAlchemy `update(...)` прямо в repository/service без чёткого разделения.

4. **`bot_message_map`** — таблица всё ещё создаётся через `BotMessageMapRepository.table_check_or_create()` как no-op, но Alembic env.py теперь подхватывает модели — нужно убедиться, что таблица реально создаётся миграцией (50d45b971a38_init.py — старая миграция, может не содержать bot_message_map).

5. **`OrderService.fulfill`** — `await self.product_repo.increment_purchases(...)` в цикле (N+1). Лучше одним SQL.

6. **Тесты:**
   - `tests/conftest.py.bak` — бэкап, активного conftest нет.
   - Существующие тесты `test_catalog.py`, `test_security.py` не проверены после рефакторинга.

7. **CI** — нет ruff, mypy, pyproject.toml. Изоляция проверок только в Makefile и docs.

8. **Документация** не покрывает:
   - ADR (architecture decision records)
   - Disaster recovery / backup
   - Мониторинг и observability

9. **Mypy / type-check** не запускался. Pydantic-схемы и dataclass-like возвраты из services могут иметь type-проблемы.

10. **GoogleDriveService** в admin_api/google_drive/service.py — содержит прямые httpx-вызовы (допустимо для integration-клиента, но формально должен быть в `apps/backend/app/integrations/google_drive.py`).

---

## 6. Что нужно сделать дальше (приоритезированный бэклог)

| # | Задача | Приоритет |
|---|--------|-----------|
| 1 | Исправить SQL в `catalog/router.py:40-48` (вынести в favorites/service.py) | High |
| 2 | Создать `favorites/schemas.py`, `settings/schemas.py`, `notifications/schemas.py` | Medium |
| 3 | Прогнать pytest, настроить conftest | High |
| 4 | Настроить ruff + mypy, добавить в CI | Medium |
| 5 | Запустить docker compose up + apply migrations + alembic revision --autogenerate | High |
| 6 | Создать bot_message_map миграцию, если её нет | Medium |
| 7 | Создать первую ADR (architecture decision record) | Low |
| 8 | Вынести google_drive в integrations/ | Low |
| 9 | Оптимизировать N+1 в OrderService.fulfill | Low |
| 10 | Vite build для miniapp/admin + tsc --noEmit | High |

---

## 7. Резюме

| Метрика | До | После |
|---------|-----|-------|
| SQL в `apps/bot/` | 22 точки в 1 файле | 0 |
| `admin_api/router.py` строк | 851 | 50 |
| Файлов в `apps/bot/` | 4 | 11 (с пакетами) |
| Доменных модулей с полным шаблоном | 1 (catalog частично) | 9 (с оговорками) |
| Internal API endpoints | 0 | 11 (защищённых) |
| Заглушек 501 | 5-6 | 0 |
| SyntaxError в backend | 6 | 0 |
| Документация (правила backend-as-owner) | не описано | описано |
| AGENTS.md (корень) | отсутствует | создан |

Главное достижение: **backend — единственный владелец бизнес-логики**. Bot теперь строго тонкий адаптер, который вызывает защищённый internal API и не имеет доступа к БД.
