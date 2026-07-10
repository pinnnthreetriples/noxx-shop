#!/bin/sh
set -e

# Optional migration step, off by default so a plain `docker run`/compose-up
# doesn't require DDL rights. Set RUN_MIGRATIONS=1 to run `alembic upgrade
# head` before starting the app — typically with ALEMBIC_DATABASE_URL pointed
# at a privileged role while DATABASE_URL (used by the app) stays restricted.
if [ "$RUN_MIGRATIONS" = "1" ]; then
    DATABASE_URL="${ALEMBIC_DATABASE_URL:-$DATABASE_URL}" alembic upgrade head
fi

exec "$@"
