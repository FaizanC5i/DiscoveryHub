"""
Reuse ODBC cursors on a connection, to save one network round trip per query.

Why: SQL Server's ODBC driver prepares every query that has parameters (all of ours do) and,
when the cursor is closed, sends a separate "unprepare" message and waits for the answer. From a
PC to Azure SQL that is one more round trip (~0.26 s) per query, so every page paid twice.
When the same cursor runs the next query instead, the driver sends the unprepare together with
it, for free. Measured: 0.59 s -> 0.31 s per query.

How: the connection handed to SQLAlchemy keeps the cursors the app has closed in a small pool and
gives one back on the next cursor() call. A cursor is reused only after the app closed it, so two
open results never share a cursor. A cursor that raised an error is really closed, not reused.

Analogy: a waiter who takes your order on the way back from clearing the last table, instead of
making a separate trip to the kitchen just to say "table cleared".
"""

from typing import Any

MAX_IDLE_CURSORS = 4


class _PooledCursor:
    """What SQLAlchemy sees as a cursor. close() hands the real cursor back to the pool."""

    __slots__ = ("_cursor", "_owner", "_closed", "_failed")

    def __init__(self, cursor: Any, owner: "CursorReusingConnection") -> None:
        self._cursor = cursor
        self._owner = owner
        self._closed = False
        self._failed = False

    def execute(self, *args: Any, **kwargs: Any) -> "_PooledCursor":
        try:
            self._cursor.execute(*args, **kwargs)
        except BaseException:
            self._failed = True
            raise
        return self

    def executemany(self, *args: Any, **kwargs: Any) -> "_PooledCursor":
        try:
            self._cursor.executemany(*args, **kwargs)
        except BaseException:
            self._failed = True
            raise
        return self

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._owner._release(self._cursor, reuse=not self._failed)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _PooledCursor.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._cursor, name, value)

    def __iter__(self):
        return iter(self._cursor)


class CursorReusingConnection:
    """Wraps a pyodbc connection; everything except cursor() and close() is passed through."""

    def __init__(self, connection: Any) -> None:
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_idle", [])

    def cursor(self) -> _PooledCursor:
        idle = self._idle
        return _PooledCursor(idle.pop() if idle else self._connection.cursor(), self)

    def _release(self, cursor: Any, reuse: bool) -> None:
        if reuse and len(self._idle) < MAX_IDLE_CURSORS:
            self._idle.append(cursor)
            return
        try:
            cursor.close()
        except Exception:  # noqa: BLE001 - the connection may already be gone
            pass

    def close(self) -> None:
        self._idle.clear()  # closing the connection closes its cursors
        if not getattr(self._connection, "closed", False):  # already closed: nothing to do
            self._connection.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._connection, name, value)  # for example autocommit
