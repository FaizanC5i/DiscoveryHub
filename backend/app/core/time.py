"""
Time helpers.

Analogy: a shared clock on the wall. Every part of the system reads the same
clock, in UTC, so a token created in one timezone expires at the same moment
when checked from another.

Why naive UTC? SQL Server's DATETIME2 column has no timezone. We store UTC values
(the database default is SYSUTCDATETIME()) and keep Python values naive UTC too,
so comparisons never mix aware and naive datetimes (which raises TypeError).
"""

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """Current time in UTC, without tzinfo, matching what the database stores."""
    return datetime.now(UTC).replace(tzinfo=None)


def add_minutes(moment: datetime, minutes: int) -> datetime:
    return moment + timedelta(minutes=minutes)


def add_days(moment: datetime, days: int) -> datetime:
    return moment + timedelta(days=days)
