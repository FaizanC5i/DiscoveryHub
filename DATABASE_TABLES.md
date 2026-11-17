# Database tables

This is a reference for every table in the `Discoveryhub` database on Azure SQL. It lists what
each table stores, its columns, its keys, and one sample row. The samples use made-up values
(no real names, emails, hashes or document text). Row counts are from the database at the time
of writing.

The schema is created only by Alembic migrations in `backend/alembic/versions/`. Current
revision: `010_checkpoint_answer_tables`.

---

## The tables at a glance

| Table | Rows | Purpose | Written by |
|---|---|---|---|
| `users` | 34 | Accounts that can sign in | Sign-up, password reset |
| `refresh_tokens` | 119 | Long-lived sign-in sessions | Login, refresh, logout |
| `password_reset_tokens` | 4 | One-time password reset links | Forgot-password flow |
| `projects` | 23 | Discovery projects, one owner each | Project create, edit, delete |
| `context_sources` | 14 | Each uploaded document | Upload, retry, delete |
| `context_content` | 14 | The text extracted from a document | Upload, retry |
| `context_chunks` | 204 | Overlapping pieces of the text | Chunking, mapping job |
| `discovery_pillars` | 3 | The three discovery areas (User, Data, Tech) | Migration 007 (fixed data) |
| `discovery_checkpoints` | 15 | The questions each pillar must answer | Migration 007 (fixed data) |
| `agents` | 4 | Who produced a mapping or run: the Helper Agent and the three pillar agents | Migrations 008 and 009 (seeded) |
| `agent_runs` | 31 | One row per agent execution | Mapping job |
| `agent_run_checkpoints` | 0 | Per-checkpoint result inside one run. Helper runs do not write here. | Nothing yet |
| `agent_run_chunks` | 0 | Chunks sent into one run. Helper runs do not write here. | Nothing yet |
| `context_checkpoint_mappings` | 407 | A chunk tagged with a checkpoint | Mapping job |
| `mapping_evidence` | 407 | The quote that justifies each mapping | Mapping job |
| `project_checkpoint_answers` | 0 | Current answer and completion state for each checkpoint in a project | Nothing yet (schema only) |
| `checkpoint_answer_proposals` | 0 | AI-proposed answers, several per checkpoint answer | Nothing yet (schema only) |
| `proposal_evidence` | 0 | Chunks and mappings that support a proposal | Nothing yet (schema only) |
| `checkpoint_answer_versions` | 0 | Saved snapshots of each checkpoint answer | Nothing yet (schema only) |
| `checkpoint_answer_evidence` | 0 | Chunks that support one saved answer version | Nothing yet (schema only) |
| `alembic_version` | 1 | The migration revision the database is at | Alembic |

---

## How the tables connect

```
users ──< projects ──< context_sources ──< context_content ──< context_chunks
  │          │              │                                       │
  │          │              └── (trigger_source_id)                 │
  │          │                                                      │
  │          ├──< agent_runs ──< agent_run_checkpoints              │
  │          │       │  └──< agent_run_chunks ──────────────────────┤
  │          │       │          └── (mapping_id)                    │
  │          │       └── agents                                     │
  │          │                                                      │
  │          └──< context_checkpoint_mappings >── context_chunks ───┘
  │                     │         │          │
  │                     │         │          └── discovery_checkpoints ──> discovery_pillars
  │                     │         └── agent_runs
  │                     └── agents (mapped_by_agent_id)
  │                     └──< mapping_evidence
  ├──< refresh_tokens
  └──< password_reset_tokens
```

`──<` means one-to-many. `>──` means many-to-one.

Checkpoint answer tables (migration 010), which hang off a project's checkpoint answers:

```
projects ──< project_checkpoint_answers ──< checkpoint_answer_proposals ──< proposal_evidence
                  │                              │ (superseded_by, self-reference)
                  │                              └──< checkpoint_answer_versions (proposal_id)
                  ├──< checkpoint_answer_versions ──< checkpoint_answer_evidence >── context_chunks
                  └──< checkpoint_answer_evidence
discovery_checkpoints ──< project_checkpoint_answers
users ──< project_checkpoint_answers (approved_by)     users ──< checkpoint_answer_versions (created_by)
agent_runs ──< checkpoint_answer_proposals             agent_runs ──< proposal_evidence
```

Deleting a project removes its sources, text, chunks, agent runs, mappings and checkpoint answers
(cascade). Deleting a user removes their projects, tokens and reset links.

---

## users

Accounts that can sign in.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `name` | NVARCHAR(100) | no | | Display name |
| `email` | NVARCHAR(255) | no | | Sign-in address, stored lowercase and unique |
| `password_hash` | NVARCHAR(255) | no | | Argon2id hash of the password. The password itself is never stored. |
| `is_active` | BIT | no | 1 | 0 blocks sign-in |
| `created_at` | DATETIME | no | UTC now | When the account was created |
| `updated_at` | DATETIME | no | UTC now | Last change to the row |

**Sample row**

| id | name | email | password_hash | is_active | created_at |
|---|---|---|---|---|---|
| 7 | Asha Patel | asha.patel@example.com | `$argon2id$v=19$m=65536,t=3,p=4$...` | 1 | 2026-11-02 09:14:00 |

Note: earlier documentation mentions a `full_name` column. The database column is `name`.

---

## refresh_tokens

Long-lived sessions. Each login gets one, and each refresh replaces it.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `user_id` | BIGINT | no | | Owner. FK to `users.id`, cascade delete |
| `token_hash` | NVARCHAR(128) | no | | SHA-256 of the token. The token itself is only in the cookie. |
| `expires_at` | DATETIME | no | | When the token stops working |
| `revoked_at` | DATETIME | yes | | Set on logout or rotation. Reuse of a revoked token revokes all of the user's sessions. |
| `created_at` | DATETIME | no | UTC now | When it was issued |

**Sample row**

| id | user_id | token_hash | expires_at | revoked_at | created_at |
|---|---|---|---|---|---|
| 201 | 7 | `4f9c...e21a` | 2026-12-02 09:14 | NULL | 2026-11-02 09:14 |

---

## password_reset_tokens

One-time links for resetting a password.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `user_id` | BIGINT | no | | Owner. FK to `users.id`, cascade delete |
| `token_hash` | NVARCHAR(128) | no | | SHA-256 of the reset token |
| `expires_at` | DATETIME | no | | Usually 30 minutes after creation |
| `used_at` | DATETIME | yes | | Set when the password is changed |
| `created_at` | DATETIME | no | UTC now | When the link was created |

**Sample row**

| id | user_id | token_hash | expires_at | used_at | created_at |
|---|---|---|---|---|---|
| 14 | 7 | `a07b...6c3d` | 2026-11-02 09:44 | 2026-11-02 09:20 | 2026-11-02 09:14 |

---

## projects

A discovery project. Every project has exactly one owner, and users only see their own.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `name` | NVARCHAR(255) | no | | Project name |
| `description` | NVARCHAR(MAX) | yes | | Free text. Empty input is stored as NULL. |
| `owner_id` | BIGINT | no | | FK to `users.id`, cascade delete |
| `start_date` | DATE | yes | | Optional |
| `end_date` | DATE | yes | | Optional. Must not be before `start_date`. |
| `created_at` | DATETIME2 | no | UTC now | When created |
| `updated_at` | DATETIME2 | no | UTC now | Last edit. Used to sort the dashboard. |

Indexes: `(owner_id, created_at)`.

**Sample row**

| id | name | description | owner_id | start_date | end_date | created_at | updated_at |
|---|---|---|---|---|---|---|---|
| 12 | Northwind Order Status | Discovery for the order status BRD | 7 | 2026-11-01 | 2026-12-15 | 2026-11-02 09:20 | 2026-11-13 18:17 |

---

## context_sources

One row per uploaded document. The file itself is in Azure Blob Storage; this row describes it.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `project_id` | BIGINT | no | | FK to `projects.id`, cascade delete |
| `created_by` | BIGINT | no | | FK to `users.id` (who uploaded it). No cascade. |
| `source_type` | NVARCHAR(30) | no | 'upload' | How it arrived |
| `title` | NVARCHAR(255) | no | | File name without its extension |
| `original_filename` | NVARCHAR(255) | no | | The name as uploaded |
| `blob_path` | NVARCHAR(500) | no | | Where the file is in Blob Storage, e.g. `projects/12/sources/<uuid>.docx` |
| `mime_type` | NVARCHAR(100) | no | | e.g. `application/pdf` |
| `file_size_bytes` | BIGINT | no | | Size of the uploaded file |
| `processing_status` | NVARCHAR(20) | no | | `processing`, `ready` or `failed` |
| `failure_reason` | NVARCHAR(500) | yes | | Why extraction or chunking failed, shown to the user |
| `created_at` | DATETIME2 | no | UTC now | When uploaded |
| `deleted_at` | DATETIME2 | yes | | Set when the user removes the document (soft delete). Hidden from lists. |

Indexes: `(project_id, created_at)`.

**Sample row**

| id | project_id | created_by | title | original_filename | blob_path | mime_type | file_size_bytes | processing_status | failure_reason | deleted_at |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 | 12 | 7 | notes | notes.txt | projects/12/sources/3f9a...c1.txt | text/plain | 148 | ready | NULL | NULL |

---

## context_content

The text extracted from one document. There is at most one per source.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `context_source_id` | BIGINT | no | | FK to `context_sources.id`, cascade delete. Unique. |
| `content_text` | NVARCHAR(MAX) | no | | The full extracted text. Chunk offsets refer to this exact string. |
| `extraction_method` | NVARCHAR(50) | no | | Which extractor produced it, e.g. `utf-8`, `python-docx`, `pdfplumber` |
| `created_at` | DATETIME2 | no | UTC now | When extracted |

**Sample row**

| id | context_source_id | content_text | extraction_method | created_at |
|---|---|---|---|---|
| 25 | 30 | `The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. Staff log in to the intranet with a single shared account per warehouse.` | utf-8 | 2026-11-02 09:21 |

---

## context_chunks

Overlapping pieces of `content_text`. These are what the Helper Agent reads and tags.
Each chunk knows its exact position, so `content_text[start_char:end_char]` always equals
`chunk_text`.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `context_content_id` | BIGINT | no | | FK to `context_content.id`, cascade delete |
| `chunk_number` | INT | no | | Position in the document, starting at 1. Unique per content. |
| `chunk_text` | NVARCHAR(MAX) | no | | The chunk's text |
| `start_char` | INT | no | | Offset of its first character in `content_text` |
| `end_char` | INT | no | | Offset just after its last character |
| `char_count` | INT | no | | `end_char - start_char` |
| `page_number` | INT | yes | | Page from a `Page N:` marker, if the extractor wrote one |
| `created_at` | DATETIME2 | no | UTC now | When created |
| `mapping_status` | NVARCHAR(20) | no | 'PENDING' | `PENDING`, `IN_PROGRESS`, `MAPPED`, `NO_MATCH` or `FAILED` |
| `mapping_attempts` | INT | no | 0 | How many times the mapping job has tried this chunk |
| `mapped_at` | DATETIME2 | yes | | When mapping finished |
| `mapping_error` | NVARCHAR(MAX) | yes | | Why mapping failed |

Constraints: unique `(context_content_id, chunk_number)`; `end_char > start_char`;
`char_count = end_char - start_char`; `start_char >= 0`; `chunk_number >= 1`.

**Sample row**

| id | context_content_id | chunk_number | chunk_text | start_char | end_char | char_count | page_number | mapping_status | mapping_attempts | mapped_at |
|---|---|---|---|---|---|---|---|---|---|---|
| 91 | 25 | 1 | The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. Staff log in to the intranet with a single shared account per warehouse. | 0 | 149 | 149 | NULL | MAPPED | 1 | 2026-11-02 09:30 |

---

## discovery_pillars

The three discovery areas. Fixed reference data, loaded by migration 007.

| Column | Type | Nullable | Meaning |
|---|---|---|---|
| `id` | BIGINT | no | Fixed ID (1, 2, 3). Not an identity column. |
| `code` | NVARCHAR(20) | no | Unique short code: `USER`, `DATA`, `TECH` |
| `name` | NVARCHAR(255) | no | `User Discovery`, `Data Discovery`, `Tech Discovery` |
| `description` | NVARCHAR(MAX) | yes | What the pillar covers and what it does not |

**Sample row**

| id | code | name | description |
|---|---|---|---|
| 3 | TECH | Tech Discovery | Documents the technology landscape: existing systems, integrations, constraints, security and hosting. |

---

## discovery_checkpoints

The questions each pillar must answer. Fixed reference data, loaded by migration 007. The
mapping job reads the active ones fresh on every run.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT | no | | Fixed ID (201 to 205 for Data, 301 to 305 for Tech, 401 to 405 for User) |
| `pillar_id` | BIGINT | no | | FK to `discovery_pillars.id` |
| `code` | NVARCHAR(20) | no | | Unique, e.g. `TECH03` |
| `name` | NVARCHAR(255) | no | | e.g. `Technical Constraints` |
| `description` | NVARCHAR(MAX) | yes | | What to look for |
| `question` | NVARCHAR(MAX) | no | | The question the document should answer |
| `why_it_matters` | NVARCHAR(MAX) | yes | | Why the answer is useful |
| `priority` | NVARCHAR(20) | no | | `high` or `medium` |
| `readiness_required_count` | INT | no | | How many answers are needed for readiness |
| `feeds_details` | NVARCHAR(255) | yes | | Which agent or section uses the answer |
| `config_json` | NVARCHAR(MAX) | yes | | Extra settings, stored as text |
| `sort_order` | INT | no | | Order within the pillar |
| `is_active` | BIT | no | 1 | 0 stops the checkpoint being sent to the agent |

**Sample row**

| id | pillar_id | code | name | question | priority | readiness_required_count | sort_order | is_active |
|---|---|---|---|---|---|---|---|---|
| 303 | 3 | TECH03 | Technical Constraints | What technical constraints limit the desired solution? | high | 1 | 3 | 1 |

---

## agents

Who produced a mapping or a run. Every mapping points here so the author is always traceable.
The Helper Agent covers all pillars, so its `pillar_id` is NULL. Each pillar agent is linked to
one pillar.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `agent_code` | NVARCHAR(50) | no | | Unique code: `HELPER_AGENT`, `USER_AGENT`, `DATA_AGENT`, `TECH_AGENT` |
| `name` | NVARCHAR(255) | no | | Display name |
| `pillar_id` | BIGINT | yes | | FK to `discovery_pillars.id`. NULL for the Helper Agent. |
| `created_at` | DATETIME2 | no | UTC now | When added |

Constraints: `agent_code` unique. Each pillar has at most one agent: unique among non-NULL `pillar_id`.

**Rows**

| id | agent_code | name | pillar_id |
|---|---|---|---|
| 1 | HELPER_AGENT | Discovery Hub Helper Agent | NULL |
| 5 | USER_AGENT | User Discovery Agent | 1 |
| 6 | DATA_AGENT | Data Discovery Agent | 2 |
| 7 | TECH_AGENT | Tech Discovery Agent | 3 |

The pillar agents were re-seeded when migration 009 was tested with a rollback, so they have IDs
5 to 7. The Helper Agent keeps ID 1. Code should look agents up by `agent_code`, not by ID.

---

## agent_runs

One row per agent execution. The row is created as `running` and then updated to `succeeded` or
`failed`. Checkpoint-mapping runs point at the Helper Agent and their batch. The 7 older
`user_discovery` runs have no agent, because that agent has been removed.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `project_id` | BIGINT | no | | FK to `projects.id`, cascade delete |
| `agent_id` | BIGINT | yes | | FK to `agents.id`: the agent that ran. NULL for the removed User Discovery runs. |
| `batch_id` | NVARCHAR(50) | yes | | Readable batch name, e.g. `BATCH-20261116-1A2B3C4D`. Older runs have `LEGACY-<id>`. |
| `trigger_source_id` | BIGINT | yes | | FK to `context_sources.id`: the document that caused the run. Not used yet. |
| `run_type` | NVARCHAR(50) | no | 'checkpoint_mapping' | `checkpoint_mapping` or `user_discovery` |
| `status` | NVARCHAR(20) | no | | `running`, `succeeded` or `failed` |
| `model` | NVARCHAR(100) | yes | | Model the agent reported, e.g. `gpt-5.6-luna` |
| `chunk_count` | INT | no | | Number of chunks sent in the batch |
| `attempt_count` | INT | no | 0 | Attempts made. Must be 0 or more. |
| `prompt_tokens` | INT | yes | | Tokens in the request, from the agent's metadata |
| `completion_tokens` | INT | yes | | Tokens in the reply |
| `input_payload` | NVARCHAR(MAX) | yes | | The request sent to the agent, as JSON text. Must be valid JSON. Not written yet. |
| `raw_output` | NVARCHAR(MAX) | yes | | The agent's output, stored as JSON text. This is the only copy of the reply. |
| `error_message` | NVARCHAR(1000) | yes | | Why the run failed, e.g. `Agent5i returned HTTP 401.` |
| `started_at` | DATETIME2 | no | UTC now | When the run started |
| `completed_at` | DATETIME2 | yes | | When it finished |

Indexes: `(project_id, status)`, `(agent_id)`, `(batch_id)`, `(trigger_source_id)` where not NULL.

**Sample row**

| id | project_id | agent_id | batch_id | run_type | status | model | chunk_count | attempt_count | prompt_tokens | completion_tokens | error_message | started_at | completed_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 70 | 12 | 1 | BATCH-20261102-7F3A9C21 | checkpoint_mapping | succeeded | gpt-5.6-luna | 1 | 0 | 13240 | 2794 | NULL | 2026-11-02 09:30 | 2026-11-02 09:30 |

---

## agent_run_checkpoints

The result for each checkpoint inside one run. Intended for per-checkpoint agent runs. The
Helper Agent does not write here: its results are the mappings, which point at the run through
`agent_run_id`.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `agent_run_id` | BIGINT | no | | FK to `agent_runs.id`, cascade delete |
| `checkpoint_id` | BIGINT | no | | FK to `discovery_checkpoints.id` |
| `status` | NVARCHAR(20) | no | 'PENDING' | `PENDING`, `ANSWERED`, `NO_EVIDENCE` or `FAILED` |

Constraints: unique `(agent_run_id, checkpoint_id)`. Index on `checkpoint_id`.

**Sample row:** none yet.

---

## agent_run_chunks

The chunks sent into one run. The Helper Agent does not write here: each mapping already records
its run, so the chunk-to-run link is available through `context_checkpoint_mappings.agent_run_id`.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `agent_run_id` | BIGINT | no | | FK to `agent_runs.id`, cascade delete |
| `context_chunk_id` | BIGINT | no | | FK to `context_chunks.id`. No cascade, to avoid a second delete path. |
| `mapping_id` | BIGINT | yes | | FK to `context_checkpoint_mappings.id`: the mapping that caused the chunk to be sent. No cascade. |
| `created_at` | DATETIME2 | no | UTC now | When linked |

Constraints: unique `(agent_run_id, context_chunk_id)`. Indexes on `context_chunk_id`, and on
`mapping_id` where not NULL.

**Sample row:** none yet.

---

## context_checkpoint_mappings

A chunk tagged with a checkpoint by an agent. The core output of the system.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `project_id` | BIGINT | no | | FK to `projects.id`, cascade delete |
| `context_chunk_id` | BIGINT | no | | FK to `context_chunks.id` |
| `checkpoint_id` | BIGINT | no | | FK to `discovery_checkpoints.id` |
| `agent_run_id` | BIGINT | no | | FK to `agent_runs.id`: the run that produced it |
| `mapped_by_agent_id` | BIGINT | no | | FK to `agents.id`: the agent that produced it |
| `is_active` | BIT | no | 1 | 1 = current. 0 = kept as history after deactivation. |
| `created_at` | DATETIME2 | no | UTC now | When created |
| `deactivated_at` | DATETIME2 | yes | | When deactivated. Must be set exactly when `is_active` is 0. |

Constraints and indexes:
- Only one **active** mapping per (project, chunk, checkpoint). Inactive history rows are unlimited.
- `(is_active = 1 AND deactivated_at IS NULL)` or `(is_active = 0 AND deactivated_at IS NOT NULL)`.
- Index on `(project_id, context_chunk_id)`, and on `(project_id, checkpoint_id)` for active rows.

**Sample row**

| id | project_id | context_chunk_id | checkpoint_id | agent_run_id | mapped_by_agent_id | is_active | created_at | deactivated_at |
|---|---|---|---|---|---|---|---|---|
| 500 | 12 | 91 | 301 | 70 | 1 | 1 | 2026-11-02 09:30 | NULL |

Checkpoint 301 is `TECH01` (Existing Systems). Its evidence is in `mapping_evidence`.

---

## mapping_evidence

The quote that justifies a mapping, with its exact position in the content.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `mapping_id` | BIGINT | no | | FK to `context_checkpoint_mappings.id`, cascade delete |
| `evidence_quote` | NVARCHAR(MAX) | no | | The quote, copied exactly from the chunk |
| `reason` | NVARCHAR(MAX) | no | | Why the agent says the quote supports the checkpoint |
| `evidence_start_char` | INT | no | | Offset of the quote in `content_text` |
| `evidence_end_char` | INT | no | | Offset just after the quote |
| `created_at` | DATETIME2 | no | UTC now | When created |

Constraints: `evidence_end_char > evidence_start_char`; `evidence_end_char - evidence_start_char = LEN(evidence_quote)`.

Check: `content_text[evidence_start_char:evidence_end_char] = evidence_quote` always holds for
stored rows.

**Sample row**

| id | mapping_id | evidence_quote | reason | evidence_start_char | evidence_end_char |
|---|---|---|---|---|---|
| 812 | 500 | The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. | The quote names the existing ERP platform, which is an existing system supporting the workflow. | 0 | 79 |

---

## project_checkpoint_answers

The current answer and completion state for one checkpoint in one project. Created by migration
010. Nothing writes to it yet. Each project has at most one row per checkpoint.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `project_id` | BIGINT | no | | FK to `projects.id`, cascade delete |
| `checkpoint_id` | BIGINT | no | | FK to `discovery_checkpoints.id` |
| `current_answer` | NVARCHAR(MAX) | yes | | The approved answer text |
| `status` | NVARCHAR(30) | no | 'NOT_STARTED' | Answer state. The allowed values are not constrained yet. |
| `is_completed` | BIT | no | 0 | Whether the checkpoint counts as complete |
| `completion_score` | DECIMAL(3,2) | yes | | Between 0.00 and 1.00 |
| `completion_updated_by_run_id` | BIGINT | yes | | FK to `agent_runs.id`: the run that last changed completion |
| `completion_updated_at` | DATETIME2 | yes | | When completion last changed |
| `approved_by` | BIGINT | yes | | FK to `users.id`: who approved the answer |
| `approved_at` | DATETIME2 | yes | | When it was approved |
| `updated_at` | DATETIME2 | no | UTC now | Last change to the row |

Constraints: unique `(project_id, checkpoint_id)`; `completion_score` between 0 and 1 when set.
Indexes: `(checkpoint_id)`, `(status)`.

**Sample row**

| id | project_id | checkpoint_id | current_answer | status | is_completed | completion_score | approved_by | approved_at |
|---|---|---|---|---|---|---|---|---|
| 40 | 12 | 301 | The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. | APPROVED | 1 | 0.80 | 7 | 2026-11-03 10:00 |

---

## checkpoint_answer_proposals

AI-proposed answers for a checkpoint answer. Many proposals can exist for one answer. Created by
migration 010. Nothing writes to it yet. A proposal's project and checkpoint are reached through
`current_answer_id`, so they are not repeated here.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `current_answer_id` | BIGINT | no | | FK to `project_checkpoint_answers.id`, cascade delete |
| `agent_run_id` | BIGINT | no | | FK to `agent_runs.id`: the run that generated the proposal |
| `base_version_number` | INT | no | | The answer version the proposal was written against. 0 or more. |
| `proposed_answer` | NVARCHAR(MAX) | no | | The proposed answer text |
| `completion_score` | DECIMAL(3,2) | yes | | Between 0.00 and 1.00 |
| `status` | NVARCHAR(20) | no | 'PENDING' | Review state. The allowed values are not constrained yet. |
| `superseded_by_proposal_id` | BIGINT | yes | | FK to this same table: the newer proposal that replaced this one |
| `created_at` | DATETIME2 | no | UTC now | When generated |
| `reviewed_at` | DATETIME2 | yes | | When reviewed |

Constraints: `base_version_number >= 0`; `completion_score` between 0 and 1 when set.
Indexes: `(current_answer_id)`, `(agent_run_id)`, `(status)`, and `(superseded_by_proposal_id)` where not NULL.

**Sample row**

| id | current_answer_id | agent_run_id | base_version_number | proposed_answer | completion_score | status | superseded_by_proposal_id | created_at |
|---|---|---|---|---|---|---|---|---|
| 61 | 40 | 71 | 0 | The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. | 0.80 | PENDING | NULL | 2026-11-03 09:45 |

---

## proposal_evidence

Links a proposal to the chunks and mappings that support it. The quote and reason are not copied
here; they stay in `mapping_evidence`. Created by migration 010. Nothing writes to it yet.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `proposal_id` | BIGINT | no | | FK to `checkpoint_answer_proposals.id`, cascade delete |
| `context_chunk_id` | BIGINT | no | | FK to `context_chunks.id`. No cascade. |
| `mapping_id` | BIGINT | no | | FK to `context_checkpoint_mappings.id`. No cascade. |
| `agent_run_id` | BIGINT | no | | FK to `agent_runs.id`. No cascade. |
| `created_at` | DATETIME2 | no | UTC now | When linked |

Constraints: unique `(proposal_id, mapping_id)`. Indexes on `proposal_id`, `context_chunk_id`,
`mapping_id` and `agent_run_id`.

**Sample row**

| id | proposal_id | context_chunk_id | mapping_id | agent_run_id | created_at |
|---|---|---|---|---|---|
| 19 | 61 | 91 | 500 | 71 | 2026-11-03 09:45 |

---

## checkpoint_answer_versions

Saved, numbered snapshots of a checkpoint answer. Old versions are never edited. Created by
migration 010. Nothing writes to it yet.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `checkpoint_answer_id` | BIGINT | no | | FK to `project_checkpoint_answers.id`, cascade delete |
| `version_number` | INT | no | | 1 or more. Unique per answer. |
| `answer_text` | NVARCHAR(MAX) | no | | The answer text at this version |
| `source` | NVARCHAR(20) | no | | `AI_PROPOSAL` or `MANUAL` |
| `proposal_id` | BIGINT | yes | | FK to `checkpoint_answer_proposals.id`. Required when `source` is `AI_PROPOSAL`. |
| `created_by` | BIGINT | no | | FK to `users.id`: who saved this version |
| `created_at` | DATETIME2 | no | UTC now | When saved |

Constraints: unique `(checkpoint_answer_id, version_number)`; `version_number >= 1`;
`source` is `AI_PROPOSAL` or `MANUAL`; an `AI_PROPOSAL` version must have a `proposal_id`.
Indexes: `(proposal_id)`, `(created_by)`.

**Sample row**

| id | checkpoint_answer_id | version_number | answer_text | source | proposal_id | created_by | created_at |
|---|---|---|---|---|---|---|---|
| 33 | 40 | 1 | The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. | AI_PROPOSAL | 61 | 7 | 2026-11-03 10:00 |

---

## checkpoint_answer_evidence

The document chunks that support one saved version of a checkpoint answer. Created by migration
010. Nothing writes to it yet. The original chunks are never deleted by deleting an answer.

| Column | Type | Nullable | Default | Meaning |
|---|---|---|---|---|
| `id` | BIGINT identity | no | | Primary key |
| `checkpoint_answer_id` | BIGINT | no | | FK to `project_checkpoint_answers.id`. No cascade: the version cascade reaches these rows. |
| `answer_version_id` | BIGINT | no | | FK to `checkpoint_answer_versions.id`, cascade delete |
| `context_chunk_id` | BIGINT | no | | FK to `context_chunks.id`. No cascade. |
| `created_at` | DATETIME2 | no | UTC now | When linked |

Constraints: unique `(answer_version_id, context_chunk_id)`. Indexes on `checkpoint_answer_id`,
`answer_version_id` and `context_chunk_id`.

**Sample row**

| id | checkpoint_answer_id | answer_version_id | context_chunk_id | created_at |
|---|---|---|---|---|
| 8 | 40 | 33 | 91 | 2026-11-03 10:00 |

---

## alembic_version

Used by Alembic to know which migration the database has reached. Do not edit it by hand.

| Column | Type | Meaning |
|---|---|---|
| `version_num` | VARCHAR(32) | Current revision: `010_checkpoint_answer_tables` |

---

## Notes

- **Timestamps:** `DATETIME2` columns are set by the database clock (`SYSUTCDATETIME()`), so they are UTC.
  Some older tables (`users`, `refresh_tokens`, `password_reset_tokens`) use `DATETIME`.
- **Soft deletes:** documents are soft-deleted (`context_sources.deleted_at`). Their text and chunks
  remain in the database. Projects are hard-deleted.
- **Immutable chunks:** chunk rows are never updated or deleted. A changed document gets new content and new chunks.
- **Mapping history:** mappings are deactivated, not deleted, so the history of what was tagged stays available.
- **Agent history:** the 7 `user_discovery` runs and their reply text remain in `agent_runs` after the feature was removed.
- **Checkpoint answer tables are schema only.** They were created in migration 010 so future features
  have a place to store answers, proposals, versions and evidence. No code writes to them yet, so they
  have no rows. The sample rows above are illustrations of the intended shape.
- **Status values:** the `status` columns on the answer and proposal tables are not constrained to a
  fixed list yet. The sample values are examples.
