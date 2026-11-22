import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / "scripts/mth602_activate_laneb_refresh_v8.py").read_text()


def test_operator_launcher_compiles():
    compile(SRC, "mth602_activate_laneb_refresh_v8.py", "exec")


def test_operator_launcher_is_exact_and_fail_closed():
    for marker in (
        'EXPECTED_PAD_MAIN = "51073327c688d243961a0caabbb5358cc065ced1"',
        'EXPECTED_WORKFLOW_BLOB = "8375dd0a0733b01de38f677dee58a373d3adcb48"',
        'for status in ("queued", "in_progress")',
        'if count != 0:',
        'helper.require_target_quiescent()',
        '"PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_PREFLIGHT"',
        '"REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V8"',
        'timedelta(minutes=10)',
        'lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v8.py',
        'MTH602_LANEB_REFRESH_V8_POSTVERIFY=PASS',
    ):
        assert marker in SRC


def test_operator_launcher_requires_user_phase_before_sudo():
    assert 'if os.geteuid() == 0:' in SRC
    assert 'raise RuntimeError("launch user phase without sudo")' in SRC
    assert 'run(["sudo", "-v"])' in SRC
