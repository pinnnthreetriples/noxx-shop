# DB schema: Alembic + least-privilege app role

Schema used to be managed at runtime: `app/main.py`'s lifespan ran
`Base.metadata.create_all` plus a hand-rolled `_add_missing_columns` (ad-hoc
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) on every startup. That forced the
app's DB user to hold DDL rights. Alembic (`apps/backend/alembic/`) is now the
source of truth; the runtime DDL still runs by default (`DB_AUTO_SCHEMA=1`) so
existing deploys keep working until migrated over deliberately.

## Rollout order (do not skip steps)

1. **Run the migration** against the current (privileged) DB user:
   ```
   ALEMBIC_DATABASE_URL=postgresql+asyncpg://<privileged_user>:<pw>@host:5432/video_shop \
     RUN_MIGRATIONS=1 <start the backend container once, or run manually:>
   alembic upgrade head
   ```
   The included `50d45b971a38_init` migration builds the schema via
   `Base.metadata.create_all(checkfirst=True)` — on a fresh DB it creates
   everything; on an existing DB (prod already has every table/column from
   the old runtime DDL) it's a no-op that just stamps the revision. Confirm
   with `alembic current` that it shows `50d45b971a38 (head)`.

2. **Create the restricted app role** (one-time, as a superuser or the
   existing owner role):
   ```
   psql "$DATABASE_URL" -v app_password="<a real password>" \
     -f apps/backend/scripts/create_app_db_role.sql
   ```
   This creates `noxx_app` with `SELECT/INSERT/UPDATE/DELETE` on all tables
   and `USAGE` on sequences in `public` — no `CREATE`/DDL rights — and sets
   `ALTER DEFAULT PRIVILEGES` so tables added by future migrations are
   granted automatically.

3. **Point the app at the restricted role and turn off runtime DDL**: set the
   app's `DATABASE_URL` to use `noxx_app`, and set `DB_AUTO_SCHEMA=0`. Keep
   `ALEMBIC_DATABASE_URL` (privileged) for future `RUN_MIGRATIONS=1` runs —
   the app itself never needs DDL rights again.

## Env vars

| Var | Default | Purpose |
|---|---|---|
| `DB_AUTO_SCHEMA` | `1` (true) | Runtime `create_all` + `_add_missing_columns` on startup. Set `0` once step 1 above has run. |
| `RUN_MIGRATIONS` | unset (off) | If `1`, the container entrypoint runs `alembic upgrade head` before starting uvicorn. |
| `ALEMBIC_DATABASE_URL` | falls back to `DATABASE_URL` | DB URL used only for the migration step, so it can point at a privileged role while `DATABASE_URL` (the app) stays restricted. |

## Future schema changes

Write a normal Alembic migration (`alembic revision --autogenerate -m "..."`)
against the updated models instead of adding another ad-hoc `ALTER TABLE` to
`_add_missing_columns`. Run it via `RUN_MIGRATIONS=1` with a privileged
`ALEMBIC_DATABASE_URL` before/alongside the deploy.
