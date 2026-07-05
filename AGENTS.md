# AGENTS.md

Инструкции для AI-агентов и разработчиков, работающих с проектом.

## TL;DR

**Backend — единственный владелец бизнес-логики и БД. Bot — тонкий адаптер. Не нарушай это.**

## Обязательные правила

### 1. bot НИКОГДА не меняет бизнес-сущности напрямую
- ❌ Никаких `asyncpg`, прямых SQL, прямых `db.add/commit` в `apps/bot/`.
- ❌ Никакой бизнес-логики в handler'ах.
- ❌ Никакого изменения `order.status`, `payment.status`, `product.real_purchases`, `support_tickets.status` из бота.
- ❌ Никакого формирования текста доставки со ссылками Google Drive без одобрения backend.
- ✅ Bot только: получить Telegram event → вызвать backend internal API → отправить ответ.

### 2. payments, orders, delivery живут ТОЛЬКО в backend services
- `orders/service.py` владеет: cart estimate, checkout, fulfillment, discount calculation, Telegram invoice creation.
- `payments` — внутри orders/service (OrderService.fulfill создаёт Payment).
- `delivery` — внутри orders/service (OrderService.fulfill создаёт LinkDeliveryLog).
- `support` — внутри support/service (SupportService.admin_reply_by_telegram).
- `notifications` — внутри notifications/service.

### 3. admin_api НЕ должен превращаться в один огромный router
- `admin_api/router.py` — только агрегатор (<80 строк).
- Каждый поддомен в `admin_api/<subdomain>/` со своими `router.py` + `service.py` + `schemas.py` (+ `repository.py` если нужны специфичные SQL).
- Общие хелперы (пагинация, сортировка, поиск) — в `admin_api/filters.py`.

### 4. Каждый новый модуль ДОЛЖЕН иметь полный набор файлов

```
modules/<name>/
├── models.py       # SQLAlchemy ORM
├── schemas.py      # Pydantic DTO
├── repository.py   # Только SQL
├── service.py      # Use-case логика
└── router.py       # Тонкий router
```

### 5. После изменений запускать проверки

В этом порядке:
1. `python3 -c "import ast, sys; ast.parse(open('<file>').read())"` — для каждого `.py`.
2. `cd apps/backend && python3 -c "from app.main import app"` — smoke-импорт.
3. `cd apps/backend && pytest` — если есть тесты.
4. `cd apps/backend && ruff check . && mypy .` — линт и типы.
5. `cd apps/miniapp && npm run build && npx tsc --noEmit`.
6. `cd apps/admin && npm run build && npx tsc --noEmit`.
7. `docker-compose -f infra/docker-compose.yml config` — compose валиден.
8. `grep -R "asyncpg\|select(\|db\.add" apps/bot/ --include="*.py"` — должно быть пусто.
9. `aislop ci` (если настроен) — общий линт проекта.

## Структура проекта

```
telegram-bot0Video/
├── apps/
│   ├── backend/          # FastAPI + SQLAlchemy
│   │   └── app/
│   │       ├── core/         # config, database, security, redis
│   │       ├── auth.py       # get_current_user, get_current_admin
│   │       ├── models.py     # HUB — только для Alembic
│   │       ├── schemas.py    # HUB — только для совместимости
│   │       ├── main.py
│   │       └── modules/      # Доменные модули
│   │           ├── catalog/
│   │           ├── users/
│   │           ├── orders/
│   │           ├── promos/
│   │           ├── favorites/
│   │           ├── support/
│   │           ├── settings/
│   │           ├── notifications/
│   │           ├── admin/         # модели Admin, AdminLog, LinkDeliveryLog, GoogleDriveToken
│   │           ├── admin_api/     # god-router разбит на подмодули
│   │           └── internal_api/  # защищённые endpoints для bot
│   ├── bot/              # aiogram 3 — ТОЛЬКО thin handlers
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── http_client.py
│   │   ├── handlers/
│   │   └── workers/
│   ├── miniapp/          # React Mini App
│   └── admin/            # react-admin
├── docs/                 # документация
├── infra/                # docker-compose
├── packages/             # shared types/constants
├── migrations/           # alembic
└── AGENTS.md             # этот файл
```

## Internal API (bot ↔ backend)

Все endpoints защищены header `X-Internal-Secret: <INTERNAL_API_SECRET>`.

| Endpoint | Назначение |
|----------|-----------|
| `POST /internal/telegram/pre-checkout` | Валидация заказа перед оплатой Stars |
| `POST /internal/telegram/successful-payment` | Фулфилл заказа |
| `POST /internal/support/admin-reply` | Обработка ответа админа на тикет |
| `POST /internal/support/tickets/{id}/mark-notified` | Пометить тикет уведомлённым |
| `GET  /internal/support/tickets/unnotified` | Список тикетов для уведомления |
| `GET  /internal/support/admins/active` | Список telegram_id активных админов |
| `POST /internal/bot/admin-message-map` | Сохранить маппинг admin_message_id → ticket_id |
| `POST /internal/notifications/send-result` | Зафиксировать результат отправки уведомления |
| `POST /internal/notifications/pop` | Достать следующее уведомление из Redis |
| `GET  /internal/notifications/{id}/recipients` | Получатели рассылки |

## Запрещено

- ❌ Создавать таблицы в БД из bot.
- ❌ Использовать `from app.models import ...` в новом коде (только Alembic).
- ❌ Создавать god-router.
- ❌ Делать `try: import; except ImportError: raise 501`.
- ❌ Использовать `httpx` или другие HTTP-клиенты напрямую в router.py для внешних API.

## При добавлении новой фичи

1. Сначала спроси: где она должна жить?
   - Пользовательская логика → `backend/modules/<domain>/`.
   - Admin-функция → `backend/modules/admin_api/<subdomain>/`.
   - Bot-обработка → `backend/modules/internal_api/<concern>.py` + `apps/bot/handlers/<concern>.py`.
2. Создай все 5 файлов модуля (если новый модуль).
3. Реализуй service и repository первыми.
4. Router — последним, и он должен быть тонким.
5. Запусти все проверки.
6. Обнови `docs/ARCHITECTURE.md` если добавил новый модуль.

## Mini App UI (apps/miniapp) — дизайн-система и FSD

Полное описание: `apps/miniapp/docs/MINIAPP_UI_ARCHITECTURE.md`. Кратко — правила,
обязательные при работе с UI Mini App:

- **Новый UI сначала ищи в `shared/ui`** (компоненты `Tma*`). Переиспользуй или
  расширяй существующий примитив, не плоди дубли.
- **Не пиши одноразовые стили в `pages`.** Если на странице появился свой
  свёрстанный блок — вынеси его в `widget` или `shared/ui`.
- **Не смешивай UI, API и бизнес-логику.** У каждого слоя своя зона
  ответственности.
- **Не копируй Figma-generated code.** Figma — это визуальный референс, а не
  исходник. Реализуй через `Tma*`, токены и семантические классы.
- **Экраны собираются по схеме:**
  `pages → widgets → features → entities → shared/ui` (импорты только вниз).
- **`shared/ui` НЕ знает про товары, корзину, оплаты, Stars.** Доменный смысл
  добавляется уровнем выше — в `entities` / `features` / `widgets`.
- **`pages` тонкие:** только композиция и проброс данных/обработчиков; без
  сложных вычислений (их место — в `features`/`entities`/`lib`).
- **API-запросы НЕ делаются внутри `shared/ui` и внутри `entities`.**
- **Токены — единый источник:** цвета/отступы/радиусы/тени берутся из
  `shared/tokens` (через Tailwind-классы или импорт). Никаких хардкод-hex.
- **Темы:** компоненты используют семантические классы (`bg-surface`, `text-text`,
  `text-hint`), которые сами резолвятся в light/dark и в тему Telegram. Цепочка:
  `--tg-theme-*` → `--ds-*` (`src/app/index.css`) → semantic Tailwind.
- **После UI-изменений запускай проверки:** `npm run typecheck`, `npm run build`,
  `npm run lint` / `aislop ci` (если подключён). Должно быть 0 ошибок.

## ⚠️ Технический нюанс: запись файлов с `import` через агент-тулинг

> Касается **только AI-агентов**, которые редактируют этот репозиторий через
> автоматизированный инструментарий (REPL / shell-обёртку). На сам код проекта
> и на обычную ручную разработку это не влияет.

**Что ломалось.** При передаче исходника файла как строки через слой выполнения
агента строковые литералы, содержащие `import ... from '...'`, **вырезались**
ещё до записи на диск (фильтр воспринимал их как «настоящие» import-инструкции).
В результате создавались `.tsx`/`.ts` файлы **без строк импортов** → TS2304
`Cannot find name ...`, TS2307 `Cannot find module ...`, «исчезающие» правки.

**Безопасный способ правок.** Записывать файлы не «сырым» текстом, а через
base64 — содержимое кодируется на стороне агента и декодируется в WSL:

```bash
echo '<base64>' | base64 -d > 'src/path/File.tsx'
```

Дополнительно — авторить контент с плейсхолдером, а реальное слово `import`
подставлять перед кодированием, чтобы литерал не появлялся в исходнике агента:

```js
// в коде агента
const real = template.split('#IMP#').join('import')   // '#IMP# { X } from "y"' → import
const b64  = Buffer.from(real, 'utf8').toString('base64')
// затем: echo <b64> | base64 -d > file
```

Чтение файлов с импортами — симметрично: `base64 -w0 file` на стороне WSL,
декодирование на стороне агента (иначе вывод тоже может потерять строки import).

**Когда применять.**
- При **создании/перезаписи** любых `.ts`/`.tsx` с секцией импортов через тулинг.
- При **чтении** файлов, если в выводе пропадают строки `import`.
- Для остальных операций (запуск `tsc`/`eslint`/`vite`, `grep`, `ls`) обходной
  путь не нужен.

## Что делать, если что-то непонятно

- Прочитай `docs/ARCHITECTURE.md` — там общая картина.
- Прочитай `docs/MODULE_BOUNDARIES.md` — там границы.
- Прочитай `docs/DEVELOPMENT_RULES.md` — там правила.
- Если всё ещё непонятно — спроси пользователя, не угадывай.