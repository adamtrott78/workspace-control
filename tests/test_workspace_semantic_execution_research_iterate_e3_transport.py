"""Static E3-LIVE authority/transport acceptance checks."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "architecture"
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_v1.sh"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e3-remote-bootstrap.sh"
WOP = ROOT / "operator-bridge/tools/run-research-iterate-e3-wop.ps1"
INSTALL = ROOT / "operator-bridge/tools/install-wop-commands.ps1"
AUTH = ARCH / "workspace-semantic-execution-research-iterate-e3-live-authority.v0.1.json"


def test_e3_authority_is_one_shot_and_exactly_bound() -> None:
    authority = json.loads(AUTH.read_text(encoding="utf-8"))
    assert authority["status"] == "PENDING_OPERATOR_WOP_EXECUTION"
    assert authority["approval_basis"]["original_statement"] == "GOOOO"
    assert authority["approval_basis"]["original_scope"] == "EXACTLY_ONE_LIVE_E3_RESOURCE_SOAK_ATTEMPT"
    assert authority["attempt_contract"]["attempts_authorized"] == 1
    assert authority["attempt_contract"]["consumed"] is False
    assert authority["attempt_contract"]["reusable"] is False
    assert authority["attempt_contract"]["no_silent_retry"] is True
    assert authority["reviewed_source"]["review_head"] == "6b1f0e9354ce4a7a266d8dbdbdcb285057f2a424"
    assert authority["execution_bindings"]["candidate_baseline"] == "6115b48dfdf4a4954b3b1626598f897e4e71eeec"
    assert authority["execution_bindings"]["e3_wrapper_blob"] == "51e471886a4911c9f00d824316c600bf8f8fae19"
    assert authority["execution_bindings"]["e2_harness_blob"] == "d6acd6a4266641813deecb900b877b7250b02530"
    assert authority["execution_bindings"]["observer_blob"] == "458a869252f108bea52952e12852961bc3158d1f"


def test_e3_linux_transport_binds_frozen_review_and_consumption_point() -> None:
    text = LINUX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="6115b48dfdf4a4954b3b1626598f897e4e71eeec"' in text
    assert 'SOURCE_HEAD="e14e71d1981a4aedbe9af75a54087683fe4718e1"' in text
    assert 'REVIEW_HEAD="6b1f0e9354ce4a7a266d8dbdbdcb285057f2a424"' in text
    assert 'EXPECTED_WRAPPER_BLOB="51e471886a4911c9f00d824316c600bf8f8fae19"' in text
    assert 'EXPECTED_E2_HARNESS_BLOB="d6acd6a4266641813deecb900b877b7250b02530"' in text
    assert 'EXPECTED_OBSERVER_BLOB="458a869252f108bea52952e12852961bc3158d1f"' in text
    assert 'SEMANTIC_SHA="2e2d6ec5bcd4ba7476baafa30780f05695043bf9"' in text
    assert "E3_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text
    assert "PRIVATE_ROUTE_RESEARCH_ITERATE_E3_V1=PASS" in text
    assert "--sample-interval-seconds 1.0" in text


def test_e3_windows_transport_preserves_accepted_a7_frontend() -> None:
    text = WOP.read_text(encoding="utf-8")
    assert "51480cc44f62d661421e975e67af127ecd0b0417" in text
    assert "a9532ca8b86b7839822939a970e16af1d4a41864" in text
    assert "ac035d2fc898274c32cad43954ce44c15b198207" in text
    assert "run-research-iterate-e3-remote-bootstrap.sh" in text
    assert "private_route_research_iterate_e3_v1.sh" in text
    assert "E3_ACCEPTED_FRONTEND_READY=PASS" in text
    assert "Ctrl+Space -> Ctrl+V -> Enter" in text


def test_e3_remote_bootstrap_and_installer_are_narrow() -> None:
    boot = BOOT.read_text(encoding="utf-8")
    install = INSTALL.read_text(encoding="utf-8")
    assert "private_route_research_iterate_e3_v1.sh" in boot
    assert "E3_WOP_REMOTE_EXACT_BINDINGS=PASS" in boot
    assert 'export E3_WINDOWS_READY_CONFIRMATION="E3_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"' in boot
    assert '"wop-e3"' in install
    assert '"wop-e3" = "e3"' in install
    assert "run-research-iterate-e3-wop.ps1" in install
    assert '"e2","e3"' in install


def test_e3_shell_scripts_parse() -> None:
    bash = shutil.which("bash")
    if bash is not None:
        for path in (LINUX, BOOT):
            proc = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
            assert proc.returncode == 0, proc.stderr
