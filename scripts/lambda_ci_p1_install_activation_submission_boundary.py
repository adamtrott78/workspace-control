#!/usr/bin/env python3
"""Install the reviewed P1 activation submission boundary without activating it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import socket
import subprocess
import tempfile
import time
from typing import Any

EXPECTED_HELPER = pathlib.Path(
    "scripts/lambda_ci_p1_install_activation_submission_boundary.py"
)
SOURCE_ROOT = pathlib.Path("scripts/lambda_ci_reconciler.py")
SOURCE_CONTROLLER = pathlib.Path("scripts/lambda_ci_reconcile_controller.py")
SOURCE_ONCE_UNIT = pathlib.Path(
    "systemd/workspace-ci-reconcile-controller-once.service"
)
INSTALLED_ROOT = pathlib.Path(
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"
)
INSTALLED_CONTROLLER = pathlib.Path(
    "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py"
)
INSTALLED_ONCE_UNIT = pathlib.Path(
    "/etc/systemd/system/workspace-ci-reconcile-controller-once.service"
)
ROOT_SERVICE = "workspace-ci-reconciler.service"
AUTO_CONTROLLER = "workspace-ci-reconcile-controller.service"
ONCE_SERVICE = "workspace-ci-reconcile-controller-once.service"
WORKSPACE_CPU = "workspace-ci-controller@workspace-control-cpu.service"
PRESERVED = [
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
    "workspace-ci-controller@research-engine-cpu.service",
    "workspace-ci-controller@research-engine-gpu.service",
]
ROOT_SOCKET = pathlib.Path("/run/workspace-ci/reconciler.sock")
EXPECTED_OLD_ROOT_SHA256 = (
    "5e3c56c84f8e9755334ca4f0db7bdd7036f70b3e4cd404ebb02e8aa6b97185a9"
)
EXPECTED_OLD_CONTROLLER_GIT_BLOB_SHA = (
    "cdb38af360676abb053c1d171cc4dc3ef39e977a"
)

class BoundaryInstallError(RuntimeError):
    pass

def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise BoundaryInstallError(
            f"command failed rc={proc.returncode}: {argv!r}: {proc.stderr.strip()}"
        )
    return proc

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())

def git_blob_sha(raw: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(raw)}\0".encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()

def attest_source(expected_head: str, invoker: str) -> pathlib.Path:
    helper = pathlib.Path(__file__).resolve()
    repo = helper.parents[1]
    if helper != (repo / EXPECTED_HELPER).resolve():
        raise BoundaryInstallError("executing helper is outside reviewed tracked path")
    prefix = ["/usr/sbin/runuser", "-u", invoker, "--", "git", "-C", str(repo)]
    if run([*prefix, "rev-parse", "--show-toplevel"]).stdout.strip() != str(repo):
        raise BoundaryInstallError("reviewed repository top-level mismatch")
    head = run([*prefix, "rev-parse", "HEAD"]).stdout.strip()
    if head != expected_head:
        raise BoundaryInstallError(
            f"HEAD mismatch: actual={head} expected={expected_head}"
        )
    if run([*prefix, "status", "--porcelain=v1", "--untracked-files=no"]).stdout.strip():
        raise BoundaryInstallError("reviewed tracked tree is dirty")
    if run([*prefix, "ls-files", "--error-unmatch", str(EXPECTED_HELPER)], check=False).returncode != 0:
        raise BoundaryInstallError("executing helper is not tracked")
    return repo

def snapshot(service: str) -> dict[str, str]:
    props = [
        "LoadState", "ActiveState", "SubState", "UnitFileState",
        "NRestarts", "ExecMainStatus", "MainPID", "InvocationID",
    ]
    out = run(
        ["systemctl", "show", service, *[f"--property={p}" for p in props]]
    ).stdout
    result = {}
    for line in out.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    if set(result) != set(props):
        raise BoundaryInstallError(f"incomplete service snapshot: {service}: {result}")
    return result

def require_frozen_auto() -> dict[str, str]:
    value = snapshot(AUTO_CONTROLLER)
    if (
        value["LoadState"] != "loaded"
        or value["ActiveState"] != "inactive"
        or value["SubState"] != "dead"
        or value["MainPID"] != "0"
    ):
        raise BoundaryInstallError(f"automatic reconcile controller is not frozen: {value}")
    return value

def require_workspace_dormant() -> dict[str, str]:
    value = snapshot(WORKSPACE_CPU)
    if (
        value["LoadState"] != "loaded"
        or value["ActiveState"] != "inactive"
        or value["SubState"] != "dead"
        or value["MainPID"] != "0"
        or value["UnitFileState"] != "disabled"
    ):
        raise BoundaryInstallError(f"workspace-control CPU is not dormant: {value}")
    return value

def require_root_healthy() -> dict[str, str]:
    value = snapshot(ROOT_SERVICE)
    if (
        value["ActiveState"] != "active"
        or value["SubState"] != "running"
        or value["ExecMainStatus"] != "0"
        or value["MainPID"] == "0"
    ):
        raise BoundaryInstallError(f"root reconciler is not healthy: {value}")
    return value

def wait_socket() -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.25)
        try:
            client.connect(str(ROOT_SOCKET))
            return
        except OSError:
            time.sleep(0.1)
        finally:
            client.close()
    raise BoundaryInstallError("root reconciler AF_UNIX socket is not ready")

def atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = pathlib.Path(tmp_raw)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()

def certify_preserved(
    auto_before: dict[str, str],
    workspace_before: dict[str, str],
    siblings_before: dict[str, dict[str, str]],
) -> None:
    if snapshot(AUTO_CONTROLLER) != auto_before:
        raise BoundaryInstallError("automatic reconcile controller changed")
    if snapshot(WORKSPACE_CPU) != workspace_before:
        raise BoundaryInstallError("workspace-control CPU changed")
    for service, before in siblings_before.items():
        if snapshot(service) != before:
            raise BoundaryInstallError(f"preserved sibling changed: {service}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise BoundaryInstallError("installer must run as root via sudo")
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        raise BoundaryInstallError("installer requires a non-root sudo invoker")
    pwd.getpwnam(invoker)

    repo = attest_source(args.expected_head, invoker)
    src_root = (repo / SOURCE_ROOT).read_bytes()
    src_controller = (repo / SOURCE_CONTROLLER).read_bytes()
    src_unit = (repo / SOURCE_ONCE_UNIT).read_bytes()

    if sha256_path(INSTALLED_ROOT) != EXPECTED_OLD_ROOT_SHA256:
        raise BoundaryInstallError("installed root reconciler baseline mismatch")
    if git_blob_sha(INSTALLED_CONTROLLER.read_bytes()) != EXPECTED_OLD_CONTROLLER_GIT_BLOB_SHA:
        raise BoundaryInstallError("installed reconcile-controller baseline mismatch")
    if INSTALLED_ONCE_UNIT.exists():
        raise BoundaryInstallError("one-shot reconcile unit already exists")

    root_before = require_root_healthy()
    auto_before = require_frozen_auto()
    workspace_before = require_workspace_dormant()
    siblings_before = {service: snapshot(service) for service in PRESERVED}

    old_root = INSTALLED_ROOT.read_bytes()
    old_controller = INSTALLED_CONTROLLER.read_bytes()
    mutated = False
    try:
        atomic_write(INSTALLED_ROOT, src_root, 0o755)
        atomic_write(INSTALLED_CONTROLLER, src_controller, 0o755)
        atomic_write(INSTALLED_ONCE_UNIT, src_unit, 0o644)
        mutated = True
        run(["systemctl", "daemon-reload"])
        run([
            "systemctl", "--job-mode=ignore-dependencies",
            "restart", ROOT_SERVICE,
        ])
        wait_socket()
        root_after = require_root_healthy()
        certify_preserved(auto_before, workspace_before, siblings_before)

        unit = snapshot(ONCE_SERVICE)
        if (
            unit["LoadState"] != "loaded"
            or unit["ActiveState"] != "inactive"
            or unit["SubState"] != "dead"
            or unit["MainPID"] != "0"
            or unit["UnitFileState"] != "static"
        ):
            raise BoundaryInstallError(f"one-shot unit is not static/inactive: {unit}")
        if sha256_path(INSTALLED_ROOT) != sha256_bytes(src_root):
            raise BoundaryInstallError("root reconciler install digest mismatch")
        if sha256_path(INSTALLED_CONTROLLER) != sha256_bytes(src_controller):
            raise BoundaryInstallError("reconcile-controller install digest mismatch")
        if sha256_path(INSTALLED_ONCE_UNIT) != sha256_bytes(src_unit):
            raise BoundaryInstallError("one-shot unit install digest mismatch")

        receipt = {
            "schema_version": 1,
            "status": "P1_ACTIVATION_SUBMISSION_BOUNDARY_INSTALLED",
            "source_head": args.expected_head,
            "installed": {
                "root_reconciler_sha256": sha256_bytes(src_root),
                "reconcile_controller_sha256": sha256_bytes(src_controller),
                "one_shot_unit_sha256": sha256_bytes(src_unit),
            },
            "root_before": root_before,
            "root_after": root_after,
            "automatic_reconcile_controller": auto_before,
            "workspace_control_cpu": workspace_before,
            "preserved_siblings": siblings_before,
            "one_shot_unit": unit,
            "automatic_workflow_triggered": False,
            "activation_performed": False,
        }
        print(
            "P1_ACTIVATION_SUBMISSION_BOUNDARY_RECEIPT="
            + json.dumps(receipt, sort_keys=True)
        )
        return 0
    except Exception as exc:
        if not mutated:
            raise
        rollback_errors = []
        try:
            atomic_write(INSTALLED_ROOT, old_root, 0o755)
            atomic_write(INSTALLED_CONTROLLER, old_controller, 0o755)
            if INSTALLED_ONCE_UNIT.exists():
                INSTALLED_ONCE_UNIT.unlink()
            run(["systemctl", "daemon-reload"])
            run([
                "systemctl", "--job-mode=ignore-dependencies",
                "restart", ROOT_SERVICE,
            ])
            wait_socket()
            require_root_healthy()
            certify_preserved(auto_before, workspace_before, siblings_before)
        except Exception as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            raise BoundaryInstallError(
                f"boundary install failed and rollback incomplete: "
                f"original={type(exc).__name__}:{exc}; "
                f"rollback={'; '.join(rollback_errors)}"
            ) from exc
        raise BoundaryInstallError(
            f"boundary install failed and rollback completed: "
            f"{type(exc).__name__}:{exc}"
        ) from exc

if __name__ == "__main__":
    raise SystemExit(main())
