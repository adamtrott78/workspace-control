from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/"architecture/workspace-semantic-execution-research-iterate-e2-live-review.v0.2.json"
PROCEDURE=ROOT/"architecture/workspace-semantic-execution-research-iterate-e2-live-procedure.v0.2.md"


def test_e2_live_review_binds_validated_executable_stack() -> None:
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    assert r["status"]=="VALIDATED_EXECUTABLE_REVIEW_NOT_AUTHORITY"
    assert r["executable"]["head"]=="d04d06cee576a21e77286f7f6efe66485ec34375"
    assert r["executable"]["candidate_baseline"]=="fdb801d895068c78b2e2e11e6984173812884deb"
    assert r["executable"]["validation"]=={
        "workspace_control_run":3202,
        "semantic_execution_run":506,
        "operator_bridge_run":775,
        "result":"SUCCESS",
    }
    assert r["executable"]["exact_bindings"]["accepted_a7_src_tree"]=="51480cc44f62d661421e975e67af127ecd0b0417"


def test_e2_live_review_requires_five_manual_cycles_and_recovery() -> None:
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    f=r["live_fault_contract"]
    assert f["manual_service_points"]==5
    assert f["replacement_process_generation"]==1
    assert f["replacement_session_generation"]==1
    assert f["stale_worker_candidate_must_be_rejected_without_mutation"] is True
    assert f["manual_durable_state_relay"] is False


def test_e2_live_review_grants_no_authority() -> None:
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    assert r["authority_gate"]["live_attempt_authorized"] is False
    assert r["authority_gate"]["fresh_one_shot_authority_required"] is True


def test_e2_live_procedure_keeps_a7_loop_and_consumption_boundary() -> None:
    text=PROCEDURE.read_text(encoding="utf-8")
    assert "Ctrl+Space -> Ctrl+V -> Enter" in text
    assert "E2_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text
    assert "grants no execution authority" in text
