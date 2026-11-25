from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AUTH_REL = "architecture/workspace-semantic-execution-research-iterate-e3-a10-live-authority.v0.1.json"
AUTH = ROOT / AUTH_REL
MANIFEST_REL = "architecture/workspace-semantic-execution-e3-live-binding-manifest.v0.1.json"
CLOSURE = ROOT / "benchmarks/workspace-semantic-execution/e3_live_binding_closure_v1.py"
ROUTE = "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a10_v1.sh"
BOOT = "operator-bridge/tools/run-research-iterate-e3-a10-remote-bootstrap.sh"
LAUNCHER = "operator-bridge/tools/run-research-iterate-e3-a10-wop.ps1"
A9_CLOSEOUT = ROOT / "architecture/workspace-semantic-execution-research-iterate-e3-a9-live-closeout.v0.1.json"
AUTH_ID = "workspace-semantic-execution-research-iterate-e3-a10-live-authority-v0.1"


def _load_closure():
    spec = importlib.util.spec_from_file_location("e3_a10_authority_closure", CLOSURE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _blob(path: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return cp.stdout.strip()


def test_e3_a10_authority_is_fresh_one_shot_after_green_zero_authority_review() -> None:
    a = json.loads(AUTH.read_text(encoding="utf-8"))
    assert a["schema_version"] == 1
    assert a["artifact_id"] == AUTH_ID
    assert a["status"] == "PENDING_OPERATOR_WOP_EXECUTION"
    approval = a["approval_basis"]
    assert approval["original_statement"] == "DO IT"
    assert approval["original_scope"] == "EXACTLY_ONE_E3_A10_LIVE_ATTEMPT_AFTER_BINDING_CLOSURE_VALIDATION"
    assert approval["attempts_granted"] == 1
    assert approval["standing_or_future_authority_inferred"] is False

    review = a["reviewed_source"]
    assert review["zero_authority_review_head"] == "fbca3389192cb14ce241c4f097b9c13e5ac84e15"
    assert review["review_head"] == "fbca3389192cb14ce241c4f097b9c13e5ac84e15"
    assert review["validation"] == {
        "workspace_control_run": 3253,
        "semantic_execution_run": 552,
        "operator_bridge_run": 821,
        "result": "SUCCESS",
    }

    attempt = a["attempt_contract"]
    assert attempt["attempts_authorized"] == 1
    assert attempt["consumed"] is False
    assert attempt["reusable"] is False
    assert attempt["no_silent_retry"] is True
    assert attempt["live_consumption_marker"] == "E3_A10_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"


def test_e3_a10_authority_closes_manifest_and_transport_blobs() -> None:
    closure = _load_closure()
    result = closure.validate_closure(
        repo_root=ROOT,
        authority_rel=AUTH_REL,
        manifest_rel=MANIFEST_REL,
        expected_authority_id=AUTH_ID,
    )
    a = result["authority"]["authority"]
    bindings = a["execution_bindings"]
    assert bindings["binding_manifest_blob"] == _blob(MANIFEST_REL)
    assert bindings["a10_private_route_blob"] == _blob(ROUTE)
    assert bindings["a10_remote_bootstrap_blob"] == _blob(BOOT)
    assert bindings["a10_windows_launcher_blob"] == _blob(LAUNCHER)


def test_e3_a9_is_durably_closed_and_cannot_be_reused() -> None:
    a10 = json.loads(AUTH.read_text(encoding="utf-8"))
    closeout = json.loads(A9_CLOSEOUT.read_text(encoding="utf-8"))
    predecessor = a10["predecessor_state"]

    assert closeout["status"] == "CONSUMED_FAILED"
    assert closeout["consumption"]["observed"] is True
    assert closeout["consumption"]["reusable"] is False
    assert closeout["failure"]["exception"] == "E3LiveError:candidate_baseline_mismatch"
    assert predecessor["e3_a9_authority_consumed"] is True
    assert predecessor["e3_a9_authority_reusable"] is False
    assert predecessor["e3_a9_reuse_forbidden"] is True
    assert predecessor["e3_a9_closeout_blob"] == _blob(
        "architecture/workspace-semantic-execution-research-iterate-e3-a9-live-closeout.v0.1.json"
    )


def test_e3_a10_consumption_contract_requires_binding_closed_preflight() -> None:
    a = json.loads(AUTH.read_text(encoding="utf-8"))
    guards = a["preconsumption_guards"]
    required_true = (
        "canonical_binding_manifest_required",
        "cross_artifact_binding_closure_required",
        "live_candidate_branch_head_must_equal_manifest",
        "frontend_bindings_must_come_from_manifest",
        "frontend_self_test_must_pass_before_remote_start",
        "semantic_source_blob_checks_must_pass",
        "pinned_dependency_setup_must_pass",
        "postgresql_setup_must_pass",
        "tailscale_private_route_verification_must_pass",
        "wrapper_preflight_only_must_pass",
        "consumption_marker_after_all_above",
        "duplicated_candidate_baseline_constant_forbidden",
        "consumed_a9_authority_reuse_forbidden",
    )
    for key in required_true:
        assert guards[key] is True
