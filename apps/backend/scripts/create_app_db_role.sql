-- Least-privilege Postgres role for the running app (no DDL rights).
-- Run once as a superuser / the existing migration owner, e.g.:
--   psql "$DATABASE_URL" -v app_password="CHANGE_ME" -f create_app_db_role.sql
--
-- Schema changes stay with the existing (privileged) DB owner role, run via
-- `alembic upgrade head` (see docs/db-least-privilege.md). This role only
-- gets DML rights, so a compromised app process can't alter the schema.

-- psql variables (:'app_password') don't interpolate inside a dollar-quoted
-- DO $$ ... $$ block, so the role is created (if missing) via \gexec instead,
-- and the password is set separately where interpolation does work.
SELECT 'CREATE ROLE noxx_app LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'noxx_app')\gexec
ALTER ROLE noxx_app WITH PASSWORD :'app_password';

GRANT USAGE ON SCHEMA public TO noxx_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO noxx_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO noxx_app;

-- So tables/sequences created by future migrations (run as the owner role)
-- are automatically granted to noxx_app without re-running this script.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noxx_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO noxx_app;
