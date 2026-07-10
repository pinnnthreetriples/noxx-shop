-- Least-privilege Postgres role for the running app (no DDL rights).
-- Run once as a superuser / the existing migration owner, e.g.:
--   psql "$DATABASE_URL" -v app_password="CHANGE_ME" -f create_app_db_role.sql
--
-- Schema changes stay with the existing (privileged) DB owner role, run via
-- `alembic upgrade head` (see docs/db-least-privilege.md). This role only
-- gets DML rights, so a compromised app process can't alter the schema.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noxx_app') THEN
        CREATE ROLE noxx_app WITH LOGIN PASSWORD :'app_password';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO noxx_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO noxx_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO noxx_app;

-- So tables/sequences created by future migrations (run as the owner role)
-- are automatically granted to noxx_app without re-running this script.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noxx_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO noxx_app;
