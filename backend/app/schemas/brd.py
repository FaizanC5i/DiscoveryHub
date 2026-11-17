"""Request and response shapes for BRD generation. Datetimes are sent as UTC ISO strings."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

UtcDatetime = Annotated[datetime, PlainSerializer(lambda v: v.replace(tzinfo=timezone.utc).isoformat())]


class ClarificationAnswer(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(max_length=20000)


class RegenerateRequest(BaseModel):
    """Optional answers to the section's clarification questions. They are saved and reused."""

    answers: list[ClarificationAnswer] = Field(default_factory=list, max_length=10)


class SectionEdit(BaseModel):
    content: str = Field(min_length=1, max_length=100000)


class BrdRunQueued(BaseModel):
    agent_run_id: int


class BrdRun(BaseModel):
    id: int
    run_type: str
    status: str
    section_key: str | None
    error_message: str | None
    started_at: UtcDatetime
    completed_at: UtcDatetime | None


class Proposal(BaseModel):
    id: int
    status: str
    content: str | None
    missing_reason: str | None
    questions: list[str]
    created_at: UtcDatetime


class Clarification(BaseModel):
    id: int
    question: str
    answer: str
    created_at: UtcDatetime


class BrdSection(BaseModel):
    section_key: str
    title: str
    sort_order: int
    fed_by_checkpoints: list[str]
    status: str
    content: str | None
    source: str | None
    approved_at: UtcDatetime | None
    open_proposal: Proposal | None
    clarifications: list[Clarification]


class BrdRead(BaseModel):
    project_id: int
    status: str
    current_version: int
    approved_answer_count: int
    sections: list[BrdSection]
    latest_run: BrdRun | None


class BrdApproved(BaseModel):
    version_number: int
    approved_at: UtcDatetime


class BrdVersionSummary(BaseModel):
    version_number: int
    approved_by: int | None
    approved_at: UtcDatetime


class BrdVersionSection(BaseModel):
    section_key: str
    title: str
    sort_order: int
    status: str
    content: str | None


class BrdVersion(BrdVersionSummary):
    sections: list[BrdVersionSection]
