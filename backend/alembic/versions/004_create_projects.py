"""Create the projects table.

Revision ID: 004_create_projects
Revises: 003_create_password_reset_tokens
Create Date: 2026-11-11

Work order 4. One row per discovery project. Each project belongs to the user
who created it. Dates are DATE columns, and the end date must not come before the start date.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "004_create_projects"
down_revision: str | None = "003_create_password_reset_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("description", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            mssql.DATETIME2(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mssql.DATETIME2(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_projects_owner_id_users",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_projects_end_after_start",
        ),
    )
    op.create_index(
        "ix_projects_owner_id_created_at", "projects", ["owner_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_projects_owner_id_created_at", table_name="projects")
    op.drop_table("projects")
