from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "controller/lambda-ci-controller/v3/main.go").read_text()
CONTROLLER = (ROOT / "controller/lambda-ci-controller/v3/controller.go").read_text()
MAIN_TEST = (ROOT / "controller/lambda-ci-controller/v3/main_test.go").read_text()
RECONCILER = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
LAUNCHER = (ROOT / "scripts/mth602_activate_v3_rest_backfill_liveness_v1.py").read_text()


def test_rate_limit_403_is_transient_but_ordinary_403_is_fail_closed():
    for marker in (
        "func githubRESTStatusIsTransient(",
        "resp.StatusCode != http.StatusForbidden",
        'resp.Header.Get("X-RateLimit-Remaining")',
        'resp.Header.Get("Retry-After")',
        'strings.Contains(message, "api rate limit exceeded")',
        'strings.Contains(message, "secondary rate limit")',
        "if !githubRESTStatusIsTransient(resp, body)",
    ):
        assert marker in MAIN
    for marker in (
        "TestGitHubRESTStatusIsTransientDistinguishesRateLimit403",
        '"ordinary forbidden stays fail closed"',
        '"primary rate limit body"',
        '"secondary rate limit"',
    ):
        assert marker in MAIN_TEST


def test_rest_attested_queued_demand_remains_a_bounded_capacity_floor():
    for marker in (
        "Using REST-attested queued demand as bounded capacity floor",
        "desired = minInt(len(jobs), s.policy.MaxRunners)",
        "restDesiredFloor",
        "return s.reconcileCapacity(ctx, stats, restDesiredFloor)",
    ):
        assert marker in CONTROLLER


def test_runtime390_reconciler_lineage_is_preserved():
    for marker in (
        "runtime-ceiling-refresh-v1",
        "compatibility-matrix.json",
        "deployment-overlay.json",
    ):
        assert marker in RECONCILER


def test_live_repair_launcher_is_controller_only():
    assert "lambda_ci_v3_live_controller_repair_v1" in LAUNCHER
    assert "REFRESH_V3_CONTROLLER_BINARY_LIVE_V1" in LAUNCHER
    assert "root-policy.json" not in LAUNCHER
    assert "PROVISIONER_UNIT" not in LAUNCHER
    assert 'systemctl", "restart"' not in LAUNCHER
