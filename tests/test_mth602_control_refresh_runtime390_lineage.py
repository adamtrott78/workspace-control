from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
A4 = (ROOT / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v4.py").read_text()
B9 = (ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py").read_text()


def test_runtime390_override_remains_authoritative_for_shared_managed_artifacts():
    assert "PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH_ACTIVE_RECEIPT" in REC
    assert 'str(V3_CONFIG_ROOT / "compatibility-matrix.json")' in REC
    loop = REC[REC.index("actual_sha = _sha256(path.read_bytes())"):]
    runtime = loop.index("if runtime_ceiling_binding is not None:")
    dual = loop.index("elif dual_binding is not None:")
    lane_a = loop.index("elif scientific_binding is not None:")
    assert runtime < dual < lane_a
    assert "PADataset scientific runtime ceiling managed artifact digest drift" in loop


def test_runtime390_receipt_stays_bound_to_live_v3_v8_predecessors():
    block = REC[
        REC.index("def _padataset_scientific_runtime_ceiling_refresh("):
        REC.index("def _verify_padataset_scientific_effective_state(")
    ]
    assert "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT.read_bytes()" in block
    assert "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_ACTIVE_RECEIPT.read_bytes()" in block
    assert "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT" not in block
    assert "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT" not in block


def test_workflow_trust_can_advance_after_runtime390_without_rebinding_runtime_receipt():
    verify = REC[REC.index("scientific_workflow_refresh_v3 ="):]
    assert "scientific_workflow_refresh_v4 =" in verify
    assert "scientific_workflow_effective_refresh = scientific_workflow_refresh_v4" in verify
    assert "scientific_dual_workflow_refresh_v9 =" in verify
    assert "scientific_dual_effective_refresh = scientific_dual_workflow_refresh_v9" in verify
    assert "scientific_runtime_ceiling_refresh = (" in verify


def test_v4_v9_helpers_verify_runtime390_aware_candidate_before_any_stop():
    for source in (A4, B9):
        verify = source.index("candidate.verify_installed(BASE_MANIFEST)")
        stop = source.index('base.run_systemctl("stop", TARGET_UNIT)')
        assert verify < stop
