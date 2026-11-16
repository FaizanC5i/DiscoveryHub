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
    """
    A document attached to a project. The original file is in Blob Storage, and
    this row describes it. The extracted text is stored in ContextContent.

    Analogy: the index card in the filing cabinet. It says what the document is
    and where it sits in the warehouse (blob_path). The document itself is not
    in the cabinet.
    """

    __tablename__ = "context_sources"
    __table_args__ = (
        Index("ix_context_sources_project_id_created_at", "project_id", "created_at"),
        CheckConstraint(
            "processing_status IN ('processing', 'ready', 'failed')",
            name="ck_context_sources_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    # No ondelete here on purpose: SQL Server rejects a second cascade path from users.
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(
        NVARCHAR(30), nullable=False, server_default=text("'upload'")
    )
    title: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(NVARCHAR(255), nullable=False)
    blob_path: Mapped[str] = mapped_column(NVARCHAR(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(NVARCHAR(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processing_status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(NVARCHAR(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=UTC_NOW
    )
    # Soft delete: hidden from lists immediately, blob removed best-effort.
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
    """One call to the agent. Every mapping points at the run that produced it."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_project_id_status", "project_id", "status"),
        CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="ck_agent_runs_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE", name="fk_agent_runs_project_id_projects"),
        nullable=False,
    )
    run_type: Mapped[str] = mapped_column(NVARCHAR(50), nullable=False, server_default=text("'checkpoint_mapping'"))
    status: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    model: Mapped[str | None] = mapped_column(NVARCHAR(100), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(NVARCHAR(length="max"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(NVARCHAR(1000), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DATETIME2, nullable=False, server_default=UTC_NOW)
    completed_at: Mapped[datetime | None] = mapped_column(DATETIME2, nullable=True)


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
