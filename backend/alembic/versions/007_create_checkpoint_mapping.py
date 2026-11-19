"""Create checkpoint mapping tables and seed discovery reference data.

Revision ID: 007_create_checkpoint_mapping
Revises: 006_create_context_chunks

Work order 7. Pillars and checkpoints are fixed reference data, so their IDs are
supplied explicitly (no identity column). Mappings link a project's chunk to a
checkpoint, and every agent batch is recorded in agent_runs.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "007_create_checkpoint_mapping"
down_revision: str | None = "006_create_context_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PILLARS = [
    {
        "id": 1,
        "code": "USER",
        "name": "User Discovery",
        "description": (
            "User Discovery captures who the people in the workflow are, how they work day to day, "
            "what frustrates them, and what they need from the solution. It is grounded in the experience "
            "of the people who do the work, not in system design or data structure. "
            "Covers: the users and their roles and work; the workflows and handoffs between people; "
            "the problems and frustrations they experience; the requirements and needs they have of the "
            "system or process; the stakeholders who influence, approve, or depend on the workflow. "
            "Does not cover how data is stored or how systems connect."
        ),
    },
    {
        "id": 2,
        "code": "DATA",
        "name": "Data Discovery",
        "description": (
            "Data Discovery establishes what data exists, where it comes from, how trustworthy it is, who is "
            "accountable for it, and what rules govern it. "
            "Covers: the sources where data originates; the quality of the data, including documented missing, "
            "incorrect, or inconsistent values; the owners and maintainers of each dataset; the flow and "
            "transformation of data between sources and consumers; the privacy, retention, and data-handling "
            "obligations that apply. Does not cover the applications that host the data or the interfaces "
            "that carry it."
        ),
    },
    {
        "id": 3,
        "code": "TECH",
        "name": "Tech Discovery",
        "description": (
            "Tech Discovery documents the technology landscape the solution must work within. It captures what "
            "already exists, how systems connect, what limits them, how they are secured, and where they are "
            "hosted. "
            "Covers: the existing systems, platforms, and applications and their business purposes; the verified "
            "integrations, APIs, and system-to-system interactions; the technical constraints; the security "
            "mechanisms, access practices, and documented control requirements; the infrastructure, hosting, "
            "environments, and deployment approaches. Does not cover the business workflow or the meaning of "
            "the data."
        ),
    },
]


def _cp(id_, pillar_id, code, name, description, question, why, priority, sort_order, feeds):
    return {
        "id": id_,
        "pillar_id": pillar_id,
        "code": code,
        "name": name,
        "description": description,
        "question": question,
        "why_it_matters": why,
        "priority": priority,
        "readiness_required_count": 1,
        "feeds_details": feeds,
        "config_json": "{}",
        "sort_order": sort_order,
        "is_active": True,
    }


USER_AGENT = "User Discovery Agent"
DATA_AGENT = "Data Discovery Agent"
TECH_AGENT = "Tech Discovery Agent"

CHECKPOINTS = [
    _cp(401, 1, "USER01", "Persona and Roles",
        "Identify the people who use or influence the workflow and the roles they perform.",
        "Who uses the system and what roles do they perform?",
        "Defines who the solution must serve.", "high", 1, USER_AGENT),
    _cp(402, 1, "USER02", "Workflows and Processes",
        "Capture how users currently complete their tasks, step by step, including handoffs between people.",
        "How do users currently complete their tasks?",
        "Shows how work actually gets done today.", "high", 2, USER_AGENT),
    _cp(403, 1, "USER03", "Pain Points",
        "Identify frustrations, delays and difficulties experienced by users.",
        "What problems or frustrations do users face?",
        "Identifies opportunities to improve user experience.", "high", 3, USER_AGENT),
    _cp(404, 1, "USER04", "User Requirements",
        "Capture documented needs and expectations users have of the system or process.",
        "What do users need the system to do?",
        "Turns user needs into requirements for the solution.", "high", 4, USER_AGENT),
    _cp(405, 1, "USER05", "Stakeholders",
        "Identify people outside the daily users who influence, approve or depend on the workflow, and their interests.",
        "Who else is affected by or involved in decisions about this workflow?",
        "Reveals sign-off authority and hidden dependencies.", "medium", 5, USER_AGENT),
    _cp(201, 2, "DATA01", "Data Sources",
        "Identify the systems, files, databases or applications where the data originates.",
        "Where does the data originate?",
        "Establishes what data exists and where it comes from.", "high", 1, DATA_AGENT),
    _cp(202, 2, "DATA02", "Data Quality",
        "Identify documented missing, incorrect, incomplete, duplicated or inconsistent data.",
        "What data problems are documented?",
        "Shows how far the data can be trusted.", "high", 2, DATA_AGENT),
    _cp(203, 2, "DATA03", "Data Ownership",
        "Identify who owns, maintains or is accountable for each dataset.",
        "Who owns and maintains the data?",
        "Identifies who can approve data decisions and fixes.", "medium", 3, DATA_AGENT),
    _cp(204, 2, "DATA04", "Data Flows",
        "Capture documented movement, exchange and transformation of data across sources and consumers.",
        "How does data move and transform between sources and outputs?",
        "Provides lineage and flow understanding.", "high", 4, DATA_AGENT),
    _cp(205, 2, "DATA05", "Privacy and Retention",
        "Identify documented personal/confidential data use, data privacy obligations and retention requirements.",
        "What privacy, retention or data-handling obligations apply?",
        "Captures data governance obligations without inventing rules.", "high", 5, DATA_AGENT),
    _cp(301, 3, "TECH01", "Existing Systems",
        "Identify current software products, platforms, applications and their business purposes.",
        "What existing systems support the workflow?",
        "Establishes technology landscape.", "high", 1, TECH_AGENT),
    _cp(302, 3, "TECH02", "Integrations",
        "Identify verified interfaces, APIs and system interactions including purpose and exchanged data.",
        "Which systems communicate and how?",
        "Identifies integration touchpoints.", "high", 2, TECH_AGENT),
    _cp(303, 3, "TECH03", "Technical Constraints",
        "Identify explicit limits or restrictions in platforms, architecture, tools or performance.",
        "What technical constraints limit the desired solution?",
        "Guides feasibility and architecture.", "high", 3, TECH_AGENT),
    _cp(304, 3, "TECH04", "Security",
        "Identify existing security mechanisms, access practices, authentication and verified control requirements.",
        "What security controls or access practices are documented?",
        "Highlights security needs without inventing controls.", "high", 4, TECH_AGENT),
    _cp(305, 3, "TECH05", "Infrastructure and Deployment",
        "Identify hosting, environments, deployment approaches, infrastructure and runtime needs.",
        "What environments, infrastructure or deployment requirements are documented?",
        "Supports deployment planning.", "high", 5, TECH_AGENT),
]


def upgrade() -> None:
    pillars = op.create_table(
        "discovery_pillars",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("code", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("description", sa.NVARCHAR(length="max"), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_discovery_pillars"),
        sa.UniqueConstraint("code", name="uq_discovery_pillars_code"),
    )

    checkpoints = op.create_table(
        "discovery_checkpoints",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("pillar_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("name", sa.NVARCHAR(length=255), nullable=False),
        sa.Column("description", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("question", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("why_it_matters", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("priority", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("readiness_required_count", sa.Integer(), nullable=False),
        sa.Column("feeds_details", sa.NVARCHAR(length=255), nullable=True),
        sa.Column("config_json", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_discovery_checkpoints"),
        sa.UniqueConstraint("code", name="uq_discovery_checkpoints_code"),
        sa.ForeignKeyConstraint(
            ["pillar_id"], ["discovery_pillars.id"],
            name="fk_discovery_checkpoints_pillar_id",
        ),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("run_type", sa.NVARCHAR(length=50), server_default="checkpoint_mapping", nullable=False),
        sa.Column("status", sa.NVARCHAR(length=20), nullable=False),
        sa.Column("model", sa.NVARCHAR(length=100), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("raw_output", sa.NVARCHAR(length="max"), nullable=True),
        sa.Column("error_message", sa.NVARCHAR(length=1000), nullable=True),
        sa.Column("started_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.Column("completed_at", mssql.DATETIME2(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_agent_runs"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_agent_runs_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="ck_agent_runs_status"),
    )
    op.create_index("ix_agent_runs_project_id_status", "agent_runs", ["project_id", "status"])

    op.create_table(
        "agent_run_chunks",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=False),
        sa.Column("context_chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_agent_run_chunks"),
        sa.ForeignKeyConstraint(
            ["agent_run_id"], ["agent_runs.id"],
            name="fk_agent_run_chunks_agent_run_id",
            ondelete="CASCADE",
        ),
        # NO ACTION: avoids a second cascade path from projects to this table.
        sa.ForeignKeyConstraint(
            ["context_chunk_id"], ["context_chunks.id"],
            name="fk_agent_run_chunks_context_chunk_id",
        ),
        sa.UniqueConstraint("agent_run_id", "context_chunk_id", name="uq_agent_run_chunks_run_chunk"),
    )
    op.create_index("ix_agent_run_chunks_context_chunk_id", "agent_run_chunks", ["context_chunk_id"])

    op.create_table(
        "context_checkpoint_mappings",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("context_chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("checkpoint_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=False),
        # No FK yet: there is no agents table in this step. Add it when agents are built.
        sa.Column("mapped_by_agent_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.Column("deactivated_at", mssql.DATETIME2(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_context_checkpoint_mappings"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_mappings_project_id_projects",
            ondelete="CASCADE",
        ),
        # NO ACTION on these three avoids multiple cascade paths into the mapping table.
        sa.ForeignKeyConstraint(
            ["context_chunk_id"], ["context_chunks.id"],
            name="fk_mappings_context_chunk_id",
        ),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"], ["discovery_checkpoints.id"],
            name="fk_mappings_checkpoint_id",
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"], ["agent_runs.id"],
            name="fk_mappings_agent_run_id",
        ),
    )
    # One active mapping per project, chunk and checkpoint. Inactive history rows are not limited.
    op.create_index(
        "uq_mappings_active_project_chunk_checkpoint",
        "context_checkpoint_mappings",
        ["project_id", "context_chunk_id", "checkpoint_id"],
        unique=True,
        mssql_where=sa.text("is_active = 1"),
    )
    op.create_index(
        "ix_mappings_project_id_chunk",
        "context_checkpoint_mappings",
        ["project_id", "context_chunk_id"],
    )

    op.create_table(
        "mapping_evidence",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("mapping_id", sa.BigInteger(), nullable=False),
        sa.Column("evidence_quote", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("reason", sa.NVARCHAR(length="max"), nullable=False),
        sa.Column("created_at", mssql.DATETIME2(), server_default=sa.text("SYSUTCDATETIME()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_mapping_evidence"),
        sa.ForeignKeyConstraint(
            ["mapping_id"], ["context_checkpoint_mappings.id"],
            name="fk_mapping_evidence_mapping_id",
            ondelete="CASCADE",
        ),
    )

    op.bulk_insert(pillars, PILLARS)
    op.bulk_insert(checkpoints, CHECKPOINTS)


def downgrade() -> None:
    op.drop_table("mapping_evidence")
    op.drop_table("context_checkpoint_mappings")
    op.drop_table("agent_run_chunks")
    op.drop_table("agent_runs")
    op.drop_table("discovery_checkpoints")
    op.drop_table("discovery_pillars")
