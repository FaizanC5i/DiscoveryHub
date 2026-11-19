"""
Response shape for one chunk. The offsets are included so a client can check any
quote with content_text[start_char:end_char], and so the agent can cite exact characters.
"""

from pydantic import BaseModel, ConfigDict


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    context_content_id: int
    chunk_number: int
    start_char: int
    end_char: int
    char_count: int
    page_number: int | None
    chunk_text: str
