import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "workspace-shell"
ROOT_CODE = PLUGIN / "root"
sys.path.insert(0, str(ROOT_CODE))

job_launcher = importlib.import_module("job_launcher")
root_broker = importlib.import_module("root_broker")
runtime_common = importlib.import_module("runtime_common")


def test_node_policy_and_approval_adversarial_suite():
    files = [
        "server.js",
        "src/core.js",
        "bin/verify-broker-request.mjs",
    ]
    for relative in files:
        proc = subprocess.run(
            ["node", "--check", str(PLUGIN / relative)],
            cwd=PLUGIN,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr

    proc = subprocess.run(
        [
            "node",
            "--test",
            str(PLUGIN / "test" / "core.test.js"),
            str(PLUGIN / "test" / "broker-verifier.test.js"),
        ],
        cwd=PLUGIN,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


def test_launcher_duplicates_profile_grammar_and_denies_escape_shapes():
    manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
    good = job_launcher.resolve_profile(manifest, "git-read", ["rev-parse", "HEAD"])
    assert good["executable"] == "/usr/bin/git"
    assert good["write_scratch"] is False

    with pytest.raises(runtime_common.ShellRuntimeError, match="PROFILE_ARGV_DENIED"):
        job_launcher.resolve_profile(
            manifest,
            "git-read",
            ["-c", "alias.pwn=!sh", "pwn"],
        )
    with pytest.raises(runtime_common.ShellRuntimeError):
        job_launcher.resolve_profile(
            manifest,
            "pytest-bounded",
            ["../../etc/passwd"],
        )
    with pytest.raises(runtime_common.ShellRuntimeError, match="PROFILE_ARGV_DENIED"):
        job_launcher.resolve_profile(
            manifest,
            "validation-bounded",
            ["preflight", "--repo", "workspace-control"],
        )


def test_worker_sandbox_command_excludes_control_plane_and_network():
    manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
    resolved = job_launcher.resolve_profile(
        manifest,
        "pytest-bounded",
        ["tests/test_workspace_shell_contract.py", "-q"],
    )
    with tempfile.TemporaryDirectory() as td:
        command = job_launcher.build_bwrap_command(
            {"bwrap_path": "/usr/bin/true"},
            Path(td),
            ".",
            resolved,
        )

    joined = "\n".join(command)
    assert "--unshare-all" in command
    assert "--cap-drop" in command
    assert "ALL" in command
    assert "/run/workspace-shell-control" not in joined
    assert "/etc/workspace-shell" not in joined
    assert "SSH_AUTH_SOCK" not in joined
    assert "GITHUB_TOKEN" not in joined
    assert command[-len(resolved["argv"]) - 1] == resolved["executable"]


def test_systemd_job_wrapper_fixes_uid_cgroup_and_host_controls():
    command = job_launcher.build_systemd_run_command(
        {"systemd_run_path": "/usr/bin/true"},
        "workspace-shell-job-test",
        ["/usr/bin/true"],
        41001,
        41001,
        Path("/var/lib/workspace-shell/jobs/test"),
    )
    joined = "\n".join(command)
    assert "--uid=41001" in command
    assert "--gid=41001" in command
    assert "--property=PrivateNetwork=yes" in command
    assert "--property=NoNewPrivileges=yes" in command
    assert "--property=CapabilityBoundingSet=" in command
    assert "--property=KillMode=control-group" in command
    assert "--property=TasksMax=48" in command
    assert "--property=MemoryMax=1G" in command
    assert "workspace-shell-exec" not in joined  # numeric identity comes only from root config


def test_replay_journal_is_single_use_before_mutation():
    with tempfile.TemporaryDirectory() as td:
        db = root_broker.ensure_replay_db({"replay_db": str(Path(td) / "replay.sqlite3")})
        verified = {
            "approval_id": "approval-one",
            "nonce": "nonce-one",
            "idempotency_key": "idem-one",
        }
        root_broker.consume_replay(db, verified)
        with pytest.raises(runtime_common.ShellRuntimeError, match="APPROVAL_REPLAY"):
            root_broker.consume_replay(db, verified)


def test_bounded_output_hashes_full_stream_even_when_return_is_truncated():
    payload = b"a" * 100_000
    result = runtime_common.bounded_run(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'a'*100000); sys.stdout.flush()",
        ],
        timeout_s=5,
        stdout_limit=1024,
        stderr_limit=1024,
    )
    assert result["exit_code"] == 0
    assert result["stdout_bytes_seen"] == len(payload)
    assert result["stdout_truncated"] is True
    assert len(result["stdout"]) == 1024
    assert result["stdout_sha256"] == hashlib.sha256(payload).hexdigest()


def test_timeout_kills_nested_process_group():
    script = (
        "import subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        "print(p.pid, flush=True); time.sleep(30)"
    )
    result = runtime_common.bounded_run(
        [sys.executable, "-c", script],
        timeout_s=0.35,
        stdout_limit=4096,
        stderr_limit=4096,
    )
    assert result["timed_out"] is True
    child_pid = int(result["stdout"].decode().splitlines()[0])

    ended = False
    for _ in range(50):
        proc_path = Path(f"/proc/{child_pid}")
        if not proc_path.exists():
            ended = True
            break
        try:
            state = (proc_path / "stat").read_text().split()[2]
            if state == "Z":
                ended = True
                break
        except FileNotFoundError:
            ended = True
            break
        time.sleep(0.02)
    assert ended, f"nested child {child_pid} survived timeout process-group kill"


def test_root_broker_exec_fd_rejects_final_symlink():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        helper = td / "helper"
        helper.write_text("#!/bin/sh\nexit 0\n")
        helper.chmod(0o755)
        digest = hashlib.sha256(helper.read_bytes()).hexdigest()
        fd = root_broker.open_verified_helper(str(helper), digest)
        os.close(fd)

        link = td / "link"
        link.symlink_to(helper)
        with pytest.raises(OSError):
            root_broker.open_verified_helper(str(link), digest)


def test_control_plane_code_freezes_peer_identity_and_ordering():
    launcher = (ROOT_CODE / "job_launcher.py").read_text()
    broker = (ROOT_CODE / "root_broker.py").read_text()
    server = (PLUGIN / "server.js").read_text()
    verifier = (PLUGIN / "bin" / "verify-broker-request.mjs").read_text()

    assert "SO_PEERCRED" in launcher
    assert "SO_PEERCRED" in broker
    assert 'uid != int(cfg["frontend_uid"])' in launcher
    assert 'peer_uid != int(cfg["frontend_uid"])' in broker
    assert broker.index("consume_replay(replay_db, verified)") < broker.index("execute_helper(cfg, verified)")
    assert 'requestCert: true' in server
    assert 'rejectUnauthorized: true' in server
    assert 'process.getuid() !== config.frontend_uid' in server
    assert "FRONTEND_SIGNATURE_INVALID" in verifier
    assert "APPROVAL_SIGNATURE_INVALID" in verifier
    assert "APPROVAL_REVOKED" in verifier
    assert "HELPER_PATH_ESCAPE" in verifier
    assert "shell=True" not in launcher
    assert "shell=True" not in broker
