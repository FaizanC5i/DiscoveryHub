"""
Authentication business rules: sign-up, login, sessions, refresh, password reset.

This layer knows the rules but not HTTP. It raises AuthError, and the route
layer turns that into a status code and a JSON body. That keeps the rules
testable without a web server.

Analogy: the back office of a hotel. The front desk (routes) talks to guests,
but the decisions about room keys, cancelled bookings and refunds are made here,
following the same policy for every guest.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.time import add_days, add_minutes, utc_now
from app.db.models import PasswordResetToken, RefreshToken, User

logger = logging.getLogger("app.auth")

# If a refresh token is presented again within this many seconds of being
# rotated, treat it as a harmless double-submit (two tabs or a race between the
# proxy and the browser), not as theft. See refresh_session() for the reasoning.
REFRESH_REUSE_GRACE_SECONDS = 10


@dataclass
class AuthError(Exception):
    """
    A rule was broken, with a stable machine-readable code for the frontend.

    status_code: HTTP status to return.
    code: short constant the frontend can branch on (e.g. ACCOUNT_NOT_FOUND).
    message: human-readable text. Safe to show to the user.
    """

    status_code: int
    code: str
    message: str


@dataclass
class IssuedSession:
    """What a successful login or refresh hands back: an access token and a raw refresh token."""

    user: User
    access_token: str
    refresh_token: str


# -----------------------------------------------------------------------------
# Lookups
# -----------------------------------------------------------------------------


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


# -----------------------------------------------------------------------------
# Sign-up
# -----------------------------------------------------------------------------


def sign_up(db: Session, name: str, email: str, password: str) -> User:
    """
    Create an account. The email must be unused.

    The pre-check gives a friendly error. The database's unique constraint is the
    real guard: two sign-ups with the same email at the same instant would both
    pass the pre-check, and the second INSERT then fails with IntegrityError.
    """
    if _get_user_by_email(db, email) is not None:
        raise AuthError(409, "EMAIL_TAKEN", "An account with this email already exists")

    user = User(
        name=name,
        email=email.lower(),
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AuthError(409, "EMAIL_TAKEN", "An account with this email already exists") from exc
    db.refresh(user)
    logger.info("user_signed_up user_id=%s", user.id)
    return user


# -----------------------------------------------------------------------------
# Login and session issuing
# -----------------------------------------------------------------------------


def authenticate(db: Session, email: str, password: str) -> User:
    """
    Check an email and password. Returns the user or raises AuthError.

    Three distinct outcomes, as the product requires:
      - no such email          -> 404 ACCOUNT_NOT_FOUND (frontend offers Sign Up)
      - wrong password         -> 401 INVALID_CREDENTIALS (generic)
      - account deactivated    -> 403 ACCOUNT_DISABLED

    Trade-off: returning ACCOUNT_NOT_FOUND lets someone discover which emails
    have accounts. That is the product decision. The rate limit on /login limits
    how fast anyone can probe.
    """
    user = _get_user_by_email(db, email)
    if user is None:
        logger.info("login_failed reason=account_not_found")
        raise AuthError(404, "ACCOUNT_NOT_FOUND", "No account found for this email")

    if not verify_password(password, user.password_hash):
        # Log the user id, never the email or the password.
        logger.info("login_failed reason=bad_password user_id=%s", user.id)
        raise AuthError(401, "INVALID_CREDENTIALS", "Incorrect email or password")

    if not user.is_active:
        logger.info("login_failed reason=inactive user_id=%s", user.id)
        raise AuthError(403, "ACCOUNT_DISABLED", "This account is disabled")

    return user


def _create_refresh_token(db: Session, user_id: int) -> str:
    """
    Make a new refresh token, store its hash, and return the raw value.

    The raw value is returned exactly once, to be placed in the cookie. After
    this function returns, the database holds only its SHA-256 fingerprint.
    """
    settings = get_settings()
    raw = generate_opaque_token()
    now = utc_now()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=add_days(now, settings.refresh_token_days),
        )
    )
    return raw


def issue_session(db: Session, user: User) -> IssuedSession:
    """Start a new login session: one access token and one refresh token row."""
    refresh_raw = _create_refresh_token(db, user.id)
    db.commit()
    logger.info("session_started user_id=%s", user.id)
    return IssuedSession(
        user=user,
        access_token=create_access_token(user.id),
        refresh_token=refresh_raw,
    )


# -----------------------------------------------------------------------------
# Refresh (rotation with reuse detection)
# -----------------------------------------------------------------------------


def refresh_session(db: Session, raw_refresh_token: str) -> IssuedSession:
    """
    Exchange a valid refresh token for a new access token and a new refresh token.

    Rotation: each refresh token is single-use. Using it cancels it and issues a
    successor. A stolen token is therefore useful only until its owner next
    refreshes.

    Reuse detection: if a token that has already been cancelled comes back, one
    of two things happened. Either a thief replayed a copy, or the legitimate
    client retried after a lost response. Because the two cannot be told apart,
    the safe response is to cancel every session for that user and force a new
    login. The grace window covers the harmless case of two requests racing
    within a few seconds, which must not log the user out.
    """
    now = utc_now()
    token_row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh_token))
    )
    if token_row is None:
        raise AuthError(401, "INVALID_REFRESH", "Session is no longer valid. Please sign in again.")

    if token_row.revoked_at is not None:
        seconds_since_rotation = (now - token_row.revoked_at).total_seconds()
        if seconds_since_rotation <= REFRESH_REUSE_GRACE_SECONDS:
            # Harmless race: another request already rotated this token moments ago.
            raise AuthError(401, "REFRESH_RACE", "Session refresh was already handled. Retry.")

        # Outside the grace window: treat as theft and end every session for this user.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == token_row.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        logger.warning("refresh_reuse_detected user_id=%s all_sessions_revoked", token_row.user_id)
        raise AuthError(401, "REFRESH_REUSED", "Session was revoked. Please sign in again.")

    if token_row.expires_at <= now:
        raise AuthError(401, "INVALID_REFRESH", "Session has expired. Please sign in again.")

    user = get_user_by_id(db, token_row.user_id)
    if user is None or not user.is_active:
        raise AuthError(401, "INVALID_REFRESH", "Session is no longer valid. Please sign in again.")

    # Rotate: cancel the presented token and issue its successor.
    token_row.revoked_at = now
    new_refresh_raw = _create_refresh_token(db, user.id)
    db.commit()
    logger.info("session_refreshed user_id=%s", user.id)
    return IssuedSession(
        user=user,
        access_token=create_access_token(user.id),
        refresh_token=new_refresh_raw,
    )


def revoke_refresh_token(db: Session, raw_refresh_token: str | None) -> None:
    """
    Cancel one session (logout). Idempotent: an unknown or already-cancelled token is not an error.

    Logging out with an expired or missing cookie should still succeed from the
    user's point of view: they just want to be signed out.
    """
    if not raw_refresh_token:
        return
    token_row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh_token))
    )
    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = utc_now()
        db.commit()
        logger.info("session_revoked user_id=%s", token_row.user_id)


# -----------------------------------------------------------------------------
# Password reset
# -----------------------------------------------------------------------------


def request_password_reset(db: Session, email: str) -> str | None:
    """
    Create a reset token for an existing account. Returns the raw token, or None.

    The route always returns the same HTTP response, so the message body never
    reveals whether the email exists. The email itself is sent in a background
    task after the response, so a slow SMTP server does not change the response
    time. Some timing difference remains (existing accounts do database writes,
    unknown ones return early); closing that fully would need a dummy write on
    the unknown path, which is left out for simplicity.

    Any earlier unused reset tokens are cancelled, so only the newest link works.
    """
    user = _get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None

    settings = get_settings()
    now = utc_now()

    # Retire older unused reset links for this user.
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )

    raw = generate_opaque_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=add_minutes(now, settings.reset_token_minutes),
        )
    )
    db.commit()
    logger.info("password_reset_requested user_id=%s", user.id)
    return raw


def reset_password(db: Session, raw_reset_token: str, new_password: str) -> None:
    """
    Spend a reset token and set a new password.

    Every failure reason (unknown, used, expired, disabled account) returns the
    same message. Telling the caller which one applied would help an attacker
    probe the token space.

    On success, every refresh token for the user is revoked: anyone who had a
    session under the old password, including an attacker, is logged out.
    """
    now = utc_now()
    invalid = AuthError(400, "INVALID_RESET_TOKEN", "This reset link is invalid or has expired")

    token_row = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(raw_reset_token)
        )
    )
    if token_row is None or token_row.used_at is not None or token_row.expires_at <= now:
        raise invalid

    user = get_user_by_id(db, token_row.user_id)
    if user is None or not user.is_active:
        raise invalid

    user.password_hash = hash_password(new_password)
    user.updated_at = now
    token_row.used_at = now
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()
    logger.info("password_reset_completed user_id=%s all_sessions_revoked", user.id)
