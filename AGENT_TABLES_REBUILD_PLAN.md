# Agent tables: corrected plan

This replaces the drop-and-recreate prompt. The inventory showed that dropping the tables would
delete data that other rows depend on, so this plan changes the tables in place instead.

## Step 1 inventory (read-only, run on Azure SQL)

| Item | Result |
|---|---|
| `agents` | exists, 1 row (`HELPER_AGENT`), columns: id, agent_code, name, pillar_id, created_at |
| `agent_runs` | exists, 30 rows: 19 `checkpoint_mapping` succeeded, 4 `checkpoint_mapping` failed, 7 `user_discovery` succeeded |
| `agent_run_chunks` | exists, 0 rows |
| `agent_run_checkpoints` | does not exist |
| `context_checkpoint_mappings` | exists, 367 rows |

Foreign keys pointing at the agent tables:

| Foreign key | Table | Column | Target | Rows in table |
|---|---|---|---|---|
| `fk_mappings_agent_run_id` | `context_checkpoint_mappings` | `agent_run_id` | `agent_runs` | 367 |
| `fk_mappings_mapped_by_agent_id` | `context_checkpoint_mappings` | `mapped_by_agent_id` | `agents` | 367 |
| `fk_agent_run_chunks_agent_run_id` | `agent_run_chunks` | `agent_run_id` | `agent_runs` | 0 |

Tables the original prompt named that do not exist in this database:
`checkpoint_answer_proposals`, `project_checkpoint_answers`, `proposal_evidence`.

**Stop condition met.** Rows exist in `context_checkpoint_mappings`, which references both
`agents` and `agent_runs`. The original drop-and-recreate would delete or orphan them, so it is
not used.

## Why the original prompt does not match the code

| Area | Original prompt | Current code and database |
|---|---|---|
| `agent_runs` columns | `agent_id`, `batch_id`, `trigger_source_id`, `model_version`, `input_payload`, `output_payload` | `run_type`, `model`, `chunk_count`, `prompt_tokens`, `completion_tokens`, `raw_output`, `error_message` |
| `run_type` values | `INITIAL`, `REGENERATION`, `REBUILD`, `RETRY` | `checkpoint_mapping`, `user_discovery` |
| `status` values | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` | `running`, `succeeded`, `failed` |
| Helper Agent runs | | Write to `agent_runs` only. No rows in `agent_run_checkpoints` or `agent_run_chunks`. |
| User Discovery | | Removed from the code. Its 7 old `agent_runs` rows remain as history. |

## Plan: additive, no drops

Each change keeps existing columns and rows, so the mapping data stays linked.

### 1. `agents`
- Add `agent_code` as unique, and seed `USER_AGENT`, `DATA_AGENT`, `TECH_AGENT`, `HELPER_AGENT`
  if they are missing. Look up pillars by `discovery_pillars.code`.
- `HELPER_AGENT` keeps `pillar_id` NULL.
- Add the filtered unique index on `pillar_id WHERE pillar_id IS NOT NULL`.
- Existing row `HELPER_AGENT` is kept. Its `id` does not change, so the 367 mapping rows stay valid.

### 2. `agent_runs`
- Keep every existing column and the existing `run_type` and `status` values.
- Add `agent_id` as a nullable column, then backfill it: checkpoint-mapping rows get
  `HELPER_AGENT`'s id. The 7 `user_discovery` rows get NULL, because the agent they used has been removed.
- Add `batch_id` NVARCHAR(50) as nullable. Mapping rows keep their current `id` as their batch.
- Add `trigger_source_id` (nullable FK to `context_sources.id`).
- Extend the `run_type` and `status` checks to include the new values, without removing the old ones.
- Add `attempt_count` (default 0) and `input_payload` and `output_payload` (nullable, `ISJSON` checks).
  Keep `raw_output` as the output store that current code uses.
- Keep the FK from `context_checkpoint_mappings.agent_run_id`.

### 3. `agent_run_checkpoints` (new)
- `id`, `agent_run_id` (FK to `agent_runs`), `checkpoint_id` (FK to `discovery_checkpoints`),
  `status` (`PENDING`, `ANSWERED`, `NO_EVIDENCE`, `FAILED`), unique `(agent_run_id, checkpoint_id)`.
- Helper runs never write here.

### 4. `agent_run_chunks` (existing, 0 rows)
- Add `mapping_id` (nullable FK to `context_checkpoint_mappings.id`) and the unique
  `(agent_run_id, context_chunk_id)` if it is not already there.
- Helper runs never write here.

### 5. `context_checkpoint_mappings`
- No change to the existing 367 rows.
- `batch_id` is not added, because `agent_run_id` already identifies the batch.

## Verification
1. Row counts for every table are the same before and after the migration.
2. Every mapping still joins to its `agent_runs` and `agents` row.
3. A Helper run creates zero rows in `agent_run_checkpoints` and `agent_run_chunks`.
4. The filtered unique index on `agents.pillar_id` rejects a second agent for the same pillar.
5. Rolling back the migration and re-applying it both succeed.

## Decisions needed before the migration runs
1. **Keep or remove the 7 `user_discovery` run rows?** Keep them as history (recommended), or delete them.
2. **Use `batch_id` as NVARCHAR or GUID?** The current mapping runs have no batch ID, so NVARCHAR
   (readable, for example `BATCH-20261116-001`) is recommended.
3. **Helper rows need no `agent_run_chunks` entries.** Confirm that the mapping's `agent_run_id` is
   enough to show which chunks a run used, or ask for the table to be filled for Helper runs too.
