import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = (ROOT / "scripts/mth602_t007_fullmatrix_local_dashboard.py").read_text()


def test_dashboard_compiles_and_osr_overlay_is_local_only():
    compile(DASH, "mth602_t007_fullmatrix_local_dashboard.py", "exec")
    for marker in (
        'OSR_OVERLAY = "PADataset PR54 58538b45"',
        '("PA1<-PA2", 14765881457)',
        '("PA8<-PA2", 14719755202)',
        'def osr_process_rows():',
        'def scan_osr_results():',
        'scientific-results/l2o_eval/result_record.json',
        'artifact_id != int(expected[direction])',
        'DUAL-GPU T007 OSR',
        '18 directions',
        'OSR is post-freeze diagnostic only',
    ):
        assert marker in DASH
    assert "gh api" not in DASH
    assert "api.github.com" not in DASH
    assert "requests.get(" not in DASH
