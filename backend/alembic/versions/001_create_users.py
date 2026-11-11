"""Create the users table.

Revision ID: 001_create_users
Revises:
Create Date: 2026-11-09

Work order 1 of 3. Creates the root table: every other table points back to it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_create_users"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        # IDENTITY(1,1): SQL Server numbers the rows itself, so the app never picks an id.
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=100), nullable=False),
        sa.Column("email", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("password_hash", sa.NVARCHAR(length=255), nullable=False),
        # BIT in SQL Server: 1 = may sign in, 0 = deactivated.
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        # Database-level uniqueness: even if application code has a bug, two rows
        # cannot share an email.
        sa.UniqueConstraint("email", name="uq_users_email"),
    )


def downgrade() -> None:
    op.drop_table("users")
