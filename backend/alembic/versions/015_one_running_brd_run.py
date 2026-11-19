"""At most one running agent run per BRD, and correct section statuses left behind by superseded drafts.

Revision ID: 015_one_running_brd_run
Revises: 014_artifact_type_pillars

- ux_agent_runs_one_running_artifact: a filtered unique index, so two requests that arrive at the
  same moment (for example two answers approved together) cannot both start a BRD run. The
  application treats the duplicate-key error as "a run is busy".
- Data fix: a section marked PENDING_REVIEW whose draft was later replaced by clarification
  questions gets the status that matches what it holds now.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "015_one_running_brd_run"
down_revision: str | None = "014_artifact_type_pillars"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Runs stuck in "running" (server stopped mid-run) would block the new index; close them first.
    op.execute(
        "UPDATE agent_runs SET status = 'failed', completed_at = SYSUTCDATETIME(), "
        "error_message = 'Stopped before it finished (closed by migration 015).' "
        "WHERE status = 'running' AND project_artifact_id IS NOT NULL"
    )
    op.create_index(
        "ux_agent_runs_one_running_artifact",
        "agent_runs",
        ["project_artifact_id"],
        unique=True,
        mssql_where=sa.text("status = 'running' AND project_artifact_id IS NOT NULL"),
    )
    op.execute(
        """
        UPDATE s SET s.status = CASE
                WHEN EXISTS (SELECT 1 FROM artifact_section_proposals p
                             WHERE p.project_artifact_section_id = s.id AND p.status = 'NEEDS_CLARIFICATION')
                     AND s.current_content IS NULL THEN 'NEEDS_CLARIFICATION'
                WHEN s.current_content IS NOT NULL THEN 'APPROVED'
                ELSE 'NOT_STARTED' END,
            s.updated_at = SYSUTCDATETIME()
        FROM project_artifact_sections s
        WHERE s.status = 'PENDING_REVIEW'
          AND NOT EXISTS (SELECT 1 FROM artifact_section_proposals p
                          WHERE p.project_artifact_section_id = s.id AND p.status = 'PENDING')
        """
    )


def downgrade() -> None:
    op.drop_index("ux_agent_runs_one_running_artifact", table_name="agent_runs")
