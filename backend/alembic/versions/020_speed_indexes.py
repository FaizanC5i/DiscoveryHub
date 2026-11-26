"""Speed: indexes on foreign-key columns that lookups, joins and deletes use but nothing indexed.

Revision ID: 020_speed_indexes
Revises: 019_prd_artifact

- mapping_evidence(mapping_id): suggested by Azure SQL's missing-index report; every mapping's
  evidence is read by mapping_id (INCLUDE: the columns read with it, so no extra lookup).
- context_checkpoint_mappings(context_chunk_id): deleting or re-mapping a chunk finds its
  mappings by chunk; the existing (project_id, context_chunk_id) index needs the project too.
- artifact_section_proposals(agent_run_id): proposals written by one BRD/PRD run.

Small today (hundreds of rows), but these grow with every upload and agent run.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "020_speed_indexes"
down_revision: str | None = "019_prd_artifact"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_mapping_evidence_mapping_id",
        "mapping_evidence",
        ["mapping_id"],
        mssql_include=["evidence_quote", "reason", "evidence_start_char", "evidence_end_char"],
    )
    op.create_index("ix_context_checkpoint_mappings_chunk", "context_checkpoint_mappings", ["context_chunk_id"])
    op.create_index("ix_artifact_section_proposals_agent_run", "artifact_section_proposals", ["agent_run_id"])


def downgrade() -> None:
    op.drop_index("ix_artifact_section_proposals_agent_run", table_name="artifact_section_proposals")
    op.drop_index("ix_context_checkpoint_mappings_chunk", table_name="context_checkpoint_mappings")
    op.drop_index("ix_mapping_evidence_mapping_id", table_name="mapping_evidence")
