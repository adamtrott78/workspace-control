from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mth602_recover_pa1_pa2_runid_local_v2.py"

def test_v2_parses_and_is_zero_provider():
    src = SCRIPT.read_text()
    ast.parse(src)
    for token in ["gh api", "api.github.com", "requests.get(", "urllib.request", "curl "]:
        assert token not in src

def test_v2_is_exactly_bound_to_recovered_job_uuid():
    src = SCRIPT.read_text()
    assert 'RUN_NAME = "l2o_t007_fullmatrix_PA1_PA2"' in src
    assert 'COMMENT_ID = "7082541725"' in src
    assert 'JOB_UUID = "p5-a5b5e2fb-53d6-5862-878a-153556b6aca6"' in src
    assert "PA1_PA2_WORKFLOW_RUN_ID" in src
