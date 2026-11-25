from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a9-live-authority.v0.1.json"
ROUTE = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a9_v1.sh"
LAUNCHER = ROOT / "operator-bridge/tools/run-research-iterate-e3-a9-wop.ps1"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e3-a9-remote-bootstrap.sh"


def test_e3_a9_authority_is_fresh_one_shot_and_exactly_bound() -> None:
    a = json.loads(AUTH.read_text(encoding="utf-8"))
    assert a["schema_version"] == 1
    assert a["artifact_id"] == "workspace-semantic-execution-research-iterate-e3-a9-live-authority-v0.1"
    assert a["status"] == "PENDING_OPERATOR_WOP_EXECUTION"
    assert a["approval_basis"]["original_scope"] == "EXACTLY_ONE_E3_A9_LIVE_ATTEMPT"
    assert a["approval_basis"]["attempts_granted"] == 1
    assert a["approval_basis"]["consumed_predecessor_authority_reused"] is False
    b = a["execution_bindings"]
    assert b["candidate_baseline"] == "968db0800e9dcdee6e5a784889d74653276fb184"
    assert b["e3_a9_wrapper_blob"] == "89f14c3e89c0773d78c2472f76db00a5b6f3edaa"
    assert b["e2_harness_blob"] == "d6acd6a4266641813deecb900b877b7250b02530"
    assert b["observer_blob"] == "458a869252f108bea52952e12852961bc3158d1f"
    assert b["a9_private_route_blob"] == "808864ddf50bc57aa06ec0a9b45b97819040e1f8"
    assert b["a9_remote_bootstrap_blob"] == "cc61c43878ed781816c42c8f266c812341415c91"
    assert b["a9_windows_launcher_blob"] == "151ca25e87cccb2af8658844bd3942c9ca92eb9a"
    assert b["worker_result_schema_blob"] == "b84d362a8adbb1bf4a47f1dfc4f0b8089487a3c1"
    attempt = a["attempt_contract"]
    assert attempt["attempts_authorized"] == 1
    assert attempt["consumed"] is False
    assert attempt["reusable"] is False
    assert attempt["no_silent_retry"] is True


def test_e3_a9_route_binds_current_candidate_and_diagnostic_wrapper() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="968db0800e9dcdee6e5a784889d74653276fb184"' in text
    assert 'WRAPPER_REL="benchmarks/workspace-semantic-execution/live_research_iterate_e3_a9_v1.py"' in text
    assert 'EXPECTED_WRAPPER_BLOB="89f14c3e89c0773d78c2472f76db00a5b6f3edaa"' in text
    assert 'AUTHORITY_REL="architecture/workspace-semantic-execution-research-iterate-e3-a9-live-authority.v0.1.json"' in text
    assert "E3_A9_AUTHORITY_BINDING=PASS" in text
    assert "E3_A9_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text


def test_e3_a9_operator_transport_is_versioned_and_nonautomatic() -> None:
    launcher = LAUNCHER.read_text(encoding="utf-8")
    boot = BOOT.read_text(encoding="utf-8")
    assert "private_route_research_iterate_e3_a9_v1.sh" in launcher
    assert "run-research-iterate-e3-a9-remote-bootstrap.sh" in launcher
    assert "Ctrl+Space -> Ctrl+V -> Enter" in launcher
    assert '$acceptedFrontendHead = "6fb315884804214f96ca0f7264a48eed40741a60"' in launcher
    assert "worktree add --detach $frontendRepo $acceptedFrontendHead" in launcher
    assert '-RepositoryRoot $frontendRepo' in launcher
    assert "private_route_research_iterate_e3_a9_v1.sh" in boot
    assert "workspace-e3-a9-wop-" in boot
