import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "launch_lambda_ci_p2b_noop.py").read_text()


def test_jit_endpoint_is_repository_scoped_and_one_job_labeled():
    assert 'REPOSITORY = "adamtrott78/research-engine"' in SCRIPT
    assert "/actions/runners/generate-jitconfig" in SCRIPT
    assert '"runner_group_id": RUNNER_GROUP_ID' in SCRIPT
    for label in (
        '"self-hosted"',
        '"Linux"',
        '"X64"',
        '"lambda-research-engine"',
        '"cpu-test"',
    ):
        assert label in SCRIPT


def test_token_is_tty_prompted_and_not_forwarded_to_subprocess_environment():
    assert "getpass.getpass" in SCRIPT
    assert "Administration: write" in SCRIPT
    assert "Authorization" in SCRIPT
    assert 'token = ""' in SCRIPT
    assert "GITHUB_TOKEN" not in SCRIPT
    assert "GH_TOKEN" not in SCRIPT
    assert "os.environ[" not in SCRIPT or "token" not in SCRIPT.lower().split("os.environ[")[-1]


def test_jit_config_is_piped_not_written_to_disk_or_argv():
    assert "proc.stdin.write(jit +" in SCRIPT
    assert "ACTIONS_RUNNER_INPUT_JITCONFIG" in SCRIPT
    assert "jit_config_persisted" in SCRIPT
    assert '"jit_config_persisted": False' in SCRIPT
    assert "--jitconfig" not in SCRIPT


def test_cpu_sandbox_denies_private_network_and_devices():
    for token in (
        "DevicePolicy=closed",
        "IPAddressAllow=127.0.0.53/32",
        "IPAddressDeny=127.0.0.0/8",
        "IPAddressDeny=10.0.0.0/8",
        "IPAddressDeny=172.16.0.0/12",
        "IPAddressDeny=192.168.0.0/16",
        "IPAddressDeny=100.64.0.0/10",
        "IPAddressDeny=169.254.0.0/16",
        "IPAddressDeny=fe80::/10",
        "IPAddressDeny=fc00::/7",
        "ProtectHome=yes",
        "ProtectSystem=strict",
        "NoNewPrivileges=yes",
        "InaccessiblePaths=/var/run/docker.sock",
    ):
        assert token in SCRIPT


def test_runner_executes_as_project_uid_with_bounded_resources():
    for token in (
        "User={RUNNER_USER}",
        "Group={RUNNER_GROUP}",
        "CPUQuota=800%",
        "MemoryMax=32G",
        "TasksMax=4096",
        "RuntimeMaxSec=15min",
        "KillMode=control-group",
    ):
        assert token in SCRIPT


def test_workspace_and_project_processes_are_destroyed_after_runner_exit():
    assert "shutil.rmtree(job_dir, ignore_errors=True)" in SCRIPT
    assert '["pgrep", "-u", str(uid)]' in SCRIPT
    assert '["pkill", "-KILL", "-u", str(uid)]' in SCRIPT
    assert '"runner_workspace_destroyed": not job_dir.exists()' in SCRIPT
    assert '"project_uid_process_cleanup": cleanup_pass' in SCRIPT


def test_script_parses_as_python():
    ast.parse(SCRIPT)
