"""
Application settings, loaded from environment variables (and an optional `.env` file).

Analogy: think of this module as the building's fuse box and the `.env` file as the
label sheet taped inside the door. The code only says "there is a database here",
and the label sheet says which one. Swapping the label sheet (dev -> prod) changes
the behaviour without touching the code, and the sheet itself is never committed.

Why not hard-code values? Credentials in source code end up in Git history, in
screenshots and in every copy of the repo. Environment variables stay on the
machine (or in the hosting platform's secret store) where they belong.
"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, resolved from this file so it works no matter which folder
# the server is started from.
BACKEND_DIR = Path(__file__).resolve().parents[2]

# The JWT secret signs every access token. Anyone who knows it can forge a
# login for any user, so we refuse to start with a short or placeholder value.
MIN_JWT_SECRET_LENGTH = 32
PLACEHOLDER_SECRETS = {"change-me", "changeme", "secret", "replace-me"}


class Settings(BaseSettings):
    """Every setting the backend needs. Field names map to env vars in UPPER_CASE."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Environment -----------------------------------------------------
    # "development" or "production". Production turns on Secure cookies.
    environment: str = "development"

    # --- Database (Azure SQL via ODBC Driver 18) -------------------------
    db_server: str
    db_name: str
    db_user: str
    db_password: str
    db_driver: str = "ODBC Driver 18 for SQL Server"

    # --- JWT -------------------------------------------------------------
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"  # pinned; we never accept "none" or RS/HS mixing
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    reset_token_minutes: int = 30

    # --- URLs and CORS ---------------------------------------------------
    frontend_url: str = "http://localhost:3000"

    # --- Cookies -----------------------------------------------------------
    # Secure cookies are only sent over HTTPS. Derived from environment by default.
    cookie_secure: bool | None = None
    cookie_samesite: str = "lax"

    # --- Email (optional). When SMTP_HOST is empty, reset links are logged. --
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "no-reply@discoveryhub.local"

    # --- Rate limits (slowapi / limits syntax) ----------------------------
    login_rate_limit: str = "5/minute"
    forgot_password_rate_limit: str = "3/minute"

    @field_validator("jwt_secret_key")
    @classmethod
    def _secret_must_be_strong(cls, value: str) -> str:
        """Fail fast at startup instead of silently signing tokens with a weak key."""
        if len(value) < MIN_JWT_SECRET_LENGTH or value.lower() in PLACEHOLDER_SECRETS:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters "
                "and not a placeholder. Generate one with secrets.token_urlsafe(64)."
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def secure_cookies(self) -> bool:
        """Secure flag: explicit setting wins, otherwise on only in production."""
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.is_production

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy URL for Azure SQL.

        The password is URL-encoded and the ODBC string is wrapped in braces so
        characters such as '@', ';' or '}' in the password cannot break parsing.
        """
        odbc = (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER=tcp:{self.db_server},1433;"
            f"DATABASE={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={{{self.db_password}}};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


@lru_cache
def get_settings() -> Settings:
    """
    Build the settings once and reuse them.

    Analogy: reading the label sheet once when the building opens, instead of
    walking back to the fuse box every time a light switch is flipped.
    """
    return Settings()  # type: ignore[call-arg]
