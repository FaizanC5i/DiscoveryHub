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

        # --- Document storage and OCR ----------------------------------------
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "project-sources"
    upload_max_mb: int = 20

    # --- Chunking -----------------------------------------------------------
    # Size of one chunk and how much of the previous chunk is repeated at its start.
    chunk_max_chars: int = 1000
    chunk_overlap_chars: int = 150

    # --- Agent5i Helper Agent (checkpoint mapping) -------------------------
    # Credentials come from the environment only. An empty value makes mapping fail
    # with a configuration error, which is never retried.
    agent5i_webhook_url: str = ""
    agent5i_username: str = ""
    agent5i_password: str = ""
    agent5i_agent_name: str = "Discovery Hub Helper Agent"
    agent5i_source_input_name: str = "source_files"
    agent5i_timeout_seconds: int = 180
    # Chunks per agent call. Larger batches cut the number of calls and the repeated checkpoint prompt.
    mapping_batch_size: int = 20

    agent5i_user_agent_name: str = "User Discovery Agent"
    user_agent_timeout_seconds: int = 300

    # --- Agent5i Meeting Minutes agent (MoM assistant), same webhook and login as above ---
    mom_agent_name: str = "Meeting Minutes"
    mom_timeout_seconds: int = 300

    # --- Pillar dispatch ----------------------------------------------------
    # Right after each Helper batch is saved, its new mappings are grouped per pillar agent.
    # Until the pillar agents exist, each package is written as JSON under backend/<this folder>.
    # Empty turns dispatch off.
    pillar_dispatch_outbox: str = "agent_outbox"

    # --- Agent5i BRD agent (BRD generation from approved checkpoint answers) --
    # Same webhook as the Helper. When the BRD agent lives in another Agent5i account, set
    # BRD_AGENT5I_USERNAME / BRD_AGENT5I_PASSWORD; empty means "use the AGENT5I_* login".
    brd_agent_name: str = "BRD Extraction Agent"
    brd_agent5i_username: str = ""
    brd_agent5i_password: str = ""
    brd_timeout_seconds: int = 300
    # Regenerate the BRD in the background whenever a User Discovery answer is approved.
    # Off: the BRD changes only when the user clicks Generate, Refresh, Regenerate or Clarify
    # (every automatic run costs a full agent call). On: regenerate after each approved answer.
    brd_auto_refresh: bool = False

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
