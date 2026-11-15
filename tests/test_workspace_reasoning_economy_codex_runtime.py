from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "lambda-ci-workspace-control-codex-bootstrap.yml"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_codex_bootstrap_targets_only_workspace_control_control_small() -> None:
    text = _workflow()

    runs_on = re.findall(r"(?m)^\s*runs-on:\s*(\S+)\s*$", text)
    assert runs_on == ["lambda-workspace-control-control-small"]
    assert "workspace-control-control-small-v1" in text

    assert "lambda-padataset-scientific-single-gpu" not in text
    assert "lambda-padataset-scientific-single-gpu-2" not in text
    assert "runs-on: self-hosted" not in text


def test_codex_bootstrap_proves_no_gpu_docker_or_sibling_project_access() -> None:
    text = _workflow()

    for forbidden_path in (
        "/home/atrott",
        "/srv/workspace-ci/research-engine",
        "/srv/workspace-ci/padataset",
    ):
        assert text.count(forbidden_path) == 1
    assert '[[ ! -r "$forbidden" ]]' in text
    assert "/home/atrott/.codex" not in text

    assert "/var/run/docker.sock" in text
    assert "/run/docker.sock" in text
    assert '[[ ! -r "$socket" && ! -w "$socket" ]]' in text
    for docker_command in (
        "docker run",
        "docker exec",
        "docker build",
        "docker pull",
        "docker compose",
    ):
        assert docker_command not in text

    assert "command -v nvidia-smi" in text
    assert "nvidia-smi -L" in text
    assert "unexpectedly has NVIDIA access" in text
    for gpu_enablement in (
        "CUDA_VISIBLE_DEVICES=",
        "NVIDIA_VISIBLE_DEVICES=",
        "--gpus",
        "/dev/nvidia",
    ):
        assert gpu_enablement not in text


def test_codex_bootstrap_is_checksum_pinned_and_persists_only_in_project_home() -> None:
    text = _workflow()

    assert 'CODEX_VERSION: "0.155.1"' in text
    assert (
        'CODEX_ARCHIVE_SHA256: '
        '"a0ef8b2debc3bf747e07b1a039354de31300ac0dcc2276498ba281470b5d9115"'
        in text
    )
    assert (
        'CODEX_ARCHIVE_URL: '
        '"https://github.com/openai/codex/releases/download/rust-v0.155.1/'
        'codex-x86_64-unknown-linux-musl.tar.gz"'
        in text
    )
    assert 'PROJECT_HOME: "/srv/workspace-ci/workspace-control/home"' in text
    assert 'runtime_root="$PROJECT_HOME/.local/share/workspace-reasoning-economy/codex"' in text
    assert 'bin_dir="$PROJECT_HOME/.local/bin"' in text
    assert 'codex_home="$PROJECT_HOME/.codex-reasoning-economy"' in text
    assert 'archive="$RUNNER_TEMP/codex-$CODEX_VERSION.tar.gz"' in text
    assert 'receipt="$RUNNER_TEMP/workspace-control-codex-bootstrap-receipt.json"' in text

    assert '~/.codex' not in text
    assert "$HOME/.codex" not in text
    assert "/tmp/.codex" not in text


def test_codex_bootstrap_forces_chatgpt_auth_and_strips_api_key() -> None:
    text = _workflow()

    assert text.count("unset OPENAI_API_KEY") >= 3
    assert not re.search(r"(?m)^\s*(?:export\s+)?OPENAI_API_KEY=", text)

    assert 'forced_login_method = "chatgpt"' in text
    assert 'cli_auth_credentials_store = "file"' in text
    assert '"$CODEX_BIN" login --device-auth' in text
    assert text.count("Logged in using ChatGPT") >= 2
    assert "[[ ! -v OPENAI_API_KEY ]]" in text

    for forbidden_auth in (
        "login --with-api-key",
        "login --api-key",
        "OPENAI_API_KEY:",
        "api_key =",
    ):
        assert forbidden_auth not in text


def test_codex_bootstrap_performs_zero_model_inference_and_emits_redacted_receipt() -> None:
    text = _workflow()

    assert '"model_inference_performed": False' in text
    assert '"credential_material_in_receipt": False' in text
    assert '"auth_mode": "chatgpt"' in text
    assert '"api_key_present": False' in text
    assert "workspace-control-codex-bootstrap-receipt.json" in text

    for inference_command in (
        '"$CODEX_BIN" exec',
        '"$CODEX_BIN" run',
        '"$CODEX_BIN" chat',
        "codex exec",
        "codex run",
    ):
        assert inference_command not in text

    for sensitive_material in (
        '"email"',
        '"user_id"',
        '"account_id"',
        '"access_token"',
        '"refresh_token"',
        '"device_code"',
        '"token"',
    ):
        assert sensitive_material not in text

    assert 'path: ${{ runner.temp }}/workspace-control-codex-bootstrap-receipt.json' in text


def test_codex_bootstrap_does_not_widen_capacity_or_root_authority() -> None:
    text = _workflow()

    for capacity_marker in (
        "reserved_project_slots",
        "max_active_runners",
        "host_concurrency",
        "project_concurrency",
        "max_concurrency",
        "PADataset concurrency",
        "Workspace Control concurrency",
    ):
        assert capacity_marker not in text

    for authority_marker in (
        "sudo ",
        "systemctl ",
        "root_policy",
        "root-policy",
        "workspace_shell",
        "run_reviewed_helper",
        "contents: write",
        "actions: write",
        "-X POST",
        "-X PUT",
        "-X PATCH",
        "-X DELETE",
    ):
        assert authority_marker not in text

    for root_path in (
        "/var/lib/workspace-ci/provisioner",
        "/var/lib/workspace-ci/reconciler",
        "/var/lib/workspace-ci/controller",
        "/run/workspace-ci",
    ):
        assert text.count(root_path) == 1
