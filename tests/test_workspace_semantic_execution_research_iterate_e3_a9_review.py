from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = (
    ROOT
    / "architecture"
    / "workspace-semantic-execution-research-iterate-e3-a9-root-intake-review.v0.1.json"
)


def _review():
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def test_e3_a9_review_records_exact_replay_pass_without_intake_repair() -> None:
    item = _review()
    replay = item["deterministic_replay"]
    assert replay["token"] == "63e9b17e492c4ed3a36d20c83172abf3"
    assert replay["root_packet_sha256"] == "f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b"
    assert replay["candidate_commit"] == "968db0800e9dcdee6e5a784889d74653276fb184"
    assert replay["candidate_parent"] == "fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
    assert replay["candidate_raw_sha256"] == "896b4fb08a4a73f5913a1dc028a4118971274795051fa90230b77d8c616c734f"
    assert replay["result"] == "PASS"
    assert replay["post_intake_state"]["worker_results"] == 1
    assert "No semantic worker-result binding/intake repair is justified" in replay["conclusion"]


def test_e3_a9_review_preserves_frozen_e2_and_a8_bytes() -> None:
    item = _review()
    impl = item["implementation"]
    assert impl["head"] == "dbd1acde9713c01f534a313e0bf31ad1254a6185"
    assert impl["accepted_e2_topology"]["blob"] == "d6acd6a4266641813deecb900b877b7250b02530"
    assert impl["accepted_e2_topology"]["modified"] is False
    assert impl["accepted_a8_wrapper"]["blob"] == "4615149b8ed20d327a8ceaf8dfd6605524f858da"
    assert impl["accepted_a8_wrapper"]["modified"] is False
    assert impl["a9_successor"]["blob"] == "89f14c3e89c0773d78c2472f76db00a5b6f3edaa"


def test_e3_a9_review_binds_validated_schema_provenance() -> None:
    item = _review()
    schema = item["schema_provenance"]
    assert schema["validated_review_head"] == "c6dd247faaee12f1d8ade2cb53c60de41e3c3cdc"
    assert schema["blob"] == "b84d362a8adbb1bf4a47f1dfc4f0b8089487a3c1"
    assert schema["candidate_branch_is_schema_source"] is False


def test_e3_a9_review_is_zero_authority_and_stops_at_fresh_gate() -> None:
    item = _review()
    assert item["status"] == "FROZEN_EXECUTABLE_REVIEW_ZERO_AUTHORITY"
    gate = item["authority_gate"]
    assert gate["live_authority_exists"] is False
    assert gate["live_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["fresh_explicit_operator_approval_required"] is True
    assert gate["a8_authority_reusable"] is False
    assert "STOP_AT_FRESH_AUTHORITY_GATE" in item["stop_condition"]


def test_e3_a9_implementation_validation_is_three_of_three_green() -> None:
    v = _review()["implementation_validation"]
    assert v["head"] == "dbd1acde9713c01f534a313e0bf31ad1254a6185"
    assert v["workspace_control"] == {
        "run_number": 3244,
        "run_id": 45694328127,
        "result": "SUCCESS",
    }
    assert v["semantic_execution"] == {
        "run_number": 543,
        "run_id": 45694327866,
        "result": "SUCCESS",
    }
    assert v["operator_bridge"] == {
        "run_number": 812,
        "run_id": 45694327851,
        "result": "SUCCESS",
    }
    assert v["result"] == "SUCCESS"
