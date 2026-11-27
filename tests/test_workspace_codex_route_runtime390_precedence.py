from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()


def test_runtime390_receipt_is_authoritative_for_shared_managed_artifacts():
    assert "PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH_ACTIVE_RECEIPT" in REC
    assert 'str(V3_CONFIG_ROOT / "compatibility-matrix.json")' in REC
    assert "runtime_ceiling_overrides" in REC
    assert "PADataset scientific runtime ceiling managed artifact digest drift" in REC


def test_runtime390_receipt_stays_bound_to_frozen_v3_v8_predecessors():
    block = REC[
        REC.index("def _padataset_scientific_runtime_ceiling_refresh("):
        REC.index("def _verify_padataset_scientific_effective_state(")
    ]
    assert "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT.read_bytes()" in block
    assert "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_ACTIVE_RECEIPT.read_bytes()" in block
    assert "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT" not in block
    assert "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT" not in block


def test_later_workflow_trust_remains_independent_of_runtime390_artifact_ownership():
    verify = REC[REC.index("scientific_workflow_refresh_v3 ="):]
    assert "scientific_workflow_refresh_v4 =" in verify
    assert "scientific_workflow_effective_refresh = scientific_workflow_refresh_v4" in verify
    assert "scientific_dual_workflow_refresh_v9 =" in verify
    assert "scientific_dual_effective_refresh = scientific_dual_workflow_refresh_v9" in verify
    assert "scientific_runtime_ceiling_refresh = (" in verify


def test_codex_route_composes_above_runtime390_then_dual_then_scientific():
    loop = REC[REC.index("actual_sha = _sha256(path.read_bytes())"):]
    codex = loop.index("if workspace_codex_digest is not None:")
    runtime = loop.index("elif runtime_ceiling_binding is not None:")
    dual = loop.index("elif dual_binding is not None:")
    lane_a = loop.index("elif scientific_binding is not None:")
    assert codex < runtime < dual < lane_a
    codex_block = loop[codex:runtime]
    assert "runtime_ceiling_overrides_seen.add(destination)" in codex_block


def test_codex_overlay_predecessor_is_runtime390_when_present():
    block = REC[
        REC.index("predecessor_overlay_sha256 = str(overlay_entry.get"):
        REC.index("workspace_codex_route = _workspace_control_codex_route_override(")
    ]
    dual = block.index("dual_overlay =")
    runtime = block.index("runtime_overlay =")
    assert dual < runtime
    assert 'predecessor_overlay_sha256 = runtime_overlay["sha256"]' in block


def test_runtime390_effective_root_state_is_used_for_dual_lane_verification():
    verify = REC[REC.index("scientific_runtime_ceiling_refresh = ("):]
    assert "scientific_dual_effective_state = scientific_dual_lane" in verify
    assert 'scientific_dual_effective_state["root_policy_sha256"]' in verify
    call = verify[verify.index("_verify_padataset_scientific_dual_lane_effective_state("):]
    assert "scientific_dual_effective_state," in call[:700]
