"""Create the BRD (artifact generation) tables, seed the BRD template and log BRD runs in agent_runs.

Revision ID: 012_brd_artifact_tables
Revises: 011_manual_note_sources

Design: "DiscoveryHub - DB Design (with BRD) v3", PART 12. The BRD is written from APPROVED
project_checkpoint_answers, not from uploaded files.

Tables (creation order follows the foreign keys):
- artifact_types                   kinds of document (BRD first), each linked to its agent
- artifact_sections                the template: 14 BRD sections
- artifact_section_checkpoints     which checkpoint answers feed which section
- project_artifacts                one BRD per project (document status, version)
- project_artifact_sections        the BRD's 14 sections for that project (current content)
- artifact_section_proposals       what the agent wrote, or why it could not, waiting for review
- artifact_section_clarifications  the user's answers to the agent's questions
- project_artifact_versions        frozen JSON snapshot of every approved BRD

agent_runs already has run_type (migration 009), so it is not added again. Its check is widened
with brd_generate / brd_regenerate / brd_clarify, and two nullable links say which BRD and which
section a run worked on.

Cascade graph (SQL Server allows one cascade path into each table, so the rest use NO ACTION):
- projects -> project_artifacts -> project_artifact_sections -> artifact_section_proposals
- project_artifact_sections -> artifact_section_clarifications
- project_artifacts -> project_artifact_versions
- artifact_sections -> artifact_section_checkpoints
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "012_brd_artifact_tables"
down_revision: str | None = "011_manual_note_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UTC_NOW = sa.text("SYSUTCDATETIME()")

OLD_RUN_TYPES = "run_type IN ('checkpoint_mapping', 'user_discovery')"
NEW_RUN_TYPES = (
    "run_type IN ('checkpoint_mapping', 'user_discovery', 'brd_generate', 'brd_regenerate', 'brd_clarify')"
)

# (sort_order, section_key, title, what the section must answer, checkpoint codes that feed it)
# An empty tuple means the section is written from every approved answer (Assumptions).
BRD_SECTIONS = [
    (1, "business_objectives", "Business Objectives",
     "Why the project exists and the business outcomes it must achieve.", ("USER03", "USER04", "USER05")),
    (2, "users_stakeholders", "Users & Stakeholders",
     "Who uses the solution, their roles, and who has a stake in it.", ("USER01", "USER05")),
    (3, "current_state", "Current State",
     "How the work is done today: processes, systems and data in use.", ("USER02", "USER03", "TECH01", "DATA01")),
    (4, "scope", "Scope",
     "What the solution will cover.", ("USER02", "USER04")),
    (5, "functional_requirements", "Functional Requirements",
     "What the solution must do, written as testable requirements.", ("USER02", "USER04")),
    (6, "out_of_scope", "Out of Scope",
     "What the solution will explicitly not cover.", ("USER04",)),
    (7, "business_rules", "Business Rules",
     "Rules and policies the solution must follow.", ("USER02", "DATA02", "DATA05")),
    (8, "constraints", "Constraints",
     "Technical, time, budget or organisational limits.", ("TECH03", "TECH05")),
    (9, "assumptions", "Assumptions",
     "What is taken as true without full confirmation.", ()),
    (10, "dependencies", "Dependencies",
     "Systems, data, teams or decisions the project depends on.", ("TECH02", "DATA01", "DATA03", "TECH05")),
    (11, "success_criteria", "Success Criteria",
     "How success will be measured.", ("USER03", "USER04")),
    (12, "risks", "Risks",
     "What could go wrong, its impact, and how to reduce it.", ("USER03", "DATA02", "TECH03", "TECH04")),
    (13, "integrations", "Integrations",
     "Systems the solution connects to and the data exchanged.", ("TECH01", "TECH02", "DATA04")),
    (14, "security_compliance", "Security & Compliance",
     "Security, privacy, retention and regulatory requirements.", ("TECH04", "DATA03", "DATA05")),
]


def _id() -> sa.Column:
    return sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False)


def _created_at() -> sa.Column:
    return sa.Column("created_at", mssql.DATETIME2(), server_default=UTC_NOW, nullable=False)


def _sql(value: str) -> str:
    return "N'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    op.create_table(
        "artifact_types",
        _id(),
        sa.Column("code", sa.NVARCHAR(length=50), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=150), nullable=False),
        sa.Column("description", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("agent_id", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_types"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_artifact_types_agent_id"),
        sa.UniqueConstraint("code", name="uq_artifact_types_code"),
    )

    op.create_table(
        "artifact_sections",
        _id(),
        sa.Column("artifact_type_id", sa.BigInteger(), nullable=False),
        sa.Column("section_key", sa.NVARCHAR(length=50), nullable=False),
        sa.Column("title", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("prompt", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("fallback_questions", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_sections"),
        sa.ForeignKeyConstraint(
            ["artifact_type_id"], ["artifact_types.id"], name="fk_artifact_sections_artifact_type_id"
        ),
        sa.UniqueConstraint("artifact_type_id", "section_key", name="uq_artifact_sections_type_key"),
        sa.CheckConstraint(
            "fallback_questions IS NULL OR ISJSON(fallback_questions) = 1",
            name="ck_artifact_sections_fallback_questions_json",
        ),
    )

    op.create_table(
        "artifact_section_checkpoints",
        _id(),
        sa.Column("artifact_section_id", sa.BigInteger(), nullable=False),
        sa.Column("checkpoint_id", sa.BigInteger(), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_section_checkpoints"),
        sa.ForeignKeyConstraint(
            ["artifact_section_id"], ["artifact_sections.id"], ondelete="CASCADE",
            name="fk_artifact_section_checkpoints_section_id",
        ),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"], ["discovery_checkpoints.id"], name="fk_artifact_section_checkpoints_checkpoint_id"
        ),
        sa.UniqueConstraint("artifact_section_id", "checkpoint_id", name="uq_artifact_section_checkpoints"),
    )
    op.create_index(
        "ix_artifact_section_checkpoints_checkpoint_id", "artifact_section_checkpoints", ["checkpoint_id"]
    )

    op.create_table(
        "project_artifacts",
        _id(),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("artifact_type_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.NVARCHAR(length=30), server_default="NOT_STARTED", nullable=False),
        sa.Column("current_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("instructions", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", mssql.DATETIME2(), nullable=True),
        _created_at(),
        sa.Column("updated_at", mssql.DATETIME2(), server_default=UTC_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_project_artifacts"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_project_artifacts_project_id"
        ),
        sa.ForeignKeyConstraint(
            ["artifact_type_id"], ["artifact_types.id"], name="fk_project_artifacts_artifact_type_id"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_project_artifacts_created_by"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_project_artifacts_approved_by"),
        sa.UniqueConstraint("project_id", "artifact_type_id", name="uq_project_artifacts_project_type"),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'DRAFT', 'IN_REVIEW', 'APPROVED')", name="ck_project_artifacts_status"
        ),
        sa.CheckConstraint("current_version >= 0", name="ck_project_artifacts_current_version"),
    )

    op.create_table(
        "project_artifact_sections",
        _id(),
        sa.Column("project_artifact_id", sa.BigInteger(), nullable=False),
        sa.Column("artifact_section_id", sa.BigInteger(), nullable=False),
        sa.Column("current_content", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("status", sa.NVARCHAR(length=30), server_default="NOT_STARTED", nullable=False),
        sa.Column("source", sa.NVARCHAR(length=20), nullable=True),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", mssql.DATETIME2(), nullable=True),
        _created_at(),
        sa.Column("updated_at", mssql.DATETIME2(), server_default=UTC_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_project_artifact_sections"),
        sa.ForeignKeyConstraint(
            ["project_artifact_id"], ["project_artifacts.id"], ondelete="CASCADE",
            name="fk_project_artifact_sections_artifact_id",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_section_id"], ["artifact_sections.id"], name="fk_project_artifact_sections_section_id"
        ),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_project_artifact_sections_approved_by"),
        sa.UniqueConstraint(
            "project_artifact_id", "artifact_section_id", name="uq_project_artifact_sections_artifact_section"
        ),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'DRAFT', 'PENDING_REVIEW', 'NEEDS_CLARIFICATION', 'APPROVED')",
            name="ck_project_artifact_sections_status",
        ),
        sa.CheckConstraint(
            "source IS NULL OR source IN ('AGENT', 'USER')", name="ck_project_artifact_sections_source"
        ),
    )

    op.create_table(
        "artifact_section_proposals",
        _id(),
        sa.Column("project_artifact_section_id", sa.BigInteger(), nullable=False),
        sa.Column("proposed_content", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("status", sa.NVARCHAR(length=30), server_default="PENDING", nullable=False),
        sa.Column("missing_reason", sa.NVARCHAR(length=1000), nullable=True),
        sa.Column("clarification_questions", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("generated_by_agent_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", mssql.DATETIME2(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_section_proposals"),
        sa.ForeignKeyConstraint(
            ["project_artifact_section_id"], ["project_artifact_sections.id"], ondelete="CASCADE",
            name="fk_artifact_section_proposals_section_id",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by_agent_id"], ["agents.id"], name="fk_artifact_section_proposals_agent_id"
        ),
        # NO ACTION: the project cascade already reaches agent_runs.
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_artifact_section_proposals_run_id"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], name="fk_artifact_section_proposals_reviewed_by"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_CLARIFICATION', 'SUPERSEDED')",
            name="ck_artifact_section_proposals_status",
        ),
        sa.CheckConstraint(
            "clarification_questions IS NULL OR ISJSON(clarification_questions) = 1",
            name="ck_artifact_section_proposals_questions_json",
        ),
    )
    op.create_index(
        "ix_artifact_section_proposals_section_status",
        "artifact_section_proposals",
        ["project_artifact_section_id", "status"],
    )

    op.create_table(
        "artifact_section_clarifications",
        _id(),
        sa.Column("project_artifact_section_id", sa.BigInteger(), nullable=False),
        sa.Column("proposal_id", sa.BigInteger(), nullable=True),
        sa.Column("question", sa.NVARCHAR(length=1000), nullable=False),
        sa.Column("answer", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("answered_by", sa.BigInteger(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_section_clarifications"),
        sa.ForeignKeyConstraint(
            ["project_artifact_section_id"], ["project_artifact_sections.id"], ondelete="CASCADE",
            name="fk_artifact_section_clarifications_section_id",
        ),
        # NO ACTION: the section cascade already reaches both tables.
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["artifact_section_proposals.id"], name="fk_artifact_section_clarifications_proposal_id"
        ),
        sa.ForeignKeyConstraint(["answered_by"], ["users.id"], name="fk_artifact_section_clarifications_answered_by"),
    )
    op.create_index(
        "ix_artifact_section_clarifications_section_id",
        "artifact_section_clarifications",
        ["project_artifact_section_id"],
    )

    op.create_table(
        "project_artifact_versions",
        _id(),
        sa.Column("project_artifact_id", sa.BigInteger(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", mssql.DATETIME2(), server_default=UTC_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_project_artifact_versions"),
        sa.ForeignKeyConstraint(
            ["project_artifact_id"], ["project_artifacts.id"], ondelete="CASCADE",
            name="fk_project_artifact_versions_artifact_id",
        ),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_project_artifact_versions_approved_by"),
        sa.UniqueConstraint("project_artifact_id", "version_number", name="uq_project_artifact_versions"),
        sa.CheckConstraint("version_number >= 1", name="ck_project_artifact_versions_version_number"),
        sa.CheckConstraint("ISJSON(snapshot) = 1", name="ck_project_artifact_versions_snapshot_json"),
    )

    # agent_runs: log BRD runs too.
    op.add_column("agent_runs", sa.Column("project_artifact_id", sa.BigInteger(), nullable=True))
    op.add_column("agent_runs", sa.Column("project_artifact_section_id", sa.BigInteger(), nullable=True))
    # NO ACTION: the project cascade already reaches agent_runs.
    op.create_foreign_key(
        "fk_agent_runs_project_artifact_id", "agent_runs", "project_artifacts", ["project_artifact_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_agent_runs_project_artifact_section_id", "agent_runs", "project_artifact_sections",
        ["project_artifact_section_id"], ["id"],
    )
    op.create_index(
        "ix_agent_runs_project_artifact_id", "agent_runs", ["project_artifact_id"],
        mssql_where=sa.text("project_artifact_id IS NOT NULL"),
    )
    op.drop_constraint("ck_agent_runs_run_type", "agent_runs", type_="check")
    op.create_check_constraint("ck_agent_runs_run_type", "agent_runs", NEW_RUN_TYPES)

    # Seed: the BRD agent, the BRD type, its 14 sections and which checkpoints feed each section.
    op.execute(
        "IF NOT EXISTS (SELECT 1 FROM agents WHERE agent_code = 'BRD_AGENT') "
        "INSERT INTO agents (agent_code, name, pillar_id) VALUES ('BRD_AGENT', N'BRD Generation Agent', NULL)"
    )
    op.execute(
        "INSERT INTO artifact_types (code, name, description, agent_id) "
        "SELECT 'BRD', N'Business Requirements Document', "
        "N'Written from the approved discovery answers of the project.', id "
        "FROM agents WHERE agent_code = 'BRD_AGENT'"
    )
    for sort_order, key, title, prompt, codes in BRD_SECTIONS:
        op.execute(
            "INSERT INTO artifact_sections (artifact_type_id, section_key, title, prompt, sort_order) "
            f"SELECT id, {_sql(key)}, {_sql(title)}, {_sql(prompt)}, {sort_order} "
            "FROM artifact_types WHERE code = 'BRD'"
        )
        if codes:
            code_list = ", ".join(_sql(code) for code in codes)
            op.execute(
                "INSERT INTO artifact_section_checkpoints (artifact_section_id, checkpoint_id) "
                "SELECT s.id, c.id FROM artifact_sections s "
                "JOIN artifact_types t ON t.id = s.artifact_type_id AND t.code = 'BRD' "
                f"JOIN discovery_checkpoints c ON c.code IN ({code_list}) "
                f"WHERE s.section_key = {_sql(key)}"
            )


def downgrade() -> None:
    # Proposals point at BRD runs, so they go first. Then the BRD runs, which the old
    # run_type check would reject.
    op.drop_index("ix_artifact_section_clarifications_section_id", table_name="artifact_section_clarifications")
    op.drop_table("artifact_section_clarifications")
    op.drop_index("ix_artifact_section_proposals_section_status", table_name="artifact_section_proposals")
    op.drop_table("artifact_section_proposals")
    op.execute("DELETE FROM agent_runs WHERE run_type IN ('brd_generate', 'brd_regenerate', 'brd_clarify')")
    op.drop_constraint("ck_agent_runs_run_type", "agent_runs", type_="check")
    op.create_check_constraint("ck_agent_runs_run_type", "agent_runs", OLD_RUN_TYPES)
    op.drop_index("ix_agent_runs_project_artifact_id", table_name="agent_runs")
    op.drop_constraint("fk_agent_runs_project_artifact_section_id", "agent_runs", type_="foreignkey")
    op.drop_constraint("fk_agent_runs_project_artifact_id", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "project_artifact_section_id")
    op.drop_column("agent_runs", "project_artifact_id")

    op.drop_table("project_artifact_versions")
    op.drop_table("project_artifact_sections")
    op.drop_table("project_artifacts")
    op.drop_index("ix_artifact_section_checkpoints_checkpoint_id", table_name="artifact_section_checkpoints")
    op.drop_table("artifact_section_checkpoints")
    op.drop_table("artifact_sections")
    op.drop_table("artifact_types")
    op.execute("DELETE FROM agents WHERE agent_code = 'BRD_AGENT'")
