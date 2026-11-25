from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a8-live-authority.v0.1.json"
REVIEW = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a8-live-review.v0.1.json"
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a8_v1.sh"


def test_e3_a8_authority_is_fresh_one_shot_and_exactly_bound() -> None:
    a=json.loads(AUTH.read_text(encoding="utf-8"))
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    assert a["schema_version"]==1
    assert a["artifact_id"]=="workspace-semantic-execution-research-iterate-e3-a8-live-authority-v0.1"
    assert a["status"]=="PENDING_OPERATOR_WOP_EXECUTION"
    assert a["approval_basis"]["original_statement"]=="GOOOO"
    assert a["approval_basis"]["original_scope"]=="EXACTLY_ONE_E3_A8_LIVE_RETRY"
    assert a["reviewed_source"]["review_head"]=="c6dd247faaee12f1d8ade2cb53c60de41e3c3cdc"
    assert r["candidate_baseline"]=="fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
    b=a["execution_bindings"]
    assert b["candidate_baseline"]=="fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
    assert b["e3_a8_wrapper_blob"]=="4615149b8ed20d327a8ceaf8dfd6605524f858da"
    assert b["e2_harness_blob"]=="d6acd6a4266641813deecb900b877b7250b02530"
    assert b["observer_blob"]=="458a869252f108bea52952e12852961bc3158d1f"
    assert b["a8_frontend_review_head"]=="6fb315884804214f96ca0f7264a48eed40741a60"
    assert b["a8_frontend_source_head"]=="b97a4c7b9309d413ced7eea14fe87b5864ad0c5b"
    assert b["operator_transport_head"]=="55edb7a6e618f5a49ddf17ec5c9426f70fa08f2d"
    attempt=a["attempt_contract"]
    assert attempt["attempts_authorized"]==1
    assert attempt["consumed"] is False
    assert attempt["reusable"] is False
    assert attempt["no_silent_retry"] is True
    assert attempt["live_consumption_marker"]=="E3_A8_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"


def test_e3_a8_authority_matches_linux_preflight_contract() -> None:
    a=json.loads(AUTH.read_text(encoding="utf-8"))
    text=LINUX.read_text(encoding="utf-8")
    for key in (
        "candidate_baseline",
        "e3_a8_wrapper_blob",
        "e2_harness_blob",
        "observer_blob",
        "a8_frontend_review_head",
        "a8_frontend_source_head",
        "operator_transport_head",
    ):
        assert key in a["execution_bindings"]
    assert "AUTHORITY_STATUS_MISMATCH" in text
    assert "AUTHORITY_ATTEMPT_STATE_MISMATCH" in text
    assert "AUTHORITY_REUSE_POLICY_MISMATCH" in text
    assert "AUTHORITY_BINDING_MISMATCH" in text
    assert "E3_A8_AUTHORITY_BINDING=PASS" in text
    assert "merge-base --is-ancestor" in text


def test_e3_a8_authority_does_not_reuse_consumed_predecessor() -> None:
    a=json.loads(AUTH.read_text(encoding="utf-8"))
    assert a["approval_basis"]["consumed_predecessor_authority_reused"] is False
    assert a["launch_contract"]["historical_wop_e3_alias_reused"] is False
    assert a["accepted_frontend"]["version"]=="A8"
