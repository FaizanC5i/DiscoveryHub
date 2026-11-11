"""
Security primitives: password hashing, JWT access tokens, and opaque token hashing.

These functions know nothing about HTTP or the database. That separation makes
them easy to test and to reason about.
"""

import hashlib
import secrets

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.core.time import add_minutes, utc_now

# -----------------------------------------------------------------------------
# Password hashing (Argon2id)
# -----------------------------------------------------------------------------
#
# Analogy: a meat grinder. You can put a password in and get a hash out, but
# you cannot turn the hash back into the password. Checking a login means
# putting the typed password through the same grinder with the same settings
# and comparing the output.
#
# Why Argon2id and not plain SHA-256? SHA-256 is designed to be fast, which is
# exactly wrong for passwords: an attacker with a stolen table can try billions
# of guesses per second on a GPU. Argon2 is deliberately memory-hungry and slow,
# so each guess costs real hardware time. Its salt (random per password) means
# two users with the same password get different hashes.
#
# Argon2 also avoids bcrypt's 72-byte input limit, which silently ignores any
# characters past 72.

_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Return a self-describing Argon2 hash string (includes salt and parameters)."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    True when the plain password matches the stored hash.

    Any failure (wrong password, malformed hash) returns False. Callers must not
    reveal which of these happened; both are reported as "invalid credentials".
    """
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# -----------------------------------------------------------------------------
# Access tokens (JWT)
# -----------------------------------------------------------------------------
#
# Analogy: a concert wristband. It proves you bought a ticket and says when the
# event ends (exp). The security staff check the band's stamp (signature) and
# its end time, but they do not phone the box office for every person. That is
# why JWTs are fast to verify, and also why they cannot be revoked instantly.
# Hence the access token is short-lived (15 minutes) and the refresh token,
# which *is* stored and revocable, does the long-term work.
#
# What goes in the token: only the user id (sub) and timestamps. Never the
# password, the password hash, the email or any other secret. Anyone holding the
# token can decode it, because the payload is base64, not encrypted.

ACCESS_TOKEN_TYPE = "access"


def create_access_token(user_id: int) -> str:
    """Sign a short-lived access token for the given user."""
    settings = get_settings()
    now = utc_now()
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,  # stops a token meant for another purpose being accepted here
        "iat": now,
        "exp": add_minutes(now, settings.access_token_minutes),
        "jti": secrets.token_urlsafe(16),  # unique id per token, useful for logging
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class InvalidAccessToken(Exception):
    """Raised for any reason the access token cannot be trusted."""


def decode_access_token(token: str) -> int:
    """
    Verify an access token and return the user id it belongs to.

    algorithms=[HS256] is pinned on purpose. Without it, an attacker could craft
    a token claiming alg "none" (no signature), which some libraries accept by
    default. Pinning the algorithm closes that door.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessToken("Access token is invalid or expired") from exc

    if claims.get("type") != ACCESS_TOKEN_TYPE:
        raise InvalidAccessToken("Token is not an access token")

    try:
        return int(claims["sub"])
    except (TypeError, ValueError) as exc:
        raise InvalidAccessToken("Token subject is malformed") from exc


# -----------------------------------------------------------------------------
# Opaque tokens (refresh tokens and password-reset tokens)
# -----------------------------------------------------------------------------
#
# Analogy: a hotel booking confirmation number. The guest keeps the real number,
# and the hotel keeps only a record of it. If the hotel's records leak, nobody
# can check in with them, because the desk only ever sees the number's
# fingerprint. Here the browser holds the raw token and the database stores its
# SHA-256 hash.
#
# secrets.token_urlsafe(48) gives 384 bits of randomness, so guessing a token is
# not feasible. A fast hash such as SHA-256 is acceptable for these tokens
# (unlike passwords) because their input is already random and long.


def generate_opaque_token() -> str:
    """A cryptographically random, URL-safe token string."""
    return secrets.token_urlsafe(48)


def hash_token(raw_token: str) -> str:
    """SHA-256 hex digest (64 chars), safe to store and index in the database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
