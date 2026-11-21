from pathlib import Path


def test_mth602_dual_gpu_osr_dashboard_compiles():
    path = Path("scripts/mth602_h1_dual_gpu_osr_dashboard.py")
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "MTH602 H1 — DUAL-GPU FROZEN-PAIR DQNGUARD OSR DASHBOARD" in source
    assert "GitHub API calls: 0" in source
    assert 'user=="ci-padataset"' in source
    assert 'user=="ci-padataset-2"' in source
