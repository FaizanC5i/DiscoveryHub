"""Update agent tables in place and add agent_run_checkpoints.

Revision ID: 009_rebuild_agent_tables
Revises: 008_mapping_agents_and_evidence

Nothing is dropped. Existing agents, agent runs and mappings keep their ids, so every
mapping still joins to its run and its agent.

- agents: seeds the three pillar agents. HELPER_AGENT is kept as it is.
- agent_runs: adds agent_id, batch_id, trigger_source_id, attempt_count and input_payload.
  Existing mapping runs are linked to the Helper Agent. User Discovery runs keep a NULL agent_id,
  because that agent has been removed.
- agent_run_checkpoints: new. Per-checkpoint results for a run. The Helper Agent never writes here.
- agent_run_chunks: adds mapping_id. The Helper Agent never writes here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "009_rebuild_agent_tables"
down_revision: str | None = "008_mapping_agents_and_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The pillar agents are looked up by pillar code, so no pillar id is hard-coded.
    op.execute(
        """
        INSERT INTO agents (agent_code, name, pillar_id)
        SELECT v.agent_code, v.name, p.id
        FROM (VALUES
            ('USER_AGENT', 'User Discovery Agent', 'USER'),
            ('DATA_AGENT', 'Data Discovery Agent', 'DATA'),
            ('TECH_AGENT', 'Tech Discovery Agent', 'TECH')
        ) AS v (agent_code, name, pillar_code)
        JOIN discovery_pillars p ON p.code = v.pillar_code
        WHERE NOT EXISTS (SELECT 1 FROM agents a WHERE a.agent_code = v.agent_code)
        """
    )

    op.add_column("agent_runs", sa.Column("agent_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_agent_runs_agent_id_agents", "agent_runs", "agents", ["agent_id"], ["id"])
    op.execute(
        """
        UPDATE r
        SET r.agent_id = h.id
        FROM agent_runs r
        CROSS JOIN (SELECT id FROM agents WHERE agent_code = 'HELPER_AGENT') h
        WHERE r.run_type = 'checkpoint_mapping' AND r.agent_id IS NULL
        """
    )
    op.create_index("ix_agent_runs_agent_id", "agent_runs", ["agent_id"])

    op.add_column("agent_runs", sa.Column("batch_id", sa.NVARCHAR(length=50), nullable=True))
    # Existing runs get a readable batch id built from their own id. New runs use the BATCH- format.
    op.execute("UPDATE agent_runs SET batch_id = CONCAT('LEGACY-', id) WHERE batch_id IS NULL")
    op.create_index("ix_agent_runs_batch_id", "agent_runs", ["batch_id"])

    # NO ACTION: the project delete already cascades through agent_runs, so a second cascade
    # path from context_sources would be rejected by SQL Server.
    op.add_column("agent_runs", sa.Column("trigger_source_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_agent_runs_trigger_source_id_context_sources",
        "agent_runs",
        "context_sources",
        ["trigger_source_id"],
        ["id"],
    )
    op.create_index(
        "ix_agent_runs_trigger_source_id",
        "agent_runs",
        ["trigger_source_id"],
        mssql_where=sa.text("trigger_source_id IS NOT NULL"),
    )

    op.add_column(
        "agent_runs",
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_check_constraint("ck_agent_runs_attempt_count", "agent_runs", "attempt_count >= 0")

    op.add_column("agent_runs", sa.Column("input_payload", sa.NVARCHAR(length="max"), nullable=True))
    op.create_check_constraint(
        "ck_agent_runs_input_payload_json",
        "agent_runs",
        "input_payload IS NULL OR ISJSON(input_payload) = 1",
    )

    op.create_check_constraint(
        "ck_agent_runs_run_type",
        "agent_runs",
        "run_type IN ('checkpoint_mapping', 'user_discovery')",
    )

    op.create_table(
        "agent_run_checkpoints",
        sa.Column("id", sa.BigInteger(), sa.Identity(start=1, increment=1), nullable=False),
        sa.Column("agent_run_id", sa.BigInteger(), nullable=False),
        sa.Column("checkpoint_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.NVARCHAR(length=20), server_default="PENDING", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_agent_run_checkpoints"),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            name="fk_agent_run_checkpoints_agent_run_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"],
            ["discovery_checkpoints.id"],
            name="fk_agent_run_checkpoints_checkpoint_id",
        ),
        sa.UniqueConstraint("agent_run_id", "checkpoint_id", name="uq_agent_run_checkpoints_run_checkpoint"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ANSWERED', 'NO_EVIDENCE', 'FAILED')",
            name="ck_agent_run_checkpoints_status",
        ),
    )
    op.create_index("ix_agent_run_checkpoints_checkpoint_id", "agent_run_checkpoints", ["checkpoint_id"])

    op.add_column("agent_run_chunks", sa.Column("mapping_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_agent_run_chunks_mapping_id",
        "agent_run_chunks",
        "context_checkpoint_mappings",
        ["mapping_id"],
        ["id"],
    )
    op.create_index(
        "ix_agent_run_chunks_mapping_id",
        "agent_run_chunks",
        ["mapping_id"],
        mssql_where=sa.text("mapping_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_agent_run_chunks_mapping_id", table_name="agent_run_chunks")
    op.drop_constraint("fk_agent_run_chunks_mapping_id", "agent_run_chunks", type_="foreignkey")
    op.drop_column("agent_run_chunks", "mapping_id")

    op.drop_index("ix_agent_run_checkpoints_checkpoint_id", table_name="agent_run_checkpoints")
    op.drop_table("agent_run_checkpoints")

    op.drop_constraint("ck_agent_runs_run_type", "agent_runs", type_="check")
    op.drop_constraint("ck_agent_runs_input_payload_json", "agent_runs", type_="check")
    op.drop_column("agent_runs", "input_payload")
    op.drop_constraint("ck_agent_runs_attempt_count", "agent_runs", type_="check")
    # SQL Server names the default constraint itself, so look its name up before dropping the column.
    op.execute(
        """
        DECLARE @name sysname = (
            SELECT dc.name FROM sys.default_constraints dc
            JOIN sys.columns c ON c.default_object_id = dc.object_id
            WHERE dc.parent_object_id = OBJECT_ID('agent_runs') AND c.name = 'attempt_count'
        );
        IF @name IS NOT NULL EXEC('ALTER TABLE agent_runs DROP CONSTRAINT ' + @name);
        """
    )
    op.drop_column("agent_runs", "attempt_count")

    op.drop_index("ix_agent_runs_trigger_source_id", table_name="agent_runs")
    op.drop_constraint("fk_agent_runs_trigger_source_id_context_sources", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "trigger_source_id")

    op.drop_index("ix_agent_runs_batch_id", table_name="agent_runs")
    op.drop_column("agent_runs", "batch_id")

    op.drop_index("ix_agent_runs_agent_id", table_name="agent_runs")
    op.drop_constraint("fk_agent_runs_agent_id_agents", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "agent_id")

    op.execute("DELETE FROM agents WHERE agent_code IN ('USER_AGENT', 'DATA_AGENT', 'TECH_AGENT')")
