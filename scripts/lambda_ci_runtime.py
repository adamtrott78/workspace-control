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
import stat
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


def resolve_gpu_assignment(target_uuid: str) -> dict[str, object]:
    """Resolve a stable NVIDIA GPU UUID to its current device node."""
    gpu_root = pathlib.Path("/proc/driver/nvidia/gpus")
    if not gpu_root.is_dir():
        raise RuntimeLaunchError("NVIDIA driver GPU metadata directory is missing")

    inventory: list[dict[str, object]] = []
    for info_path in sorted(gpu_root.glob("*/information")):
        fields: dict[str, str] = {}
        for raw_line in info_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            fields[key.strip()] = value.strip()

        gpu_uuid = fields.get("GPU UUID")
        minor_text = fields.get("Device Minor")
        if not gpu_uuid or minor_text is None:
            raise RuntimeLaunchError(
                f"NVIDIA information file missing GPU UUID/Device Minor: {info_path}"
            )
        try:
            minor = int(minor_text)
        except ValueError as exc:
            raise RuntimeLaunchError(
                f"invalid NVIDIA Device Minor in {info_path}: {minor_text!r}"
            ) from exc

        device = pathlib.Path(f"/dev/nvidia{minor}")
        if not device.exists() or not stat.S_ISCHR(device.stat().st_mode):
            raise RuntimeLaunchError(f"NVIDIA device node invalid for {gpu_uuid}: {device}")

        inventory.append(
            {
                "uuid": gpu_uuid,
                "minor": minor,
                "device": str(device),
                "bus_location": fields.get("Bus Location"),
                "model": fields.get("Model"),
                "information_path": str(info_path),
            }
        )

    if not inventory:
        raise RuntimeLaunchError("NVIDIA driver reported no GPUs")

    selected = [row for row in inventory if str(row["uuid"]).lower() == target_uuid.lower()]
    if len(selected) != 1:
        raise RuntimeLaunchError(
            f"expected exactly one GPU matching {target_uuid}, found {len(selected)}"
        )

    selected_row = selected[0]
    denied_devices = [
        str(row["device"])
        for row in inventory
        if str(row["uuid"]).lower() != target_uuid.lower()
    ]
    if not denied_devices:
        raise RuntimeLaunchError("gpu-small requires at least one non-selected GPU denial target")

    nvidiactl = pathlib.Path("/dev/nvidiactl")
    if not nvidiactl.exists() or not stat.S_ISCHR(nvidiactl.stat().st_mode):
        raise RuntimeLaunchError("/dev/nvidiactl missing or not a character device")

    return {
        "target_uuid": target_uuid,
        "selected_device": str(selected_row["device"]),
        "selected_minor": int(selected_row["minor"]),
        "denied_devices": denied_devices,
        "inventory": inventory,
    }


def resolve_cuda_support_devices() -> list[str]:
    """Return only the shared NVIDIA compute-support devices accepted by P4."""
    allowed = (
        pathlib.Path("/dev/nvidia-uvm"),
        pathlib.Path("/dev/nvidia-uvm-tools"),
    )
    resolved: list[str] = []
    for path in allowed:
        if not path.exists():
            continue
        if not stat.S_ISCHR(path.stat().st_mode):
            raise RuntimeLaunchError(f"NVIDIA support path is not a character device: {path}")
        resolved.append(str(path))
    if "/dev/nvidia-uvm" not in resolved:
        raise RuntimeLaunchError("CUDA UVM device /dev/nvidia-uvm is missing")
    return resolved


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
        raise RuntimeLaunchError(
            "unable to inspect NVIDIA compute processes: " + proc.stderr.strip()
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
        if owner_uid != uid:
            continue
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


def build_gpu_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
    assignment: dict[str, object],
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

    selected_device = str(assignment["selected_device"])
    target_uuid = str(assignment["target_uuid"])
    denied_devices = ",".join(str(path) for path in assignment["denied_devices"])
    support_devices = [str(path) for path in assignment["support_devices"]]

    memory_max = int(resources["memory_max_bytes"])
    memory_high = max(1, memory_max - (8 * 1024**3))

    command = [
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
        "-p", "DeviceAllow=/dev/nvidiactl rw",
        "-p", f"DeviceAllow={selected_device} rw",
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
        "-p", f"Environment=CUDA_VISIBLE_DEVICES={target_uuid}",
        "-p", f"Environment=P5_GPU_TARGET_UUID={target_uuid}",
        "-p", f"Environment=P5_GPU_SELECTED_DEVICE={selected_device}",
        "-p", f"Environment=P5_GPU_DENIED_DEVICES={denied_devices}",
        "-p", f"Environment=P5_GPU_SUPPORT_DEVICES={','.join(support_devices)}",
        "/bin/bash",
        "-ceu",
        bash_script,
    ]

    insert_at = command.index("-p", command.index(f"DeviceAllow={selected_device} rw") + 1)
    for support_device in support_devices:
        command[insert_at:insert_at] = ["-p", f"DeviceAllow={support_device} rw"]
        insert_at += 2
    return command


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


def launch_gpu_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Launch one accepted gpu-small runner and return a non-secret cleanup receipt."""
    if spec["profile"] != "gpu-small":
        raise RuntimeLaunchError("GPU runtime accepts gpu-small only")
    if spec["allow_production_services"]:
        raise RuntimeLaunchError("production-service access is forbidden")
    if spec["resources"]["gpu_indices"] != [0]:
        raise RuntimeLaunchError("gpu-small authority must remain exactly one GPU")
    target_uuid = spec["resources"].get("gpu_uuid")
    if target_uuid != "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea":
        raise RuntimeLaunchError("gpu-small target UUID drift")

    runner_base, uid, gid = verify_foundation(spec)
    subnet = primary_subnet()
    assignment = resolve_gpu_assignment(target_uuid)
    assignment["support_devices"] = resolve_cuda_support_devices()
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
    command = build_gpu_systemd_command(
        spec,
        runner_dir,
        staging_dir,
        subnet,
        assignment,
    )

    result = "FAIL"
    rc = None
    cleanup_pass = False
    gpu_cleanup_pass = False
    leaked_gpu_processes: list[dict[str, object]] = []
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
            "project_uid_gpu_process_cleanup": gpu_cleanup_pass,
            "leaked_gpu_processes": leaked_gpu_processes,
            "runner_workspace_destroyed": not job_dir.exists(),
            "staging_workspace_destroyed": not staging_dir.exists(),
            "network_local_subnet_denied": subnet,
            "jit_config_persisted": False,
            "github_credential_present": False,
            "gpu_target_uuid": assignment["target_uuid"],
            "gpu_selected_device": assignment["selected_device"],
            "gpu_selected_minor": assignment["selected_minor"],
            "gpu_denied_devices": assignment["denied_devices"],
            "gpu_inventory": assignment["inventory"],
            "gpu_support_devices": assignment["support_devices"],
            "cuda_visible_devices": assignment["target_uuid"],
        }
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if result != "RUNNER_EXITED_CLEANLY" or not cleanup_pass or not gpu_cleanup_pass:
        raise RuntimeLaunchError(
            "GPU runner did not complete cleanly "
            f"result={result} cleanup={cleanup_pass} gpu_cleanup={gpu_cleanup_pass}"
        )
    return receipt


def launch_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Dispatch only the two explicitly accepted autonomous P5 profiles."""
    profile = spec["profile"]
    if profile == "cpu-test":
        return launch_cpu_runner(request, spec)
    if profile == "gpu-small":
        return launch_gpu_runner(request, spec)
    raise RuntimeLaunchError(f"autonomous profile rejected: {profile}")
