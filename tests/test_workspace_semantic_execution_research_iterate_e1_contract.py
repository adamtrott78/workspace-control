import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "architecture/workspace-semantic-execution-research-iterate-e1.v0.1.md"

def test_e1_topology_is_mixed_and_fanin() -> None:
    text = DOC.read_text(encoding="utf-8")
    for needle in ("Root decomposer", "Exact-source leaf", "Analysis leaf", "Workspace Shell probe", "Fan-in", "Synthesis"):
        assert needle in text

def test_e1_workspace_shell_probe_is_literal_read_only() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "@Workspace Shell" in text
    assert "@github" in text
    assert 'operation="runtime_inventory"' in text
    assert "workspace_shell_exec" in text
    assert "workspace_shell_run_reviewed_helper" in text
    assert "prohibited" in text
    assert "expected runtime-inventory digest is validator-side evidence" in text

def test_e1_supervisor_is_projection_only() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "projection-only" in text
    assert "Conversation memory is a cache only" in text
    assert "zero authority/task mutations" in text

def test_e1_keeps_recovery_and_soak_separate() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "E2 is deliberate worker/session/process loss" in text
    assert "E3 is resource accounting and soak" in text


class DiscoveryTests_tests_test_workspace_semantic_execution_research_iterate_e1_contract_py(unittest.TestCase):
    def test_e1_topology_is_mixed_and_fanin(self) -> None:
        globals()["test_e1_topology_is_mixed_and_fanin"]()

    def test_e1_workspace_shell_probe_is_literal_read_only(self) -> None:
        globals()["test_e1_workspace_shell_probe_is_literal_read_only"]()

    def test_e1_supervisor_is_projection_only(self) -> None:
        globals()["test_e1_supervisor_is_projection_only"]()

    def test_e1_keeps_recovery_and_soak_separate(self) -> None:
        globals()["test_e1_keeps_recovery_and_soak_separate"]()
