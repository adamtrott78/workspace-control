from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WOP = ROOT / "operator-bridge/tools/run-research-iterate-e3-a8-wop.ps1"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e3-a8-remote-bootstrap.sh"


def test_e3_a8_launcher_binds_validated_successor_without_mutating_a7() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "f3fd3b2c65b5780b511af9a90477d3a6bbfee873" in text
    assert "6fb315884804214f96ca0f7264a48eed40741a60" in text
    assert "b97a4c7b9309d413ced7eea14fe87b5864ad0c5b" in text
    assert "ac035d2fc898274c32cad43954ce44c15b198207" in text
    assert "private_route_research_iterate_e3_a8_v1.sh" in text
    assert "run-research-iterate-e3-a8-remote-bootstrap.sh" in text


def test_e3_a8_launcher_preserves_manual_input_boundary() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "Ctrl+Space -> Ctrl+V -> Enter" in text
    assert "SendKeys" not in text
    assert "E3_A8_ACCEPTED_FRONTEND_READY=PASS" in text
    assert "E3_A8_WOP_WINDOWS_CLEANUP=PASS" in text


def test_e3_a8_remote_bootstrap_is_exact_and_noninteractive() -> None:
    text = BOOT.read_text(encoding="utf-8")
    assert "private_route_research_iterate_e3_a8_v1.sh" in text
    assert "E3_A8_WOP_REMOTE_EXACT_BINDINGS=PASS" in text
    assert 'E3_A8_WINDOWS_READY_CONFIRMATION="E3_A8_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"' in text
    bash = shutil.which("bash")
    if bash is not None:
        proc = subprocess.run([bash, "-n", str(BOOT)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
