from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.15.json"
REVIEW_HEAD = "d7bdd6e90bcb6ed15050bb66dc9af08241418cd5"
CANDIDATE_BASELINE = "d9f636ef508245459b3dd0a35b8d5587f533bac6"


def git(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()


def authority() -> dict:
    return json.loads(AUTHORITY.read_text(encoding="utf-8"))


def test_v115_authority_is_exactly_one_pending_attempt() -> None:
    a = authority()
    assert a["status"] == "PENDING_OPERATOR_WOP_EXECUTION"
    assert a["approval_basis"]["approved_scope"] == "EXACTLY_ONE_V1_15_D4_ATTEMPT"
    assert a["approval_basis"]["standing_or_future_authority_inferred"] is False
    assert a["attempt_contract"]["attempts_authorized"] == 1
    assert a["attempt_contract"]["consumed"] is False
    assert a["attempt_contract"]["reusable"] is True
    assert a["attempt_contract"]["no_silent_retry"] is True
    assert a["predecessor"]["consumed"] is True
    assert a["predecessor"]["reusable"] is False


def test_v115_authority_binds_exact_reviewed_bytes() -> None:
    a = authority()
    b = a["exact_execution_bindings"]
    assert b["authority_parent_head"] == REVIEW_HEAD
    assert b["candidate_baseline"] == CANDIDATE_BASELINE
    for path in (
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.15.json",
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.15.md",
        "architecture/workspace-semantic-execution-supervisor-chat.v0.1.md",
        "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh",
        "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py",
        "tests/test_workspace_semantic_execution_stage12_real_instant.py",
        "tests/test_workspace_semantic_execution_stage12_v114.py",
        "operator-bridge/tools/workspace-operator-dev.ps1",
        "operator-bridge/tools/run-stage12-wop.ps1",
        "operator-bridge/tools/run-stage12-remote-bootstrap.sh",
    ):
        assert git(f"{REVIEW_HEAD}:{path}") == b[path]
    assert git(f"{REVIEW_HEAD}:operator-bridge/src") == b["operator-bridge/src_tree"]


def test_v115_authority_requires_true_hidden_continuity_before_q2() -> None:
    a = authority()
    c = a["attempt_contract"]
    assert c["q2_token_hidden_marker"] == "STAGE12_Q2_CONTINUITY_TOKEN_HIDDEN=PASS"
    assert c["q2_fail_closed_error"] == "q2_continuity_token_disclosed_in_worker_packet"
    assert c["required_post_consumption_order"].index(
        "STAGE12_Q2_CONTINUITY_TOKEN_HIDDEN=PASS"
    ) < c["required_post_consumption_order"].index("STAGE12_Q2_REUSE_READY")
    assert a["launch_contract"]["q2_compiled_packet_token_absence_required"] is True
    assert a["launch_contract"]["q2_hidden_marker_required_before_q2_ready"] is True


def test_v115_preserves_a7_and_workspace_shell_authority_boundary() -> None:
    a = authority()
    f = a["accepted_frontend"]
    assert f["checkpoint"] == "a9532ca8b86b7839822939a970e16af1d4a41864"
    assert f["literal_github_prefix"] == "@github"
    assert f["autocomplete_selection_required"] is False
    assert f["tab_required"] is False
    assert f["click_required"] is False
    w = a["plugin_contract"]["workspace_shell"]
    assert w["literal"] == "@Workspace Shell"
    assert w["live_proven"] is False
    assert w["used_by_this_d4_authority"] is False
    assert w["authority_widened_by_this_artifact"] is False
    p = a["retained_prohibitions"]
    assert p["workspace_shell_authority_widening"] is False
    assert p["workspace_shell_live_execution_under_this_authority"] is False


def test_v115_execution_tip_must_be_green_and_frozen() -> None:
    a = authority()
    assert a["execution_start"]["exact_command"] == "wop d4"
    assert a["execution_tip_contract"]["no_branch_mutation_after_final_validation_before_wop"] is True
    assert a["approval_basis"]["frozen_review_validation"] == {
        "workspace_control_run": 3159,
        "semantic_execution_run": 461,
        "operator_bridge_run": 732,
        "result": "SUCCESS",
    }
