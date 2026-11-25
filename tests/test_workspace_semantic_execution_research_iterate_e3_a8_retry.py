from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a8-live-review.v0.1.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a8-live-procedure.v0.1.md"
WRAPPER = ROOT / "benchmarks/workspace-semantic-execution/live_research_iterate_e3_a8_v1.py"
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a8_v1.sh"
WOP = ROOT / "operator-bridge/tools/run-research-iterate-e3-a8-wop.ps1"
BOOT = ROOT / "operator-bridge/tools/run-research-iterate-e3-a8-remote-bootstrap.sh"


def test_e3_a8_retry_review_binds_validated_repair_and_current_candidate() -> None:
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    assert r["status"]=="FROZEN_EXECUTABLE_REVIEW_ZERO_AUTHORITY"
    assert r["candidate_baseline"]=="fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
    assert r["bindings"]["a8_frontend_review_head"]=="6fb315884804214f96ca0f7264a48eed40741a60"
    assert r["bindings"]["a8_frontend_source_head"]=="b97a4c7b9309d413ced7eea14fe87b5864ad0c5b"
    assert r["bindings"]["operator_transport_head"]=="55edb7a6e618f5a49ddf17ec5c9426f70fa08f2d"
    assert r["bindings"]["e3_a8_wrapper"]["blob"]=="4615149b8ed20d327a8ceaf8dfd6605524f858da"
    assert r["bindings"]["linux_transaction"]["blob"]=="3a186e7ec8f4cc8ec0ab14e7e8fc408c6619be12"


def test_e3_a8_retry_review_grants_zero_authority() -> None:
    r=json.loads(REVIEW.read_text(encoding="utf-8"))
    gate=r["authority_gate"]
    assert gate["live_authority_exists"] is False
    assert gate["live_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["fresh_explicit_operator_approval_required"] is True
    assert gate["prior_authority_reusable"] is False
    text=PROCEDURE.read_text(encoding="utf-8")
    assert "Live attempts authorized by this review alone: 0" in text


def test_e3_a8_linux_requires_future_authority_before_consumption() -> None:
    text=LINUX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"' in text
    assert 'AUTHORITY_REL="architecture/workspace-semantic-execution-research-iterate-e3-a8-live-authority.v0.1.json"' in text
    assert "E3_A8_AUTHORITY_BINDING=PASS" in text
    assert "E3_A8_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS" in text
    assert text.index("E3_A8_AUTHORITY_BINDING=PASS") < text.index("E3_A8_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS")
    assert "merge-base --is-ancestor" in text


def test_e3_a8_wrapper_and_transport_are_versioned_and_manual() -> None:
    assert 'CANDIDATE_BASELINE = "fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"' in WRAPPER.read_text(encoding="utf-8")
    wop=WOP.read_text(encoding="utf-8")
    boot=BOOT.read_text(encoding="utf-8")
    assert "Ctrl+Space -> Ctrl+V -> Enter" in wop
    assert "private_route_research_iterate_e3_a8_v1.sh" in wop
    assert "private_route_research_iterate_e3_a8_v1.sh" in boot
    assert "SendKeys" not in wop


def test_e3_a8_linux_is_bash_syntax_valid() -> None:
    bash=shutil.which("bash")
    if bash is not None:
        proc=subprocess.run([bash,"-n",str(LINUX)],capture_output=True,text=True)
        assert proc.returncode==0,proc.stderr
