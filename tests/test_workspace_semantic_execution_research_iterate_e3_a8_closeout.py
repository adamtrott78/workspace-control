from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a8-live-closeout.v0.1.json"


def test_e3_a8_closeout_is_consumed_fail_without_retry_authority() -> None:
    item=json.loads(CLOSEOUT.read_text(encoding="utf-8"))
    assert item["status"]=="CONSUMED_FAIL_ROOT_CANDIDATE_NOT_DURABLY_INGESTED"
    assert item["attempt"]["authority_consumed"] is True
    assert item["attempt"]["authority_reusable"] is False
    assert item["attempt"]["silent_retry_permitted"] is False
    assert item["attempt"]["backend_exit_code"]==1
    assert item["root_service_point"]["candidate_commit"]=="968db0800e9dcdee6e5a784889d74653276fb184"
    assert item["root_service_point"]["candidate_parent"]=="fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
    assert item["root_service_point"]["candidate_durable_intake_registered"] is False
    terminal=item["terminal_durable_state"]
    assert terminal["reasoning_processes"]["by_state_generation"]=={"RUNNING@0":1}
    assert terminal["executor_sessions"]["by_state_generation"]=={"BOUND@0":1}
    assert terminal["operator_actions"]["by_state"]=={"AWAITING_DURABLE_ACK":1}
    assert terminal["operator_actions"]["sent_unconfirmed_current_binding"]==1
    assert terminal["worker_results"]==0
    assert item["rollback_cleanup"]["tailscale_existing_config_exactly_restored"] is True
    assert item["rollback_cleanup"]["workspace_operator_dev_offline"] is True
    assert item["new_live_authority_exists"] is False


def test_e3_a8_closeout_requires_deterministic_replay_before_any_retry() -> None:
    item=json.loads(CLOSEOUT.read_text(encoding="utf-8"))
    assert item["next_stage"]=="E3-A9_ROOT_CANDIDATE_INTAKE_DIAGNOSTIC_REPAIR"
    assert item["diagnosis"]["exact_execution_error"]=="UNAVAILABLE_FROM_CAPTURED_TERMINAL_TAIL"
    assert item["diagnosis"]["classification"]=="ROOT_CANDIDATE_EVENT_OR_INTAKE_FAILURE_REQUIRES_DETERMINISTIC_REPLAY"
    joined="\n".join(item["repair_requirements"])
    assert "f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b" in joined
    assert "968db0800e9dcdee6e5a784889d74653276fb184" in joined
    assert "Do not create a new live authority" in joined
