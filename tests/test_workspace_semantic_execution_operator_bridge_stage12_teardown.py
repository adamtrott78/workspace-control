import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WOP = ROOT / "operator-bridge/tools/run-stage12-wop.ps1"

def test_d4_route_teardown_grace_accepts_only_clean_remote_exit() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "D4_EXPECTED_POSTSUCCESS_ROUTE_TEARDOWN=PASS" in text
    assert "$teardownDeadline = (Get-Date).AddSeconds(10)" in text
    assert "if ($sshProcess.ExitCode -eq 0)" in text
    assert "D4_WOP_REMOTE_EXIT_AFTER_ROUTE_LOSS" in text
    assert "D4_OPERATOR_BACKEND_ROUTE_LOST:" in text


class DiscoveryTests_tests_test_workspace_semantic_execution_operator_bridge_stage12_teardown_py(unittest.TestCase):
    def test_d4_route_teardown_grace_accepts_only_clean_remote_exit(self) -> None:
        globals()["test_d4_route_teardown_grace_accepts_only_clean_remote_exit"]()
