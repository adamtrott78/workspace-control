from __future__ import annotations

import unittest
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-research-iterate-e1-review.v0.1.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-research-iterate-e1-procedure.v0.1.md"
IMPLEMENTATION_HEAD = "aaa64ec83165f8761e6511ff4a766cd3c88e32ec"

def git(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

def review() -> dict:
    return json.loads(REVIEW.read_text(encoding="utf-8"))

def test_e1_review_is_non_authority_and_exact_green_implementation() -> None:
    r = review()
    assert r["status"] == "VALIDATED_IMPLEMENTATION_REVIEW_CANDIDATE_NOT_AUTHORITY"
    assert r["implementation"]["head"] == IMPLEMENTATION_HEAD
    assert r["implementation"]["validation"] == {
        "workspace_control_run": 3168,
        "semantic_execution_run": 470,
        "operator_bridge_run": 741,
        "result": "SUCCESS",
    }
    assert r["authority_gate"]["live_attempt_authorized"] is False
    assert r["authority_gate"]["fresh_one_shot_authority_required"] is True

def test_e1_review_binds_exact_implementation_bytes() -> None:
    r = review()
    for path, blob in r["implementation"]["exact_bindings"].items():
        assert git(f"{IMPLEMENTATION_HEAD}:{path}") == blob
    assert r["implementation"]["candidate_baseline"] == "8aacc7eebbbafabcb20b372aa53b88350a44e633"

def test_e1_review_workspace_shell_is_read_only_and_hidden_expected_values() -> None:
    w = review()["workspace_shell_probe"]
    assert w["literal_prefixes"] == ["@Workspace Shell", "@github"]
    assert w["allowed_tool"] == "workspace_shell_inspect"
    assert w["exact_args"]["operation"] == "runtime_inventory"
    assert "workspace_shell_exec" in w["prohibited_tools"]
    assert "workspace_shell_run_reviewed_helper" in w["prohibited_tools"]
    assert w["expected_values_disclosed_in_worker_packet"] is False
    assert w["authority_widening"] is False

def test_e1_review_supervisor_is_durable_projection_only() -> None:
    s = review()["supervisor_s1"]
    assert s["read_only"] is True
    assert s["fresh_store_rehydration_required"] is True
    assert s["conversation_memory_authoritative"] is False
    assert s["authority_mutations_allowed"] == 0

def test_e1_procedure_preserves_manual_loop_and_no_silent_retry() -> None:
    text = PROCEDURE.read_text(encoding="utf-8")
    assert "Ctrl+Space -> Ctrl+V -> Enter" in text
    assert "@Workspace Shell" in text
    assert "workspace_shell_inspect" in text
    assert "No silent retry" in text


class DiscoveryTests_tests_test_workspace_semantic_execution_research_iterate_e1_review_py(unittest.TestCase):
    def test_e1_review_is_non_authority_and_exact_green_implementation(self) -> None:
        globals()[\"test_e1_review_is_non_authority_and_exact_green_implementation\"]()\n\n    def test_e1_review_binds_exact_implementation_bytes(self) -> None:
        globals()[\"test_e1_review_binds_exact_implementation_bytes\"]()\n\n    def test_e1_review_workspace_shell_is_read_only_and_hidden_expected_values(self) -> None:
        globals()[\"test_e1_review_workspace_shell_is_read_only_and_hidden_expected_values\"]()\n\n    def test_e1_review_supervisor_is_durable_projection_only(self) -> None:
        globals()[\"test_e1_review_supervisor_is_durable_projection_only\"]()\n\n    def test_e1_procedure_preserves_manual_loop_and_no_silent_retry(self) -> None:
        globals()[\"test_e1_procedure_preserves_manual_loop_and_no_silent_retry\"]()\n\n