#!/usr/bin/env python3
"""Read-only live-host preflight for GitRunner P1 activation.

This helper intentionally performs no installation, service mutation, reconciliation,
workflow trigger, or filesystem write. It may be run via sudo so root-owned metadata
can be inspected, but all Git identity checks are executed as the invoking operator.

Untracked files are reported but do not fail the preflight. Modified/deleted tracked
files fail closed because they can change the reviewed source being inspected.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pathlib
import pwd
import subprocess
import sys
from datetime import datetime, timezone
from typing import Iterable

SERVICES = [
    "workspace-ci-provisioner.service",
    "workspace-ci-reconciler.service",
    "workspace-ci-reconcile-controller.service",
    "workspace-ci-controller@research-engine-cpu.service",
    "workspace-ci-controller@research-engine-gpu.service",
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
    "workspace-ci-controller@workspace-control-cpu.service",
    "workspace-ci-maintenance.service",
    "workspace-ci-maintenance-controller.service",
    "workspace-ci-controller.service",
    "workspace-ci-controller-gpu.service",
]

IDENTITIES = [
    "ci-controller",
    "ci-reconciler",
    "ci-maintenance",
    "ci-research-engine",
    "ci-padataset",
    "ci-workspace-control",
]

TOKEN_PATHS = [
    "/var/lib/workspace-ci/controller/github-token",
    "/var/lib/workspace-ci/reconcile-controller/github-token",
    "/var/lib/workspace-ci/maintenance-controller/github-read-token",
    "/var/lib/workspace-ci/maintenance-controller/runner-token",
]

INSTALLED_FILES = [
    "/opt/workspace-ci/controller/lambda-ci-controller",
    "/opt/workspace-ci/provisioner/lambda_ci_admission.py",
    "/opt/workspace-ci/provisioner/lambda_ci_multirepo.py",
    "/opt/workspace-ci/provisioner/lambda_ci_provisioner.py",
    "/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py",
    "/opt/workspace-ci/provisioner/lambda_ci_runtime.py",
    "/opt/workspace-ci/reconciler/lambda_ci_multirepo.py",
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py",
    "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py",
    "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py",
    "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py",
    "/etc/systemd/system/workspace-ci-controller@.service",
    "/etc/systemd/system/workspace-ci-reconciler.service",
    "/etc/systemd/system/workspace-ci-reconcile-controller.service",
    "/etc/systemd/system/workspace-ci-maintenance.service",
    "/etc/systemd/system/workspace-ci-maintenance-controller.service",
    "/etc/tmpfiles.d/workspace-ci.conf",
    "/etc/sysusers.d/workspace-ci.conf",
    "/etc/workspace-ci/lambda-ci-project-registry.v1.json",
    "/etc/workspace-ci/lambda-ci-execution-contracts.v1.json",
    "/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json",
    "/etc/workspace-ci/lambda-ci-systemd-profiles.v1.json",
    "/etc/workspace-ci/lambda-ci-upstream-pins.v1.json",
    "/etc/workspace-ci/lambda-ci-workload-policy.v1.json",
    "/etc/workspace-ci/projects/research-engine.json",
    "/etc/workspace-ci/projects/padataset.json",
    "/etc/workspace-ci/projects/workspace-control.json",
]

STATE_PATHS = [
    "/srv/workspace-ci",
    "/srv/workspace-ci/research-engine",
    "/srv/workspace-ci/padataset",
    "/srv/workspace-ci/workspace-control",
    "/var/lib/workspace-ci/controller",
    "/var/lib/workspace-ci/controller/state",
    "/var/lib/workspace-ci/reconciler",
    "/var/lib/workspace-ci/reconcile-controller",
    "/var/lib/workspace-ci/maintenance",
    "/var/lib/workspace-ci/maintenance-controller",
]

ALLOWLISTED_ENV_PREFIXES = (
    "WORKSPACE_CI_ADMISSION_V2_ENABLED=",
    "WORKSPACE_CI_GITHUB_URL=",
    "WORKSPACE_CI_LANE=",
    "WORKSPACE_CI_CONTROLLER_STATE_ROOT=",
    "WORKSPACE_CI_PROJECT_ID=",
    "WORKSPACE_CI_PROVISIONER_SOCKET=",
    "WORKSPACE_CI_RUNNER_PREFIX=",
    "WORKSPACE_CI_SCALESET_NAME=",
)


def run(argv: list[str], *, user: str | None = None) -> subprocess.CompletedProcess[str]:
    command = argv
    if user is not None:
        command = ["runuser", "-u", user, "--", *argv]
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def emit_run(argv: list[str]) -> None:
    p = run(argv)
    if p.stdout:
        print(p.stdout.rstrip())
    if p.stderr:
        print(p.stderr.rstrip())
    if p.returncode:
        print(f"RC={p.returncode} ARGV={json.dumps(argv)}")


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def owner_group_mode(path: pathlib.Path) -> str:
    st = path.stat()
    return (
        f"owner={pwd.getpwuid(st.st_uid).pw_name} "
        f"group={grp.getgrgid(st.st_gid).gr_name} "
        f"mode={st.st_mode & 0o777:o} "
        f"size={st.st_size}"
    )


def print_json_semantics(path: pathlib.Path) -> None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"{path}=UNREADABLE_JSON:{type(exc).__name__}:{exc}")
        return
    if path.name == "lambda-ci-project-registry.v1.json":
        print("registry_status=", value.get("status"))
        print("registry_epoch=", value.get("registry_epoch"))
        for project_id, entry in sorted(value.get("projects", {}).items()):
            print(
                "registry_project",
                project_id,
                "activation_state=", entry.get("activation_state"),
                "lanes=", entry.get("lanes"),
            )
        return
    routes = {
        key: route.get("activation_state")
        for key, route in value.get("routes", {}).items()
        if isinstance(route, dict)
    }
    print(
        "manifest",
        path.name,
        "project_id=", value.get("project_id"),
        "status=", value.get("status"),
        "concurrency=", value.get("concurrency"),
        "routes=", routes,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("ERROR=ROOT_REQUIRED_RUN_VIA_SUDO", file=sys.stderr)
        return 70
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        print("ERROR=RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT", file=sys.stderr)
        return 70

    repo_proc = run(["git", "rev-parse", "--show-toplevel"], user=invoker)
    if repo_proc.returncode:
        print("ERROR=NOT_IN_GIT_REPO", file=sys.stderr)
        return 70
    repo = pathlib.Path(repo_proc.stdout.strip()).resolve()

    head_proc = run(["git", "-C", str(repo), "rev-parse", "HEAD"], user=invoker)
    if head_proc.returncode:
        print("ERROR=HEAD_READ_FAILED", file=sys.stderr)
        return 70
    head = head_proc.stdout.strip()
    print(f"repo={repo}")
    print(f"head={head}")
    if head != args.expected_head:
        print(f"ERROR=UNEXPECTED_HEAD expected={args.expected_head} actual={head}")
        return 70

    tracked = run(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
        user=invoker,
    )
    if tracked.returncode:
        print("ERROR=TRACKED_STATUS_FAILED")
        return 70
    if tracked.stdout.strip():
        print("ERROR=TRACKED_WORKTREE_DIRTY")
        print(tracked.stdout.rstrip())
        return 70

    untracked = run(
        ["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard"],
        user=invoker,
    )
    print("TRACKED_REVIEWED_SOURCE=PASS")
    if untracked.stdout.strip():
        print("UNTRACKED_FILES_PRESENT=INFORMATIONAL_ONLY")
        print(untracked.stdout.rstrip())
    else:
        print("UNTRACKED_FILES_PRESENT=NO")

    print()
    print("========== P1 LAMBDA READ-ONLY PREFLIGHT ==========")
    print("timestamp_utc=", datetime.now(timezone.utc).isoformat())
    print("hostname=", os.uname().nodename)

    print()
    print("=== TOOLCHAIN ===")
    go = pathlib.Path("/opt/workspace-ci/go/1.26.3/bin/go")
    if go.is_file():
        emit_run([str(go), "version"])
    else:
        print("GO_1_26_3=MISSING")
    emit_run(["systemd", "--version"])

    print()
    print("=== IDENTITIES ===")
    for name in IDENTITIES:
        try:
            row = pwd.getpwnam(name)
        except KeyError:
            print(f"{name}=MISSING")
            continue
        print(
            f"{name}=PRESENT uid={row.pw_uid} gid={row.pw_gid} "
            f"home={row.pw_dir} shell={row.pw_shell}"
        )
        emit_run(["id", name])

    print()
    print("=== SERVICE STATE / SANDBOX ===")
    properties = [
        "LoadState", "ActiveState", "SubState", "UnitFileState", "NRestarts",
        "ExecMainPID", "ExecMainStatus", "FragmentPath", "DropInPaths", "User",
        "Group", "ProtectSystem", "ProtectHome", "PrivateDevices", "DevicePolicy",
        "ReadOnlyPaths", "ReadWritePaths", "InaccessiblePaths",
        "CPUQuotaPerSecUSec", "MemoryHigh", "MemoryMax", "RuntimeMaxUSec",
    ]
    for service in SERVICES:
        print(f"--- {service}")
        p = run(["systemctl", "show", service, "--no-pager", *sum((["-p", x] for x in properties), [])])
        if p.stdout:
            print(p.stdout.rstrip())
        if p.stderr:
            print(p.stderr.rstrip())
        if p.returncode:
            print(f"SYSTEMCTL_SHOW_RC={p.returncode}")

    print()
    print("=== ACTIVE WORKSPACE-CI UNITS ===")
    emit_run(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "workspace-ci-*"])

    print()
    print("=== SOCKET METADATA ===")
    socket_root = pathlib.Path("/run/workspace-ci")
    if not socket_root.is_dir():
        print("/run/workspace-ci=MISSING")
    else:
        print(f"{socket_root} {owner_group_mode(socket_root)}")
        for child in sorted(socket_root.iterdir()):
            if child.is_socket() or child.is_file():
                try:
                    print(f"{child} {owner_group_mode(child)}")
                except FileNotFoundError:
                    pass

    print()
    print("=== CREDENTIAL METADATA ONLY — CONTENTS NOT READ ===")
    for raw in TOKEN_PATHS:
        path = pathlib.Path(raw)
        if not path.exists():
            print(f"{path}=MISSING")
        else:
            print(f"{path} {owner_group_mode(path)}")

    print()
    print("=== INSTALLED CONTROL-PLANE HASHES ===")
    for raw in INSTALLED_FILES:
        path = pathlib.Path(raw)
        if not path.is_file():
            print(f"{path}=MISSING")
        else:
            print(f"{sha256(path)}  {path}")
            print(f"  {owner_group_mode(path)}")

    print()
    print("=== INSTALLED REGISTRY / PROJECT SEMANTICS ===")
    registry = pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json")
    if registry.is_file():
        print_json_semantics(registry)
    else:
        print("REGISTRY=MISSING")
    projects = pathlib.Path("/etc/workspace-ci/projects")
    if projects.is_dir():
        for path in sorted(projects.glob("*.json")):
            print_json_semantics(path)
    else:
        print("/etc/workspace-ci/projects=MISSING")

    print()
    print("=== CONTROLLER ENV — NONSECRET ALLOWLIST ONLY ===")
    controllers = pathlib.Path("/etc/workspace-ci/controllers")
    if not controllers.is_dir():
        print("/etc/workspace-ci/controllers=MISSING")
    else:
        for path in sorted(controllers.glob("*.env")):
            print(f"--- {path}")
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except Exception as exc:
                print(f"UNREADABLE:{type(exc).__name__}:{exc}")
                continue
            for line in lines:
                if line.startswith(ALLOWLISTED_ENV_PREFIXES):
                    print(line)

    print()
    print("=== PROJECT / CONTROL STATE DIRECTORY METADATA ===")
    for raw in STATE_PATHS:
        path = pathlib.Path(raw)
        if not path.exists():
            print(f"{path}=MISSING")
        else:
            print(f"{path} {owner_group_mode(path)}")

    print()
    print("=== EFFECTIVE GENERIC CONTROLLER UNIT ===")
    emit_run(["systemctl", "cat", "workspace-ci-controller@research-engine-cpu.service", "--no-pager"])

    print()
    print("========== PREFLIGHT RESULT ==========")
    print("P1_LAMBDA_HOST_PREFLIGHT=COMPLETE_READ_ONLY")
    print("NO_INSTALL_RESTART_RECONCILE_ACTIVATE_TRIGGER_PERFORMED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
