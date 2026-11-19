"""
Testing aid: sends Helper mapping batches that already exist to the pillar-agent outbox.

New uploads are dispatched automatically right after each batch is mapped. This script replays
batches that were mapped before dispatch existed, or one batch you want to look at again.
Nothing in the database is changed; packages are written to backend/agent_outbox/.

Run from backend/:
    python scripts/dispatch_mapping_runs.py --run 70          one Helper batch (agent_runs.id)
    python scripts/dispatch_mapping_runs.py --project 12      every succeeded Helper batch of a project
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.models import AgentRun  # noqa: E402
from app.db.session import get_session_factory  # noqa: E402
from app.services.pillar_dispatch_service import dispatch_mapping_run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Send existing Helper batches to the pillar-agent outbox.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", type=int, help="one Helper agent_runs.id")
    group.add_argument("--project", type=int, help="every succeeded Helper batch of this project")
    args = parser.parse_args()

    if args.run is not None:
        run_ids = [args.run]
    else:
        with get_session_factory()() as db:
            run_ids = list(
                db.scalars(
                    select(AgentRun.id)
                    .where(
                        AgentRun.project_id == args.project,
                        AgentRun.run_type == "checkpoint_mapping",
                        AgentRun.status == "succeeded",
                    )
                    .order_by(AgentRun.id)
                )
            )
        if not run_ids:
            print(f"No succeeded Helper batches for project {args.project}.")
            return 1

    for run_id in run_ids:
        packages = dispatch_mapping_run(run_id)
        summary = ", ".join(
            f"{p['agent_code'] or p['pillar_code'] + ' (no agent)'}: {p['chunk_count']} chunks / "
            f"{p['checkpoint_count']} checkpoints"
            for p in packages
        )
        print(f"Batch {run_id}: {summary or 'no active mappings'}")
    print("Packages written under backend/agent_outbox/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
