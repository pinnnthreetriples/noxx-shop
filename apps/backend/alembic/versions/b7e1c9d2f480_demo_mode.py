"""demo mode storefront switch

Revision ID: b7e1c9d2f480
Revises: a1b2c3d4e5f6
Create Date: 2026-08-11

Adds settings.demo_mode_enabled. With it on, the storefront hides every real
product and serves only the demo product (slug `demo-preview`). Idempotent, and
mirrored by `_add_missing_columns` in app/main.py while prod runs with
DB_AUTO_SCHEMA=1.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7e1c9d2f480'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMN = "demo_mode_enabled"


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("settings")}
    if _COLUMN not in existing:
        op.add_column(
            "settings",
            sa.Column(_COLUMN, sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("settings")}
    if _COLUMN in existing:
        op.drop_column("settings", _COLUMN)
