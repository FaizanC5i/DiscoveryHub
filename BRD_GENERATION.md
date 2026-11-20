# BRD generation

The BRD is written by the Agent5i **BRD Extraction Agent** from the project's **approved User Discovery
answers**: `project_checkpoint_answers` rows with `approved_at` set, for the checkpoints USR-01 to USR-19.
Answers of other pillars are not sent (`artifact_type_pillars`: BRD → USER). It does not read uploaded files.
Everything else works like the stand-alone BRD app: generate, clarify, regenerate, edit, approve.

**Refresh button.** The draft editor shows how many answers were approved since the BRD was generated
(`isOutdated`, `newAnswerCount`) and a **Refresh** button (`POST .../artifacts/BRD/refresh`). Refresh is one agent
call with ALL approved User Discovery answers, the saved clarification answers and the **current BRD text**, so
the agent updates the BRD instead of starting again. Answers approved since the BRD was last generated (for
example after a new document was uploaded and its answers approved) are sent first, as **NEW OR UPDATED ANSWERS
(HIGHEST PRIORITY)**: where they disagree with the current BRD or older answers, the agent follows them. The
unchanged answers follow as background. New text arrives as drafts; a section the agent
cannot update keeps its text and gets questions. The current content stays until "Save new version".
Automatic regeneration after each approval is **off** by default (`BRD_AUTO_REFRESH=false`) to save agent tokens;
set it to true to turn it back on.

## Flow

```
approved checkpoint answers ──► BRD agent ──► proposals (one per section) ──► user approves / edits
                                                                              │
                                                       approve BRD ──► frozen version (v1, v2 ...)
```

1. **Generate** – one agent call writes all 14 sections from every approved User Discovery answer,
   plus the user's saved clarification answers of every section (so a refresh keeps them). Sections the agent
   cannot write come back as `NEEDS_CLARIFICATION`, each with up to 3 questions (fetched automatically
   if the agent gave none).
2. **Clarify** – the agent asks up to 3 questions for one section.
3. **Regenerate** – the agent rewrites one section from:
   every approved User Discovery answer (or only the checkpoints listed for the section in
   `artifact_section_checkpoints`, when there are rows; there are none today),
   the user's saved clarification answers, and the section's current content.
   If the agent fails, the existing content is kept.
4. **Edit** – the user's own text becomes the section's approved content.
5. **Approve** – approving a proposal makes it the section's content; approving the BRD freezes a version.

The agent never writes into a section directly: its output is always a proposal.
Agent calls run in the background and are logged in `agent_runs`
(`brd_generate` / `brd_regenerate` / `brd_clarify`). One BRD run per project at a time: the database
enforces it (`ux_agent_runs_one_running_artifact`, migration 015), so two approvals at the same moment
start one run, and the other is picked up when it ends. A run left "running" for over an hour (server
stopped) is closed as failed when the next run starts. A generate run with all 19 answers takes about
10 minutes with the real agent.

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

--- CHECKPOINT USR-09: Stakeholders and Sponsors (User Discovery pillar) ---
Question: ...
Approved answer:
...
```

The agent's prompt on Agent5i still talks about an "uploaded file"; its owner may want to say
"approved discovery answers" instead. The reply format did not change.

## Tables (migrations `012_brd_artifact_tables` and `014_artifact_type_pillars`, design doc PART 12)

| Table | What it holds |
|---|---|
| `artifact_types` | Kinds of document. BRD is one row, linked to `BRD_AGENT` |
| `artifact_type_pillars` | Which pillars' answers each type reads. BRD → USER (PRD later: USER + TECH) |
| `artifact_sections` | The 14 BRD sections (template) |
| `artifact_section_checkpoints` | Which checkpoints feed which section (Assumptions has none = reads every answer) |
| `project_artifacts` | One BRD per project: `NOT_STARTED` / `DRAFT` / `IN_REVIEW` / `APPROVED`, current version |
| `project_artifact_sections` | The BRD's 14 sections: approved content, status, `AGENT` or `USER` |
| `artifact_section_proposals` | Agent output: `PENDING` (content) or `NEEDS_CLARIFICATION` (reason + questions) |
| `artifact_section_clarifications` | The user's answers to the questions, reused on every regenerate |
| `project_artifact_versions` | **Older** BRD versions only (JSON snapshot). The current version is the content in `project_artifact_sections` |
| `agent_runs` (changed) | + `project_artifact_id`, `project_artifact_section_id`; `run_type` also allows the 3 BRD values |
| `agents` (new row) | `BRD_AGENT` |

Section → checkpoints routing: `artifact_section_checkpoints` is empty for the BRD since the old
checkpoints were replaced by USR-01..USR-19, so every section reads every approved User Discovery answer.
Add rows there only if a section should read fewer checkpoints.

Section statuses use the frontend's names (`NOT_STARTED`, `DRAFT`, `PENDING_REVIEW`,
`NEEDS_CLARIFICATION`, `APPROVED`), so `APPROVED` is used where the design doc says `CONFIRMED`.

## Artifact Studio API (what the screens call)

These are the paths already written in `frontend/features/artifact-studio/services/artifact-studio.service.ts`,
and they return the shapes in `artifact-studio.types.ts`. The frontend only has to replace each placeholder
body with the API call (`backend/app/api/routes/artifact_studio.py`, `services/artifact_studio_service.py`).

| Screen | Method and path | Returns |
|---|---|---|
| Studio page | GET `/api/projects/{id}/artifact-studio` | `ArtifactStudioData`: 9 types, available artifacts, audiences, readiness per type (BRD: the 19 USR checkpoints) |
| "Configure the draft" → Generate | POST `/api/projects/{id}/artifacts/BRD/generate` body `{title, audience, scope}` | 202 `{agentRunId}`. Title, audience and scope are saved and sent to the agent |
| Draft editor | GET `/api/projects/{id}/artifacts/BRD` | `ArtifactDraft`: 5 sections as bullets, status, snapshot banner, versions. Extra: `audience`, `scope`, `isOutdated`, `latestRun`, `proposalId` per section |
| Edit section | PUT `/api/projects/{id}/artifacts/BRD/sections/{sectionId}` body `{bullets}` | `DraftSection` |
| Regenerate / Clarify | POST `.../sections/{sectionId}/regenerate` (body optional `{answers:[{question,answer}]}`) and `.../clarify` | 202 `{agentRunId}` |
| Save new version | POST `/api/projects/{id}/artifacts/BRD/versions` | `{versionNumber, label}`. The previous version moves to `project_artifact_versions`; the drafts on screen become the current content |
| Export | GET `/api/projects/{id}/artifacts/BRD/export?format=md\|docx\|pdf&sources=true&questions=true` | the file |

`sectionId` is the section key (`business_objectives`, `users_stakeholders`, `current_state`, `scope`,
`functional_requirements`). Other artifact codes answer 404 `ARTIFACT_NOT_AVAILABLE` until they are built.
A section shows the agent's draft waiting for review first (PENDING_REVIEW), else its approved content,
else the agent's questions (NEEDS_CLARIFICATION).

**The BRD has all 14 sections again** (migration 018; 016 had cut it to 5). The draft editor shows them on one
scrolling page, like the original BRD tool: each section has Regenerate, Clarify and Edit, shows its text as
Markdown (lists, tables), and lists the agent's questions with an answer box each. "Submit answers" sends
the answers with Regenerate; they are saved and reused on every later rewrite. A section can show a draft
waiting for review and new questions at the same time. Each section also returns `content` (Markdown),
`isWorking` (the agent is busy with it) and `lastError` (why its last run failed). PUT section accepts
`{content}` (Markdown) as well as `{bullets}`.

## BRD API (all need login; other users' projects return 404)

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
BRD_AUTO_REFRESH=true           # regenerate the BRD when a User Discovery answer is approved
```

## Code

| File | Role |
|---|---|
| `backend/alembic/versions/012_create_brd_artifact_tables.py` | Tables, seed, agent_runs change |
| `backend/alembic/versions/014_artifact_type_pillars.py` | BRD reads the User Discovery pillar only |
| `backend/alembic/versions/015_one_running_brd_run.py` | One running BRD run per BRD; status data fix |
| `backend/app/api/routes/answers.py` | Approving an answer queues `brd_service.refresh_brd` |
| `backend/alembic/versions/016_artifact_draft_settings.py` | Title / audience / scope |
| `backend/alembic/versions/018_brd_all_sections.py` | All 14 BRD sections on again |
| `backend/app/services/artifact_readiness.py` | Verified / awaiting review / missing per checkpoint |
| `backend/app/services/artifact_studio_service.py`, `api/routes/artifact_studio.py` | The screens' API, bullets, versions, export |
| `backend/app/services/brd_agent_io.py` | Builds the agent input, reads the reply (pure) |
| `backend/app/services/brd_service.py` | Runs, proposals, approve, edit, versions |
| `backend/app/api/routes/brd.py`, `backend/app/schemas/brd.py` | Endpoints and shapes |
| `backend/app/services/agent_client.py` | `call_brd_agent()` |
| `backend/tests/test_brd_agent_io.py` | Unit tests |

## Not done yet

- The Artifact Studio screens are connected (`artifact-studio.service.ts`). The Document title default still
  comes from the Discovery overview placeholder (`features/discovery/services/discovery.service.ts`).

- PDF export needs `fpdf2` (added to requirements.txt): run `pip install -r requirements.txt`.
- The BRD agent's prompt still says "uploaded file" in its empty-section message; its owner can reword it.
- `is_required` in `artifact_section_checkpoints` is stored but not enforced.
