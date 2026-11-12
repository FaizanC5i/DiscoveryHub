"""
Response shape for a document. The extracted text is deliberately not included:
the list endpoint would otherwise send every document's full text.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    processing_status: str
    failure_reason: str | None
    created_at: datetime

    @field_serializer("created_at")
    def _as_utc(self, value: datetime) -> str:
        return value.replace(tzinfo=timezone.utc).isoformat()