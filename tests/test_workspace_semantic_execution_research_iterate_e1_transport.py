import unittest
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e1_v1.sh"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e1-remote-bootstrap.sh"
WOP = ROOT / "operator-bridge/tools/run-research-iterate-e1-wop.ps1"
INSTALL = ROOT / "operator-bridge/tools/install-wop-commands.ps1"


def test_e1_linux_binds_candidate_harness_fixture_and_consumption() -> None:
    text = LINUX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="5bcd6df3aac855a181c02effa2189b3b5706a1c7"' in text
    assert 'HARNESS_REL="benchmarks/workspace-semantic-execution/live_research_iterate_e1.py"' in text
    assert 'FIXTURE_REL="benchmarks/workspace-semantic-execution/backend/research-engine-1031861/orchestration.py"' in text
    assert "E1_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text
    assert "PRIVATE_ROUTE_RESEARCH_ITERATE_E1_V1=PASS" in text
    assert "\\nFIXTURE_REL=" not in text
    assert '$HARNESS_REL"\\nmkdir' not in text
    assert "E1_RESEARCH_ENGINE_FIXTURE_MISSING" in text


def test_e1_remote_bootstrap_binds_only_exact_e1_linux_path() -> None:
    text = BOOT.read_text(encoding="utf-8")
    assert "private_route_research_iterate_e1_v1.sh" in text
    assert "E1_WOP_REMOTE_EXACT_BINDINGS=PASS" in text
    assert "E1_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS" in text


def test_e1_windows_launcher_preserves_a7_and_clean_teardown() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "51480cc44f62d661421e975e67af127ecd0b0417" in text
    assert "ac035d2fc898274c32cad43954ce44c15b198207" in text
    assert "E1_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS" in text
    assert "E1_EXPECTED_POSTSUCCESS_ROUTE_TEARDOWN=PASS" in text
    assert "E1_WOP_REMOTE_WORKFLOW=PASS" in text


def test_wop_installer_exposes_e1_without_removing_d4() -> None:
    text = INSTALL.read_text(encoding="utf-8")
    assert '"d4","e1"' in text
    assert '"wop-d4"' in text
    assert '"wop-e1"' in text
    assert '"wop-e1" = "e1"' in text
    assert "run-research-iterate-e1-wop.ps1" in text


def test_e1_shell_scripts_parse() -> None:
    bash = shutil.which("bash")
    if bash is not None:
        for path in (LINUX, BOOT):
            proc = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
            assert proc.returncode == 0, proc.stderr


class DiscoveryTests_tests_test_workspace_semantic_execution_research_iterate_e1_transport_py(unittest.TestCase):
    def test_e1_linux_binds_candidate_harness_fixture_and_consumption(self) -> None:
        globals()["test_e1_linux_binds_candidate_harness_fixture_and_consumption"]()

    def test_e1_remote_bootstrap_binds_only_exact_e1_linux_path(self) -> None:
        globals()["test_e1_remote_bootstrap_binds_only_exact_e1_linux_path"]()

    def test_e1_windows_launcher_preserves_a7_and_clean_teardown(self) -> None:
        globals()["test_e1_windows_launcher_preserves_a7_and_clean_teardown"]()

    def test_wop_installer_exposes_e1_without_removing_d4(self) -> None:
        globals()["test_wop_installer_exposes_e1_without_removing_d4"]()

    def test_e1_shell_scripts_parse(self) -> None:
        globals()["test_e1_shell_scripts_parse"]()


def test_e1_private_route_candidate_baseline_matches_current_retry_chain() -> None:
    text = E1_LINUX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="5bcd6df3aac855a181c02effa2189b3b5706a1c7"' in text
    assert '8aacc7eebbbafabcb20b372aa53b88350a44e633' not in text


def test_e1_runtime_archives_repaired_semantic_execution() -> None:
    text = LINUX.read_text(encoding="utf-8")
    assert 'SEMANTIC_SHA="2e2d6ec5bcd4ba7476baafa30780f05695043bf9"' in text
    assert 'EXPECTED_PACKET_COMPILER_BLOB="cf6200aa4b5a669dd023bc3c6478770bf4658528"' in text
    assert "LIVE_SEMANTIC_PACKET_COMPILER_BLOB_MISMATCH" in text
    assert 'git -C "$ROOT" archive "$SEMANTIC_SHA" semantic-execution' in text
