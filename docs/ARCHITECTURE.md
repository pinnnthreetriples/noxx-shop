# Architecture

## Overview

Monorepo + modular monolith. Главный принцип: **backend — единственный владелец бизнес-логики и единственный, кто работает с БД**. Bot — тонкий адаптер над Telegram Bot API.

- **Backend:** FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + Redis 7 + Alembic
- **Bot:** aiogram 3 (thin handler, вызывает backend internal API)
- **Mini App:** React 18 + Vite + TypeScript (feature-sliced structure)
- **Admin:** React + react-admin + Material UI

## High-level flow

```
Telegram → bot handler (только транспорт)
        → backend internal API (INTERNAL_API_SECRET)
        → backend service (use-case)
        → backend repository (SQLAlchemy)
        → PostgreSQL / Redis
        → ответ в обратном направлении
```

Bot **никогда** не работает с БД напрямую, **никогда** не принимает бизнес-решений, **никогда** не формирует payload для пользователя без явного одобрения backend.

## Backend Modules

Все доменные модули находятся в `apps/backend/app/modules/`. Каждый модуль реализует единый шаблон:

```
modules/<name>/
├── models.py       # SQLAlchemy ORM-модели
├── schemas.py      # Pydantic-схемы (request/response)
├── repository.py   # Только SQLAlchemy-запросы
├── service.py      # Use-case логика
└── router.py       # Тонкий: request → service → response
```

### Доменные модули

| Module | Responsibility |
|--------|---------------|
| `catalog` | products, categories, tags, translations, search, filtering |
| `users` | Telegram auth (initData), profiles, language, notifications, age confirmation |
| `orders` | cart estimate, checkout, order list, payment webhook, fulfillment |
| `promos` | promo codes, validation, usage tracking |
| `favorites` | user favorites, recently viewed |
| `support` | tickets, messages, admin replies |
| `settings` | global settings, language list |
| `notifications` | broadcast queue via Redis, recipient tracking |
| `admin` | Admin, AdminLog, LinkDeliveryLog, GoogleDriveToken (модели, живут здесь) |
| `admin_api` | CRUD endpoints для react-admin (только для админки) |
| `internal_api` | защищённые endpoints для bot (см. ниже) |
| `core` | config, database, security, exceptions, redis_client |

### internal_api

`apps/backend/app/modules/internal_api/` — отдельный модуль, **НЕ admin_api**. Это мост между bot'ом и backend'ом.

Все endpoints защищены заголовком `X-Internal-Secret`, значение проверяется через `app.core.config.settings.internal_api_secret` (env `INTERNAL_API_SECRET`). Зависимость `verify_internal_secret` подключается на уровне роутера — если секрет невалиден, endpoint возвращает 403.

Endpoints:

| Method | Path | Назначение |
|--------|------|-----------|
| `POST` | `/internal/telegram/pre-checkout` | Валидация заказа перед оплатой Telegram Stars |
| `POST` | `/internal/telegram/successful-payment` | Фулфилл заказа: paid → payment → delivery log → сообщение для пользователя |
| `POST` | `/internal/support/admin-reply` | Обработка ответа админа на тикет (resolve admin, ticket, message, status) |
| `POST` | `/internal/support/tickets/{id}/mark-notified` | Пометить тикет как уведомлённый |
| `GET`  | `/internal/support/tickets/unnotified` | Список тикетов, ожидающих уведомления админов |
| `GET`  | `/internal/support/admins/active` | Список telegram_id активных админов |
| `POST` | `/internal/bot/admin-message-map` | Сохранить маппинг admin_message_id → ticket_id |
| `POST` | `/internal/notifications/send-result` | Зафиксировать результат отправки уведомления пользователю |
| `POST` | `/internal/notifications/pop` | Достать следующее задание из Redis-очереди |
| `GET`  | `/internal/notifications/{id}/recipients` | Список telegram_id получателей рассылки |

Все схемы request/response — в `apps/backend/app/modules/internal_api/schemas.py`.

## Integrations

Внешние HTTP-клиенты живут в `apps/backend/app/integrations/` (планируется) или в соответствующем service-модуле:

| Integration | External API | Где используется |
|-------------|--------------|------------------|
| Telegram Bot API (createInvoiceLink) | api.telegram.org | `orders/service.py` |
| Google Drive API (OAuth, files) | googleapis.com | `admin_api/google_drive/service.py` |
| Redis (notifications:queue) | redis | `notifications/service.py`, `internal_api/notifications.py` |

## Frontend Architecture

### Mini App

Based on Feature-Sliced Design (FSD):

- `app/` — entry points, providers (query client, router, i18n), styles
- `shared/` — reusable UI primitives, API client, types, utilities
- `entities/` — domain entities (product, user, order, promo)
- `features/` — self-contained business features (cart, favorites, checkout, support, language)
- `pages/` — top-level screens (Home, Catalog, Product, Cart, Profile...)
- `widgets/` — complex reusable UI blocks (BottomNav, ProductList)

### Admin

- `app/` — entry point, providers
- `resources/` — react-admin resource pages
- `shared/` — reusable utilities and types

## Layer Rules (Backend)

| Слой | Может содержать | Запрещено |
|------|----------------|-----------|
| `router.py` | FastAPI Depends, парсинг request, вызов service, формирование response | SQLAlchemy-запросы, `db.add/commit/delete`, бизнес-логика, прямые HTTP-вызовы |
| `service.py` | use-case логика, вызов repository, оркестрация, расчёты, формирование payload | `select`, `db.add`, прямые HTTP-вызовы (должны быть в integration) |
| `repository.py` | `select`, `update`, `delete`, `db.add/commit/flush` | бизнес-логика, расчёты, HTTP-вызовы |
| `models.py` | SQLAlchemy ORM-модели | бизнес-логика |
| `schemas.py` | Pydantic DTO | SQLAlchemy, бизнес-логика |

## Bot Architecture

```
apps/bot/
├── main.py           # Dispatcher, регистрация роутеров, init HTTP-клиента
├── config.py         # BOT_TOKEN, INTERNAL_API_URL, INTERNAL_API_SECRET
├── http_client.py    # InternalAPIClient — тонкая обёртка над httpx
├── handlers/         # Только: получить event → вызвать API → отправить ответ
│   ├── start.py
│   ├── pre_checkout.py
│   ├── successful_payment.py
│   └── admin_reply.py
└── workers/          # Фоновые задачи, читают backend через HTTP
    ├── ticket_notifications.py
    └── notification_dispatch.py
```

### Что бот ДЕЛАЕТ
- Принимает Telegram update.
- Парсит `successful_payment`, `PreCheckoutQuery`, `Message`.
- Вызывает `api_client.<method>(...)` для всех бизнес-операций.
- Отправляет пользователю/админу готовый текст или файл.
- Периодически polling'ит backend (тикеты, уведомления) через HTTP.

### Что бот НЕ ДЕЛАЕТ
- ❌ Прямой доступ к БД (asyncpg удалён).
- ❌ Расчёт скидок, валидация заказов, формирование delivery-сообщений.
- ❌ Изменение `order.status`, `payment.status`, `product.real_purchases`.
- ❌ Чтение из БД для бот-специфичных таблиц (bot_message_map).
- ❌ Подключение к Redis напрямую (использует `/internal/notifications/pop`).

## Защита internal API

```python
# apps/backend/app/modules/internal_api/deps.py
async def verify_internal_secret(x_internal_secret: str = Header(...)) -> None:
    if not settings.internal_api_secret:
        raise HTTPException(503, "Internal API not configured")
    if x_internal_secret != settings.internal_api_secret:
        raise HTTPException(403, "Invalid internal secret")
```

Зависимость подключается на уровне корневого роутера `/internal`, поэтому все endpoints наследуют проверку автоматически.

В docker-compose и `.env.example` обязательно должны быть:
```
INTERNAL_API_SECRET=<random-secret>
INTERNAL_API_URL=http://backend:8000
```

Эти переменные должны быть **только** в сервисах `backend` и `bot`. Никогда не экспонируются наружу.

## Models / Schemas Hub

`apps/backend/app/models.py` и `apps/backend/app/schemas.py` — wildcard-re-export хабы для Alembic и обратной совместимости. Новый код **должен** импортировать из конкретных модулей:

```python
# ✅ правильно
from app.modules.orders.models import Order
from app.modules.orders.schemas import CheckoutIn

# ⚠️ допустимо только для Alembic / легаси
from app.models import Order
```

## Сводка инвариантов

1. Backend — единственный владелец бизнес-логики и БД.
2. Bot — тонкий адаптер, вызывает internal API.
3. Каждый модуль = models + schemas + repository + service + router.
4. Router — request → service → response.
5. Repository — только SQL.
6. Service — use-case.
7. internal API защищён `INTERNAL_API_SECRET`.
8. Новый код импортирует из `app.modules.<name>`, не из hub.
