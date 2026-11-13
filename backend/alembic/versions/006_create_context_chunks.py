"""Create context_chunks table.

Revision ID: 006_create_context_chunks
Revises: 005_create_context_sources

Work order 6. Splits the extracted text in context_content into overlapping
chunks. Each chunk stores its start and end offsets into content_text, so any
quote the helper agent makes can be checked against the exact source characters.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "006_create_context_chunks"
down_revision: str | None = "005_create_context_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "context_chunks",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("context_content_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_number", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            mssql.DATETIME2(),
            server_default=sa.text("SYSUTCDATETIME()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_context_chunks"),
        sa.ForeignKeyConstraint(
            ["context_content_id"],
            ["context_content.id"],
            name="fk_context_chunks_context_content_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "context_content_id",
            "chunk_number",
            name="uq_context_chunks_content_number",
        ),
        sa.CheckConstraint("chunk_number >= 1", name="ck_context_chunks_chunk_number"),
        sa.CheckConstraint("start_char >= 0", name="ck_context_chunks_start_char"),
        sa.CheckConstraint("end_char > start_char", name="ck_context_chunks_end_after_start"),
        sa.CheckConstraint(
            "char_count = end_char - start_char",
            name="ck_context_chunks_char_count",
        ),
    )
    op.create_index(
        "ix_context_chunks_context_content_id",
        "context_chunks",
        ["context_content_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_context_chunks_context_content_id", table_name="context_chunks")
    op.drop_table("context_chunks")
