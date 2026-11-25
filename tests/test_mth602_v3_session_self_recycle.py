from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_controller_getmessage_retry_is_bounded_and_systemd_self_restarts():
    controller = (ROOT / "controller/lambda-ci-controller/v3/controller.go").read_text()
    main = (ROOT / "controller/lambda-ci-controller/v3/main.go").read_text()
    unit = (ROOT / "systemd/workspace-ci-v3-controller@.service").read_text()

    assert "getMessageMaxRetries int" in controller
    assert "retryBudgetExhausted(attempt, c.getMessageMaxRetries)" in controller
    assert "scale-set GetMessage retry budget exhausted" in controller
    assert "getMessageMaxRetries: 8" in main
    assert "Restart=on-failure" in unit
    assert "RestartSec=5s" in unit


def test_activation_bootstrap_proves_zero_work_before_controller_refresh_and_restores_on_failure():
    path = ROOT / "scripts/mth602_activate_v3_session_self_recycle_v1.py"
    source = path.read_text()
    ast.parse(source, filename=str(path))

    preflight = source.index("repair.require_no_live_provisioner_records()")
    invoke = source.index("proc = subprocess.run(cmd")
    restore = source.index("for cid in active_before:", invoke)
    failure = source.index('raise RuntimeError(f"controller repair helper failed', restore)

    assert preflight < invoke
    assert invoke < restore < failure
    assert "repair.require_no_transients(units)" in source
    assert "MTH602_V3_SESSION_SELF_RECYCLE=PASS" in source
    assert "gh api" not in source.lower()
    assert "api.github.com" not in source.lower()
