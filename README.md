# Telegram Mini App — Video Shop

Полноценный Telegram Mini App для продажи видеоконтента через Telegram Stars.

## Архитектура

```text
telegram-bot0Video/
├─ apps/
│  ├─ miniapp/          # React + Vite + TypeScript (покупатели)
│  ├─ admin/            # React + react-admin (админка)
│  ├─ backend/          # FastAPI API
│  ├─ bot/              # aiogram 3 bot
│  └─ admin/            # react-admin приложение
├─ packages/
│  └─ shared/           # shared types / constants
├─ infra/
│  ├─ docker-compose.yml
│  ├─ cloudflared/
│  └─ nginx-or-caddy/
├─ migrations/
│  └─ alembic/
├─ .env.example
├─ Makefile
└─ README.md
```

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните все переменные.
2. Запустите инфраструктуру:
   ```bash
   make up
   ```
3. Примените миграции:
   ```bash
   make migrate
   ```
4. Залейте seed-данные:
   ```bash
   make seed
   ```
5. Откройте Mini App через Telegram.

## Сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| Backend API | `http://localhost:8000` | FastAPI |
| Admin Panel | `http://localhost:3000` | react-admin |
| Media Server | `http://localhost:9000` | Preview / Covers |
| PostgreSQL | `localhost:5432` | База данных |
| Redis | `localhost:6379` | Кэш / очереди |
| Bot | — | aiogram long polling |

## Переменные окружения

См. `.env.example`.

### Admin Panel

- `ADMIN_PUBLIC_URL` — публичный URL админки
- `ADMIN_JWT_SECRET` — секрет для JWT админов
- `ADMIN_DEFAULT_EMAIL` — email для первого входа (seed)
- `ADMIN_DEFAULT_PASSWORD` — пароль для первого входа (seed)
- `ADMIN_DEFAULT_TELEGRAM_ID` — Telegram ID первого админа (seed)

## Команды

- `make up` — запуск docker-compose
- `make down` — остановка
- `make migrate` — применить миграции Alembic
- `make seed` — загрузить начальные данные
- `make logs` — логи сервисов
- `make backend-shell` — shell в backend
- `make bot-shell` — shell в bot

## Как добавить первого админа

1. Укажите `ADMIN_DEFAULT_TELEGRAM_ID` в `.env`.
2. Запустите `make seed` — он автоматически создаст первого админа с ролью `owner`.
3. Откройте админку по адресу `http://localhost:3000`.

## Как создать товар

1. Войдите в админку.
2. Перейдите в раздел **Товары**.
3. Нажмите **Создать**.
4. Заполните slug, цену, статус, категорию.
5. Укажите переводы title/description для поддерживаемых языков.
6. Вставьте Google Drive ссылку в поле `google_drive_link`.
7. Сохраните.

## Как загрузить preview / cover

Загрузите файлы на media-сервер или в поля `cover_url` / `preview_video_url` вставьте прямую ссылку на файл.

## Как отправить рассылку

1. Создайте запись в разделе **Рассылки** через админку.
2. Бэкенд поставит задачу в очередь Redis.

## Как протестировать оплату

1. Запустите бота через Telegram.
2. Откройте Mini App.
3. Добавьте товар в корзину и нажмите **Checkout**.
4. Бот создаст Telegram-инвойс.
5. Оплатите через Telegram Stars.
6. После оплаты бот отправит сообщение со ссылками.

## Стек

- **Frontend (Mini App):** React, Vite, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, TanStack Query, Zustand, react-i18next
- **Frontend (Admin):** React, Vite, TypeScript, react-admin, Material UI
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic
- **Bot:** aiogram 3, Telegram Stars payments
- **Database:** PostgreSQL 16
- **Cache / Queue:** Redis 7
- **Storage:** Google Drive (full videos), локальный media-сервер (preview/covers)
- **Deploy:** Docker, Cloudflare Tunnel, Cloudflare Pages (Mini App)
