"""Checkpoint answer rules: statuses, agent fields on proposals, one pending proposal.

Revision ID: 013_checkpoint_answer_rules
Revises: 012_brd_artifact_tables

- Answer and proposal statuses are restricted to the values the code uses.
- Proposals keep the agent's own status, is_completed, missing information and questions.
- proposal_evidence stores the agent's reason per chunk. The run comes from the proposal.
- At most one PENDING proposal per answer row.
- agent_runs accepts run_type 'pillar_answer' and keeps the BRD run types added by 012.

The answer and proposal tables must be empty. The upgrade stops otherwise.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013_checkpoint_answer_rules"
down_revision: str | None = "012_brd_artifact_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Must match the list in 012_brd_artifact_tables, plus pillar_answer.
RUN_TYPES_AFTER_BRD = ("checkpoint_mapping", "user_discovery", "brd_generate", "brd_regenerate", "brd_clarify")
RUN_TYPES_THIS_REVISION = RUN_TYPES_AFTER_BRD + ("pillar_answer",)

PROPOSAL_COLUMNS = ("agent_status", "is_completed", "missing_information", "clarification_questions")
PROPOSAL_CHECKS = (
    "ck_checkpoint_answer_proposals_status",
    "ck_checkpoint_answer_proposals_agent_status",
    "ck_checkpoint_answer_proposals_is_completed",
    "ck_checkpoint_answer_proposals_missing_json",
    "ck_checkpoint_answer_proposals_questions_json",
)


def _run_type_check(values: tuple[str, ...]) -> str:
    return "run_type IN (" + ", ".join(f"'{value}'" for value in values) + ")"


def _drop_default_constraint(table: str, column: str) -> None:
    """SQL Server names default constraints itself. Find the name, then drop it before the column."""
    op.execute(
        f"""
        DECLARE @name sysname = (
            SELECT dc.name FROM sys.default_constraints dc
            JOIN sys.columns c ON c.default_object_id = dc.object_id
            WHERE dc.parent_object_id = OBJECT_ID('{table}') AND c.name = '{column}'
        );
        IF @name IS NOT NULL EXEC('ALTER TABLE {table} DROP CONSTRAINT ' + @name);
        """
    )


def _count(table: str) -> int:
    return op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()


def upgrade() -> None:
    for table in ("project_checkpoint_answers", "checkpoint_answer_proposals"):
        rows = _count(table)
        if rows:
            raise RuntimeError(f"{table} has {rows} rows. Migrate its data before running 013.")

    op.create_check_constraint(
        "ck_project_checkpoint_answers_status",
        "project_checkpoint_answers",
        "status IN ('NOT_STARTED', 'PENDING_REVIEW', 'APPROVED')",
    )

    op.add_column(
        "checkpoint_answer_proposals",
        sa.Column("agent_status", sa.NVARCHAR(length=30), server_default="Needs Clarification", nullable=False),
    )
    op.add_column(
        "checkpoint_answer_proposals",
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "checkpoint_answer_proposals",
        sa.Column("missing_information", sa.NVARCHAR(length="max"), nullable=True),
    )
    op.add_column(
        "checkpoint_answer_proposals",
        sa.Column("clarification_questions", sa.NVARCHAR(length="max"), nullable=True),
    )
    op.create_check_constraint(
        "ck_checkpoint_answer_proposals_status",
        "checkpoint_answer_proposals",
        "status IN ('PENDING', 'APPROVED', 'SUPERSEDED')",
    )
    op.create_check_constraint(
        "ck_checkpoint_answer_proposals_agent_status",
        "checkpoint_answer_proposals",
        "agent_status IN ('Pending Approval', 'Needs Clarification')",
    )
    op.create_check_constraint(
        "ck_checkpoint_answer_proposals_is_completed",
        "checkpoint_answer_proposals",
        "(is_completed = 1 AND agent_status = 'Pending Approval') "
        "OR (is_completed = 0 AND agent_status = 'Needs Clarification')",
    )
    op.create_check_constraint(
        "ck_checkpoint_answer_proposals_missing_json",
        "checkpoint_answer_proposals",
        "missing_information IS NULL OR ISJSON(missing_information) = 1",
    )
    op.create_check_constraint(
        "ck_checkpoint_answer_proposals_questions_json",
        "checkpoint_answer_proposals",
        "clarification_questions IS NULL OR ISJSON(clarification_questions) = 1",
    )

    op.create_index(
        "ux_checkpoint_answer_proposals_one_pending",
        "checkpoint_answer_proposals",
        ["current_answer_id"],
        unique=True,
        mssql_where=sa.text("status = 'PENDING'"),
    )

    op.drop_index("ix_proposal_evidence_agent_run_id", table_name="proposal_evidence")
    op.drop_constraint("fk_proposal_evidence_agent_run_id", "proposal_evidence", type_="foreignkey")
    op.drop_column("proposal_evidence", "agent_run_id")
    op.add_column("proposal_evidence", sa.Column("reason", sa.NVARCHAR(length="max"), nullable=True))

    op.drop_constraint("ck_agent_runs_run_type", "agent_runs", type_="check")
    op.create_check_constraint("ck_agent_runs_run_type", "agent_runs", _run_type_check(RUN_TYPES_THIS_REVISION))


def downgrade() -> None:
    if _count("agent_runs") and op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM agent_runs WHERE run_type = 'pillar_answer'")
    ).scalar():
        raise RuntimeError("Pillar answer runs exist. They cannot be removed by this downgrade.")

    op.drop_constraint("ck_agent_runs_run_type", "agent_runs", type_="check")
    op.create_check_constraint("ck_agent_runs_run_type", "agent_runs", _run_type_check(RUN_TYPES_AFTER_BRD))

    op.drop_column("proposal_evidence", "reason")
    op.add_column("proposal_evidence", sa.Column("agent_run_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_proposal_evidence_agent_run_id", "proposal_evidence", "agent_runs", ["agent_run_id"], ["id"]
    )
    op.create_index("ix_proposal_evidence_agent_run_id", "proposal_evidence", ["agent_run_id"])

    op.drop_index("ux_checkpoint_answer_proposals_one_pending", table_name="checkpoint_answer_proposals")
    for name in PROPOSAL_CHECKS:
        op.drop_constraint(name, "checkpoint_answer_proposals", type_="check")
    for column in ("agent_status", "is_completed"):
        _drop_default_constraint("checkpoint_answer_proposals", column)
    for column in PROPOSAL_COLUMNS:
        op.drop_column("checkpoint_answer_proposals", column)

    op.drop_constraint("ck_project_checkpoint_answers_status", "project_checkpoint_answers", type_="check")