# Development Rules

## Главные принципы (non-negotiable)

1. **Backend — единственный владелец бизнес-логики.**
2. **Bot — тонкий handler, вызывает backend internal API.**
3. **Каждый модуль = models + schemas + repository + service + router.**
4. **Router — тонкий: request → service → response.**
5. **Repository — только SQLAlchemy-запросы.**
6. **Service — use-case логика, может вызывать несколько repository и integrations.**
7. **internal API защищён `INTERNAL_API_SECRET` (header `X-Internal-Secret`).**
8. **Новый код импортирует из `app.modules.<name>`, не из `app.models` хаба.**

## Что и куда писать

### Backend
- Бизнес-логика → `service.py`.
- SQL → `repository.py`.
- HTTP-вызовы к внешним API → `service.py` через integration-клиент.
- Pydantic-схемы → `schemas.py`.
- FastAPI endpoints → `router.py`.

### Bot
- Обработка Telegram event → `handlers/<concern>.py`.
- HTTP к backend → `http_client.py` (метод на каждый endpoint internal API).
- Фоновые задачи → `workers/<concern>.py`.
- Никакой БД-логики.

## Code Quality

- ❌ Бизнес-логика в frontend-компонентах или bot-handler'ах.
- ❌ Дублирование бизнес-логики между bot и backend.
- ❌ Прямой SQL в router или bot handler.
- ❌ HTTP-вызовы к Telegram/Google в router.py.
- ❌ `try: import; ... except ImportError: raise 501` — маскировка незавершённой работы.
- ❌ `TODO`, `FIXME`, мёртвый код в закоммиченных файлах.
- ❌ `console.log` / `print` для отладки в production-коде.

- ✅ Soft-delete только через `status = "deleted"`.
- ✅ Все env/config через `app/core/config.py` (Pydantic Settings).
- ✅ Доменные ошибки через `app/core/exceptions.py`.
- ✅ Type hints везде.
- ✅ Pydantic-схемы для всех request/response.

## Module Creation Checklist

При создании нового доменного модуля:

```bash
mkdir -p apps/backend/app/modules/<name>
touch apps/backend/app/modules/<name>/{__init__,models,schemas,repository,service,router}.py
```

Затем:
1. `models.py` — SQLAlchemy ORM-модели.
2. `schemas.py` — Pydantic DTO.
3. `repository.py` — `class XRepository` с SQL-методами.
4. `service.py` — `class XService` с use-case методами.
5. `router.py` — `APIRouter`, тонкие endpoints, `Depends(get_db)`, вызов service.
6. `__init__.py` — re-export моделей и схем.
7. Подключить в `apps/backend/app/main.py`: `app.include_router(<name>_router)`.
8. Добавить wildcard import в `apps/backend/app/models.py` (для Alembic).

## Verification (после КАЖДОГО изменения)

```bash
# Python syntax
python3 -c "import ast, sys; ast.parse(open('file.py').read())"

# Python import smoke
cd apps/backend && python3 -c "from app.main import app; print(len(app.routes))"

# TypeScript (если меняли .ts/.tsx)
cd apps/miniapp && npx tsc --noEmit
cd apps/admin && npx tsc --noEmit

# Docker compose
docker-compose -f infra/docker-compose.yml config

# Bot (нет прямого SQL)
grep -R "asyncpg\|select(\|db\.add\|db\.commit" apps/bot/ --include="*.py"

# Backend — SQL только в repository
grep -R "select\|db\.add\|db\.commit" apps/backend/app/modules/ --include="*.py" \
  | grep -v "repository.py\|alembic/"
```

## Stack Guardrails

- ❌ Не добавлять Directus.
- ❌ Не добавлять новые библиотеки без явной причины.
- ❌ Не менять версии фреймворков без обсуждения.
- ❌ Не использовать `any` в TypeScript без крайней необходимости.
- ✅ Перед добавлением зависимости проверить, нет ли её уже.

## Git Workflow

- Один PR = один модуль или один сквозной рефактор.
- Название ветки: `refactor/<scope>` или `feat/<scope>`.
- Описание PR содержит:
  - Какие правила нарушены (если это fix).
  - Какие файлы добавлены/изменены/удалены.
  - Какие проверки запущены и их вывод.
  - Какие архитектурные долги остались.

## Когда что-то не вписывается в шаблон

Если кажется, что нужно нарушить правило:
1. Записать в `docs/ARCHITECTURE.md` в раздел "Исключения" с обоснованием.
2. Добавить ADR в `docs/adr/NNNN-<topic>.md`.
3. Упомянуть в PR.