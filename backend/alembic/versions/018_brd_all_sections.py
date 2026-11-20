"""BRD: back to all 14 sections.

Revision ID: 018_brd_all_sections
Revises: 017_checkpoint_owner_input

Migration 016 kept 5 BRD sections. The draft editor now shows the full BRD again (all 14
sections on one scrolling page, as in the original BRD tool), so every BRD section is switched
back on, and BRDs created while only 5 were on get rows for the other 9.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "018_brd_all_sections"
down_revision: str | None = "017_checkpoint_owner_input"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BRD_SECTIONS_OF_016 = ("business_objectives", "users_stakeholders", "current_state", "scope", "functional_requirements")


def upgrade() -> None:
    op.execute(
        "UPDATE s SET s.is_active = 1 FROM artifact_sections s "
        "JOIN artifact_types t ON t.id = s.artifact_type_id WHERE t.code = 'BRD'"
    )
    op.execute(
        "INSERT INTO project_artifact_sections (project_artifact_id, artifact_section_id) "
        "SELECT a.id, s.id FROM project_artifacts a "
        "JOIN artifact_sections s ON s.artifact_type_id = a.artifact_type_id "
        "JOIN artifact_types t ON t.id = a.artifact_type_id AND t.code = 'BRD' "
        "WHERE NOT EXISTS (SELECT 1 FROM project_artifact_sections x "
        "                  WHERE x.project_artifact_id = a.id AND x.artifact_section_id = s.id)"
    )


def downgrade() -> None:
    kept = ", ".join(f"'{key}'" for key in BRD_SECTIONS_OF_016)
    op.execute(
        "UPDATE s SET s.is_active = CASE WHEN s.section_key IN (" + kept + ") THEN 1 ELSE 0 END "
        "FROM artifact_sections s JOIN artifact_types t ON t.id = s.artifact_type_id WHERE t.code = 'BRD'"
    )
