#!/usr/bin/env python3
"""Read-only host attestation for Workspace Shell MCP v1.

This script intentionally does not read secret file contents, process
environments, SSH material, API tokens, or browser credentials.  It records
only the host capabilities and path/process metadata needed to render a safe
installation plan.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import pwd
import grp
import shutil
import socket
import stat
import subprocess
import sys
import tempfile


PLANNED_USERS = (
    "workspace-shell-mcp",
    "workspace-shell-exec",
    "workspace-shell-tunnel",
)
PLANNED_GROUPS = (
    "workspace-shell-mcp",
    "workspace-shell-exec",
    "workspace-shell-tunnel",
)
PLANNED_UNITS = (
    "workspace-shell-job-launcher.service",
    "workspace-shell-root-broker.service",
    "workspace-shell-mcp.service",
    "workspace-shell-tunnel.service",
)
PLANNED_PATHS = (
    "/etc/workspace-shell",
    "/opt/workspace-shell",
    "/run/workspace-shell-control",
    "/var/lib/workspace-shell",
    "/srv/workspace-shell",
)


def run(argv, *, timeout=5):
    try:
        proc = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            close_fds=True,
            env={
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "TZ": "UTC",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
        return {
            "argv": list(argv),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[:8192],
            "stderr": proc.stderr.strip()[:8192],
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "argv": list(argv),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc)[:8192],
        }


def read_text(path, limit=4096):
    try:
        data = Path(path).read_text(encoding="utf-8", errors="replace")
        return data[:limit].strip()
    except OSError:
        return None


def path_meta(path):
    p = Path(path)
    try:
        st = os.lstat(p)
    except FileNotFoundError:
        return {"exists": False, "path": str(p)}
    kind = (
        "dir" if stat.S_ISDIR(st.st_mode)
        else "file" if stat.S_ISREG(st.st_mode)
        else "symlink" if stat.S_ISLNK(st.st_mode)
        else "socket" if stat.S_ISSOCK(st.st_mode)
        else "other"
    )
    return {
        "exists": True,
        "path": str(p),
        "type": kind,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode": format(stat.S_IMODE(st.st_mode), "04o"),
    }


def account_meta(name):
    try:
        entry = pwd.getpwnam(name)
    except KeyError:
        return {"exists": False, "name": name}
    return {
        "exists": True,
        "name": name,
        "uid": entry.pw_uid,
        "gid": entry.pw_gid,
        "home": entry.pw_dir,
        "shell": entry.pw_shell,
    }


def group_meta(name):
    try:
        entry = grp.getgrnam(name)
    except KeyError:
        return {"exists": False, "name": name}
    return {
        "exists": True,
        "name": name,
        "gid": entry.gr_gid,
        "members": list(entry.gr_mem),
    }


def command_meta(name, explicit=None):
    path = explicit or shutil.which(name)
    if not path:
        return {"exists": False, "name": name, "path": None}
    version_args = {
        "node": [path, "--version"],
        "python3": [path, "--version"],
        "git": [path, "--version"],
        "bwrap": [path, "--version"],
        "systemd-run": ["/usr/bin/systemd", "--version"],
        "openssl": [path, "version"],
        "tunnel-client": [path, "--version"],
    }
    result = run(version_args.get(name, [path, "--version"]))
    return {
        "exists": True,
        "name": name,
        "path": str(Path(path).resolve()),
        "version": (result["stdout"] or result["stderr"]).splitlines()[:1],
        "version_returncode": result["returncode"],
    }


def git_meta(source_root, source_sha):
    root = Path(source_root)
    result = {"path": str(root), "exists": root.is_dir()}
    if not root.is_dir():
        return result

    def git(*args):
        return run([
            "/usr/bin/git",
            "-C",
            str(root),
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "diff.external=",
            "-c",
            "credential.helper=",
            *args,
        ])

    result["head"] = git("rev-parse", "HEAD")
    result["tree"] = git("rev-parse", "HEAD^{tree}")
    result["status"] = git("status", "--porcelain=v1", "--untracked-files=normal")
    if source_sha:
        result["requested_sha"] = source_sha
        result["requested_sha_exists"] = git("cat-file", "-e", source_sha + "^{commit}")
    return result


def listener_meta(port):
    ss = shutil.which("ss")
    if not ss:
        return {"port": port, "ss_available": False, "occupied": None}
    result = run([ss, "-ltnH"], timeout=3)
    occupied = False
    matching = []
    if result["returncode"] == 0:
        suffix = f":{port}"
        for line in result["stdout"].splitlines():
            fields = line.split()
            if len(fields) >= 4 and fields[3].endswith(suffix):
                occupied = True
                matching.append(line[:512])
    return {
        "port": port,
        "ss_available": True,
        "occupied": occupied,
        "matching_listeners": matching,
    }


def systemd_unit_meta(unit):
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return {"unit": unit, "systemctl_available": False}
    result = run([
        systemctl,
        "show",
        unit,
        "--no-pager",
        "--property=LoadState",
        "--property=ActiveState",
        "--property=SubState",
        "--property=User",
        "--property=Group",
        "--property=FragmentPath",
    ])
    values = {}
    if result["returncode"] == 0:
        for line in result["stdout"].splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
    return {
        "unit": unit,
        "returncode": result["returncode"],
        "properties": values,
        "stderr": result["stderr"][:1024],
    }


def bwrap_probe(path):
    if not path:
        return {"attempted": False, "reason": "bwrap missing"}
    argv = [
        path,
        "--die-with-parent",
        "--unshare-all",
        "--cap-drop",
        "ALL",
        "--ro-bind", "/usr", "/usr",
    ]
    for candidate in ("/bin", "/lib", "/lib64"):
        if Path(candidate).exists():
            argv.extend(["--ro-bind", candidate, candidate])
    argv.extend([
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--", "/usr/bin/true",
    ])
    result = run(argv, timeout=5)
    return {
        "attempted": True,
        "returncode": result["returncode"],
        "stderr": result["stderr"][:2048],
        "passed": result["returncode"] == 0,
    }


def node_major(command):
    version = (command.get("version") or [""])[0]
    if version.startswith("v"):
        version = version[1:]
    try:
        return int(version.split(".", 1)[0])
    except (ValueError, IndexError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default="/home/atrott/adamArchives/Adam/workspace-control",
    )
    parser.add_argument("--source-sha")
    parser.add_argument(
        "--heartbeat-node",
        default="/home/atrott/miniforge3/envs/workspace-heartbeat-node/bin/node",
    )
    parser.add_argument(
        "--heartbeat-node-modules",
        default="/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v048/plugins/workspace-heartbeat/node_modules",
    )
    parser.add_argument(
        "--tunnel-client",
        default="/home/atrott/adamArchives/Adam/tooling/openai-tunnel-client/v0.0.18/unpacked/tunnel-client",
    )
    parser.add_argument("--port", type=int, default=8797)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    commands = {
        "python3": command_meta("python3"),
        "git": command_meta("git"),
        "bwrap": command_meta("bwrap"),
        "systemd-run": command_meta("systemd-run"),
        "openssl": command_meta("openssl"),
        "node": command_meta("node", args.heartbeat_node),
        "tunnel-client": command_meta("tunnel-client", args.tunnel_client),
    }

    cgroup_controllers = read_text("/sys/fs/cgroup/cgroup.controllers")
    userns_clone = read_text("/proc/sys/kernel/unprivileged_userns_clone")
    max_userns = read_text("/proc/sys/user/max_user_namespaces")
    lsm = read_text("/sys/kernel/security/lsm")
    apparmor = read_text("/sys/module/apparmor/parameters/enabled")
    selinux = read_text("/sys/fs/selinux/enforce")

    source = git_meta(args.source_root, args.source_sha)
    listener = listener_meta(args.port)
    bwrap = bwrap_probe(commands["bwrap"]["path"] if commands["bwrap"]["exists"] else None)

    blockers = []
    provisioning_requirements = []
    for required in ("python3", "git", "systemd-run", "openssl"):
        if not commands[required]["exists"]:
            blockers.append(f"missing required base-host command: {required}")
    for staged in ("bwrap", "node", "tunnel-client"):
        if not commands[staged]["exists"]:
            provisioning_requirements.append(f"stage required runtime dependency: {staged}")
    if node_major(commands["node"]) is not None and node_major(commands["node"]) < 20:
        blockers.append("Node runtime is older than v20")
    if cgroup_controllers is None:
        blockers.append("cgroup v2 controllers file is unavailable")
    if not source.get("exists"):
        blockers.append("workspace-control source repository is missing")
    if args.source_sha and source.get("requested_sha_exists", {}).get("returncode") != 0:
        blockers.append("requested source SHA is absent from the local source repository")
    if listener.get("occupied") is True:
        blockers.append(f"planned loopback port {args.port} is already occupied")
    if bwrap.get("attempted") and not bwrap.get("passed"):
        blockers.append("bubblewrap exists but namespace probe failed")

    evidence = {
        "schema": "workspace-shell-host-attestation.v1",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "effective_identity": {
            "uid": os.geteuid(),
            "gid": os.getegid(),
            "user": pwd.getpwuid(os.geteuid()).pw_name,
        },
        "commands": commands,
        "kernel": {
            "uname": list(os.uname()),
            "cgroup_v2_controllers": cgroup_controllers,
            "unprivileged_userns_clone": userns_clone,
            "max_user_namespaces": max_userns,
            "lsm": lsm,
            "apparmor_enabled": apparmor,
            "selinux_enforce": selinux,
        },
        "bwrap_probe": bwrap,
        "source": source,
        "dependency_source": path_meta(args.heartbeat_node_modules),
        "planned_listener": listener,
        "planned_users": [account_meta(name) for name in PLANNED_USERS],
        "planned_groups": [group_meta(name) for name in PLANNED_GROUPS],
        "planned_paths": [path_meta(path) for path in PLANNED_PATHS],
        "planned_units": [systemd_unit_meta(unit) for unit in PLANNED_UNITS],
        "heartbeat_listener": listener_meta(8787),
        "blockers": blockers,
        "provisioning_requirements": provisioning_requirements,
        "decision": "READY_FOR_INSTALL_PLAN" if not blockers else "BLOCKED",
        "secret_policy": {
            "process_environments_read": False,
            "secret_file_contents_read": False,
            "ssh_material_read": False,
            "api_tokens_read": False,
        },
    }

    print(json.dumps(evidence, indent=2, sort_keys=True))
    if args.strict and blockers:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
