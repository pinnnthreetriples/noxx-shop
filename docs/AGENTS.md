# Agent Rules for Future Sessions

## Architecture

- Maintain modular monolith architecture (core + modules + integrations).
- Never write business logic in UI layers or bot handlers.
- Bot is an adapter: receive update → call backend service → send response.

## Stack

- Never add Directus.
- Never change stack (React, FastAPI, aiogram, PostgreSQL) without explicit reason.
- Never add new libraries without checking existing ones first.

## Code Quality

- Never write temporary workarounds or stubs.
- Never leave `TODO`, `FIXME`, dead code, or narrative/trivial comments.
- Never swallow exceptions silently.
- Never use `any` in TypeScript without extreme justification.
- Always run checks after changes (ast.parse, typecheck, lint).

## Imports

- Use `app.core` for config, database, redis_client, security, exceptions.
- Use `app.modules.<name>` for domain logic.
- Use `app.integrations` for external APIs.
