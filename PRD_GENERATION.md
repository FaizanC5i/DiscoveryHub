# PRD generation

The PRD works exactly like the BRD (see BRD_GENERATION.md): same tables, same screens, same
buttons (Generate, Refresh, Regenerate, Clarify, Edit, Save new version, Export). Only three
things differ: what it reads, its sections, and its agent.

| | BRD | PRD |
|---|---|---|
| Reads | approved User Discovery answers | approved User Discovery **and** Tech Discovery answers |
| Sections | 14 | 25 (migration 019) |
| Agent | BRD Extraction Agent (text request) | PRD Generation Agent (JSON request) |

## Setup

1. `alembic upgrade head` (migration `019_prd_artifact`): adds rows only, no new tables.
   - `agents`: PRD_AGENT
   - `artifact_types`: PRD
   - `artifact_type_pillars`: PRD reads USER and TECH
   - `artifact_sections`: the 25 sections. `prompt` holds each section's definition as JSON
     (key contents, required details, expected format, question). `fallback_questions` holds
     3 questions, used when the agent sends none.
2. Optional `.env` settings (the defaults work):
   - `PRD_AGENT_NAME` (default "PRD Generation Agent")
   - `PRD_AGENT5I_USERNAME` / `PRD_AGENT5I_PASSWORD` (empty means use the AGENT5I_* login)
   - `PRD_TIMEOUT_SECONDS=300`, `PRD_BATCH_SIZE=3`, `PRD_PARALLEL_CALLS=3`
3. Tech answers: the 4 Tech checkpoints (PRDCP01 Frontend Requirements, PRDCP02 Backend
   Requirements, PRDCP03 Current Technology Stack, PRDCP04 Current System Architecture) are
   **not** added yet. Adding them changes chunk mapping for everyone (the Helper Agent maps
   to every active checkpoint), so agree on it with the team first. Until then the PRD is
   written from the User answers only.

## The agent request

The text `PRD_REQUEST`, a new line, then JSON. This is the format of the PRD agent builder's
stand-alone app (`app/services/prd_agent_io.py`):

- `action`: generate | clarify | regenerate
- `approved_user_discovery`: User answers
- `prd_checkpoints`: Tech answers (approved only)
- `prd_sections`: the sections to write, ids 1-25 (= sort_order), codes PRDS01-PRDS25
- `existing_sections`: current text and the saved clarification answers
- `clarifications`, `target_section_id`
- Added by us: `document_settings` (title, audience, scope) and `new_or_updated_answers`
  (Refresh: answers approved since the last generation, HIGHEST PRIORITY)

The reply is a `sections` array: `section_id`, `proposed_answer`, `missing_information`,
`clarification_questions`. A section can come back with text, with questions, or with both.

## Buttons and agent calls (`app/services/prd_runs.py`)

| Button | Agent call |
|---|---|
| Generate / Refresh | `generate`, 3 sections per call (9 calls for 25 sections), 3 calls at a time. A section the agent leaves out is asked for again on its own. |
| Clarify | `generate` for 1 section, asking for 3 questions (fallback questions if it sends none) |
| Regenerate with answers | `clarify` for 1 section with the user's answers; no new questions after that |
| Regenerate without answers | `regenerate` for 1 section |

Requests and replies are saved under `backend/logs/prd_agent_inputs/` and `prd_agent_replies/`.
Both folders are git-ignored because they contain client text.
