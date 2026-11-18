"""Artifact Studio: draft settings (title, audience, scope) and the 5-section BRD.

Revision ID: 016_artifact_draft_settings
Revises: 015_one_running_brd_run

- project_artifacts gets title, audience and scope, filled from the "Configure the draft" form and
  sent to the agent with every request.
- The BRD keeps the 5 sections shown in the draft editor: Business Objectives, Users &
  Stakeholders, Current State, Scope, Functional Requirements. The other 9 are switched off
  (is_active = 0), not deleted, so existing rows stay valid and they can be switched back on.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "016_artifact_draft_settings"
down_revision: str | None = "015_one_running_brd_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BRD_SECTIONS_KEPT = ("business_objectives", "users_stakeholders", "current_state", "scope", "functional_requirements")


def upgrade() -> None:
    op.add_column("project_artifacts", sa.Column("title", sa.NVARCHAR(length=255), nullable=True))
    op.add_column("project_artifacts", sa.Column("audience", sa.NVARCHAR(length=100), nullable=True))
    op.add_column("project_artifacts", sa.Column("scope", sa.NVARCHAR(length=1000), nullable=True))
    kept = ", ".join(f"'{key}'" for key in BRD_SECTIONS_KEPT)
    op.execute(
        "UPDATE s SET s.is_active = CASE WHEN s.section_key IN (" + kept + ") THEN 1 ELSE 0 END "
        "FROM artifact_sections s JOIN artifact_types t ON t.id = s.artifact_type_id WHERE t.code = 'BRD'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE s SET s.is_active = 1 FROM artifact_sections s "
        "JOIN artifact_types t ON t.id = s.artifact_type_id WHERE t.code = 'BRD'"
    )
    op.drop_column("project_artifacts", "scope")
    op.drop_column("project_artifacts", "audience")
    op.drop_column("project_artifacts", "title")
