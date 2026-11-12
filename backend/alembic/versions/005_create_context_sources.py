"""Create context_sources and context_content tables.

Revision ID: 005_create_context_sources
Revises: 004_create_projects

Work order 5. Documents attached to a project (context_sources) and the text
extracted from them (context_content). The original files live in Blob Storage.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "005_create_context_sources"
down_revision: str | None = "004_create_projects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "context_sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sa.NVARCHAR(length=30), server_default="upload", nullable=False),
        sa.Column("title", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("original_filename", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("blob_path", sa.NVARCHAR(length=500), nullable=False),
        sa.Column("mime_type", sa.NVARCHAR(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("processing_status", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("failure_reason", sa.NVARCHAR(length=500), nullable=True),
        sa.Column(
            "created_at",
            mssql.DATETIME2(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.Column("deleted_at", mssql.DATETIME2(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_context_sources"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_context_sources_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_context_sources_created_by_users",
        ),
        sa.CheckConstraint(
            "processing_status IN ('processing', 'ready', 'failed')",
            name="ck_context_sources_status",
        ),
    )
    op.create_index(
        "ix_context_sources_project_id_created_at",
        "context_sources",
        ["project_id", "created_at"],
    )

    op.create_table(
        "context_content",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("context_source_id", sa.BigInteger(), nullable=False),
        sa.Column("content_text", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("extraction_method", sa.NVARCHAR(length=50), nullable=False),
        sa.Column(
            "created_at",
            mssql.DATETIME2(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_context_content"),
        sa.ForeignKeyConstraint(
            ["context_source_id"],
            ["context_sources.id"],
            name="fk_context_content_context_source_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("context_source_id", name="uq_context_content_source_id"),
    )


def downgrade() -> None:
    op.drop_table("context_content")
    op.drop_index("ix_context_sources_project_id_created_at", table_name="context_sources")
    op.drop_table("context_sources")