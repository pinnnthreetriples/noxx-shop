"""subscription prices in USD as the source of truth

Revision ID: a1b2c3d4e5f6
Revises: 7c2a91d4b6e3
Create Date: 2026-07-13

Adds settings.sub_price_month_usd / sub_price_year_usd. Stars are now derived
from the live rate at checkout, so the old sub_price_*_stars columns are left
in place (harmless orphans) rather than dropped. Idempotent, and mirrored by
`_add_missing_columns` in app/main.py while prod runs with DB_AUTO_SCHEMA=1.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7c2a91d4b6e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = {"sub_price_month_usd": "5.98", "sub_price_year_usd": "49.98"}


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("settings")}
    for name, default in _COLUMNS.items():
        if name not in existing:
            op.add_column(
                "settings",
                sa.Column(name, sa.Numeric(10, 2), nullable=False, server_default=default),
            )


def downgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("settings")}
    for name in _COLUMNS:
        if name in existing:
            op.drop_column("settings", name)
