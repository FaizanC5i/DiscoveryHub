# BRD generation

The BRD is written by the Agent5i **BRD Extraction Agent** from the project's **approved checkpoint
answers** (`project_checkpoint_answers` rows with `approved_at` set). It no longer reads uploaded files.
Everything else works like the stand-alone BRD app: generate, clarify, regenerate, edit, approve.

## Flow

```
approved checkpoint answers ──► BRD agent ──► proposals (one per section) ──► user approves / edits
                                                                              │
                                                       approve BRD ──► frozen version (v1, v2 ...)
```

1. **Generate** – one agent call writes all 14 sections from every approved answer. Sections the agent
   cannot write come back as `NEEDS_CLARIFICATION`, each with up to 3 questions (fetched automatically
   if the agent gave none).
2. **Clarify** – the agent asks up to 3 questions for one section.
3. **Regenerate** – the agent rewrites one section from:
   the approved answers of the checkpoints that feed it (`artifact_section_checkpoints`),
   the user's saved clarification answers, and the section's current content.
   If the agent fails, the existing content is kept.
4. **Edit** – the user's own text becomes the section's approved content.
5. **Approve** – approving a proposal makes it the section's content; approving the BRD freezes a version.

The agent never writes into a section directly: its output is always a proposal.
Agent calls run in the background and are logged in `agent_runs`
(`brd_generate` / `brd_regenerate` / `brd_clarify`). One BRD run per project at a time.

## What the agent receives

The same text format as before, only the part after `ORIGINAL_SOURCE_DOCUMENT:` changed:

```
AGENT_REQUEST
mode: generate_all | regenerate_section | clarify_questions
target_section: <section key or empty>
clarification:
Q1: ...
A1: ...
current_section_content:
...
END_AGENT_REQUEST

ORIGINAL_SOURCE_DOCUMENT:
APPROVED DISCOVERY ANSWERS

--- CHECKPOINT USER05: Stakeholders (User pillar) ---
Question: ...
Approved answer:
...
```

The agent's prompt on Agent5i still talks about an "uploaded file"; its owner may want to say
"approved discovery answers" instead. The reply format did not change.

## Tables (migration `012_brd_artifact_tables`, design doc PART 12)

| Table | What it holds |
|---|---|
| `artifact_types` | Kinds of document. BRD is one row, linked to `BRD_AGENT` |
| `artifact_sections` | The 14 BRD sections (template) |
| `artifact_section_checkpoints` | Which checkpoints feed which section (Assumptions has none = reads every answer) |
| `project_artifacts` | One BRD per project: `NOT_STARTED` / `DRAFT` / `IN_REVIEW` / `APPROVED`, current version |
| `project_artifact_sections` | The BRD's 14 sections: approved content, status, `AGENT` or `USER` |
| `artifact_section_proposals` | Agent output: `PENDING` (content) or `NEEDS_CLARIFICATION` (reason + questions) |
| `artifact_section_clarifications` | The user's answers to the questions, reused on every regenerate |
| `project_artifact_versions` | JSON snapshot of each approved BRD |
| `agent_runs` (changed) | + `project_artifact_id`, `project_artifact_section_id`; `run_type` also allows the 3 BRD values |
| `agents` (new row) | `BRD_AGENT` |

Section → checkpoints routing (configuration, change it in `artifact_section_checkpoints`):

| Section | Fed by |
|---|---|
| Business Objectives | USER03, USER04, USER05 |
| Users & Stakeholders | USER01, USER05 |
| Current State | USER02, USER03, TECH01, DATA01 |
| Scope | USER02, USER04 |
| Functional Requirements | USER02, USER04 |
| Out of Scope | USER04 |
| Business Rules | USER02, DATA02, DATA05 |
| Constraints | TECH03, TECH05 |
| Assumptions | all approved answers |
| Dependencies | TECH02, DATA01, DATA03, TECH05 |
| Success Criteria | USER03, USER04 |
| Risks | USER03, DATA02, TECH03, TECH04 |
| Integrations | TECH01, TECH02, DATA04 |
| Security & Compliance | TECH04, DATA03, DATA05 |

Section statuses use the frontend's names (`NOT_STARTED`, `DRAFT`, `PENDING_REVIEW`,
`NEEDS_CLARIFICATION`, `APPROVED`), so `APPROVED` is used where the design doc says `CONFIRMED`.

## API (all need login; other users' projects return 404)

| Method | Path | Does |
|---|---|---|
| GET | `/api/projects/{id}/brd` | BRD with all sections, open proposal, clarifications, latest run |
| POST | `/api/projects/{id}/brd/generate` | 202 + `agent_run_id`. 409 if no approved answers |
| POST | `/api/projects/{id}/brd/sections/{key}/clarify` | 202. Questions for one section |
| POST | `/api/projects/{id}/brd/sections/{key}/regenerate` | 202. Body (optional): `{"answers":[{"question","answer"}]}` |
| PUT | `/api/projects/{id}/brd/sections/{key}` | Body `{"content"}`. User text becomes approved content |
| POST | `/api/projects/{id}/brd/proposals/{pid}/approve` | Proposal becomes the section's content |
| POST | `/api/projects/{id}/brd/proposals/{pid}/reject` | Close a proposal |
| POST | `/api/projects/{id}/brd/approve` | Freeze the next version |
| GET | `/api/projects/{id}/brd/versions` and `/versions/{n}` | Approved versions |
| GET | `/api/projects/{id}/brd/runs/{run_id}` | Status of one agent run (poll after a 202) |

## Configuration (`backend/.env`, never committed)

```
AGENT5I_WEBHOOK_URL=...
AGENT5I_USERNAME=...            # shared with the Helper Agent
AGENT5I_PASSWORD=...
BRD_AGENT_NAME=BRD Extraction Agent
BRD_AGENT5I_USERNAME=           # only if the BRD agent is in another Agent5i account
BRD_AGENT5I_PASSWORD=
BRD_TIMEOUT_SECONDS=300
```

## Code

| File | Role |
|---|---|
| `backend/alembic/versions/012_create_brd_artifact_tables.py` | Tables, seed, agent_runs change |
| `backend/app/services/brd_agent_io.py` | Builds the agent input, reads the reply (pure) |
| `backend/app/services/brd_service.py` | Runs, proposals, approve, edit, versions |
| `backend/app/api/routes/brd.py`, `backend/app/schemas/brd.py` | Endpoints and shapes |
| `backend/app/services/agent_client.py` | `call_brd_agent()` |
| `backend/tests/test_brd_agent_io.py` | Unit tests |

## Not done yet

- Word / PDF export of a version.
- The UI (Artifact Studio) is not connected to these endpoints yet.
- `is_required` in `artifact_section_checkpoints` is stored but not enforced.
