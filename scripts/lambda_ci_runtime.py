#!/usr/bin/env python3
"""Privileged runtime primitives for bounded Lambda CI project runners.

This module contains no GitHub authentication and performs no GitHub API calls.
Authority is supplied only through a launch spec produced from root-owned
workspace-control policy.
"""

from __future__ import annotations

import json
import os
import pathlib
import pwd
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from typing import Any


class RuntimeLaunchError(RuntimeError):
    pass


def run(argv: list[str], *, check: bool = True):
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeLaunchError(
            f"command failed rc={proc.returncode}: {argv[0]}: {proc.stderr.strip()}"
        )
    return proc


def project_identity(user: str) -> tuple[int, int]:
    try:
        row = pwd.getpwnam(user)
    except KeyError as exc:
        raise RuntimeLaunchError(f"project runner identity missing: {user}") from exc

    active = run(["pgrep", "-u", str(row.pw_uid)], check=False)
    if active.returncode == 0 and active.stdout.strip():
        raise RuntimeLaunchError(
            f"existing project process detected for {user}; refusing concurrency"
        )
    if active.returncode not in (0, 1):
        raise RuntimeLaunchError(f"unable to inspect process state for {user}")
    return row.pw_uid, row.pw_gid


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
    raise RuntimeLaunchError("unable to resolve directly connected primary IPv4 subnet")


def chown_tree(path: pathlib.Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)
        for name in files:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)


def verify_foundation(spec: dict[str, Any]) -> tuple[pathlib.Path, int, int]:
    runner_version = spec["runner"]["version"]
    runner_base = pathlib.Path("/opt/workspace-ci/actions-runner") / runner_version
    if not (runner_base / "run.sh").is_file():
        raise RuntimeLaunchError(f"pinned Actions runner missing: {runner_base}")

    paths = spec["paths"]
    for key in ("job_root", "staging_cache", "trusted_cache", "home", "logs"):
        path = pathlib.Path(paths[key])
        if not path.is_dir():
            raise RuntimeLaunchError(f"required project path missing: {key}={path}")

    user = spec["run_as"]["user"]
    uid, gid = project_identity(user)

    isolation = run(
        [
            "runuser",
            "-u",
            user,
            "--",
            "/bin/bash",
            "-ceu",
            """
            test ! -r /home/atrott
            test ! -r /home/atrott/.ssh
            if [[ -e /var/run/docker.sock ]]; then
              test ! -r /var/run/docker.sock
              test ! -w /var/run/docker.sock
            fi
            """,
        ],
        check=False,
    )
    if isolation.returncode != 0:
        raise RuntimeLaunchError("project identity isolation no longer matches acceptance")

    return runner_base, uid, gid


def build_cpu_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
) -> list[str]:
    resources = spec["resources"]
    paths = spec["paths"]
    bash_script = r"""
        IFS= read -r jit
        [[ -n "$jit" ]]
        export ACTIONS_RUNNER_INPUT_JITCONFIG="$jit"
        unset jit
        exec ./run.sh
    """

    memory_max = int(resources["memory_max_bytes"])
    memory_high = max(1, memory_max - (4 * 1024**3))

    return [
        "systemd-run",
        "--quiet",
        "--wait",
        "--collect",
        "--pipe",
        f"--unit={spec['unit_name']}",
        "-p", "Type=exec",
        "-p", f"User={spec['run_as']['user']}",
        "-p", f"Group={spec['run_as']['group']}",
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
        "-p", f"ReadWritePaths={paths['job_root']}",
        "-p", f"ReadWritePaths={staging_dir}",
        "-p", f"ReadWritePaths={paths['home']}",
        "-p", f"ReadWritePaths={paths['logs']}",
        "-p", f"ReadOnlyPaths={paths['trusted_cache']}",
        "-p", "InaccessiblePaths=/var/run/docker.sock",
        "-p", "InaccessiblePaths=/run/docker.sock",
        "-p", "DevicePolicy=closed",
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
        "-p", f"CPUQuota={int(resources['cpu_quota_percent'])}%",
        "-p", f"MemoryHigh={memory_high}",
        "-p", f"MemoryMax={memory_max}",
        "-p", f"TasksMax={int(resources['tasks_max'])}",
        "-p", f"RuntimeMaxSec={int(resources['runtime_max_seconds'])}s",
        "-p", "KillMode=control-group",
        "-p", "SendSIGKILL=yes",
        "-p", "TimeoutStopSec=20s",
        "-p", f"Environment=HOME={paths['home']}",
        "-p", f"Environment=XDG_CACHE_HOME={staging_dir}",
        "-p", f"Environment=HF_HOME={staging_dir / 'huggingface'}",
        "/bin/bash",
        "-ceu",
        bash_script,
    ]


def _pump(stream, log) -> None:
    try:
        for line in iter(stream.readline, ""):
            log.write(line)
            log.flush()
    finally:
        stream.close()


def launch_cpu_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Launch one accepted CPU runner and return a non-secret cleanup receipt."""
    if spec["profile"] != "cpu-test":
        raise RuntimeLaunchError("P5 pilot runtime accepts cpu-test only")
    if spec["resources"]["gpu_indices"]:
        raise RuntimeLaunchError("cpu-test spec unexpectedly contains GPU authority")
    if spec["allow_production_services"]:
        raise RuntimeLaunchError("production-service access is forbidden")

    runner_base, uid, gid = verify_foundation(spec)
    subnet = primary_subnet()
    request_id = request.request_id

    job_root = pathlib.Path(spec["paths"]["job_root"])
    staging_root = pathlib.Path(spec["paths"]["staging_cache"])
    logs_root = pathlib.Path(spec["paths"]["logs"])
    job_dir = job_root / f"p5-{request_id}"
    runner_dir = job_dir / "runner"
    staging_dir = staging_root / f"p5-{request_id}"

    if job_dir.exists() or staging_dir.exists():
        raise RuntimeLaunchError("request workspace already exists")

    job_dir.mkdir(mode=0o700)
    staging_dir.mkdir(mode=0o700)
    shutil.copytree(runner_base, runner_dir, symlinks=True)
    chown_tree(job_dir, uid, gid)
    chown_tree(staging_dir, uid, gid)

    console_log = logs_root / f"p5-{request_id}-runner.log"
    journal_log = logs_root / f"p5-{request_id}-journal.log"
    receipt_path = logs_root / f"p5-{request_id}-receipt.json"
    command = build_cpu_systemd_command(spec, runner_dir, staging_dir, subnet)

    result = "FAIL"
    rc = None
    cleanup_pass = False
    jit = request.jit_config

    try:
        with console_log.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None
            output_thread = threading.Thread(target=_pump, args=(proc.stdout, log), daemon=True)
            output_thread.start()
            proc.stdin.write(jit + "\n")
            proc.stdin.flush()
            proc.stdin.close()
            jit = ""
            rc = proc.wait(timeout=int(spec["resources"]["runtime_max_seconds"]) + 120)
            output_thread.join(timeout=10)
        if rc != 0:
            raise RuntimeLaunchError(f"runner/systemd unit exited rc={rc}")
        result = "RUNNER_EXITED_CLEANLY"
    finally:
        jit = ""

        leaked = run(["pgrep", "-u", str(uid)], check=False)
        if leaked.returncode == 0 and leaked.stdout.strip():
            run(["pkill", "-KILL", "-u", str(uid)], check=False)
            cleanup_pass = False
        elif leaked.returncode in (0, 1):
            cleanup_pass = True

        journal = run(
            ["journalctl", "-u", spec["unit_name"], "--no-pager", "-n", "1000"],
            check=False,
        )
        journal_log.write_text(
            journal.stdout + ("\n" + journal.stderr if journal.stderr else ""),
            encoding="utf-8",
        )

        diag = runner_dir / "_diag"
        if diag.is_dir():
            target = logs_root / f"p5-{request_id}-diag"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(diag, target, symlinks=True)

        shutil.rmtree(job_dir, ignore_errors=True)
        shutil.rmtree(staging_dir, ignore_errors=True)

        receipt = {
            "schema_version": 1,
            "phase": "P5-provisioner-runtime",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "decision": result,
            "request_id": request_id,
            "project_id": spec["project_id"],
            "profile": spec["profile"],
            "runner_name": spec["runner_name"],
            "unit_name": spec["unit_name"],
            "runner_exit_code": rc,
            "project_uid_process_cleanup": cleanup_pass,
            "runner_workspace_destroyed": not job_dir.exists(),
            "staging_workspace_destroyed": not staging_dir.exists(),
            "network_local_subnet_denied": subnet,
            "jit_config_persisted": False,
            "github_credential_present": False,
        }
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if result != "RUNNER_EXITED_CLEANLY" or not cleanup_pass:
        raise RuntimeLaunchError(
            f"runner did not complete cleanly result={result} cleanup={cleanup_pass}"
        )
    return receipt
