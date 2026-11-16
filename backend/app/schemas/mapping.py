"""
Response shapes for saved checkpoint mappings. The evidence offsets are included so a client
can verify any quote with content_text[evidence_start_char:evidence_end_char].
"""

from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer


class MappingRead(BaseModel):
    id: int
    project_id: int
    context_chunk_id: int
    context_content_id: int
    chunk_number: int
    checkpoint_id: int
    checkpoint_code: str
    checkpoint_name: str
    pillar_name: str
    evidence_quote: str
    evidence_start_char: int
    evidence_end_char: int
    reason: str
    created_at: datetime

    @field_serializer("created_at")
    def _as_utc(self, value: datetime) -> str:
        return value.replace(tzinfo=timezone.utc).isoformat()


class MappingRetryQueued(BaseModel):
    queued: int
