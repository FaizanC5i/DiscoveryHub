# What happens when you upload a file

This walks through one upload from the browser to the last table write. The IDs in the
example (project 12, source 30, and so on) are made up to show the shape of the data.

There are two phases:

1. **Inside the upload request.** The file is saved, its text is extracted, and the text is
   split into chunks. The response is sent back when this finishes.
2. **After the response, in the background.** Each chunk is sent to the Helper Agent, and the
   matches are saved. The job then stops.

---

## Example

You upload `notes.txt` (a plain text file) to project 12. The file contains:

> The ERP runs on a fixed on-premise server and cannot be upgraded before 2027.
> Staff log in to the intranet with a single shared account per warehouse.

---

## Phase 1: inside the upload request

### Step 1: the request arrives

`POST /api/projects/12/sources` with the file.

| Function | File | What it does |
|---|---|---|
| `get_current_user` (via `CurrentUser`) | `app/dependencies/auth.py` | Reads the access cookie and loads the user. No cookie, no upload. |
| `upload_source` (route) | `app/api/routes/context.py` | Reads the bytes, checks the size limit (`UPLOAD_MAX_MB`) and that the file is not empty. |

### Step 2: the service checks and saves the file

`context_service.upload_source(db, storage, user, 12, "notes.txt", data)`

| Order | Function | Database | Outside the database |
|---|---|---|---|
| a | `_require_project` | `SELECT projects` (checks the owner) | |
| b | `resolve_kind`, `check_content` (`core/file_types.py`) | | Checks the extension and the file's leading bytes. |
| c | `storage.save` | | Uploads `projects/12/sources/<random>.txt` to Azure Blob Storage. |
| d | `extract_text` (`services/extraction/extractors.py`) | | Plain text is decoded as UTF-8. PDF and DOCX use other extractors. |
| e | `ContextSource(...)`, `_apply_result` | | Builds the source row and the content row in memory. |
| f | `db.add` and `db.commit()` | **INSERT `context_sources`** (status `ready`), **INSERT `context_content`** (the full text) | |

If step d or f fails, the blob is deleted so nothing is left orphaned.

### Step 3: chunking, still inside the same request

`context_chunk_service.chunk_uploaded_content(db, content, source)`

| Order | Function | Database | Notes |
|---|---|---|---|
| g | `_chunk_content` | `UPDATE context_sources` status to `processing` (commit) | Shows "processing" while the chunks are built. |
| h | `chunk_text` (`services/chunking_service.py`) | | Pure function. Splits the text into overlapping chunks, each with `start_char` and `end_char`. |
| i | `page_number_at` | | Reads `Page N:` markers if the extractor wrote them. |
| j | `db.add_all` and `db.commit()` | **INSERT `context_chunks`** (one row per chunk), **UPDATE `context_sources`** status to `ready` | All chunks are written in one transaction. |

For the example, `chunk_text` returns one chunk (the text is short):

| Column | Value |
|---|---|
| `id` | 91 |
| `context_content_id` | 25 |
| `chunk_number` | 1 |
| `chunk_text` | the full two sentences |
| `start_char` | 0 |
| `end_char` | 149 |
| `char_count` | 149 |
| `page_number` | NULL (no page markers in a text file) |
| `mapping_status` | `PENDING` (the default) |

If chunking fails, the source is set to `failed` with the reason
"The text could not be split into chunks." The upload still succeeds, and the user can retry.

### Step 4: the route queues the mapping and responds

`_queue_mapping` in `app/api/routes/context.py`:

- `chunk_ids_for_content` runs `SELECT context_chunks.id` for content 25. Result: `[91]`.
- `enqueue_chunk_mapping(background, [91])` adds `run_mapping_job` to FastAPI's background
  tasks.

The route returns **201** with the source (`processing_status: "ready"`). At this point
the browser shows the file as ready, even though mapping has not started yet.

**Tables changed in phase 1:** `context_sources`, `context_content`, `context_chunks`.

---

## Phase 2: in the background, after the response

`run_mapping_job([91])` in `app/services/chunk_mapping_service.py`.

### Step 5: claim the chunks

`_claim_chunks` runs one statement:

```sql
UPDATE context_chunks SET mapping_status = 'IN_PROGRESS'
WHERE id IN (91) AND mapping_status IN ('PENDING', 'FAILED')
RETURNING id
```

Only chunks that are `PENDING` or `FAILED` are claimed. Chunks that are already `MAPPED`,
`NO_MATCH` or `IN_PROGRESS` are never sent again. The claim and the status change happen in one
statement, so two jobs cannot take the same chunk.

Then the job looks up each chunk's project and groups the chunks by project.

### Step 6: one batch per project

`map_batch(12, [91])` handles up to `MAPPING_BATCH_SIZE` chunks (20 by default). The batch is
one agent call.

| Order | Function | Database | Outside the database |
|---|---|---|---|
| k | `_load_chunks`, `_content_texts` | `SELECT context_chunks`, `SELECT context_content` | |
| l | `build_mapping_request` (`mapping_payload_service.py`) | `SELECT discovery_checkpoints` joined to `discovery_pillars` (only active ones, read fresh every time) | |
| m | `_helper_agent_id` | `SELECT agents` where `agent_code = 'HELPER_AGENT'` | |
| n | `AgentRun(...)` and commit | **INSERT `agent_runs`** with status `running` | |
| o | `_call_with_retry` → `call_helper_agent` | | **HTTP POST to the Agent5i webhook.** Retried up to 3 times on timeouts and 5xx. A 401 is not retried. |
| p | `find_checkpoint_output` (`agent_reply.py`) | | Finds the `chunk_results` inside the nested reply. |
| q | `validate_batch` (`mapping_validation_service.py`) | | Pure checks: the quote must be in the chunk, the checkpoint must be active, the reason must not be empty, the offsets must match the stored text. Bad matches are dropped with a warning. |
| r | `_save_success` | see below | |

In the example, the agent returns two matches for chunk 91: TECH01 and TECH04. Both pass
validation.

### Step 7: save the result in one transaction (`_save_success`)

| Function part | Database |
|---|---|
| Read the active mappings for chunk 91 (to skip duplicates) | `SELECT context_checkpoint_mappings` |
| One mapping per valid match | **INSERT `context_checkpoint_mappings`** (two rows: checkpoint 301 and 304, `agent_run_id = 70`, `mapped_by_agent_id` = the Helper Agent) |
| One evidence row per mapping | **INSERT `mapping_evidence`** (two rows: the quote, the reason, `evidence_start_char`, `evidence_end_char`) |
| Set the chunk status | **UPDATE `context_chunks`** set `mapping_status = 'MAPPED'`, `mapped_at`, `mapping_attempts + 1` |
| Mark the run finished | **UPDATE `agent_runs`** set `status = 'succeeded'`, `completed_at`, `model`, token counts, `raw_output` |
| Commit | all of the above together |

If the batch had no valid matches, the chunk would be set to `NO_MATCH` instead of `MAPPED`.

### Step 8: if the agent call fails

`_record_failure` (for example, the 401 from the earlier error):

| Database |
|---|
| **UPDATE `agent_runs`** set `status = 'failed'`, `error_message` |
| **UPDATE `context_chunks`** set `mapping_status = 'FAILED'`, `mapping_error`, `mapping_attempts + 1` |

No mapping rows are written. Other batches still run. The chunk can be sent again with
`POST /api/context-content/{id}/chunks/map`.

---

## Summary: which tables change

| Table | When | What changes |
|---|---|---|
| `context_sources` | Upload | Row inserted (`ready`). Set to `processing`, then `ready` again after chunking. |
| `context_content` | Upload | Row inserted with the full extracted text. |
| `context_chunks` | Upload | One row per chunk, `mapping_status = PENDING`. |
| `context_chunks` | Background | `IN_PROGRESS`, then `MAPPED`, `NO_MATCH` or `FAILED`. |
| `agent_runs` | Background | A `running` row, then `succeeded` or `failed`. |
| `context_checkpoint_mappings` | Background | One row per valid match. Never updated except to deactivate. |
| `mapping_evidence` | Background | One row per mapping: the quote and its offsets. |

Blob Storage is also written, once, during the upload (`projects/12/sources/<uuid>.txt`).

## Summary: the order of calls

```
POST /api/projects/12/sources
  get_current_user
  upload_source (route)
    context_service.upload_source
      _require_project                      SELECT projects
      resolve_kind, check_content
      storage.save                          Blob Storage upload
      extract_text
      db.commit                             INSERT context_sources, INSERT context_content
      chunk_uploaded_content
        _chunk_content
          UPDATE context_sources (processing)
          chunk_text, page_number_at        pure
          db.commit                         INSERT context_chunks, UPDATE context_sources (ready)
    _queue_mapping
      chunk_ids_for_content                 SELECT context_chunks
      enqueue_chunk_mapping                 queued as a background task
  return 201                                <- the browser gets the response here

[background, after the response]
run_mapping_job([91])
  _claim_chunks                             UPDATE context_chunks (IN_PROGRESS)
  map_batch(12, [91])
    _load_chunks, _content_texts            SELECT
    build_mapping_request                   SELECT discovery_checkpoints, discovery_pillars
    INSERT agent_runs (running)
    call_helper_agent                       HTTP POST to Agent5i (retried on timeout / 5xx)
    find_checkpoint_output, validate_batch  pure
    _save_success                           INSERT mappings and evidence,
                                            UPDATE context_chunks (MAPPED),
                                            UPDATE agent_runs (succeeded)
    (on failure)  _record_failure           UPDATE agent_runs (failed),
                                            UPDATE context_chunks (FAILED)
```

## What to look at when something goes wrong

- **Upload fails with an error response:** nothing was saved, or the blob was removed again.
- **File shows `failed` right after upload:** text extraction failed. `failure_reason` says why.
  No chunks exist.
- **File is `ready` but has no mappings:** check `context_chunks.mapping_status`. `PENDING` means
  the background job has not run. `FAILED` means the agent call failed, and `mapping_error` says
  why. `NO_MATCH` means the agent found nothing for the chunk.
- **Log warning `Agent5i returned HTTP 401`:** the webhook rejected the credentials or the agent
  name. See `agent_runs.error_message` for the same reason.
