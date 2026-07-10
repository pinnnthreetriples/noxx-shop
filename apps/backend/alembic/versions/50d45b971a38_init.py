"""init

Revision ID: 50d45b971a38
Revises:
Create Date: 2026-06-25 16:12:32.904550

Brings the DB to the current `app.models` state. Before this migration existed,
the app managed schema at runtime via `Base.metadata.create_all` plus ad-hoc
`ADD COLUMN IF NOT EXISTS` calls (see `_add_missing_columns` in app/main.py) —
so any already-deployed DB (e.g. prod) already has every table and column
below. `create_all(checkfirst=True)` only creates tables that don't exist yet,
so running `alembic upgrade head` against such a DB is a safe no-op that just
records this revision; against a fresh DB it builds the full schema.
"""
from typing import Sequence, Union

from alembic import op

from app.models import Base

# revision identifiers, used by Alembic.
revision: str = '50d45b971a38'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
