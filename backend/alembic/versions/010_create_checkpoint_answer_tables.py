"""Create checkpoint answer tables: answers, proposals, versions and their evidence.

Revision ID: 010_checkpoint_answer_tables
Revises: 009_rebuild_agent_tables

Schema only. No application logic is added here. The tables give future features a place to
store current answers, AI proposals, saved versions, and the evidence behind each.

Creation order follows the foreign keys: answers, proposals, proposal evidence, versions, and
answer evidence last, because it refers to versions.

Cascade graph (SQL Server allows one cascade path into each table, so the rest use NO ACTION):
- projects -> project_checkpoint_answers -> checkpoint_answer_proposals -> proposal_evidence
- project_checkpoint_answers -> checkpoint_answer_versions -> checkpoint_answer_evidence
- checkpoint_answer_evidence.checkpoint_answer_id is NO ACTION, because the version cascade
  already reaches it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "010_checkpoint_answer_tables"
down_revision: str | None = "009_rebuild_agent_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_checkpoint_answers",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("checkpoint_id", sa.BigInteger(), nullable=False),
        sa.Column("current_answer", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("status", sa.NVARCHAR(length=30), server_default="NOT_STARTED", nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("completion_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("completion_updated_by_run_id", sa.BigInteger(), nullable=True),
        sa.Column("completion_updated_at", mssql.DATETIME2(), nullable=True),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", mssql.DATETIME2(), nullable=True),
        sa.Column("updated_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_project_checkpoint_answers"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_project_checkpoint_answers_project_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"], ["discovery_checkpoints.id"],
            name="fk_project_checkpoint_answers_checkpoint_id",
        ),
        sa.ForeignKeyConstraint(
            ["completion_updated_by_run_id"], ["agent_runs.id"],
            name="fk_project_checkpoint_answers_completion_run_id",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"], ["users.id"],
            name="fk_project_checkpoint_answers_approved_by",
        ),
        sa.UniqueConstraint("project_id", "checkpoint_id", name="uq_project_checkpoint_answers_project_checkpoint"),
        sa.CheckConstraint(
            "completion_score IS NULL OR (completion_score >= 0 AND completion_score <= 1)",
            name="ck_project_checkpoint_answers_completion_score",
        ),
    )
    op.create_index("ix_project_checkpoint_answers_checkpoint_id", "project_checkpoint_answers", ["checkpoint_id"])
    op.create_index("ix_project_checkpoint_answers_status", "project_checkpoint_answers", ["status"])

    op.create_table(
        "checkpoint_answer_proposals",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("current_answer_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=False),
        sa.Column("base_version_number", sa.Integer(), nullable=False),
        sa.Column("proposed_answer", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("completion_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("status", sa.NVARCHAR(length=20), server_default="PENDING", nullable=False),
        sa.Column("superseded_by_proposal_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.Column("reviewed_at", mssql.DATETIME2(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_checkpoint_answer_proposals"),
        sa.ForeignKeyConstraint(
            ["current_answer_id"], ["project_checkpoint_answers.id"],
            name="fk_checkpoint_answer_proposals_current_answer_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"], ["agent_runs.id"],
            name="fk_checkpoint_answer_proposals_agent_run_id",
        ),
        # Self-reference with NO ACTION, so superseding never cascades into other proposals.
        sa.ForeignKeyConstraint(
            ["superseded_by_proposal_id"], ["checkpoint_answer_proposals.id"],
            name="fk_checkpoint_answer_proposals_superseded_by",
        ),
        sa.CheckConstraint(
            "base_version_number >= 0",
            name="ck_checkpoint_answer_proposals_base_version_number",
        ),
        sa.CheckConstraint(
            "completion_score IS NULL OR (completion_score >= 0 AND completion_score <= 1)",
            name="ck_checkpoint_answer_proposals_completion_score",
        ),
    )
    op.create_index("ix_checkpoint_answer_proposals_current_answer_id", "checkpoint_answer_proposals", ["current_answer_id"])
    op.create_index("ix_checkpoint_answer_proposals_agent_run_id", "checkpoint_answer_proposals", ["agent_run_id"])
    op.create_index("ix_checkpoint_answer_proposals_status", "checkpoint_answer_proposals", ["status"])
    op.create_index(
        "ix_checkpoint_answer_proposals_superseded_by_proposal_id",
        "checkpoint_answer_proposals",
        ["superseded_by_proposal_id"],
        mssql_where=sa.text("superseded_by_proposal_id IS NOT NULL"),
    )

    op.create_table(
        "proposal_evidence",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("proposal_id", sa.BigInteger(), nullable=False),
        sa.Column("context_chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("mapping_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_proposal_evidence"),
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["checkpoint_answer_proposals.id"],
            name="fk_proposal_evidence_proposal_id",
            ondelete="CASCADE",
        ),
        # NO ACTION: the chunks, mappings and runs are not deleted by proposal deletion.
        sa.ForeignKeyConstraint(
            ["context_chunk_id"], ["context_chunks.id"],
            name="fk_proposal_evidence_context_chunk_id",
        ),
        sa.ForeignKeyConstraint(
            ["mapping_id"], ["context_checkpoint_mappings.id"],
            name="fk_proposal_evidence_mapping_id",
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"], ["agent_runs.id"],
            name="fk_proposal_evidence_agent_run_id",
        ),
        sa.UniqueConstraint("proposal_id", "mapping_id", name="uq_proposal_evidence_proposal_mapping"),
    )
    op.create_index("ix_proposal_evidence_proposal_id", "proposal_evidence", ["proposal_id"])
    op.create_index("ix_proposal_evidence_context_chunk_id", "proposal_evidence", ["context_chunk_id"])
    op.create_index("ix_proposal_evidence_mapping_id", "proposal_evidence", ["mapping_id"])
    op.create_index("ix_proposal_evidence_agent_run_id", "proposal_evidence", ["agent_run_id"])

    op.create_table(
        "checkpoint_answer_versions",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("checkpoint_answer_id", sa.BigInteger(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("source", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("proposal_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_checkpoint_answer_versions"),
        sa.ForeignKeyConstraint(
            ["checkpoint_answer_id"], ["project_checkpoint_answers.id"],
            name="fk_checkpoint_answer_versions_answer_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["checkpoint_answer_proposals.id"],
            name="fk_checkpoint_answer_versions_proposal_id",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"],
            name="fk_checkpoint_answer_versions_created_by",
        ),
        sa.UniqueConstraint(
            "checkpoint_answer_id", "version_number",
            name="uq_checkpoint_answer_versions_answer_version",
        ),
        sa.CheckConstraint("version_number >= 1", name="ck_checkpoint_answer_versions_version_number"),
        sa.CheckConstraint("source IN ('AI_PROPOSAL', 'MANUAL')", name="ck_checkpoint_answer_versions_source"),
        sa.CheckConstraint(
            "source <> 'AI_PROPOSAL' OR proposal_id IS NOT NULL",
            name="ck_checkpoint_answer_versions_proposal_required",
        ),
    )
    op.create_index("ix_checkpoint_answer_versions_proposal_id", "checkpoint_answer_versions", ["proposal_id"])
    op.create_index("ix_checkpoint_answer_versions_created_by", "checkpoint_answer_versions", ["created_by"])

    op.create_table(
        "checkpoint_answer_evidence",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("checkpoint_answer_id", sa.BigInteger(), nullable=False),
        sa.Column("answer_version_id", sa.BigInteger(), nullable=False),
        sa.Column("context_chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_checkpoint_answer_evidence"),
        # NO ACTION: the version cascade already removes these rows, so a second path would be rejected.
        sa.ForeignKeyConstraint(
            ["checkpoint_answer_id"], ["project_checkpoint_answers.id"],
            name="fk_checkpoint_answer_evidence_answer_id",
        ),
        sa.ForeignKeyConstraint(
            ["answer_version_id"], ["checkpoint_answer_versions.id"],
            name="fk_checkpoint_answer_evidence_version_id",
            ondelete="CASCADE",
        ),
        # NO ACTION: original document chunks are never deleted by answer deletion.
        sa.ForeignKeyConstraint(
            ["context_chunk_id"], ["context_chunks.id"],
            name="fk_checkpoint_answer_evidence_context_chunk_id",
        ),
        sa.UniqueConstraint(
            "answer_version_id", "context_chunk_id",
            name="uq_checkpoint_answer_evidence_version_chunk",
        ),
    )
    op.create_index(
        "ix_checkpoint_answer_evidence_checkpoint_answer_id", "checkpoint_answer_evidence", ["checkpoint_answer_id"]
    )
    op.create_index("ix_checkpoint_answer_evidence_answer_version_id", "checkpoint_answer_evidence", ["answer_version_id"])
    op.create_index("ix_checkpoint_answer_evidence_context_chunk_id", "checkpoint_answer_evidence", ["context_chunk_id"])


def downgrade() -> None:
    # Reverse dependency order: tables that refer to others are dropped first.
    op.drop_table("checkpoint_answer_evidence")
    op.drop_table("checkpoint_answer_versions")
    op.drop_table("proposal_evidence")
    op.drop_table("checkpoint_answer_proposals")
    op.drop_table("project_checkpoint_answers")
