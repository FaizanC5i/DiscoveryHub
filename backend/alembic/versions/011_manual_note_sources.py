"""Let context_sources hold manual notes as well as uploaded files.

Revision ID: 011_manual_note_sources
Revises: 010_create_checkpoint_answer_tables

Manual notes reuse context_sources, context_content and context_chunks. A note has
no file, so blob_path and original_filename become nullable, and updated_at records
the last edit. source_type already existed with the value 'upload'; it becomes
'FILE_UPLOAD' and gains a check for 'MANUAL_NOTE'.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "011_manual_note_sources"
down_revision: str | None = "010_checkpoint_answer_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE context_sources SET source_type = 'FILE_UPLOAD' WHERE source_type = 'upload'")

    # SQL Server names the default constraint itself, so it has to be looked up before it can be replaced.
    op.execute(
        """
        DECLARE @name sysname;
        SELECT @name = dc.name
        FROM sys.default_constraints dc
        JOIN sys.columns c ON c.default_object_id = dc.object_id
        WHERE dc.parent_object_id = OBJECT_ID('context_sources') AND c.name = 'source_type';
        IF @name IS NOT NULL
            EXEC('ALTER TABLE context_sources DROP CONSTRAINT ' + @name);
        """
    )
    op.execute(
        "ALTER TABLE context_sources ADD CONSTRAINT df_context_sources_source_type "
        "DEFAULT 'FILE_UPLOAD' FOR source_type"
    )
    op.create_check_constraint(
        "ck_context_sources_source_type",
        "context_sources",
        "source_type IN ('FILE_UPLOAD', 'MANUAL_NOTE')",
    )

    op.alter_column("context_sources", "blob_path", existing_type=sa.NVARCHAR(500), nullable=True)
    op.alter_column(
        "context_sources", "original_filename", existing_type=sa.NVARCHAR(255), nullable=True
    )
    op.add_column("context_sources", sa.Column("updated_at", mssql.DATETIME2(), nullable=True))


def downgrade() -> None:
    # Notes cannot be represented without a file, so they are not deleted here. Restoring
    # NOT NULL on blob_path and original_filename would fail while notes exist.
    op.drop_column("context_sources", "updated_at")
    op.drop_constraint("ck_context_sources_source_type", "context_sources", type_="check")
    op.execute("ALTER TABLE context_sources DROP CONSTRAINT df_context_sources_source_type")
    op.execute("ALTER TABLE context_sources ADD CONSTRAINT df_context_sources_source_type DEFAULT 'upload' FOR source_type")
    op.execute("UPDATE context_sources SET source_type = 'upload' WHERE source_type = 'FILE_UPLOAD'")
