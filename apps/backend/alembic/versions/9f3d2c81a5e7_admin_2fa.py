"""admin 2FA (TOTP) + JWT revocation columns

Revision ID: 9f3d2c81a5e7
Revises: 50d45b971a38
Create Date: 2026-07-10

Idempotent on purpose: the init migration is `create_all` over the live
models, so a fresh DB already gets these columns from init; only a DB whose
admins table predates this feature (prod) actually needs the ALTERs. The same
columns are also added by `_add_missing_columns` in app/main.py while prod
still runs with DB_AUTO_SCHEMA=1 (deliberate transitional duplication).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9f3d2c81a5e7'
down_revision: Union[str, None] = '50d45b971a38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _new_columns() -> list[sa.Column]:
    return [
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("totp_secret", sa.Text(), nullable=True),
        sa.Column("totp_pending_secret", sa.Text(), nullable=True),
        sa.Column("backup_codes", sa.Text(), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    ]


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("admins")}
    for col in _new_columns():
        if col.name not in existing:
            op.add_column("admins", col)


def downgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("admins")}
    for col in _new_columns():
        if col.name in existing:
            op.drop_column("admins", col.name)
