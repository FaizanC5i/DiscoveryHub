"""Store the owner's own input per checkpoint.

Revision ID: 017_checkpoint_owner_input
Revises: 016_artifact_draft_settings
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "017_checkpoint_owner_input"
down_revision: str | None = "016_artifact_draft_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_checkpoint_answers",
        sa.Column("owner_input", sa.NVARCHAR(length="max"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("project_checkpoint_answers", "owner_input")
