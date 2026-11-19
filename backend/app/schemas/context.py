"""
Response shapes for documents and notes. The extracted text is deliberately not
included in SourceRead: the list endpoint would otherwise send every document's full
text. NoteRead is the one-note detail view and does carry the text.
"""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_serializer

from app.services.context_service import NOTE_BODY_MAX_LENGTH, NOTE_TITLE_MAX_LENGTH


def _as_utc(value: datetime | None) -> str | None:
    return None if value is None else value.replace(tzinfo=timezone.utc).isoformat()


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    source_type: str
    title: str
    original_filename: str | None
    mime_type: str
    file_size_bytes: int
    processing_status: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime | None
    # True while the helper agent still has chunks of this source to map.
    mapping_pending: bool = False

    @field_serializer("created_at")
    def _created_utc(self, value: datetime) -> str:
        return _as_utc(value)

    @field_serializer("updated_at")
    def _updated_utc(self, value: datetime | None) -> str | None:
        return _as_utc(value)


class NoteInput(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NOTE_TITLE_MAX_LENGTH)]
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NOTE_BODY_MAX_LENGTH)]


class NoteRead(BaseModel):
    id: int
    project_id: int
    title: str
    body: str
    processing_status: str
    failure_reason: str | None
    chunk_count: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime | None

    @field_serializer("created_at")
    def _created_utc(self, value: datetime) -> str:
        return _as_utc(value)

    @field_serializer("updated_at")
    def _updated_utc(self, value: datetime | None) -> str | None:
        return _as_utc(value)
