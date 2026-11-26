"""
The Artifact Studio screens' data, in exactly the shapes the frontend already uses
(frontend/features/artifact-studio/types/artifact-studio.types.ts), so the frontend only has to
replace each placeholder in artifact-studio.service.ts with the matching API call.

Analogy: the shop window. The BRD itself lives in the stock room (brd_service and its tables);
this module arranges it the way the window is designed: bullets, badges, a banner and a
version list. It adds no rules of its own: every change goes through brd_service.

The BRD and the PRD can be generated (both through brd_service, with code="BRD" or "PRD").
The other artifact types are listed (the picker shows them) but their draft routes answer
404 ARTIFACT_NOT_AVAILABLE.
"""

import io as _io
import re
from pathlib import Path

from app.services import mom_documents
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.db.models import (
    ArtifactType,
    ArtifactTypePillar,
    ContextSource,
    Project,
    ProjectArtifact,
    ProjectArtifactVersion,
)
from app.services import artifact_readiness, brd_service

# The artifact picker (same order and wording as the screen).
ARTIFACT_CATALOG = [
    {"code": "BRD", "name": "BRD", "description": "Business Requirements Document"},
    {"code": "PRD", "name": "PRD", "description": "Product Requirements Document"},
    {"code": "PROBLEM_STATEMENT", "name": "Problem Statement", "description": "A structured statement of the problem"},
    {"code": "USER_PERSONAS", "name": "User Personas", "description": "Representative users and their context"},
    {"code": "USER_STORIES", "name": "User Stories", "description": "Stories with acceptance criteria"},
    {"code": "DATA_DICTIONARY", "name": "Data Dictionary", "description": "Entities, fields, owners, and quality rules"},
    {"code": "ONTOLOGY", "name": "Ontology", "description": "Concepts, relationships, and shared vocabulary"},
    {"code": "SOLUTION_ARCHITECTURE", "name": "Solution Architecture", "description": "Components, integrations, data flows, and deployment"},
    {"code": "NFR", "name": "NFR", "description": "Non-functional requirements and targets"},
]
AUDIENCES = ["Executive sponsor", "Project owner", "Delivery team", "End users"]
GENERATED_CODES = {"BRD", "PRD"}
NAMES = {"BRD": "Business Requirements Document", "PRD": "Product Requirements Document"}
DEFAULT_MISSING_REASON = "No approved answer covers this section yet."
EXPORT_FORMATS = {"md", "docx", "pdf"}


# ---------------------------------------------------------------------------------------------
# Markdown <-> bullets (the editor shows and edits a list of bullet points)
# ---------------------------------------------------------------------------------------------


def markdown_to_bullets(markdown: str | None) -> list[str]:
    """
    One bullet per meaningful line. List markers, heading marks and bold marks are removed;
    a table becomes one bullet per row ("cell – cell"), without its header row.
    """
    if not markdown:
        return []
    lines = markdown.replace("\r\n", "\n").split("\n")
    is_separator = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
    bullets: list[str] = []
    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line or is_separator.match(line):
            continue
        if "|" in line and line.startswith("|"):
            if index + 1 < len(lines) and is_separator.match(lines[index + 1].strip()):
                continue  # table header row
            cells = [c.strip() for c in line.strip("|").split("|") if c.strip()]
            line = " – ".join(cells)
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^([-*•]|\d+[.)])\s+", "", line)
        line = line.replace("**", "").replace("__", "").strip()
        if line:
            bullets.append(line)
    return bullets


def bullets_to_markdown(bullets: list[str]) -> str:
    return "\n".join(f"- {b.strip()}" for b in bullets if b and b.strip())


# ---------------------------------------------------------------------------------------------
# Studio page
# ---------------------------------------------------------------------------------------------


def studio_data(db: Session, owner_id: int, project_id: int) -> dict:
    """GET /api/projects/{id}/artifact-studio"""
    _owned_project(db, owner_id, project_id)
    type_ids = {t.code: t.id for t in db.scalars(select(ArtifactType))}
    pillars_by_type: dict[int, set[int]] = {}
    for type_id, pillar_id in db.execute(select(ArtifactTypePillar.artifact_type_id, ArtifactTypePillar.pillar_id)):
        pillars_by_type.setdefault(type_id, set()).add(pillar_id)

    available = []
    for code, status in db.execute(
        select(ArtifactType.code, ProjectArtifact.status)
        .join(ProjectArtifact, ProjectArtifact.artifact_type_id == ArtifactType.id)
        .where(ProjectArtifact.project_id == project_id, ProjectArtifact.status != "NOT_STARTED")
    ):
        available.append({"code": code, "status": "ready" if status == "APPROVED" else "draft"})

    states = artifact_readiness.checkpoint_states(db, project_id, None)  # read once, shared by every type
    readiness = {}
    for item in ARTIFACT_CATALOG:
        pillar_ids = pillars_by_type.get(type_ids.get(item["code"], -1))  # None = every pillar
        readiness[item["code"]] = artifact_readiness.summarize(states, pillar_ids)

    return {
        "artifactTypes": ARTIFACT_CATALOG,
        "availableArtifacts": available,
        "audiences": AUDIENCES,
        "readiness": readiness,
    }


def generate(db: Session, owner_id: int, project_id: int, code: str, config: dict) -> int:
    """POST /api/projects/{id}/artifacts/{code}/generate  body {title, audience, scope}"""
    code = _require_generated(code)
    if config.get("audience") and config["audience"] not in AUDIENCES:
        raise api_error(422, "UNKNOWN_AUDIENCE", f"Audience must be one of: {', '.join(AUDIENCES)}")
    return brd_service.start_generate(db, owner_id, project_id, config, code=code)


# ---------------------------------------------------------------------------------------------
# Draft editor
# ---------------------------------------------------------------------------------------------


def draft(db: Session, owner_id: int, project_id: int, code: str) -> dict:
    """GET /api/projects/{id}/artifacts/{code}"""
    code = _require_generated(code)
    project = _owned_project(db, owner_id, project_id)
    brd = brd_service.get_brd(db, owner_id, project_id, code)
    artifact = _artifact(db, project_id, code)
    pillar_ids = brd_service._brd_pillar_ids(db, code)  # noqa: SLF001 - same package, one source of truth

    run = brd["latest_run"]
    sections = []
    for s in brd["sections"]:
        section = _draft_section(s)
        # The agent is busy with this section (a full generation counts for every section).
        section["isWorking"] = bool(run and run["status"] == "running" and run["section_key"] in (None, s["section_key"]))
        section["lastError"] = (
            run["error_message"] if run and run["status"] == "failed" and run["section_key"] == s["section_key"] else None
        )
        sections.append(section)
    ready = artifact_readiness.readiness(db, project_id, pillar_ids)
    current_snapshot = {
        "verified": ready["verified"], "total": ready["total"],
        "sources": artifact_readiness.source_count(db, project_id),
        "missing": ready["withoutEvidence"], "unreviewedExcluded": ready["awaitingReview"],
    }
    is_client_ready = (
        ready["total"] > 0
        and ready["verified"] == ready["total"]
        and all(s["status"] in ("APPROVED", "PENDING_REVIEW") for s in sections)
    )
    running = brd["latest_run"] is not None and brd["latest_run"]["status"] == "running"
    if running:
        status = "Generating"
    elif brd["status"] == "APPROVED":
        status = "Approved"
    elif brd["status"] == "NOT_STARTED":
        status = "Not started"
    else:
        status = "In Progress"

    return {
        "artifactCode": code,
        "artifactName": NAMES[code],
        "title": (artifact.title if artifact and artifact.title else project.name),
        "description": project.description or "",
        "status": status,
        "isClientReady": is_client_ready,
        "snapshot": _generation_snapshot(db, artifact) or current_snapshot,
        "versions": _versions(db, artifact),
        "sections": sections,
        # Extra fields the screen can use (not in the placeholder types yet).
        "audience": artifact.audience if artifact else None,
        "scope": artifact.scope if artifact else None,
        "isOutdated": brd["is_outdated"],
        # Answers approved since the BRD was last generated (shown next to the Refresh button).
        "newAnswerCount": (
            brd_service.answers_approved_since(db, project_id, brd["answers_as_of"], code) if brd["is_outdated"] else 0
        ),
        "latestRun": brd["latest_run"],
    }


def save_section(
    db: Session, owner_id: int, project_id: int, code: str, section_id: str,
    bullets: list[str] | None = None, content: str | None = None,
) -> dict:
    """PUT /api/projects/{id}/artifacts/{code}/sections/{sectionId}  body {content} (Markdown) or {bullets}"""
    code = _require_generated(code)
    content = (content or "").strip() or bullets_to_markdown(bullets or [])
    if not content:
        raise api_error(422, "EMPTY_CONTENT", "Add at least one bullet point")
    brd_service.edit_section(db, owner_id, project_id, section_id, content, code)
    return _one_section(db, owner_id, project_id, section_id, code)


def refresh(db: Session, owner_id: int, project_id: int, code: str) -> int:
    """POST /api/projects/{id}/artifacts/{code}/refresh: rewrite the BRD from all approved answers + current text."""
    code = _require_generated(code)
    return brd_service.start_refresh(db, owner_id, project_id, code)


def regenerate_section(db: Session, owner_id: int, project_id: int, code: str, section_id: str, answers: list[dict]) -> int:
    code = _require_generated(code)
    return brd_service.start_regenerate(db, owner_id, project_id, section_id, answers, code)


def clarify_section(db: Session, owner_id: int, project_id: int, code: str, section_id: str) -> int:
    code = _require_generated(code)
    return brd_service.start_clarify(db, owner_id, project_id, section_id, code)


def save_version(db: Session, owner_id: int, project_id: int, code: str) -> dict:
    """
    POST /api/projects/{id}/artifacts/{code}/versions -> the new version number.
    The previous version moves to the versions table; the drafts on screen become the current
    content (see brd_service.save_new_version).
    """
    code = _require_generated(code)
    saved = brd_service.save_new_version(db, owner_id, project_id, code=code)
    return {"versionNumber": saved["version_number"], "label": _version_label(saved["approved_at"])}


# ---------------------------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------------------------


def export(
    db: Session, owner_id: int, project_id: int, code: str, fmt: str, include_sources: bool, include_questions: bool
) -> tuple[str, str, bytes]:
    """GET /api/projects/{id}/artifacts/{code}/export -> (file name, media type, bytes)."""
    if fmt not in EXPORT_FORMATS:
        raise api_error(422, "UNKNOWN_FORMAT", "format must be md, docx or pdf")
    current = draft(db, owner_id, project_id, code)
    code = current["artifactCode"]
    sources = _source_titles(db, project_id) if include_sources else []
    doc = _export_model(current, sources, include_questions)
    base = f"{code.lower()}-draft"
    if fmt == "md":
        return f"{base}.md", "text/markdown; charset=utf-8", _export_md(doc).encode("utf-8")
    if fmt == "docx":
        return (f"{base}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", _export_docx(doc))
    return f"{base}.pdf", "application/pdf", _export_pdf(doc)


def _export_model(current: dict, sources: list[str], include_questions: bool) -> dict:
    sections = []
    for s in current["sections"]:
        sections.append({
            "heading": f"{s['number']:02d} {s['title']}",
            "content": s.get("content") or "",
            "bullets": s["bullets"],
            "note": None if s["bullets"] else (s.get("missingReason") or DEFAULT_MISSING_REASON),
            "questions": (s.get("clarificationQuestions") or []) if include_questions else [],
        })
    return {
        "title": f"{current['title']}: {current['artifactName']}",
        "description": current["description"],
        "warning": None if current["isClientReady"] else "Incomplete draft: discovery is not complete. Not client-ready.",
        "settings": [x for x in (
            f"Audience: {current['audience']}" if current.get("audience") else None,
            f"Scope: {current['scope']}" if current.get("scope") else None,
        ) if x],
        "sections": sections,
        "sources": sources,
        "snapshot": current["snapshot"],
    }


def _export_md(doc: dict) -> str:
    lines = [f"# {doc['title']}", ""]
    if doc["description"]:
        lines += [doc["description"], ""]
    lines += [f"_{s}_" for s in doc["settings"]] + ([""] if doc["settings"] else [])
    if doc["warning"]:
        lines += [f"> {doc['warning']}", ""]
    for s in doc["sections"]:
        lines += [f"## {s['heading']}", ""]
        lines += [f"- {b}" for b in s["bullets"]] or [f"_{s['note']}_"]
        if s["questions"]:
            lines += ["", "**Open questions**", ""] + [f"- {q}" for q in s["questions"]]
        lines.append("")
    if doc["sources"]:
        lines += ["---", "", "**Sources**", ""] + [f"- {t}" for t in doc["sources"]]
    return "\n".join(lines) + "\n"


C5I_LOGO = Path(__file__).resolve().parents[1] / "assets" / "c5i-logo.png"


def _export_docx(doc: dict) -> bytes:
    """The BRD as Word: logo in the header, every section's Markdown laid out with its tables."""
    blocks: list[tuple] = []
    if doc["description"]:
        blocks.append(("para", doc["description"]))
    blocks += [("para", f"_{s}_") for s in doc["settings"]]
    if doc["warning"]:
        blocks.append(("para", f"**{doc['warning']}**"))
    for s in doc["sections"]:
        blocks.append(("heading", 1, s["heading"]))
        if (s.get("content") or "").strip():
            blocks += mom_documents.text_to_blocks(s["content"])
        elif s["bullets"]:
            blocks += [("bullet", b, 1) for b in s["bullets"]]
        else:
            blocks.append(("para", s["note"] or DEFAULT_MISSING_REASON))
        if s["questions"]:
            blocks.append(("para", "**Open questions**"))
            blocks += [("bullet", q, 1) for q in s["questions"]]
    if doc["sources"]:
        blocks.append(("heading", 1, "Sources"))
        blocks += [("bullet", t, 1) for t in doc["sources"]]
    return mom_documents.to_docx(
        {"title": doc["title"], "project_name": None, "meta_line": "", "blocks": blocks, "output": None},
        logo=C5I_LOGO,
    )


def _export_pdf(doc: dict) -> bytes:
    try:
        from fpdf import FPDF  # fpdf2
    except ImportError:
        raise api_error(501, "PDF_NOT_AVAILABLE", "PDF export needs the fpdf2 package (pip install -r requirements.txt)") from None

    def latin(text: str) -> str:
        # The built-in PDF fonts cover Latin-1 only; replace the few common characters outside it.
        for a, b in {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "•": "-", "€": "EUR", "…": "..."}.items():
            text = text.replace(a, b)
        return text.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    width = pdf.w - pdf.l_margin - pdf.r_margin

    def para(text: str, size: int = 11, style: str = "", gap: float = 2) -> None:
        pdf.set_font("Helvetica", style, size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(width, size * 0.5, latin(text))
        pdf.ln(gap)

    para(doc["title"], 18, "B", 4)
    if doc["description"]:
        para(doc["description"])
    for s in doc["settings"]:
        para(s, 10, "I")
    if doc["warning"]:
        para(doc["warning"], 10, "B", 4)
    for s in doc["sections"]:
        para(s["heading"], 14, "B")
        for b in s["bullets"]:
            para(f"- {b}", gap=1)
        if s["note"]:
            para(s["note"], 10, "I")
        if s["questions"]:
            para("Open questions", 11, "B", 1)
            for q in s["questions"]:
                para(f"- {q}", gap=1)
        pdf.ln(2)
    if doc["sources"]:
        para("Sources", 14, "B")
        for t in doc["sources"]:
            para(f"- {t}", gap=1)
    return bytes(pdf.output())


# ---------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------


def _require_generated(code: str) -> str:
    """The artifact code in capitals, when it can be generated."""
    code = code.upper()
    if code not in GENERATED_CODES:
        raise api_error(404, "ARTIFACT_NOT_AVAILABLE", f"{code} cannot be generated yet. Only the BRD and PRD are available.")
    return code


def _owned_project(db: Session, owner_id: int, project_id: int) -> Project:
    return brd_service._owned_project(db, owner_id, project_id)  # noqa: SLF001 - read once per request


def _artifact(db: Session, project_id: int, code: str) -> ProjectArtifact | None:
    # read once per request, shared with brd_service
    return brd_service._find_brd(db, project_id, brd_service._brd_type(db, code).id)  # noqa: SLF001


def _draft_section(s: dict) -> dict:
    """
    One brd_service section -> the editor's DraftSection.
    Text: the agent's draft waiting for review first, else the approved content.
    Questions: the agent's open questions, shown with answer boxes whether or not there is text.
    `content` is the Markdown (tables, lists); `bullets` is the same text as plain points.
    """
    pending = s.get("pending_draft")
    asking = s.get("open_questions")
    out = {"id": s["section_key"], "number": s["sort_order"], "title": s["title"]}
    if pending:
        out.update(status="PENDING_REVIEW", content=pending["content"], proposalId=pending["id"])
    elif s["content"]:
        out.update(status=s["status"] if s["status"] in ("APPROVED", "PENDING_REVIEW", "DRAFT") else "APPROVED",
                   content=s["content"])
    elif asking:
        out.update(status="NEEDS_CLARIFICATION", content="")
    else:
        out.update(status="NOT_STARTED", content="")
    out["bullets"] = markdown_to_bullets(out["content"])
    if asking and asking["questions"]:
        out["clarificationQuestions"] = asking["questions"]
        out["missingReason"] = asking["missing_reason"] or (DEFAULT_MISSING_REASON if not out["content"] else "")
    return out


def _one_section(db: Session, owner_id: int, project_id: int, section_id: str, code: str) -> dict:
    for s in brd_service.get_brd(db, owner_id, project_id, code)["sections"]:
        if s["section_key"] == section_id:
            return _draft_section(s)
    raise api_error(404, "SECTION_NOT_FOUND", f"{code} section not found")


def _generation_snapshot(db: Session, artifact: ProjectArtifact | None) -> dict | None:
    if artifact is None:
        return None
    return brd_service.last_generate_payload(db, artifact.id).get("snapshot")


def _versions(db: Session, artifact: ProjectArtifact | None) -> list[dict]:
    if artifact is None:
        return []
    # Older versions come from the versions table; the current one is the content in the sections.
    older = db.scalars(
        select(ProjectArtifactVersion)
        .where(
            ProjectArtifactVersion.project_artifact_id == artifact.id,
            ProjectArtifactVersion.version_number < artifact.current_version,
        )
        .order_by(ProjectArtifactVersion.version_number)
    )
    versions = [{"number": v.version_number, "label": _version_label(v.approved_at), "isCurrent": False} for v in older]
    if artifact.current_version >= 1:
        versions.append({
            "number": artifact.current_version,
            "label": _version_label(artifact.approved_at or artifact.updated_at),
            "isCurrent": True,
        })
    return versions


def _version_label(moment: datetime) -> str:
    """'Nov 18, 5:49 PM UTC'."""
    hour = moment.strftime("%I").lstrip("0") or "12"
    return f"{moment:%b} {moment.day}, {hour}:{moment:%M} {moment:%p} UTC"


def _source_titles(db: Session, project_id: int) -> list[str]:
    return list(db.scalars(
        select(ContextSource.title)
        .where(ContextSource.project_id == project_id, ContextSource.deleted_at.is_(None))
        .order_by(ContextSource.created_at)
    ))

