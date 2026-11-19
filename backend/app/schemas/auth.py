"""
Request and response shapes for the /api/auth endpoints.

Analogy: these are the order forms. Each field on the form has rules printed next
to it (required, max length, must be an email). Pydantic checks the form before
the clerk (the route) ever reads it, so the rest of the code can assume the data
is well-formed.

These checks are the backend's source of truth. The frontend repeats them only
to give faster feedback; it is never trusted.
"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# A password needs at least one letter and one digit, on top of the length rule.
# Length is the strongest single factor; the letter/digit rule rejects the most
# obvious choices like "12345678".
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"[0-9]")

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128  # long enough for passphrases, short enough to stop hashing abuse


def validate_password_strength(password: str) -> str:
    """
    Shared password rule for sign-up and reset.

    Keeping this in one function means the two entry points can never drift apart.
    Raises ValueError, which Pydantic turns into a 422 with a readable message.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
    if not _HAS_LETTER.search(password) or not _HAS_DIGIT.search(password):
        raise ValueError("Password must contain at least one letter and one number")
    return password


class SignUpRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        # Strip surrounding spaces and collapse inner runs, so "  Alex   Kim " is stored as "Alex Kim".
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        # Email local parts are technically case-sensitive, but in practice nobody relies on that.
        # Lowercasing prevents "Alex@x.com" and "alex@x.com" from becoming two accounts.
        return value.lower()

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    # No strength rules on login: old accounts must still be able to sign in,
    # and the rules only apply when a password is chosen.
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return value.lower()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return value.lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserResponse(BaseModel):
    """
    What the outside world may see about a user.

    Deliberately has no password_hash field. Keeping the response model narrow
    means a future model change cannot leak new columns by accident.
    """

    id: int
    name: str
    email: str


class MessageResponse(BaseModel):
    message: str
