from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mth602_t007_fullmatrix_local_dashboard.py"


def _module():
    spec = importlib.util.spec_from_file_location("t007_wave_dashboard", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_t007_wave_contains_all_ten_canonical_pairs_once():
    mod = _module()
    pairs = [row[0] for row in mod.RUNS]
    assert len(pairs) == 10
    assert len(set(pairs)) == 10
    assert sorted(pairs) == sorted([
        "PA1-PA2", "PA1-PA3", "PA1-PA4", "PA1-PA8",
        "PA2-PA3", "PA2-PA4", "PA2-PA8",
        "PA3-PA4", "PA3-PA8", "PA4-PA8",
    ])
    assert set(mod.SEED) == {
        "l2o_hpo_tight60_PA2_PA3_t007",
        "l2o_hpo_v2_PA2_PA8_t007_finalist",
    }


def test_t007_wave_is_host_local_only():
    src = SCRIPT.read_text()
    forbidden = [
        "api.github.com",
        "requests.get(",
        "urllib.request",
        "gh api",
        "gh run",
        "curl ",
    ]
    for token in forbidden:
        assert token not in src


def test_t007_wave_redraw_is_width_safe():
    mod = _module()
    src = SCRIPT.read_text()

    styled = mod.BOLD + ("X" * 200) + mod.RESET
    fitted = mod.fit_ansi_line(styled, 37)
    visible = mod.ANSI_CSI_RE.sub("", fitted)
    assert len(visible) <= 37

    assert "max(104" not in src
    assert "safe_width = max(1, width - 1)" in src
    assert 'sys.stdout.write("\\033[2J\\033[H"' in src


def test_osr_terminal_result_dominates_live_process_and_stale_cache():
    mod = _module()
    direction = "PA1<-PA2"
    cache = {
        "osr": {
            direction: {
                "status": "RUNNING",
                "github_run_id": 999,
            }
        }
    }
    active = {
        direction: {
            "elapsed": 123,
            "github_run_id": "45103679764",
        }
    }
    results = {
        direction: {
            "status": "SUCCESS",
            "artifact_id": 14765881457,
            "unknown_f1": 0.0184953572105362,
            "unknown_auroc": 0.0439551294941176,
            "known_reject_rate": 0.0535555555555555,
        }
    }

    rows = mod.build_osr_rows(cache, active, results)
    row = next(r for r in rows if r["direction"] == direction)

    assert row["status"] == "SUCCESS"
    assert row["elapsed"] is None
    assert row["unknown_f1"] == 0.0184953572105362
    assert cache["osr"][direction]["status"] == "SUCCESS"
