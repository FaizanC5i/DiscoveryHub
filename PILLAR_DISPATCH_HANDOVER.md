# Pillar dispatch: handover

What happens after the Helper Agent has mapped chunks to checkpoints, where everything is stored,
and what is still to do. Branch: `feature/pillar-agent-grouping`.

## The flow

```
Upload -> context_sources -> context_content -> context_chunks
       -> Helper Agent maps a batch of chunks -> context_checkpoint_mappings (+ mapping_evidence)
       -> PILLAR DISPATCH (this work), right after the batch is saved:
            for each new mapping: checkpoint -> pillar -> that pillar's agent
            one package per agent (USER_AGENT, DATA_AGENT, TECH_AGENT) per batch
       -> pillar agent (not built yet)
```

Each package holds, per checkpoint:
- the checkpoint (code, name, question, why it matters),
- `existing_answer` and `existing_answer_status`: the current answer from `project_checkpoint_answers`
  (`null` when there is none yet), so the agent updates it instead of starting again,
- the new chunks: full `chunk_text`, file name, page, and the Helper's evidence quote and reason.

Rules:
- Runs immediately after each Helper batch is committed. It does not wait for other files.
- Only the batch's new mappings are sent. A pair the Helper had already mapped is never sent again.
- A chunk mapped to checkpoints of two pillars goes to both agents.
- Only agents with something new get a package; only checkpoints the batch touched are listed.
- If any mapping reaches no package, the dispatch raises an error (nothing silently dropped).
- A dispatch error is logged and never undoes or fails the mapping.

## Where things are stored

| What | Where |
|---|---|
| Chunk -> checkpoint mappings (the input) | `context_checkpoint_mappings` (active rows: `is_active = 1`) |
| Why a chunk was mapped | `mapping_evidence` (quote, reason, character offsets) |
| Which Helper batch produced a mapping | `context_checkpoint_mappings.agent_run_id` -> `agent_runs` (`batch_id`) |
| Checkpoint -> pillar | `discovery_checkpoints.pillar_id` -> `discovery_pillars` |
| Pillar -> agent | `agents.pillar_id` (`USER_AGENT`, `DATA_AGENT`, `TECH_AGENT`; seeded by migration 009) |
| Existing answer sent to the agent | `project_checkpoint_answers.current_answer` (read only) |
| The packages (until the agents exist) | JSON files: `backend/agent_outbox/project_<id>/<batch_id>/<AGENT_CODE>.json` (git-ignored, contains client text) |

The dispatch writes nothing to the database. It only reads.

## Code

| File | Purpose |
|---|---|
| `backend/app/services/pillar_dispatch_service.py` | Reads a batch's mappings, groups them per pillar agent, adds existing answers, sends each package |
| `backend/app/services/chunk_mapping_service.py` | Calls `_dispatch_to_pillar_agents(agent_run_id)` right after a batch's mappings are committed |
| `backend/app/core/config.py` | `pillar_dispatch_outbox` (default `agent_outbox`; empty turns dispatch off) |
| `backend/scripts/dispatch_mapping_runs.py` | Replays batches mapped before dispatch existed: `--run <agent_runs.id>` or `--project <id>` |
| `backend/tests/test_pillar_dispatch.py` | 17 unit tests (grouping, existing answer, outbox, failure handling) |

To plug in a real agent: pass a `send` function to `dispatch_mapping_run(run_id, send=...)`, or replace
`json_file_outbox()` with a function that calls the agent. The grouping does not change.

## How it was tested (17 Nov 2026)

- Unit tests: `python -m pytest -q --noconftest tests/test_pillar_dispatch.py` -> 17 passed.
- Real data, project 212 (3 files, 3 Helper batches): all 58 active mappings reached exactly the
  right agent's file, none missing, none extra. One chunk was `NO_MATCH`, so it correctly went nowhere.
- Real database, existing answer: inside a rolled-back transaction, an answer for USER05 in project 212
  was sent to `USER_AGENT` together with its 3 new chunks; checkpoints without an answer carried `null`.
  Nothing was saved.

## Not done yet (next steps)

1. The pillar agents (User, Data, Tech) themselves.
2. Saving each agent's reply as a draft in `checkpoint_answer_proposals` (+ `proposal_evidence`). Note:
   a draft requires an `agent_run_id`, and `agent_runs.run_type` only allows `checkpoint_mapping` and
   `user_discovery`; a value for pillar-agent runs (for example `checkpoint_answer`) must be added first.
3. Approval (draft -> `project_checkpoint_answers` -> `checkpoint_answer_versions`): handled by the team.
   A first version of draft/approve code was written and then removed from this branch; ask Sumanjali
   if it is useful as a starting point.
4. Deciding whether the agent should also see a waiting (not yet approved) draft, so that two uploads in
   a row build on each other before anyone approves.
