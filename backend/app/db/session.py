"""
Database engine and session factory for Azure SQL (ODBC Driver 18).

Analogy: the engine is the building's water main, and a session is one
person's tap. Each request opens its own tap, uses it, and closes it, so one
request's half-finished work never leaks into another.

The engine is created lazily, on first use. Importing this module never opens a
network connection, which keeps imports, tests and `alembic --help` fast.
"""

from collections.abc import Iterator
import time
from functools import lru_cache

from sqlalchemy import create_engine, event, exc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.cursor_pool import CursorReusingConnection


PING_AFTER_IDLE_SECONDS = 60


@lru_cache
def get_engine() -> Engine:
    """
    One engine (and its connection pool) for the whole process.

    Ping before reuse, only after a quiet spell: a pooled connection that sat idle for more than
    PING_AFTER_IDLE_SECONDS gets a tiny query first, and a dead one is replaced (Azure SQL closes
    idle connections after a while). A connection used moments ago is not pinged: pinging on every
    request (pool_pre_ping) cost one extra round trip (~0.25 s from a PC) per request.
    """
    engine = create_engine(
        get_settings().database_url,
        pool_recycle=1800,  # replace connections older than 30 minutes
    )

    @event.listens_for(engine, "checkin")
    def _remember_last_use(dbapi_connection, connection_record):
        connection_record.info["last_used"] = time.monotonic()

    @event.listens_for(engine, "checkout")
    def _ping_if_idle(dbapi_connection, connection_record, connection_proxy):
        last = connection_record.info.get("last_used")
        if last is None or time.monotonic() - last < PING_AFTER_IDLE_SECONDS:
            return  # new, or used moments ago
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.fetchall()
        except Exception as error:
            # The pool discards this connection and checks out a fresh one.
            raise exc.DisconnectionError() from error
        finally:
            cursor.close()

    @event.listens_for(engine, "do_connect")
    def _reuse_cursors(dialect, conn_rec, cargs, cparams):
        # Saves one round trip per query; see app/db/cursor_pool.py.
        return CursorReusingConnection(dialect.loaded_dbapi.connect(*cargs, **cparams))

    return engine


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
