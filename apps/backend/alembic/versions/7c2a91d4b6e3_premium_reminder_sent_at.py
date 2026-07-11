"""users.premium_reminder_sent_at for premium-expiry reminders

Revision ID: 7c2a91d4b6e3
Revises: 9f3d2c81a5e7
Create Date: 2026-07-11

Idempotent on purpose: the init migration is `create_all` over the live
models, so a fresh DB already gets this column from init; only a DB whose
users table predates this feature (prod) actually needs the ALTER. The same
column is also added by `_add_missing_columns` in app/main.py while prod
still runs with DB_AUTO_SCHEMA=1 (deliberate transitional duplication).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7c2a91d4b6e3'
down_revision: Union[str, None] = '9f3d2c81a5e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMN = "premium_reminder_sent_at"


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if _COLUMN not in existing:
        op.add_column("users", sa.Column(_COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if _COLUMN in existing:
        op.drop_column("users", _COLUMN)
