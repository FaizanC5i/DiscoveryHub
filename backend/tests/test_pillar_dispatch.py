# tests/test_pillar_dispatch.py
"""
Tests for grouping one Helper batch's mappings into per-pillar agent packages, and for the
JSON outbox. Pure logic: no database and no network.
Run from backend/: python -m pytest -q tests/test_pillar_dispatch.py
"""

import json

from app.services import chunk_mapping_service, pillar_dispatch_service
from app.services.pillar_dispatch_service import group_batch_by_pillar, json_file_outbox, missing_mapping_ids

BATCH = {"project_id": 12, "batch_id": "BATCH-20261116-ABCD1234", "helper_agent_run_id": 70}
AGENTS = {
    1: {"agent_id": 2, "agent_code": "USER_AGENT"},
    2: {"agent_id": 3, "agent_code": "DATA_AGENT"},
    3: {"agent_id": 4, "agent_code": "TECH_AGENT"},
}
PILLARS = {401: (1, "USER"), 402: (1, "USER"), 201: (2, "DATA"), 301: (3, "TECH"), 302: (3, "TECH"), 303: (3, "TECH")}
SORT = {401: 1, 402: 2, 201: 1, 301: 1, 302: 2, 303: 3}


def _row(mapping_id, checkpoint_id, chunk_id, quote="q", source_id=30):
    pillar_id, pillar_code = PILLARS[checkpoint_id]
    return {
        "mapping_id": mapping_id,
        "checkpoint_id": checkpoint_id,
        "checkpoint_code": f"{pillar_code}0{SORT[checkpoint_id]}",
        "checkpoint_name": f"cp {checkpoint_id}",
        "question": f"question {checkpoint_id}?",
        "why_it_matters": None,
        "sort_order": SORT[checkpoint_id],
        "pillar_id": pillar_id,
        "pillar_code": pillar_code,
        "pillar_name": f"{pillar_code.title()} Discovery",
        "chunk_id": chunk_id,
        "chunk_number": chunk_id,
        "chunk_text": f"text of chunk {chunk_id}",
        "page_number": None,
        "source_id": source_id,
        "source_title": "notes",
        "evidence_quote": quote,
        "evidence_reason": "reason" if quote is not None else None,
        "evidence_start_char": 0 if quote is not None else None,
        "evidence_end_char": len(quote) if quote is not None else None,
    }


def _group(rows, agents=AGENTS):
    return group_batch_by_pillar(BATCH, rows, agents, created_at="2026-11-16T10:00:00")


def _by_code(packages):
    return {p["pillar_code"]: p for p in packages}


def test_each_mapping_goes_to_the_agent_of_its_checkpoints_pillar():
    rows = [_row(500, 401, 91), _row(501, 201, 92), _row(502, 303, 93)]
    packages = _by_code(_group(rows))

    assert packages["USER"]["agent_code"] == "USER_AGENT"
    assert [c["chunks"][0]["chunk_id"] for c in packages["USER"]["checkpoints"]] == [91]
    assert [c["chunks"][0]["chunk_id"] for c in packages["DATA"]["checkpoints"]] == [92]
    assert [c["chunks"][0]["chunk_id"] for c in packages["TECH"]["checkpoints"]] == [93]


def test_the_chunk_text_is_sent_not_just_the_id():
    tech = _by_code(_group([_row(500, 303, 93)]))["TECH"]
    chunk = tech["checkpoints"][0]["chunks"][0]

    assert chunk["chunk_text"] == "text of chunk 93"
    assert chunk["evidence"][0]["quote"] == "q"


def test_only_pillars_touched_by_the_batch_get_a_package():
    packages = _group([_row(500, 301, 91)])

    assert [p["pillar_code"] for p in packages] == ["TECH"]


def test_only_checkpoints_touched_by_the_batch_are_listed():
    tech = _by_code(_group([_row(500, 303, 91)]))["TECH"]

    assert [c["checkpoint_id"] for c in tech["checkpoints"]] == [303]
    assert tech["checkpoint_count"] == 1


def test_chunk_mapped_to_two_pillars_goes_to_both_agents():
    packages = _by_code(_group([_row(500, 401, 91), _row(501, 301, 91)]))

    assert packages["USER"]["checkpoints"][0]["chunks"][0]["chunk_id"] == 91
    assert packages["TECH"]["checkpoints"][0]["chunks"][0]["chunk_id"] == 91


def test_chunk_mapped_to_two_checkpoints_of_one_pillar_is_listed_under_each_and_counted_once():
    tech = _by_code(_group([_row(500, 301, 91), _row(501, 302, 91)]))["TECH"]

    assert [c["checkpoint_id"] for c in tech["checkpoints"]] == [301, 302]
    assert tech["chunk_count"] == 1
    assert tech["mapping_count"] == 2


def test_checkpoints_follow_sort_order_whatever_order_the_rows_arrive_in():
    tech = _by_code(_group([_row(500, 303, 91), _row(501, 301, 92), _row(502, 302, 93)]))["TECH"]

    assert [c["checkpoint_id"] for c in tech["checkpoints"]] == [301, 302, 303]


def test_several_evidence_rows_for_one_mapping_land_on_one_chunk():
    tech = _by_code(_group([_row(500, 301, 91, quote="first"), _row(500, 301, 91, quote="second")]))["TECH"]
    chunks = tech["checkpoints"][0]["chunks"]

    assert len(chunks) == 1
    assert [e["quote"] for e in chunks[0]["evidence"]] == ["first", "second"]


def test_mapping_without_evidence_is_still_sent():
    tech = _by_code(_group([_row(500, 301, 91, quote=None)]))["TECH"]

    assert tech["checkpoints"][0]["chunks"][0]["evidence"] == []


def test_package_carries_the_batch_it_came_from():
    package = _group([_row(500, 301, 91)])[0]

    assert package["project_id"] == 12
    assert package["batch_id"] == "BATCH-20261116-ABCD1234"
    assert package["helper_agent_run_id"] == 70


def test_pillar_without_an_agent_still_gets_its_package():
    package = _group([_row(500, 301, 91)], agents={})[0]

    assert package["agent_code"] is None
    assert package["chunk_count"] == 1


def test_no_mapping_is_left_out():
    rows = [_row(500, 401, 91), _row(501, 201, 91), _row(502, 301, 92), _row(503, 302, 92), _row(504, 303, 93)]
    packages = _group(rows)

    assert missing_mapping_ids(rows, packages) == []
    assert sum(p["mapping_count"] for p in packages) == 5


def test_empty_batch_gives_no_packages():
    assert _group([]) == []


def test_json_outbox_writes_one_file_per_agent_under_project_and_batch(tmp_path):
    send = json_file_outbox(tmp_path)
    for package in _group([_row(500, 401, 91), _row(501, 303, 92)]):
        send(package)

    folder = tmp_path / "project_12" / "BATCH-20261116-ABCD1234"
    assert sorted(p.name for p in folder.iterdir()) == ["TECH_AGENT.json", "USER_AGENT.json"]
    tech = json.loads((folder / "TECH_AGENT.json").read_text(encoding="utf-8"))
    assert tech["checkpoints"][0]["chunks"][0]["chunk_text"] == "text of chunk 92"


def test_mapping_job_dispatch_failure_is_logged_not_raised(monkeypatch):
    def _boom(run_id):
        raise RuntimeError("outbox unavailable")

    monkeypatch.setattr(pillar_dispatch_service, "dispatch_mapping_run", _boom)

    chunk_mapping_service._dispatch_to_pillar_agents(70)  # must not raise
