#!/usr/bin/env python3
"""Read-only host capability probe for the Lambda self-hosted runner pilot.

The only writes are the requested diagnostic output directory/file.
No users, services, firewall rules, runner registrations, packages, or
repository state are modified.
"""

from __future__ import annotations

import json
import os
import pathlib
import pwd
import grp
import shutil
import socket
import stat
import subprocess
import sys
from datetime import datetime, timezone


def run(argv: list[str]) -> dict[str, object]:
    try:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        return {
            "argv": argv,
            "rc": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {
            "argv": argv,
            "rc": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def read_text(path: str) -> str | None:
    try:
        return pathlib.Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def path_record(path: str) -> dict[str, object]:
    p = pathlib.Path(path)
    out: dict[str, object] = {"path": path, "exists": p.exists()}
    if not p.exists():
        return out
    try:
        s = p.stat()
        out.update(
            {
                "mode": stat.filemode(s.st_mode),
                "mode_octal": oct(stat.S_IMODE(s.st_mode)),
                "uid": s.st_uid,
                "gid": s.st_gid,
                "owner": pwd.getpwuid(s.st_uid).pw_name,
                "group": grp.getgrgid(s.st_gid).gr_name,
            }
        )
        if p.is_dir():
            usage = shutil.disk_usage(path)
            out["disk"] = {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
            }
    except OSError as exc:
        out["stat_error"] = f"{type(exc).__name__}: {exc}"
    return out


def account_record(name: str) -> dict[str, object]:
    try:
        row = pwd.getpwnam(name)
        return {
            "exists": True,
            "uid": row.pw_uid,
            "gid": row.pw_gid,
            "home": row.pw_dir,
            "shell": row.pw_shell,
        }
    except KeyError:
        return {"exists": False}


def command_inventory(names: list[str]) -> dict[str, str | None]:
    return {name: shutil.which(name) for name in names}


def device_records() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for p in sorted(pathlib.Path("/dev").glob("nvidia*")):
        try:
            s = p.stat()
            rows.append(
                {
                    "path": str(p),
                    "mode": stat.filemode(s.st_mode),
                    "mode_octal": oct(stat.S_IMODE(s.st_mode)),
                    "owner": pwd.getpwuid(s.st_uid).pw_name,
                    "group": grp.getgrgid(s.st_gid).gr_name,
                    "major": os.major(s.st_rdev) if stat.S_ISCHR(s.st_mode) else None,
                    "minor": os.minor(s.st_rdev) if stat.S_ISCHR(s.st_mode) else None,
                }
            )
        except OSError as exc:
            rows.append({"path": str(p), "error": str(exc)})
    return rows


def filtered_resolv_conf() -> list[str]:
    text = read_text("/etc/resolv.conf") or ""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
        and line.split(maxsplit=1)[0] in {"nameserver", "search", "options"}
    ]


def main() -> int:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    default_root = (
        pathlib.Path.home()
        / "adamArchives"
        / "Adam"
        / "workspace-control-tmp"
        / f"lambda-runner-host-probe-{stamp}"
    )
    out_dir = pathlib.Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_root
    out_dir.mkdir(parents=True, exist_ok=False)
    report_path = out_dir / "lambda-runner-host-probe.json"

    facts: dict[str, object] = {
        "schema_version": 1,
        "probe": "workspace-lambda-self-hosted-execution-v1:P0_HOST_PROBE",
        "timestamp_utc": now.isoformat(),
        "writes_performed": [
            str(out_dir),
            str(report_path),
        ],
        "host": {
            "hostname": socket.gethostname(),
            "uname": run(["uname", "-a"]),
            "os_release": read_text("/etc/os-release"),
            "systemd": run(["systemd", "--version"]),
            "cgroup_controllers": read_text("/sys/fs/cgroup/cgroup.controllers"),
            "cgroup_type": (
                "v2"
                if pathlib.Path("/sys/fs/cgroup/cgroup.controllers").exists()
                else "unknown_or_v1"
            ),
            "unprivileged_userns_clone": read_text("/proc/sys/kernel/unprivileged_userns_clone"),
            "unprivileged_userfaultfd": read_text("/proc/sys/vm/unprivileged_userfaultfd"),
        },
        "capacity": {
            "cpu_count": os.cpu_count(),
            "lscpu": run(["lscpu"]),
            "memory": run(["free", "-b"]),
            "filesystems": [
                path_record("/"),
                path_record("/home"),
                path_record("/home/atrott"),
                path_record("/srv"),
                path_record("/tmp"),
            ],
        },
        "gpu": {
            "inventory": run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,uuid,name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ]
            ),
            "compute_processes": run(
                [
                    "nvidia-smi",
                    "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                    "--format=csv,noheader,nounits",
                ]
            ),
            "topology": run(["nvidia-smi", "topo", "-m"]),
            "devices": device_records(),
        },
        "accounts": {
            "current": run(["id"]),
            "ci_research_engine": account_record("ci-research-engine"),
            "docker_group": run(["getent", "group", "docker"]),
            "docker_socket": path_record("/var/run/docker.sock"),
        },
        "network": {
            "resolv_conf": filtered_resolv_conf(),
            "resolvectl": run(["resolvectl", "status"]),
            "listeners_tcp": run(["ss", "-H", "-lnt"]),
            "listeners_udp": run(["ss", "-H", "-lnu"]),
        },
        "project_paths": [
            path_record("/home/atrott/adamArchives/Adam/workspace-control"),
            path_record("/home/atrott/adamArchives/Adam/research-engine"),
            path_record("/home/atrott/adamArchives/Adam/.research-engine"),
            path_record("/home/atrott/adamArchives/Adam/workspace-control-tmp"),
        ],
        "commands": command_inventory(
            [
                "bash",
                "curl",
                "git",
                "tar",
                "gzip",
                "python3",
                "jq",
                "systemctl",
                "systemd-run",
                "systemd-analyze",
                "runuser",
                "setpriv",
                "useradd",
                "nft",
                "iptables",
                "ss",
                "nvidia-smi",
                "psql",
                "pg_config",
                "initdb",
                "pg_ctl",
                "docker",
                "podman",
            ]
        ),
        "mounts": run(["findmnt", "-J", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS", "/", "/home", "/srv"]),
        "limits": run(["bash", "-lc", "ulimit -a"]),
        "runner_prereq_note": (
            "This probe does not install or register a GitHub runner and does not "
            "test root/system service mutation. Its purpose is to select safe "
            "sandbox/bootstrap settings for the next gate."
        ),
    }

    report_path.write_text(
        json.dumps(facts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    gpu_ok = facts["gpu"]["inventory"]["rc"] == 0  # type: ignore[index]
    systemd_ok = facts["host"]["systemd"]["rc"] == 0  # type: ignore[index]
    cgroup = facts["host"]["cgroup_type"]  # type: ignore[index]
    ci_exists = facts["accounts"]["ci_research_engine"]["exists"]  # type: ignore[index]

    print("=== LAMBDA RUNNER P0 HOST PROBE ===")
    print(f"REPORT={report_path}")
    print(f"SYSTEMD_AVAILABLE={str(systemd_ok).lower()}")
    print(f"CGROUP_TYPE={cgroup}")
    print(f"NVIDIA_SMI_AVAILABLE={str(gpu_ok).lower()}")
    print(f"CI_RESEARCH_ENGINE_USER_EXISTS={str(ci_exists).lower()}")
    print("HOST_MUTATION_PERFORMED=false")
    print("RUNNER_REGISTERED=false")
    print("RUNNER_SERVICE_INSTALLED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
