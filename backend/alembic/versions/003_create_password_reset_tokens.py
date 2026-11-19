"""Create the password_reset_tokens table.

Revision ID: 003_create_password_reset_tokens
Revises: 002_create_refresh_tokens
Create Date: 2026-11-09

Work order 3 of 3. One row per "forgot password" request. Single-use, 30-minute lifetime.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_create_password_reset_tokens"
down_revision: str | None = "002_create_refresh_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.NVARCHAR(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        # NULL = not yet used. Set once, when the password is reset: the token is spent.
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_password_reset_tokens"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_password_reset_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
