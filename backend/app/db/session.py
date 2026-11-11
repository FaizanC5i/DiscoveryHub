"""
Database engine and session factory for Azure SQL (ODBC Driver 18).

Analogy: the engine is the building's water main, and a session is one
person's tap. Each request opens its own tap, uses it, and closes it, so one
request's half-finished work never leaks into another.

The engine is created lazily, on first use. Importing this module never opens a
network connection, which keeps imports, tests and `alembic --help` fast.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """
    One engine (and its connection pool) for the whole process.

    pool_pre_ping=True: before reusing a pooled connection, send a tiny query to
    check it still works. Azure SQL closes idle connections after a while, and
    without this check the first request after a quiet period fails.
    """
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_recycle=1800,  # replace connections older than 30 minutes
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """
    Factory that produces new Session objects.

    expire_on_commit=False keeps loaded attributes readable after commit, so a
    response built after commit does not trigger another database round trip.
    """
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency: yields one session per request, then closes it.

    The `finally` guarantees the session is closed even if the route raises.
    Commits are explicit in the service layer, so a failed request rolls back
    instead of saving half a change.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
