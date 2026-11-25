"""PRD: the artifact type, its agent, its 25 sections, and which answers it is written from.

Revision ID: 019_prd_artifact
Revises: 018_brd_all_sections

Rows only, no new tables: the PRD uses the same artifact tables as the BRD.
- agents: PRD_AGENT ("PRD Generation Agent" on Agent5i).
- artifact_types: PRD.
- artifact_type_pillars: the PRD reads the approved answers of the User Discovery AND Tech
  Discovery pillars.
- artifact_sections: the 25 PRD sections agreed with the team. sort_order is the section_id the
  PRD agent uses (1-25, codes PRDS01-PRDS25). prompt holds the section's definition as JSON
  (key contents, required details, expected format, question), sent to the agent as it is.
  fallback_questions: 3 questions from the required details, used when the agent sends none.

The 4 Tech Discovery checkpoints (PRDCP01-PRDCP04) are NOT added here: the Helper Agent maps
chunks to every active checkpoint, so adding them changes mapping for the whole team.
"""

import json
from collections.abc import Sequence

from alembic import op

revision: str = "019_prd_artifact"
down_revision: str | None = "018_brd_all_sections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXPECTED_FORMAT = (
    "Structured PRD prose with subsection headings and numbered requirements or tables where supported by evidence."
)

# (section_key, title, key contents, required details)
PRD_SECTIONS = [('document_overview',
  'Document Overview',
  'Document title, version, status, owner, stakeholders, executive summary',
  ['Document title', 'version', 'status', 'owner', 'stakeholders', 'executive summary']),
 ('product_overview',
  'Product Overview & Background',
  'Product description, business context, existing system overview',
  ['Product description', 'business context', 'existing system overview']),
 ('problem_objectives',
  'Problem Statement & Objectives',
  'Problem definition, user pain points, business objectives, product goals',
  ['Problem definition', 'user pain points', 'business objectives', 'product goals']),
 ('target_users_personas',
  'Target Users & Personas',
  'User segments, personas, roles and permissions',
  ['User segments', 'personas', 'roles and permissions']),
 ('product_scope',
  'Product Scope',
  'In-scope features, out-of-scope features, non-goals',
  ['In-scope features', 'out-of-scope features', 'non-goals']),
 ('functional_requirements',
  'Functional Requirements',
  'Feature descriptions, functional specifications, business rules, validations',
  ['Feature descriptions', 'functional specifications', 'business rules', 'validations']),
 ('user_stories_use_cases',
  'User Stories & Use Cases',
  'User stories, user scenarios, system interactions (where applicable)',
  ['User stories', 'user scenarios', 'system interactions (where applicable)']),
 ('user_workflows',
  'User Workflows & Process Flows',
  'End-to-end workflows, process diagrams, decision flows',
  ['End-to-end workflows', 'process diagrams', 'decision flows']),
 ('ui_ux_requirements',
  'UI/UX Requirements',
  'User journeys, navigation, wireframes, screen-level requirements, accessibility',
  ['User journeys', 'navigation', 'wireframes', 'screen-level requirements', 'accessibility']),
 ('technical_architecture',
  'Technical Architecture & Design',
  'Existing architecture, proposed architecture, technology stack, system components',
  ['Existing architecture', 'proposed architecture', 'technology stack', 'system components']),
 ('data_requirements',
  'Data Requirements',
  'Data entities, database requirements, data sources, storage, processing and retention',
  ['Data entities', 'database requirements', 'data sources', 'storage', 'processing and retention']),
 ('api_integration',
  'API & Integration Requirements',
  'API specifications, external integrations, third-party dependencies, data exchange',
  ['API specifications', 'external integrations', 'third-party dependencies', 'data exchange']),
 ('non_functional_requirements',
  'Non-Functional Requirements',
  'Performance, scalability, availability, reliability, security and compatibility',
  ['Performance', 'scalability', 'availability', 'reliability', 'security and compatibility']),
 ('infrastructure_deployment',
  'Infrastructure & Deployment Requirements',
  'Cloud infrastructure, hosting, environments, CI/CD and deployment strategy',
  ['Cloud infrastructure', 'hosting', 'environments', 'CI/CD and deployment strategy']),
 ('security_compliance',
  'Security & Compliance Requirements',
  'Authentication, authorization, encryption, privacy, regulatory compliance',
  ['Authentication', 'authorization', 'encryption', 'privacy', 'regulatory compliance']),
 ('error_handling',
  'Error Handling & Edge Cases',
  'Exception scenarios, validation failures, fallback mechanisms, recovery',
  ['Exception scenarios', 'validation failures', 'fallback mechanisms', 'recovery']),
 ('constraints_assumptions',
  'Constraints, Assumptions & Dependencies',
  'Technical limitations, business constraints, assumptions, external dependencies',
  ['Technical limitations', 'business constraints', 'assumptions', 'external dependencies']),
 ('risks_mitigation',
  'Risks & Mitigation',
  'Technical, operational, security and integration risks with mitigation strategies',
  ['Technical', 'operational', 'security and integration risks with mitigation strategies']),
 ('prioritization_mvp',
  'Prioritization & MVP Scope',
  'P0/P1/P2 priorities, MVP definition, phased implementation',
  ['P0/P1/P2 priorities', 'MVP definition', 'phased implementation']),
 ('acceptance_criteria',
  'Acceptance Criteria',
  'Requirement-level acceptance criteria, expected outcomes, validation conditions',
  ['Requirement-level acceptance criteria', 'expected outcomes', 'validation conditions']),
 ('testing_qa',
  'Testing & Quality Assurance',
  'Functional, integration, performance, security and UAT requirements',
  ['Functional', 'integration', 'performance', 'security and UAT requirements']),
 ('success_metrics',
  'Success Metrics & KPIs',
  'Adoption, activation, task completion, performance and business outcomes',
  ['Adoption', 'activation', 'task completion', 'performance and business outcomes']),
 ('timeline_release',
  'Timeline & Release Planning',
  'Milestones, delivery phases, dependencies, rollout strategy',
  ['Milestones', 'delivery phases', 'dependencies', 'rollout strategy']),
 ('open_questions',
  'Open Questions & Pending Decisions',
  'Unresolved requirements, clarification points, decision owners',
  ['Unresolved requirements', 'clarification points', 'decision owners']),
 ('appendices_references',
  'Appendices & References',
  'Glossary, supporting documents, diagrams, API references, revision history',
  ['Glossary', 'supporting documents', 'diagrams', 'API references', 'revision history'])]


def _sql(text: str) -> str:
    return text.replace("'", "''")


def _prompt(title: str, key_contents: str, details: list[str]) -> str:
    return json.dumps(
        {
            "description": (
                f"Document the confirmed project-specific information for {title.lower()}, identifying gaps "
                "and unresolved decisions instead of inferring facts."
            ),
            "key_contents": key_contents,
            "required_details": details,
            "expected_format": EXPECTED_FORMAT,
            "question": f"What confirmed information and requirements are available for {title.lower()}?",
        },
        ensure_ascii=False,
    )


def _fallback(details: list[str]) -> str:
    return json.dumps(
        [f"Please describe the confirmed {d.strip().rstrip('.?').lower()} for this project." for d in details[:3]],
        ensure_ascii=False,
    )


def upgrade() -> None:
    op.execute(
        "IF NOT EXISTS (SELECT 1 FROM agents WHERE agent_code = 'PRD_AGENT') "
        "INSERT INTO agents (agent_code, name, pillar_id) VALUES ('PRD_AGENT', N'PRD Generation Agent', NULL)"
    )
    op.execute(
        "IF NOT EXISTS (SELECT 1 FROM artifact_types WHERE code = 'PRD') "
        "INSERT INTO artifact_types (code, name, description, agent_id) "
        "SELECT 'PRD', N'Product Requirements Document', N'Product requirements written from approved User and "
        "Tech Discovery answers', id FROM agents WHERE agent_code = 'PRD_AGENT'"
    )
    op.execute(
        "INSERT INTO artifact_type_pillars (artifact_type_id, pillar_id) "
        "SELECT t.id, p.id FROM artifact_types t JOIN discovery_pillars p ON p.code IN ('USER', 'TECH') "
        "WHERE t.code = 'PRD' AND NOT EXISTS (SELECT 1 FROM artifact_type_pillars x "
        "WHERE x.artifact_type_id = t.id AND x.pillar_id = p.id)"
    )
    for order, (key, title, key_contents, details) in enumerate(PRD_SECTIONS, start=1):
        op.execute(
            "INSERT INTO artifact_sections (artifact_type_id, section_key, title, prompt, fallback_questions, sort_order) "
            f"SELECT id, '{key}', N'{_sql(title)}', N'{_sql(_prompt(title, key_contents, details))}', "
            f"N'{_sql(_fallback(details))}', {order} FROM artifact_types WHERE code = 'PRD'"
        )


def downgrade() -> None:
    prd = "(SELECT id FROM artifact_types WHERE code = 'PRD')"
    op.execute(f"DELETE FROM project_artifact_versions WHERE project_artifact_id IN (SELECT id FROM project_artifacts WHERE artifact_type_id = {prd})")
    op.execute(f"DELETE FROM agent_runs WHERE project_artifact_id IN (SELECT id FROM project_artifacts WHERE artifact_type_id = {prd})")
    op.execute(f"DELETE FROM project_artifacts WHERE artifact_type_id = {prd}")
    op.execute(f"DELETE FROM artifact_sections WHERE artifact_type_id = {prd}")
    op.execute(f"DELETE FROM artifact_type_pillars WHERE artifact_type_id = {prd}")
    op.execute("DELETE FROM artifact_types WHERE code = 'PRD'")
    op.execute("DELETE FROM agents WHERE agent_code = 'PRD_AGENT'")

