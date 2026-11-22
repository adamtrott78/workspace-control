from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mth602_recover_pa1_pa2_runid_local.py"


def test_recovery_script_parses_and_is_zero_provider():
    src = SCRIPT.read_text()
    ast.parse(src)
    forbidden = [
        "gh api",
        "api.github.com",
        "requests.get(",
        "urllib.request",
        "curl ",
    ]
    for token in forbidden:
        assert token not in src


def test_recovery_is_bound_to_pa1_pa2_t007():
    src = SCRIPT.read_text()
    assert 'RUN_NAME = "l2o_t007_fullmatrix_PA1_PA2"' in src
    assert 'COMMENT_ID = "7082541725"' in src
    assert "PA1_PA2_WORKFLOW_RUN_ID" in src
