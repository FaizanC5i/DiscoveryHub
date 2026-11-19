"""Add agents, evidence offsets, chunk mapping status and mapping constraints.

Revision ID: 008_mapping_agents_and_evidence
Revises: 007_create_checkpoint_mapping

Work order 8. Builds on 007:
- agents: every mapping names the agent that produced it. The Helper Agent is seeded here.
- mapping_evidence: stores where each quote sits in the content, so it can be checked
  with content_text[start:end] == evidence_quote.
- context_chunks: mapping_status tracks whether a chunk has been sent to the agent.
- context_checkpoint_mappings: the active/inactive state must agree, and the dispatcher
  gets an index on (project_id, checkpoint_id).

agent_run_id already identifies the agent call that produced a mapping, so no separate
batch_id column is added.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "008_mapping_agents_and_evidence"
down_revision: str | None = "007_create_checkpoint_mapping"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

HELPER_AGENT_CODE = "HELPER_AGENT"
HELPER_AGENT_NAME = "Discovery Hub Helper Agent"


def upgrade() -> None:
    agents = op.create_table(
        "agents",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("agent_code", sa.NVARCHAR(length=50), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=255), nullable=False),
        # NULL for the Helper Agent, which is not tied to one pillar.
        sa.Column("pillar_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_agents"),
        sa.UniqueConstraint("agent_code", name="uq_agents_agent_code"),
        sa.ForeignKeyConstraint(
            ["pillar_id"], ["discovery_pillars.id"],
            name="fk_agents_pillar_id",
        ),
    )
    # Each pillar has at most one agent. The Helper Agent (pillar_id NULL) is not limited.
    op.create_index(
        "ux_agents_pillar_id",
        "agents",
        ["pillar_id"],
        unique=True,
        mssql_where=sa.text("pillar_id IS NOT NULL"),
    )
    op.bulk_insert(
        agents,
        [{"agent_code": HELPER_AGENT_CODE, "name": HELPER_AGENT_NAME, "pillar_id": None}],
    )

    op.create_foreign_key(
        "fk_mappings_mapped_by_agent_id",
        "context_checkpoint_mappings",
        "agents",
        ["mapped_by_agent_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_mappings_active_state",
        "context_checkpoint_mappings",
        "(is_active = 1 AND deactivated_at IS NULL) OR (is_active = 0 AND deactivated_at IS NOT NULL)",
    )
    op.create_index(
        "ix_mappings_project_id_checkpoint_active",
        "context_checkpoint_mappings",
        ["project_id", "checkpoint_id"],
        mssql_where=sa.text("is_active = 1"),
    )

    # The table is empty before this migration (created in 007 and not yet written to),
    # so NOT NULL columns can be added without a default.
    op.add_column("mapping_evidence", sa.Column("evidence_start_char", sa.Integer(), nullable=False))
    op.add_column("mapping_evidence", sa.Column("evidence_end_char", sa.Integer(), nullable=False))
    op.create_check_constraint(
        "ck_mapping_evidence_end_after_start",
        "mapping_evidence",
        "evidence_end_char > evidence_start_char",
    )
    op.create_check_constraint(
        "ck_mapping_evidence_length",
        "mapping_evidence",
        "evidence_end_char - evidence_start_char = LEN(evidence_quote)",
    )

    op.add_column(
        "context_chunks",
        sa.Column("mapping_status", sa.NVARCHAR(length=20), server_default="PENDING", nullable=False),
    )
    op.create_check_constraint(
        "ck_context_chunks_mapping_status",
        "context_chunks",
        "mapping_status IN ('PENDING', 'IN_PROGRESS', 'MAPPED', 'NO_MATCH', 'FAILED')",
    )
    op.add_column(
        "context_chunks",
        sa.Column("mapping_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("context_chunks", sa.Column("mapped_at", mssql.DATETIME2(), nullable=True))
    op.add_column("context_chunks", sa.Column("mapping_error", sa.NVARCHAR(length="max"), nullable=True))
    op.create_index(
        "ix_context_chunks_content_mapping_status",
        "context_chunks",
        ["context_content_id", "mapping_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_context_chunks_content_mapping_status", table_name="context_chunks")
    op.drop_column("context_chunks", "mapping_error")
    op.drop_column("context_chunks", "mapped_at")
    op.drop_column("context_chunks", "mapping_attempts")
    op.drop_constraint("ck_context_chunks_mapping_status", "context_chunks", type_="check")
    op.drop_column("context_chunks", "mapping_status")

    op.drop_constraint("ck_mapping_evidence_length", "mapping_evidence", type_="check")
    op.drop_constraint("ck_mapping_evidence_end_after_start", "mapping_evidence", type_="check")
    op.drop_column("mapping_evidence", "evidence_end_char")
    op.drop_column("mapping_evidence", "evidence_start_char")

    op.drop_index("ix_mappings_project_id_checkpoint_active", table_name="context_checkpoint_mappings")
    op.drop_constraint("ck_mappings_active_state", "context_checkpoint_mappings", type_="check")
    op.drop_constraint("fk_mappings_mapped_by_agent_id", "context_checkpoint_mappings", type_="foreignkey")

    op.drop_index("ux_agents_pillar_id", table_name="agents")
    op.drop_table("agents")
