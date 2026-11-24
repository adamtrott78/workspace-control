import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e2_v1.sh"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e2-remote-bootstrap.sh"
WOP = ROOT / "operator-bridge/tools/run-research-iterate-e2-wop.ps1"
INSTALL = ROOT / "operator-bridge/tools/install-wop-commands.ps1"


def test_e2_transport_binds_live_harness_baseline_and_consumption() -> None:
    text = LINUX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="fdb801d895068c78b2e2e11e6984173812884deb"' in text
    assert 'HARNESS_REL="benchmarks/workspace-semantic-execution/live_research_iterate_e2.py"' in text
    assert 'SEMANTIC_SHA="2e2d6ec5bcd4ba7476baafa30780f05695043bf9"' in text
    assert 'EXPECTED_PACKET_COMPILER_BLOB="cf6200aa4b5a669dd023bc3c6478770bf4658528"' in text
    assert 'EXPECTED_OPERATOR_HTTP_BLOB="3b6893c157c9f567c837aa70c110012eb96ee18c"' in text
    assert "3b6893c157c9f567c837aa70c110012eb96ee28c" not in text
    assert "E2_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text
    assert "PRIVATE_ROUTE_RESEARCH_ITERATE_E2_V1=PASS" in text


def test_e2_remote_bootstrap_binds_only_e2_transport() -> None:
    text = BOOT.read_text(encoding="utf-8")
    assert "private_route_research_iterate_e2_v1.sh" in text
    assert "E2_WOP_REMOTE_EXACT_BINDINGS=PASS" in text
    assert "E2_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS" in text


def test_e2_windows_launcher_preserves_accepted_a7_frontend() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "51480cc44f62d661421e975e67af127ecd0b0417" in text
    assert "E2_FRONTEND_BASELINE_SHA=a9532ca8b86b7839822939a970e16af1d4a41864" in text
    assert "970e26af1d4a41864" not in text
    assert "ac035d2fc898274c32cad43954ce44c15b198207" in text
    assert "E2_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS" in text
    assert "E2_EXPECTED_POSTSUCCESS_ROUTE_TEARDOWN=PASS" in text
    assert "E2_WOP_REMOTE_WORKFLOW=PASS" in text


def test_wop_installer_exposes_e2_without_removing_prior_commands() -> None:
    text = INSTALL.read_text(encoding="utf-8")
    assert '"e1","e2"' in text
    assert '"wop-d4"' in text
    assert '"wop-e1"' in text
    assert '"wop-e2"' in text
    assert '"wop-e2" = "e2"' in text
    assert "run-research-iterate-e2-wop.ps1" in text


def test_e2_shell_scripts_parse() -> None:
    bash = shutil.which("bash")
    if bash is not None:
        for path in (LINUX, BOOT):
            proc = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
            assert proc.returncode == 0, proc.stderr
