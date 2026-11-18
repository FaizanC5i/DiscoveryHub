"""
ORM models: Python classes that describe the tables.

The tables themselves are created by Alembic migrations (backend/alembic/versions),
not by Base.metadata.create_all(). Keep these classes and the migrations in sync:
any change here needs a new migration.

Analogy: these models are the blueprints, and the migrations are the
construction crew's dated work orders. You never rebuild a wall by editing the
blueprint in secret; you issue a new work order so every site (dev, staging,
production) ends up in the same state.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    NVARCHAR,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Shared server-side default: the database stamps the row with its own UTC clock,
# so a client with a wrong system time cannot write bogus timestamps.
UTC_NOW = text("SYSUTCDATETIME()")


class User(Base):
    """
    A registered person.

    Analogy: the member card on file at the gym. It holds the name, the contact
    email and a scrambled version of the PIN (password_hash), never the PIN itself.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(NVARCHAR(100), nullable=False)
    # Unique constraint is created in the migration. Emails are stored lowercased
    # by the service layer so "Alex@x.com" and "alex@x.com" cannot both exist.
    email: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    # Deactivated accounts can be kept for audit without being able to sign in.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=UTC_NOW
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class RefreshToken(Base):
    """
    One login session on one device.

    Analogy: a hotel booking. The guest holds the confirmation (the raw token in
    an HttpOnly cookie). The hotel keeps only a fingerprint (token_hash). Setting
    revoked_at is like cancelling the booking, and it takes effect immediately.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # SHA-256 hex of the raw token. Unique, so lookups by hash are instant.
    token_hash: Mapped[str] = mapped_column(NVARCHAR(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=UTC_NOW
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    """
    A one-time code for resetting a forgotten password.

    Analogy: a one-time locker code. It works once, for a short window, and the
    locker company keeps only a record of it. used_at marks the moment it was spent.
    """

    __tablename__ = "password_reset_tokens"
    __table_args__ = (Index("ix_password_reset_tokens_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(NVARCHAR(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=UTC_NOW
    )

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class Project(Base):
    """
    A discovery project owned by one user.

    Analogy: a client folder in an agency's filing cabinet. The folder has a
    label (name), a summary sheet (description), the agreed dates, and the name
    of the clerk who opened it (owner_id). Every lookup starts from the owner, so
    one person's folders are never shown to another person.
    """

    __tablename__ = "projects"
    __table_args__ = (
        # The owner's list is always sorted by creation time, so this index serves the query directly.
        Index("ix_projects_owner_id_created_at", "owner_id", "created_at"),
        # The finish date cannot come before the start date. When either date is
        # missing there is nothing to compare, so the check passes.
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_projects_end_after_start",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=UTC_NOW
    )

    owner: Mapped[User] = relationship()


class ContextSource(Base):
    """A document or note in a project. Files have a blob; notes have text only."""

    __tablename__ = "context_sources"
    __table_args__ = (
        Index("ix_context_sources_project_id_created_at", "project_id", "created_at"),
        CheckConstraint("processing_status IN ('processing', 'ready', 'failed')", name="ck_context_sources_status"),
        CheckConstraint("source_type IN ('FILE_UPLOAD', 'MANUAL_NOTE')", name="ck_context_sources_source_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'FILE_UPLOAD'"))
    title: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(NVARCHAR(255), nullable=True)
    blob_path: Mapped[str | None] = mapped_column(NVARCHAR(500), nullable=True)
    mime_type: Mapped[str] = mapped_column(NVARCHAR(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processing_status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(NVARCHAR(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    updated_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)

    content: Mapped["ContextContent | None"] = relationship(
        back_populates="source", cascade="all, delete-orphan", uselist=False
    )


class ContextContent(Base):
    """The text extracted from one ContextSource. Only exists when extraction succeeded."""

    __tablename__ = "context_content"
    __table_args__ = (
        UniqueConstraint("context_source_id", name="uq_context_content_source_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    context_source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_sources.id", ondelete="CASCADE"), nullable=False
    )
    content_text: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    extraction_method: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=UTC_NOW
    )

    source: Mapped[ContextSource] = relationship(back_populates="content")

class ContextChunk(Base):
    """
    One overlapping slice of a ContextContent's text. Chunks are what the helper
    agent tags to checkpoints, so each one must be traceable: content_text[start_char:end_char]
    is exactly chunk_text. Rows are never updated or deleted; a changed document gets a new content row.

    Analogy: cutting a printed report into numbered strips. Each strip has the page
    line numbers printed on its edge (start_char, end_char), so anyone can lay it back
    on the original and see exactly where it came from.
    """

    __tablename__ = "context_chunks"
    __table_args__ = (
        UniqueConstraint(
            "context_content_id", "chunk_number", name="uq_context_chunks_content_number"
        ),
        CheckConstraint("chunk_number >= 1", name="ck_context_chunks_chunk_number"),
        CheckConstraint("start_char >= 0", name="ck_context_chunks_start_char"),
        CheckConstraint("end_char > start_char", name="ck_context_chunks_end_after_start"),
        CheckConstraint("char_count = end_char - start_char", name="ck_context_chunks_char_count"),
        CheckConstraint(
            "mapping_status IN ('PENDING', 'IN_PROGRESS', 'MAPPED', 'NO_MATCH', 'FAILED')",
            name="ck_context_chunks_mapping_status",
        ),
        Index("ix_context_chunks_context_content_id", "context_content_id"),
        Index("ix_context_chunks_content_mapping_status", "context_content_id", "mapping_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    context_content_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_content.id", ondelete="CASCADE"), nullable=False
    )
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=UTC_NOW
    )
    # Mapping progress, owned by the mapping job: PENDING -> IN_PROGRESS -> MAPPED / NO_MATCH / FAILED.
    mapping_status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False, server_default=text("'PENDING'"))
    mapping_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    mapped_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    mapping_error: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)


class DiscoveryPillar(Base):
    """One of the three discovery areas (User, Data, Tech). Fixed reference data seeded by migration 007."""

    __tablename__ = "discovery_pillars"
    __table_args__ = (UniqueConstraint("code", name="uq_discovery_pillars_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    code: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    name: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)


class DiscoveryCheckpoint(Base):
    """A question the discovery must answer, such as USER01 or TECH03. Fixed reference data."""

    __tablename__ = "discovery_checkpoints"
    __table_args__ = (UniqueConstraint("code", name="uq_discovery_checkpoints_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    pillar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("discovery_pillars.id", name="fk_discovery_checkpoints_pillar_id"), nullable=False
    )
    code: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    name: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    question: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    why_it_matters: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    priority: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    readiness_required_count: Mapped[int] = mapped_column(Integer, nullable=False)
    feeds_details: Mapped[str | None] = mapped_column(NVARCHAR(255), nullable=True)
    config_json: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))

    pillar: Mapped[DiscoveryPillar] = relationship()


class Agent(Base):
    """
    An author of mappings. Each pillar has one agent. The Helper Agent has no pillar
    (pillar_id NULL) and is the author of every checkpoint mapping.
    """

    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("agent_code", name="uq_agents_agent_code"),
        Index("ux_agents_pillar_id", "pillar_id", unique=True, mssql_where=text("pillar_id IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_code: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False)
    name: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    pillar_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("discovery_pillars.id", name="fk_agents_pillar_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class AgentRun(Base):
    """One agent call: a mapping batch or a pillar answer run."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_project_id_status", "project_id", "status"),
        # Migration 015: at most one running run per BRD.
        Index(
            "ux_agent_runs_one_running_artifact", "project_artifact_id", unique=True,
            mssql_where=text("status = 'running' AND project_artifact_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("agents.id"), nullable=True)
    batch_id: Mapped[str | None] = mapped_column(NVARCHAR(50), nullable=True)
    trigger_source_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("context_sources.id"), nullable=True)
    run_type: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False, server_default="checkpoint_mapping")
    status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    model: Mapped[str | None] = mapped_column(NVARCHAR(100), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    input_payload: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    raw_output: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(NVARCHAR(1000), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    completed_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    # BRD runs only (migration 012): the BRD, and the section for a single-section regenerate or clarify.
    # NO ACTION: the project cascade already reaches agent_runs.
    project_artifact_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("project_artifacts.id", name="fk_agent_runs_project_artifact_id"), nullable=True
    )
    project_artifact_section_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("project_artifact_sections.id", name="fk_agent_runs_project_artifact_section_id"),
        nullable=True,
    )


class AgentRunCheckpoint(Base):
    """A per-checkpoint result inside one run. Helper runs do not write here."""

    __tablename__ = "agent_run_checkpoints"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "checkpoint_id", name="uq_agent_run_checkpoints_run_checkpoint"),
        Index("ix_agent_run_checkpoints_checkpoint_id", "checkpoint_id"),
        CheckConstraint(
            "status IN ('PENDING', 'ANSWERED', 'NO_EVIDENCE', 'FAILED')", name="ck_agent_run_checkpoints_status"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", ondelete="CASCADE", name="fk_agent_run_checkpoints_agent_run_id"),
        nullable=False,
    )
    checkpoint_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("discovery_checkpoints.id", name="fk_agent_run_checkpoints_checkpoint_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False, server_default=text("'PENDING'"))


class AgentRunChunk(Base):
    """The chunks sent into one run. Helper runs link their chunks through mappings instead."""

    __tablename__ = "agent_run_chunks"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "context_chunk_id", name="uq_agent_run_chunks_run_chunk"),
        Index("ix_agent_run_chunks_context_chunk_id", "context_chunk_id"),
        Index("ix_agent_run_chunks_mapping_id", "mapping_id", mssql_where=text("mapping_id IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", ondelete="CASCADE", name="fk_agent_run_chunks_agent_run_id"),
        nullable=False,
    )
    context_chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_chunks.id", name="fk_agent_run_chunks_context_chunk_id"), nullable=False
    )
    mapping_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("context_checkpoint_mappings.id", name="fk_agent_run_chunks_mapping_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ContextCheckpointMapping(Base):
    """
    A chunk tagged with a checkpoint by an agent. Only one active row may exist per
    (project, chunk, checkpoint). Inactive rows are kept as history.
    """

    __tablename__ = "context_checkpoint_mappings"
    __table_args__ = (
        Index(
            "uq_mappings_active_project_chunk_checkpoint",
            "project_id", "context_chunk_id", "checkpoint_id",
            unique=True, mssql_where=text("is_active = 1"),
        ),
        Index("ix_mappings_project_id_chunk", "project_id", "context_chunk_id"),
        Index(
            "ix_mappings_project_id_checkpoint_active", "project_id", "checkpoint_id",
            mssql_where=text("is_active = 1"),
        ),
        CheckConstraint(
            "(is_active = 1 AND deactivated_at IS NULL) OR (is_active = 0 AND deactivated_at IS NOT NULL)",
            name="ck_mappings_active_state",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE", name="fk_mappings_project_id_projects"),
        nullable=False,
    )
    # NO ACTION on the chunk, checkpoint, run and agent keys: one cascade path into this table is enough.
    context_chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_chunks.id", name="fk_mappings_context_chunk_id"), nullable=False
    )
    checkpoint_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("discovery_checkpoints.id", name="fk_mappings_checkpoint_id"), nullable=False
    )
    agent_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", name="fk_mappings_agent_run_id"), nullable=False
    )
    mapped_by_agent_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agents.id", name="fk_mappings_mapped_by_agent_id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    deactivated_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)

    checkpoint: Mapped[DiscoveryCheckpoint] = relationship()
    evidence: Mapped[list["MappingEvidence"]] = relationship(back_populates="mapping")


class MappingEvidence(Base):
    """
    The quote that justifies a mapping, with its position in the content:
    content_text[evidence_start_char:evidence_end_char] == evidence_quote.
    """

    __tablename__ = "mapping_evidence"
    __table_args__ = (
        CheckConstraint("evidence_end_char > evidence_start_char", name="ck_mapping_evidence_end_after_start"),
        CheckConstraint(
            "evidence_end_char - evidence_start_char = LEN(evidence_quote)", name="ck_mapping_evidence_length"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mapping_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("context_checkpoint_mappings.id", ondelete="CASCADE", name="fk_mapping_evidence_mapping_id"),
        nullable=False,
    )
    evidence_quote: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    reason: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    evidence_start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_end_char: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    mapping: Mapped[ContextCheckpointMapping] = relationship(back_populates="evidence")


class ProjectCheckpointAnswer(Base):
    """
    The current answer and completion state for one checkpoint in one project.
    Analogy: the index card for one question in the project's binder. It holds the
    answer that was approved, and the card is what the reader looks at first.
    """

    __tablename__ = "project_checkpoint_answers"
    __table_args__ = (
        UniqueConstraint("project_id", "checkpoint_id", name="uq_project_checkpoint_answers_project_checkpoint"),
        Index("ix_project_checkpoint_answers_checkpoint_id", "checkpoint_id"),
        Index("ix_project_checkpoint_answers_status", "status"),
        CheckConstraint(
            "completion_score IS NULL OR (completion_score >= 0 AND completion_score <= 1)",
            name="ck_project_checkpoint_answers_completion_score",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE", name="fk_project_checkpoint_answers_project_id"),
        nullable=False,
    )
    checkpoint_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("discovery_checkpoints.id", name="fk_project_checkpoint_answers_checkpoint_id"),
        nullable=False,
    )
    current_answer: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    status: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'NOT_STARTED'"))
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    completion_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    completion_updated_by_run_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", name="fk_project_checkpoint_answers_completion_run_id"), nullable=True
    )
    completion_updated_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_project_checkpoint_answers_approved_by"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    checkpoint: Mapped[DiscoveryCheckpoint] = relationship()
    proposals: Mapped[list["CheckpointAnswerProposal"]] = relationship(back_populates="current_answer")
    versions: Mapped[list["CheckpointAnswerVersion"]] = relationship(back_populates="checkpoint_answer")
    evidence: Mapped[list["CheckpointAnswerEvidence"]] = relationship(back_populates="checkpoint_answer")


class CheckpointAnswerProposal(Base):
    """
    A proposed answer generated by an agent run. Many proposals can exist for one checkpoint answer.
    Analogy: a draft memo put on a colleague's desk. The memo is kept even after a newer draft replaces it,
    and superseded_by shows which draft came next.
    """

    __tablename__ = "checkpoint_answer_proposals"
    __table_args__ = (
        Index("ix_checkpoint_answer_proposals_current_answer_id", "current_answer_id"),
        Index("ix_checkpoint_answer_proposals_agent_run_id", "agent_run_id"),
        Index("ix_checkpoint_answer_proposals_status", "status"),
        Index(
            "ix_checkpoint_answer_proposals_superseded_by_proposal_id",
            "superseded_by_proposal_id",
            mssql_where=text("superseded_by_proposal_id IS NOT NULL"),
        ),
        Index(
            "ux_checkpoint_answer_proposals_one_pending",
            "current_answer_id",
            unique=True,
            mssql_where=text("status = 'PENDING'"),
        ),
        CheckConstraint("base_version_number >= 0", name="ck_checkpoint_answer_proposals_base_version_number"),
        CheckConstraint(
            "completion_score IS NULL OR (completion_score >= 0 AND completion_score <= 1)",
            name="ck_checkpoint_answer_proposals_completion_score",
        ),
        CheckConstraint("status IN ('PENDING', 'APPROVED', 'SUPERSEDED')", name="ck_checkpoint_answer_proposals_status"),
        CheckConstraint(
            "agent_status IN ('Pending Approval', 'Needs Clarification')",
            name="ck_checkpoint_answer_proposals_agent_status",
        ),
        CheckConstraint(
            "(is_completed = 1 AND agent_status = 'Pending Approval') "
            "OR (is_completed = 0 AND agent_status = 'Needs Clarification')",
            name="ck_checkpoint_answer_proposals_is_completed",
        ),
        CheckConstraint(
            "missing_information IS NULL OR ISJSON(missing_information) = 1",
            name="ck_checkpoint_answer_proposals_missing_json",
        ),
        CheckConstraint(
            "clarification_questions IS NULL OR ISJSON(clarification_questions) = 1",
            name="ck_checkpoint_answer_proposals_questions_json",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # The project and checkpoint are reached through this answer, so they are not repeated here.
    current_answer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "project_checkpoint_answers.id",
            ondelete="CASCADE",
            name="fk_checkpoint_answer_proposals_current_answer_id",
        ),
        nullable=False,
    )
    agent_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", name="fk_checkpoint_answer_proposals_agent_run_id"), nullable=False
    )
    base_version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_answer: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    completion_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False, server_default=text("'PENDING'"))
    # The agent's own status and completion flag, kept beside our status.
    agent_status: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'Needs Clarification'"))
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    missing_information: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    clarification_questions: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    # Self-reference with NO ACTION, so superseding never cascades into other proposals.
    superseded_by_proposal_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("checkpoint_answer_proposals.id", name="fk_checkpoint_answer_proposals_superseded_by"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    reviewed_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)

    current_answer: Mapped[ProjectCheckpointAnswer] = relationship(back_populates="proposals")
    agent_run: Mapped[AgentRun] = relationship()
    superseded_by: Mapped["CheckpointAnswerProposal | None"] = relationship(
        remote_side="CheckpointAnswerProposal.id",
        foreign_keys="[CheckpointAnswerProposal.superseded_by_proposal_id]",
    )

class ProposalEvidence(Base):
    """
    Links a proposal to the chunks and mappings that support it, with the agent's reason per chunk.
    The quote itself stays in mapping_evidence.
    """

    __tablename__ = "proposal_evidence"
    __table_args__ = (
        UniqueConstraint("proposal_id", "mapping_id", name="uq_proposal_evidence_proposal_mapping"),
        Index("ix_proposal_evidence_proposal_id", "proposal_id"),
        Index("ix_proposal_evidence_context_chunk_id", "context_chunk_id"),
        Index("ix_proposal_evidence_mapping_id", "mapping_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proposal_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("checkpoint_answer_proposals.id", ondelete="CASCADE", name="fk_proposal_evidence_proposal_id"),
        nullable=False,
    )
    context_chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_chunks.id", name="fk_proposal_evidence_context_chunk_id"), nullable=False
    )
    mapping_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_checkpoint_mappings.id", name="fk_proposal_evidence_mapping_id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    proposal: Mapped[CheckpointAnswerProposal] = relationship()

class CheckpointAnswerVersion(Base):
    """
    A saved snapshot of a checkpoint answer, numbered within that answer.
    Analogy: the dated copies kept in a filing drawer. Old copies are never edited.
    """

    __tablename__ = "checkpoint_answer_versions"
    __table_args__ = (
        UniqueConstraint(
            "checkpoint_answer_id", "version_number", name="uq_checkpoint_answer_versions_answer_version"
        ),
        Index("ix_checkpoint_answer_versions_proposal_id", "proposal_id"),
        Index("ix_checkpoint_answer_versions_created_by", "created_by"),
        CheckConstraint("version_number >= 1", name="ck_checkpoint_answer_versions_version_number"),
        CheckConstraint("source IN ('AI_PROPOSAL', 'MANUAL')", name="ck_checkpoint_answer_versions_source"),
        CheckConstraint(
            "source <> 'AI_PROPOSAL' OR proposal_id IS NOT NULL",
            name="ck_checkpoint_answer_versions_proposal_required",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    checkpoint_answer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_checkpoint_answers.id", ondelete="CASCADE", name="fk_checkpoint_answer_versions_answer_id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_text: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    source: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    proposal_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("checkpoint_answer_proposals.id", name="fk_checkpoint_answer_versions_proposal_id"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_checkpoint_answer_versions_created_by"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    checkpoint_answer: Mapped[ProjectCheckpointAnswer] = relationship(back_populates="versions")
    proposal: Mapped[CheckpointAnswerProposal | None] = relationship()
    creator: Mapped[User] = relationship()


class CheckpointAnswerEvidence(Base):
    """The document chunks that support one saved version of a checkpoint answer."""

    __tablename__ = "checkpoint_answer_evidence"
    __table_args__ = (
        UniqueConstraint("answer_version_id", "context_chunk_id", name="uq_checkpoint_answer_evidence_version_chunk"),
        Index("ix_checkpoint_answer_evidence_checkpoint_answer_id", "checkpoint_answer_id"),
        Index("ix_checkpoint_answer_evidence_answer_version_id", "answer_version_id"),
        Index("ix_checkpoint_answer_evidence_context_chunk_id", "context_chunk_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # NO ACTION: the version cascade already removes these rows, and a second cascade path would be rejected.
    checkpoint_answer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_checkpoint_answers.id", name="fk_checkpoint_answer_evidence_answer_id"),
        nullable=False,
    )
    answer_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("checkpoint_answer_versions.id", ondelete="CASCADE", name="fk_checkpoint_answer_evidence_version_id"),
        nullable=False,
    )
    context_chunk_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("context_chunks.id", name="fk_checkpoint_answer_evidence_context_chunk_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    checkpoint_answer: Mapped[ProjectCheckpointAnswer] = relationship(back_populates="evidence")
    answer_version: Mapped[CheckpointAnswerVersion] = relationship()
    context_chunk: Mapped[ContextChunk] = relationship()


# --- BRD (artifact generation), migration 012 ------------------------------------------------


class ArtifactType(Base):
    """A kind of document Discovery Hub can write (BRD first). Linked to the agent that writes it."""

    __tablename__ = "artifact_types"
    __table_args__ = (UniqueConstraint("code", name="uq_artifact_types_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False)
    name: Mapped[str] = mapped_column(NVARCHAR(150), nullable=False)
    description: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    agent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agents.id", name="fk_artifact_types_agent_id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ArtifactTypePillar(Base):
    """A discovery pillar whose APPROVED answers an artifact type is written from (BRD: User)."""

    __tablename__ = "artifact_type_pillars"
    __table_args__ = (UniqueConstraint("artifact_type_id", "pillar_id", name="uq_artifact_type_pillars"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("artifact_types.id", ondelete="CASCADE", name="fk_artifact_type_pillars_artifact_type_id"),
        nullable=False,
    )
    pillar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("discovery_pillars.id", name="fk_artifact_type_pillars_pillar_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ArtifactSection(Base):
    """One section of an artifact template, such as the BRD's "Scope". Configuration rows."""

    __tablename__ = "artifact_sections"
    __table_args__ = (
        UniqueConstraint("artifact_type_id", "section_key", name="uq_artifact_sections_type_key"),
        CheckConstraint(
            "fallback_questions IS NULL OR ISJSON(fallback_questions) = 1",
            name="ck_artifact_sections_fallback_questions_json",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("artifact_types.id", name="fk_artifact_sections_artifact_type_id"), nullable=False
    )
    section_key: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False)
    title: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    prompt: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    fallback_questions: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ArtifactSectionCheckpoint(Base):
    """Which checkpoint's approved answer feeds which section. A section with no rows reads every answer."""

    __tablename__ = "artifact_section_checkpoints"
    __table_args__ = (
        UniqueConstraint("artifact_section_id", "checkpoint_id", name="uq_artifact_section_checkpoints"),
        Index("ix_artifact_section_checkpoints_checkpoint_id", "checkpoint_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("artifact_sections.id", ondelete="CASCADE", name="fk_artifact_section_checkpoints_section_id"),
        nullable=False,
    )
    checkpoint_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("discovery_checkpoints.id", name="fk_artifact_section_checkpoints_checkpoint_id"),
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ProjectArtifact(Base):
    """One artifact (for example the BRD) of one project: document status and approved version."""

    __tablename__ = "project_artifacts"
    __table_args__ = (
        UniqueConstraint("project_id", "artifact_type_id", name="uq_project_artifacts_project_type"),
        CheckConstraint(
            "status IN ('NOT_STARTED', 'DRAFT', 'IN_REVIEW', 'APPROVED')", name="ck_project_artifacts_status"
        ),
        CheckConstraint("current_version >= 0", name="ck_project_artifacts_current_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE", name="fk_project_artifacts_project_id"),
        nullable=False,
    )
    artifact_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("artifact_types.id", name="fk_project_artifacts_artifact_type_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'NOT_STARTED'"))
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    instructions: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    # "Configure the draft" form (migration 016). Sent to the agent with every request.
    title: Mapped[str | None] = mapped_column(NVARCHAR(255), nullable=True)
    audience: Mapped[str | None] = mapped_column(NVARCHAR(100), nullable=True)
    scope: Mapped[str | None] = mapped_column(NVARCHAR(1000), nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_project_artifacts_created_by"), nullable=False
    )
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_project_artifacts_approved_by"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    updated_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ProjectArtifactSection(Base):
    """
    The current content of one section of a project's artifact. Like project_checkpoint_answers,
    it only changes when the user approves a proposal or edits the section.
    """

    __tablename__ = "project_artifact_sections"
    __table_args__ = (
        UniqueConstraint(
            "project_artifact_id", "artifact_section_id", name="uq_project_artifact_sections_artifact_section"
        ),
        CheckConstraint(
            "status IN ('NOT_STARTED', 'DRAFT', 'PENDING_REVIEW', 'NEEDS_CLARIFICATION', 'APPROVED')",
            name="ck_project_artifact_sections_status",
        ),
        CheckConstraint("source IS NULL OR source IN ('AGENT', 'USER')", name="ck_project_artifact_sections_source"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_artifact_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_artifacts.id", ondelete="CASCADE", name="fk_project_artifact_sections_artifact_id"),
        nullable=False,
    )
    artifact_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("artifact_sections.id", name="fk_project_artifact_sections_section_id"), nullable=False
    )
    current_content: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    status: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'NOT_STARTED'"))
    source: Mapped[str | None] = mapped_column(NVARCHAR(20), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_project_artifact_sections_approved_by"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    updated_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)

    section: Mapped[ArtifactSection] = relationship()


class ArtifactSectionProposal(Base):
    """What the agent wrote for a section (PENDING), or why it could not (NEEDS_CLARIFICATION)."""

    __tablename__ = "artifact_section_proposals"
    __table_args__ = (
        Index("ix_artifact_section_proposals_section_status", "project_artifact_section_id", "status"),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_CLARIFICATION', 'SUPERSEDED')",
            name="ck_artifact_section_proposals_status",
        ),
        CheckConstraint(
            "clarification_questions IS NULL OR ISJSON(clarification_questions) = 1",
            name="ck_artifact_section_proposals_questions_json",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_artifact_section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_artifact_sections.id", ondelete="CASCADE", name="fk_artifact_section_proposals_section_id"),
        nullable=False,
    )
    proposed_content: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    status: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False, server_default=text("'PENDING'"))
    missing_reason: Mapped[str | None] = mapped_column(NVARCHAR(1000), nullable=True)
    clarification_questions: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    generated_by_agent_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agents.id", name="fk_artifact_section_proposals_agent_id"), nullable=False
    )
    # NO ACTION: the project cascade already reaches agent_runs.
    agent_run_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agent_runs.id", name="fk_artifact_section_proposals_run_id"), nullable=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_artifact_section_proposals_reviewed_by"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ArtifactSectionClarification(Base):
    """The user's answer to one agent question. Re-sent on every later regeneration of the section."""

    __tablename__ = "artifact_section_clarifications"
    __table_args__ = (Index("ix_artifact_section_clarifications_section_id", "project_artifact_section_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_artifact_section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "project_artifact_sections.id", ondelete="CASCADE", name="fk_artifact_section_clarifications_section_id"
        ),
        nullable=False,
    )
    # NO ACTION: the section cascade already reaches both tables.
    proposal_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("artifact_section_proposals.id", name="fk_artifact_section_clarifications_proposal_id"),
        nullable=True,
    )
    question: Mapped[str] = mapped_column(NVARCHAR(1000), nullable=False)
    answer: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    answered_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_artifact_section_clarifications_answered_by"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)


class ProjectArtifactVersion(Base):
    """A frozen JSON snapshot of the whole artifact each time it is approved (v1, v2 ...)."""

    __tablename__ = "project_artifact_versions"
    __table_args__ = (
        UniqueConstraint("project_artifact_id", "version_number", name="uq_project_artifact_versions"),
        CheckConstraint("version_number >= 1", name="ck_project_artifact_versions_version_number"),
        CheckConstraint("ISJSON(snapshot) = 1", name="ck_project_artifact_versions_snapshot_json"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_artifact_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_artifacts.id", ondelete="CASCADE", name="fk_project_artifact_versions_artifact_id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[str] = mapped_column(NVARCHAR(length="max"), nullable=False)
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", name="fk_project_artifact_versions_approved_by"), nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
