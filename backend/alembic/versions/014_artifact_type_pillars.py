"""Say which pillars' approved answers each artifact type is written from (BRD: User Discovery).

Revision ID: 014_artifact_type_pillars
Revises: 013_checkpoint_answer_rules

artifact_type_pillars lists, per artifact type, the discovery pillars whose APPROVED checkpoint
answers the artifact agent receives. The BRD reads only the User Discovery pillar. The PRD will
later read User and Tech.

artifact_section_checkpoints stays: a section with rows there reads only those checkpoints; a
section without rows reads every approved answer of the type's pillars. The BRD has no rows
since the checkpoints were replaced by USR-01..USR-19, so every BRD section reads every approved
User Discovery answer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "014_artifact_type_pillars"
down_revision: str | None = "013_checkpoint_answer_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifact_type_pillars",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("artifact_type_id", sa.BigInteger(), nullable=False),
        sa.Column("pillar_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_type_pillars"),
        sa.ForeignKeyConstraint(
            ["artifact_type_id"], ["artifact_types.id"], ondelete="CASCADE",
            name="fk_artifact_type_pillars_artifact_type_id",
        ),
        sa.ForeignKeyConstraint(["pillar_id"], ["discovery_pillars.id"], name="fk_artifact_type_pillars_pillar_id"),
        sa.UniqueConstraint("artifact_type_id", "pillar_id", name="uq_artifact_type_pillars"),
    )
    op.execute(
        "INSERT INTO artifact_type_pillars (artifact_type_id, pillar_id) "
        "SELECT t.id, p.id FROM artifact_types t JOIN discovery_pillars p ON p.code = 'USER' WHERE t.code = 'BRD'"
    )


def downgrade() -> None:
    op.drop_table("artifact_type_pillars")
