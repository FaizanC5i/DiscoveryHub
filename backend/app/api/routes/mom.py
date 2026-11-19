"""
Meeting Minutes assistant endpoints. Each request carries the transcript and any earlier output it
needs, so the server keeps no state between requests. Every route requires a signed-in user.
"""

from typing import Any, Literal

from fastapi import APIRouter, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.errors import api_error
from app.dependencies.auth import CurrentUser
from app.services import mom_documents
from app.services.agent_client import (
    AgentConfigurationError,
    AgentError,
    AgentTimeoutError,
    call_mom_agent,
    call_with_retry,
)
from app.services.mom_response import MomResponseError, extract_meeting_output, unwrap_output
from app.services.mom_transcript import TranscriptError, read_transcript

router = APIRouter(prefix="/api/mom", tags=["mom"])

MAX_FILES = 10


class TranscriptBody(BaseModel):
    transcript: str


class DetailedBody(BaseModel):
    transcript: str
    previous_mom: Any


class DownloadBody(BaseModel):
    document: Literal["mom", "detailed-summary"]
    format: Literal["docx", "md", "json"]
    output: Any
    project_name: str | None = None
    source_name: str | None = None


def _call_agent(payload: dict, document_type: str) -> dict:
    try:
        response = call_with_retry(lambda: call_mom_agent(payload), f"Meeting minutes ({document_type})")
        output = extract_meeting_output(response)
    except AgentConfigurationError as exc:
        raise api_error(503, "AGENT_NOT_CONFIGURED", str(exc)) from None
    except AgentTimeoutError as exc:
        raise api_error(504, "AGENT_TIMEOUT", str(exc)) from None
    except AgentError as exc:
        raise api_error(502, "AGENT_FAILED", str(exc)) from None
    except MomResponseError as exc:
        raise api_error(502, "UNEXPECTED_AGENT_RESPONSE", str(exc)) from None

    body, project_title = unwrap_output(output)
    document = mom_documents.build_document(output, body, project_title, None, document_type)
    return {
        "output": output,
        "project_name": document["project_name"],
        "preview": mom_documents.to_markdown(document),
    }


@router.post("/transcripts")
async def read_transcripts(files: list[UploadFile]) -> dict:
    if not files:
        raise api_error(422, "NO_FILES", "Please upload at least one meeting transcript.")
    if len(files) > MAX_FILES:
        raise api_error(422, "TOO_MANY_FILES", f"Upload at most {MAX_FILES} transcripts at once.")

    parts: list[str] = []
    details: list[dict] = []
    for upload in files:
        name = upload.filename or "transcript"
        raw = await upload.read()
        try:
            text = read_transcript(name, raw)
        except TranscriptError as exc:
            raise api_error(422, "TRANSCRIPT_INVALID", str(exc)) from None
        parts.append(f"=== {name} ===\n{text}")
        details.append({
            "name": name,
            "type": upload.content_type or "",
            "size": len(raw),
            "characters": len(text),
        })
    return {"transcript": "\n\n".join(parts), "files": details}


@router.post("/minutes")
def generate_minutes(body: TranscriptBody, user: CurrentUser) -> dict:
    if not body.transcript.strip():
        raise api_error(422, "EMPTY_TRANSCRIPT", "The transcript is empty.")
    payload = {"generation_mode": "generate_mom", "meeting_transcript": body.transcript}
    return _call_agent(payload, "mom")


@router.post("/detailed-summary")
def generate_detailed(body: DetailedBody, user: CurrentUser) -> dict:
    if not body.transcript.strip():
        raise api_error(422, "EMPTY_TRANSCRIPT", "The transcript is empty.")
    if not body.previous_mom:
        raise api_error(422, "MOM_REQUIRED", "Generate the Minutes of Meeting before the detailed summary.")
    payload = {
        "generation_mode": "generate_detailed_summary",
        "meeting_transcript": body.transcript,
        "previous_mom": body.previous_mom,
    }
    return _call_agent(payload, "detailed-summary")


@router.post("/download")
def download(body: DownloadBody, user: CurrentUser) -> Response:
    if body.output is None:
        raise api_error(422, "NOTHING_TO_DOWNLOAD", "Generate this document first.")

    body_part, project_title = unwrap_output(body.output)
    document = mom_documents.build_document(
        body.output, body_part, body.project_name or project_title, body.source_name, body.document
    )

    base = (body.source_name or "meeting").rsplit(".", 1)[0]
    safe_base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in base).strip("_") or "meeting"
    suffix = "MoM" if body.document == "mom" else "Detailed_Summary"
    filename = f"{safe_base}_{suffix}.{body.format}"

    if body.format == "json":
        return Response(
            mom_documents.to_json(document),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    if body.format == "md":
        return Response(
            mom_documents.to_markdown(document).encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return Response(
        mom_documents.to_docx(document),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
