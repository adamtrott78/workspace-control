from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.14.json"
FROZEN_HANDOFF_HEAD = "992542dbdfabb70c25d00704f97db634a781dd01"
Q1_BASELINE = "daa18627982a1d406eb88d44145113f0e99561e0"


def git(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()


def authority() -> dict:
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def test_v114_authority_is_exactly_one_pending_attempt_after_cleanup() -> None:
    a = authority()
    assert a["status"] == "PENDING_OPERATOR_WOP_EXECUTION"
    assert a["approval_basis"]["approved_scope"] == "EXACTLY_ONE_V1_14_D4_ATTEMPT"
    assert a["approval_basis"]["frozen_handoff_head"] == FROZEN_HANDOFF_HEAD
    assert a["attempt_contract"]["attempts_authorized"] == 1
    assert a["attempt_contract"]["consumed"] is False
    assert a["attempt_contract"]["reusable"] is True
    assert a["attempt_contract"]["no_silent_retry"] is True
    p = a["predecessor"]
    assert p["consumed"] is True
    assert p["reusable"] is False
    assert p["windows_cleaned"] is True
    assert p["cleanup_evidence"]["wop_down"] == "WORKSPACE_OPERATOR_DEV_OFFLINE=PASS"
    assert p["cleanup_evidence"]["wop_status"] == "WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE"


def test_v114_authority_binds_exact_repair_and_successful_q1_baseline() -> None:
    a = authority()
    b = a["exact_execution_bindings"]
    source = b["authority_parent_head"]
    assert source == FROZEN_HANDOFF_HEAD
    assert b["candidate_baseline"] == Q1_BASELINE
    for path in (
        "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh",
        "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py",
        "tests/test_workspace_semantic_execution_stage12_v114.py",
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.14.json",
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.14.md",
        "operator-bridge/tools/workspace-operator-dev.ps1",
        "operator-bridge/tools/run-stage12-wop.ps1",
        "operator-bridge/tools/run-stage12-remote-bootstrap.sh",
    ):
        assert git(f"{source}:{path}") == b[path]
    assert git(f"{source}:operator-bridge/src") == b["operator-bridge/src_tree"]
    assert git(
        f"{b['live_semantic_sha']}:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"
    ) == b["live_operator_http_blob"]


def test_v114_authority_preserves_a6_a7_and_observability_contract() -> None:
    a = authority()
    f = a["accepted_frontend"]
    assert f["checkpoint"] == "a9532ca8b86b7839822939a970e16af1d4a41864"
    assert f["exact_src_tree"] == "51480cc44f62d661421e975e67af127ecd0b0417"
    assert f["literal_plugin_prefix"] == "@github"
    assert f["autocomplete_selection_required"] is False
    assert f["tab_required"] is False
    assert f["click_required"] is False
    assert a["launch_contract"]["q1_packet_must_already_include_literal_github"] is True
    assert a["launch_contract"]["manual_packet_editing_allowed"] is False
    assert a["attempt_contract"]["q1_post_consumption_required_order"] == [
        "STAGE12_Q1_CANDIDATE_OBSERVED=<sha>",
        "STAGE12_Q1_DURABLE_INGEST=PASS",
        "STAGE12_Q1_REAL_INSTANT=PASS",
        "STAGE12_Q2_REUSE_READY",
    ]


def test_v114_authority_preserves_route_and_security_fail_closed_boundaries() -> None:
    a = authority()
    r = a["stale_route_normalization_contract"]
    assert r["remove_only_if_no_listener"] is True
    assert r["arbitrary_handler_drift_allowed"] is False
    assert r["funnel_allowed"] is False
    assert r["post_normalization_clean_root_snapshot_required"] is True
    assert a["attempt_contract"]["required_marker_order"] == [
        "STAGE12_CANDIDATE_BASELINE=PASS",
        "TAILSCALE_STAGE12_ROUTE_ABSENT=PASS",
        "STAGE12_SEMANTIC_LIVE_BINDING=PASS",
        "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
    ]
    p = a["retained_prohibitions"]
    assert p["automatic_typing"] is False
    assert p["automatic_paste"] is False
    assert p["automatic_submission"] is False
    assert p["mouse_automation"] is False
    assert p["dom_or_page_content_scraping"] is False
    assert p["candidate_history_rewrite"] is False
