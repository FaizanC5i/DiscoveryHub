"""
Request and response shapes for the /api/projects endpoints.

Analogy: the project intake form. Each box has a rule printed beside it: the
name is required, the description has a length limit, and the finish date
cannot come before the start date. Pydantic checks the form before the service
runs, so the service can assume the data is well-formed.

The frontend checks the same rules to give faster feedback. The backend check
is the real one, because the browser can always be bypassed.
"""

from datetime import date, datetime, timezone

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

NAME_MAX_LENGTH = 255
DESCRIPTION_MAX_LENGTH = 12000


def clean_name(value: str) -> str:
    """Trim the name and reject a blank one. Shared by create and update."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Project name is required")
    if len(cleaned) > NAME_MAX_LENGTH:
        raise ValueError(f"Project name must be at most {NAME_MAX_LENGTH} characters")
    return cleaned


def clean_description(value: str | None) -> str | None:
    """Trim the description. An empty description is stored as NULL, not as an empty string."""
    if value is None:
        return None
    cleaned = value.strip()
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters")
    return cleaned or None


def check_date_order(start: date | None, end: date | None) -> None:
    """Raise when the finish date is before the start date. Missing dates are allowed."""
    if start is not None and end is not None and end < start:
        raise ValueError("End date cannot be before the start date")


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        return clean_name(value)

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str | None) -> str | None:
        return clean_description(value)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "ProjectCreate":
        check_date_order(self.start_date, self.end_date)
        return self


class ProjectUpdate(BaseModel):
    """
    Partial update. A field that is left out keeps its stored value.
    A field sent as null clears it (only allowed for description and dates).
    """

    name: str | None = Field(default=None)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        # Only runs when the field is sent. A name cannot be cleared, so an explicit null is rejected.
        if value is None:
            raise ValueError("Project name is required")
        return clean_name(value)

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str | None) -> str | None:
        return clean_description(value)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "ProjectUpdate":
        # Only checks dates sent together. The service re-checks against the stored dates.
        check_date_order(self.start_date, self.end_date)
        return self


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    owner_name: str
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _as_utc(self, value: datetime) -> str:
        # The database stores naive UTC. Adding the offset means the browser converts it to local time correctly.
        return value.replace(tzinfo=timezone.utc).isoformat()
