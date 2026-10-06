import ast
import io
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "launch_lambda_ci_p4_gpu.py"
SCRIPT = SCRIPT_PATH.read_text()


def load():
    return runpy.run_path(str(SCRIPT_PATH), run_name="lambda_ci_p4_gpu_test")


def test_jit_scope_and_labels():
    assert 'REPOSITORY = "adamtrott78/research-engine"' in SCRIPT
    assert "/actions/runners/generate-jitconfig" in SCRIPT
    for label in (
        '"self-hosted"',
        '"Linux"',
        '"X64"',
        '"lambda-research-engine"',
        '"gpu-small-v1"',
    ):
        assert label in SCRIPT
    assert '"cpu-test-v2"' not in SCRIPT


def test_token_and_jit_secret_boundary():
    assert "getpass.getpass" in SCRIPT
    assert "Administration: write" in SCRIPT
    assert "Authorization" in SCRIPT
    assert 'token = ""' in SCRIPT
    assert "proc.stdin.write(jit +" in SCRIPT
    assert "ACTIONS_RUNNER_INPUT_JITCONFIG" in SCRIPT
    assert "--jitconfig" not in SCRIPT


def test_gpu_boundary_is_uuid_resolved_not_static_indexed():
    assert "DevicePolicy=closed" in SCRIPT
    assert "DeviceAllow=/dev/nvidiactl rw" in SCRIPT
    assert 'TARGET_GPU_UUID = "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"' in SCRIPT
    assert '"--query-gpu=uuid,minor_number"' in SCRIPT
    assert 'f"DeviceAllow={selected_device} rw"' in SCRIPT
    assert "DeviceAllow=/dev/nvidia0 rw" not in SCRIPT
    assert "DeviceAllow=/dev/nvidia1 rw" not in SCRIPT
    assert "Environment=CUDA_VISIBLE_DEVICES={target_uuid}" in SCRIPT
    assert "P4_SELECTED_GPU_DEVICE" in SCRIPT
    assert "P4_DENIED_GPU_DEVICES" in SCRIPT


def test_network_home_docker_boundaries_preserved():
    for token in (
        "ProtectHome=yes",
        "ProtectSystem=strict",
        "NoNewPrivileges=yes",
        "InaccessiblePaths=/var/run/docker.sock",
        "IPAddressDeny=127.0.0.0/8",
        "IPAddressDeny=10.0.0.0/8",
        "IPAddressDeny=172.16.0.0/12",
        "IPAddressDeny=192.168.0.0/16",
        "IPAddressDeny=100.64.0.0/10",
    ):
        assert token in SCRIPT


def test_p4_timeout_hierarchy():
    ns = load()
    workflow = ns["WORKFLOW_TIMEOUT_SECONDS"]
    systemd_runtime = ns["SYSTEMD_RUNTIME_SECONDS"]
    watchdog = ns["LAUNCHER_WATCHDOG_SECONDS"]
    assert workflow == 15 * 60
    assert systemd_runtime == 20 * 60
    assert watchdog == 22 * 60
    assert workflow < systemd_runtime < watchdog

    assignment = {
        "target_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
        "selected_device": "/dev/nvidia1",
        "selected_minor": 1,
        "denied_devices": ["/dev/nvidia0"],
        "inventory": [],
    }
    command = ns["systemd_command"](
        "workspace-ci-test.service",
        Path("/tmp/runner"),
        "134.88.12.0/22",
        assignment,
    )
    assert f"RuntimeMaxSec={systemd_runtime}s" in command
    assert "DeviceAllow=/dev/nvidia1 rw" in command
    assert "DeviceAllow=/dev/nvidia0 rw" not in command
    assert "Environment=CUDA_VISIBLE_DEVICES=GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea" in command
    assert "Environment=P4_SELECTED_GPU_DEVICE=/dev/nvidia1" in command
    assert "Environment=P4_DENIED_GPU_DEVICES=/dev/nvidia0" in command


def test_gpu_cleanup_is_checked_after_runner_exit():
    assert "def project_gpu_processes" in SCRIPT
    assert '"--query-compute-apps=pid,gpu_uuid,used_memory"' in SCRIPT
    assert '"project_uid_gpu_process_cleanup": gpu_cleanup_pass' in SCRIPT
    assert '"leaked_gpu_processes": leaked_gpu_processes' in SCRIPT
    assert 'return 0 if result == "RUNNER_EXITED_CLEANLY" and cleanup_pass and gpu_cleanup_pass else 1' in SCRIPT


def test_live_output_is_preserved():
    ns = load()

    class NonClosingStringIO(io.StringIO):
        def close(self):
            self.flush()

    source = NonClosingStringIO("gpu-step-one\ngpu-step-two\n")
    durable = io.StringIO()
    visible = io.StringIO()
    original_stdout = ns["sys"].stdout
    try:
        ns["sys"].stdout = visible
        ns["pump_runner_output"](source, durable)
    finally:
        ns["sys"].stdout = original_stdout

    assert durable.getvalue() == "gpu-step-one\ngpu-step-two\n"
    assert visible.getvalue() == "gpu-step-one\ngpu-step-two\n"
    assert "P4_RUNNER_STARTED" in SCRIPT


def test_script_parses():
    ast.parse(SCRIPT)


def test_launcher_receipt_records_resolved_gpu_identity():
    for token in (
        '"gpu_target_uuid": gpu_assignment["target_uuid"]',
        '"gpu_selected_device": gpu_assignment["selected_device"]',
        '"gpu_denied_devices": gpu_assignment["denied_devices"]',
        '"gpu_inventory": gpu_assignment["inventory"]',
    ):
        assert token in SCRIPT
