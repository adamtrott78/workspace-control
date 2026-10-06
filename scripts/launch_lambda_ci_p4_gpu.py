#!/usr/bin/env python3
"""Launch exactly one repository-scoped JIT Actions runner for P4 GPU validation.

Security properties:
- must run as root through sudo from the operator account;
- prompts for the repository-admin token via TTY with echo disabled;
- token is used only in-process for the JIT API call;
- token is never passed to subprocesses, argv, environment, disk, logs, or job;
- encoded JIT config is passed to systemd-run only over stdin;
- runner executes once as ci-research-engine with only GPU0 granted by systemd DevicePolicy;
- runner workspace/config is destroyed after exit;
- production services are not modified.
"""

from __future__ import annotations

import getpass
import json
import os
import pathlib
import pwd
import shutil
import subprocess
import sys
import time
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

REPOSITORY = "adamtrott78/research-engine"
RUNNER_GROUP_ID = 1
RUNNER_BASE = pathlib.Path("/opt/workspace-ci/actions-runner/2.337.0")
PROJECT_ROOT = pathlib.Path("/srv/workspace-ci/research-engine")
JOBS_ROOT = PROJECT_ROOT / "jobs"
STAGING_CACHE = PROJECT_ROOT / "staging-cache"
TRUSTED_CACHE = PROJECT_ROOT / "trusted-cache"
PROJECT_HOME = PROJECT_ROOT / "home"
LOG_ROOT = PROJECT_ROOT / "logs"
RUNNER_USER = "ci-research-engine"
RUNNER_GROUP = "ci-research-engine"
API_VERSION = "2026-03-10"
WORKFLOW_TIMEOUT_SECONDS = 15 * 60
SYSTEMD_RUNTIME_SECONDS = 20 * 60
LAUNCHER_WATCHDOG_SECONDS = 22 * 60


class LaunchError(RuntimeError):
    pass


def run(argv: list[str], *, check: bool = True, text: bool = True):
    proc = subprocess.run(
        argv,
        text=text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise LaunchError(
            f"command failed rc={proc.returncode}: {argv[0]}: "
            f"{proc.stderr.strip() if text else '<binary stderr>'}"
        )
    return proc


def require_clean_identity() -> tuple[int, int]:
    try:
        row = pwd.getpwnam(RUNNER_USER)
    except KeyError as exc:
        raise LaunchError("ci-research-engine does not exist; P2 incomplete") from exc

    active = run(["pgrep", "-u", str(row.pw_uid)], check=False)
    if active.returncode == 0 and active.stdout.strip():
        raise LaunchError(
            "existing ci-research-engine process detected; refusing concurrent P4"
        )
    if active.returncode not in (0, 1):
        raise LaunchError("unable to verify ci-research-engine process state")

    return row.pw_uid, row.pw_gid


def verify_host_foundation() -> None:
    required_dirs = (RUNNER_BASE, JOBS_ROOT, STAGING_CACHE, TRUSTED_CACHE, PROJECT_HOME, LOG_ROOT)
    for path in required_dirs:
        if not path.is_dir():
            raise LaunchError(f"required P2 directory missing: {path}")
    if not (RUNNER_BASE / "run.sh").is_file():
        raise LaunchError("pinned Actions runner base is missing run.sh")

    if os.access(TRUSTED_CACHE, os.W_OK):
        # Root itself can write. This assertion is done as the runner identity below.
        pass

    isolation = run(
        [
            "runuser",
            "-u",
            RUNNER_USER,
            "--",
            "/bin/bash",
            "-ceu",
            """
            test ! -r /home/atrott
            test ! -r /home/atrott/.ssh
            test -w /srv/workspace-ci/research-engine/jobs
            test -w /srv/workspace-ci/research-engine/staging-cache
            test ! -w /srv/workspace-ci/research-engine/trusted-cache
            if [[ -e /var/run/docker.sock ]]; then
              test ! -r /var/run/docker.sock
              test ! -w /var/run/docker.sock
            fi
            """,
        ],
        check=False,
    )
    if isolation.returncode != 0:
        raise LaunchError("project identity isolation no longer matches P2 acceptance")


def primary_subnet() -> str:
    proc = run(["ip", "-4", "route", "show"])
    for line in proc.stdout.splitlines():
        parts = line.split()
        if (
            parts
            and "/" in parts[0]
            and "proto" in parts
            and "kernel" in parts
            and "scope" in parts
            and "link" in parts
            and parts[0][0].isdigit()
            and not parts[0].startswith(("127.", "169.254.", "172.17.", "172.18.", "100."))
        ):
            return parts[0]
    raise LaunchError("unable to resolve directly connected primary IPv4 subnet")


def github_jit_config(token: str, runner_name: str) -> tuple[str, int]:
    url = f"https://api.github.com/repos/{REPOSITORY}/actions/runners/generate-jitconfig"
    body = json.dumps(
        {
            "name": runner_name,
            "runner_group_id": RUNNER_GROUP_ID,
            "labels": [
                "self-hosted",
                "Linux",
                "X64",
                "lambda-research-engine",
                "gpu-small-v1",
            ],
            "work_folder": "_work",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "workspace-control-lambda-ci-p4",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # GitHub error bodies do not echo the submitted authorization token.
        body_text = exc.read().decode("utf-8", errors="replace")[:2000]
        raise LaunchError(
            f"GitHub JIT API failed HTTP {exc.code}: {body_text}"
        ) from exc

    jit = payload.get("encoded_jit_config")
    runner = payload.get("runner") or {}
    runner_id = runner.get("id")
    if not isinstance(jit, str) or not jit:
        raise LaunchError("GitHub JIT response missing encoded_jit_config")
    if not isinstance(runner_id, int):
        raise LaunchError("GitHub JIT response missing runner id")
    return jit, runner_id


def chown_tree(path: pathlib.Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)
        for name in files:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)


def systemd_command(unit: str, runner_dir: pathlib.Path, subnet: str) -> list[str]:
    bash_script = r"""
        IFS= read -r jit
        [[ -n "$jit" ]]
        export ACTIONS_RUNNER_INPUT_JITCONFIG="$jit"
        unset jit
        exec ./run.sh
    """
    return [
        "systemd-run",
        "--quiet",
        "--wait",
        "--collect",
        "--pipe",
        f"--unit={unit}",
        "-p", "Type=exec",
        "-p", f"User={RUNNER_USER}",
        "-p", f"Group={RUNNER_GROUP}",
        "-p", f"WorkingDirectory={runner_dir}",
        "-p", "NoNewPrivileges=yes",
        "-p", "CapabilityBoundingSet=",
        "-p", "AmbientCapabilities=",
        "-p", "RestrictSUIDSGID=yes",
        "-p", "PrivateTmp=yes",
        "-p", "ProtectSystem=strict",
        "-p", "ProtectHome=yes",
        "-p", "ProtectKernelTunables=yes",
        "-p", "ProtectKernelModules=yes",
        "-p", "ProtectKernelLogs=yes",
        "-p", "ProtectControlGroups=yes",
        "-p", "ProtectClock=yes",
        "-p", "ProtectHostname=yes",
        "-p", "RestrictRealtime=yes",
        "-p", "LockPersonality=yes",
        "-p", "ProtectProc=invisible",
        "-p", "ProcSubset=pid",
        "-p", "UMask=0077",
        "-p", f"ReadWritePaths={JOBS_ROOT}",
        "-p", f"ReadWritePaths={STAGING_CACHE}",
        "-p", f"ReadWritePaths={PROJECT_HOME}",
        "-p", f"ReadWritePaths={LOG_ROOT}",
        "-p", f"ReadOnlyPaths={TRUSTED_CACHE}",
        "-p", "InaccessiblePaths=/var/run/docker.sock",
        "-p", "InaccessiblePaths=/run/docker.sock",
        "-p", "DevicePolicy=closed",
        "-p", "DeviceAllow=/dev/nvidiactl rw",
        "-p", "DeviceAllow=/dev/nvidia0 rw",
        "-p", "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        "-p", "IPAddressAllow=127.0.0.53/32",
        "-p", "IPAddressDeny=127.0.0.0/8",
        "-p", "IPAddressDeny=::1/128",
        "-p", "IPAddressDeny=10.0.0.0/8",
        "-p", "IPAddressDeny=172.16.0.0/12",
        "-p", "IPAddressDeny=192.168.0.0/16",
        "-p", "IPAddressDeny=100.64.0.0/10",
        "-p", "IPAddressDeny=169.254.0.0/16",
        "-p", "IPAddressDeny=fe80::/10",
        "-p", "IPAddressDeny=fc00::/7",
        "-p", f"IPAddressDeny={subnet}",
        "-p", "CPUQuota=1200%",
        "-p", "MemoryHigh=56G",
        "-p", "MemoryMax=64G",
        "-p", "TasksMax=8192",
        "-p", f"RuntimeMaxSec={SYSTEMD_RUNTIME_SECONDS}s",
        "-p", "KillMode=control-group",
        "-p", "SendSIGKILL=yes",
        "-p", "TimeoutStopSec=20s",
        "-p", f"Environment=HOME={PROJECT_HOME}",
        "-p", f"Environment=XDG_CACHE_HOME={STAGING_CACHE}",
        "-p", f"Environment=HF_HOME={STAGING_CACHE}/huggingface",
        "-p", "Environment=CUDA_VISIBLE_DEVICES=0",
        "/bin/bash",
        "-ceu",
        bash_script,
    ]


def pump_runner_output(stream, log) -> None:
    """Mirror runner output live to the operator terminal and durable log."""
    try:
        for line in iter(stream.readline, ""):
            log.write(line)
            log.flush()
            sys.stdout.write(line)
            sys.stdout.flush()
    finally:
        stream.close()


def collect_diag(runner_dir: pathlib.Path, output_dir: pathlib.Path) -> None:
    diag = runner_dir / "_diag"
    if not diag.is_dir():
        return
    target = output_dir / "runner-diag"
    shutil.copytree(diag, target, symlinks=True)


def project_gpu_processes(uid: int) -> list[dict[str, object]]:
    """Return active NVIDIA compute processes owned by the project UID."""
    proc = run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid,used_memory",
            "--format=csv,noheader,nounits",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise LaunchError(
            "unable to inspect NVIDIA compute processes after P4 runner exit: "
            + proc.stderr.strip()
        )

    rows: list[dict[str, object]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        try:
            owner_uid = os.stat(f"/proc/{pid}").st_uid
        except FileNotFoundError:
            continue
        if owner_uid == uid:
            try:
                used_memory = int(parts[2])
            except ValueError:
                used_memory = None
            rows.append(
                {
                    "pid": pid,
                    "gpu_uuid": parts[1],
                    "used_memory_mib": used_memory,
                }
            )
    return rows


def main() -> int:
    if os.geteuid() != 0:
        raise LaunchError("P4 launcher must run as root via sudo")
    if os.environ.get("WORKSPACE_CI_P4_AUTHORIZED") != "YES":
        raise LaunchError("WORKSPACE_CI_P4_AUTHORIZED=YES is required")

    sudo_user = os.environ.get("SUDO_USER")
    if not sudo_user or sudo_user == "root":
        raise LaunchError("run through sudo from the operator account")
    operator = pwd.getpwnam(sudo_user)

    uid, gid = require_clean_identity()
    verify_host_foundation()
    subnet = primary_subnet()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = uuid.uuid4().hex
    runner_name = f"lambda-research-engine-p4-{run_id[:12]}"
    unit = f"workspace-ci-research-engine-p4-{run_id}.service"
    job_dir = JOBS_ROOT / f"p4-{run_id}"
    runner_dir = job_dir / "runner"

    output_dir = (
        pathlib.Path(operator.pw_dir)
        / "adamArchives"
        / "Adam"
        / "workspace-control-tmp"
        / f"lambda-ci-p4-{stamp}"
    )
    output_dir.mkdir(parents=True, mode=0o700)
    console_log = output_dir / "runner-console.log"
    receipt_path = output_dir / "lambda-ci-p4-launcher.json"

    job_dir.mkdir(mode=0o700)
    shutil.copytree(RUNNER_BASE, runner_dir, symlinks=True)
    chown_tree(job_dir, uid, gid)

    token = getpass.getpass(
        "Fine-grained GitHub token (research-engine only; Administration: write; P4 one-job JIT): "
    )
    if not token:
        raise LaunchError("empty GitHub token")

    jit: str | None = None
    runner_id: int | None = None
    proc: subprocess.Popen[str] | None = None
    result = "FAIL"
    cleanup_pass = False
    gpu_cleanup_pass = False
    leaked_gpu_processes: list[dict[str, object]] = []

    try:
        jit, runner_id = github_jit_config(token, runner_name)

        with console_log.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                systemd_command(unit, runner_dir, subnet),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None

            output_thread = threading.Thread(
                target=pump_runner_output,
                args=(proc.stdout, log),
                name="p4-runner-output",
                daemon=True,
            )
            output_thread.start()

            proc.stdin.write(jit + "\n")
            proc.stdin.flush()
            proc.stdin.close()

            # The administrator token has served its only purpose.
            token = ""
            jit = None

            print(
                f"P4_RUNNER_STARTED name={runner_name} id={runner_id} "
                f"systemd_limit={SYSTEMD_RUNTIME_SECONDS}s "
                f"watchdog={LAUNCHER_WATCHDOG_SECONDS}s",
                flush=True,
            )

            try:
                rc = proc.wait(timeout=LAUNCHER_WATCHDOG_SECONDS)
            except subprocess.TimeoutExpired:
                run(["systemctl", "stop", unit], check=False)
                run(["systemctl", "kill", "--kill-who=all", "--signal=KILL", unit], check=False)
                raise LaunchError("P4 runner exceeded launcher watchdog")
            finally:
                output_thread.join(timeout=10)

        if rc != 0:
            raise LaunchError(f"systemd-run/runner exited rc={rc}")

        result = "RUNNER_EXITED_CLEANLY"
    finally:
        token = ""
        jit = None

        try:
            collect_diag(runner_dir, output_dir)
        except Exception as exc:
            (output_dir / "diag-copy-error.txt").write_text(str(exc) + "\n")

        leaked = run(["pgrep", "-u", str(uid)], check=False)
        if leaked.returncode == 0 and leaked.stdout.strip():
            run(["pkill", "-KILL", "-u", str(uid)], check=False)
            cleanup_pass = False
        elif leaked.returncode in (0, 1):
            cleanup_pass = True

        try:
            leaked_gpu_processes = project_gpu_processes(uid)
        except Exception as exc:
            leaked_gpu_processes = [{"inspection_error": str(exc)}]
            gpu_cleanup_pass = False
        else:
            if leaked_gpu_processes:
                run(["pkill", "-KILL", "-u", str(uid)], check=False)
                gpu_cleanup_pass = False
            else:
                gpu_cleanup_pass = True

        journal = run(
            ["journalctl", "-u", unit, "--no-pager", "-n", "1000"],
            check=False,
        )
        (output_dir / "runner-journal.log").write_text(
            journal.stdout + ("\n" + journal.stderr if journal.stderr else ""),
            encoding="utf-8",
        )

        shutil.rmtree(job_dir, ignore_errors=True)

        payload = {
            "schema_version": 1,
            "phase": "P4-launcher",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "decision": result,
            "repository": REPOSITORY,
            "runner_name": runner_name,
            "runner_id": runner_id,
            "unit": unit,
            "profile": "gpu-small-v1",
            "runner_user": RUNNER_USER,
            "network_local_subnet_denied": subnet,
            "jit_config_persisted": False,
            "admin_token_persisted": False,
            "runner_workspace_destroyed": not job_dir.exists(),
            "project_uid_process_cleanup": cleanup_pass,
            "project_uid_gpu_process_cleanup": gpu_cleanup_pass,
            "leaked_gpu_processes": leaked_gpu_processes,
            "gpu_device_grants": ["/dev/nvidiactl", "/dev/nvidia0"],
            "cuda_visible_devices": "0",
            "github_workflow_result": "inspect Lambda CI P4 GPU Validation via GitHub Actions",
        }
        receipt_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chown(output_dir, operator.pw_uid, operator.pw_gid)
        for root, dirs, files in os.walk(output_dir):
            for name in dirs:
                os.chown(pathlib.Path(root) / name, operator.pw_uid, operator.pw_gid)
            for name in files:
                os.chown(pathlib.Path(root) / name, operator.pw_uid, operator.pw_gid)

    print(f"P4_LAUNCHER={result}")
    print(f"CLEANUP_PASS={str(cleanup_pass).lower()}")
    print(f"REPORT={receipt_path}")
    print("GitHub workflow/artifact result must be inspected separately.")
    return 0 if result == "RUNNER_EXITED_CLEANLY" and cleanup_pass and gpu_cleanup_pass else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LaunchError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(70)
