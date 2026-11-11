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

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    NVARCHAR,
    text,
)
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
