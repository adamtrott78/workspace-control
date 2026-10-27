#!/usr/bin/env python3
"""One-shot source-bound installer for the P1 activation-delta reconciler hotfix.

This helper may replace only the installed root reconciler Python service and
restart only workspace-ci-reconciler.service with dependency propagation
suppressed. It preserves the frozen automatic reconcile controller, the
successful preactivation diagnose receipt/cursor, workspace-control dormancy,
and every project-controller state. On any failure after replacement, it
restores the exact prior reconciler bytes and re-certifies the same invariants.
"""

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
    "scripts/lambda_ci_p1_install_activation_delta_reconciler_hotfix.py"
)
SOURCE_SERVICE = pathlib.Path("scripts/lambda_ci_reconciler.py")
INSTALLED_SERVICE = pathlib.Path(
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"
)
ROOT_SERVICE = "workspace-ci-reconciler.service"
CONTROLLER_SERVICE = "workspace-ci-reconcile-controller.service"
ROOT_SOCKET = pathlib.Path("/run/workspace-ci/reconciler.sock")
CURSOR = pathlib.Path("/var/lib/workspace-ci/maintenance-controller/cursor.json")
DIAGNOSE_RECEIPT = pathlib.Path(
    "/var/lib/workspace-ci/maintenance-controller/receipts/6438723476.json"
)
REGISTRY = pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json")
MANIFEST = pathlib.Path("/etc/workspace-ci/projects/workspace-control.json")
EXPECTED_OLD_SERVICE_SHA256 = (
    "c424e62c20cd38fa0380d315e4cf28831ce63ff63dd7aa9711913a41c405fcc6"
)
EXPECTED_COMMENT_ID = 6438723476
EXPECTED_COMMAND_SHA256 = (
    "93488cdfc9ed7e2b36de40db40a02d7ebcf55b8698eff6ad4ba861e7eb5e3a56"
)
RESEARCH_CPU = "workspace-ci-controller@research-engine-cpu.service"
HEALTHY_CONTROLLERS = [
    "workspace-ci-controller@research-engine-gpu.service",
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
]
SOCKET_TIMEOUT_SECONDS = 5.0
SOCKET_POLL_SECONDS = 0.1


class HotfixError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    check: bool = True,
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = list(argv)
    if user is not None:
        command = ["/usr/sbin/runuser", "-u", user, "--", *command]
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise HotfixError(
            f"command failed rc={proc.returncode}: {command!r}: "
            f"{proc.stderr.strip()}"
        )
    return proc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def attest_source(expected_head: str, invoker: str) -> pathlib.Path:
    helper = pathlib.Path(__file__).resolve()
    try:
        repo = helper.parents[1]
    except IndexError as exc:
        raise HotfixError("helper is outside reviewed repository layout") from exc
    if helper != (repo / EXPECTED_HELPER).resolve():
        raise HotfixError("executing helper is outside reviewed tracked helper path")

    top = run(
        [
            "/usr/sbin/runuser",
            "-u",
            invoker,
            "--",
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--show-toplevel",
        ]
    ).stdout.strip()
    if pathlib.Path(top).resolve() != repo:
        raise HotfixError("reviewed repository top-level mismatch")
    head = run(
        [
            "/usr/sbin/runuser",
            "-u",
            invoker,
            "--",
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()
    if head != expected_head:
        raise HotfixError(f"HEAD mismatch: actual={head} expected={expected_head}")
    dirty = run(
        [
            "/usr/sbin/runuser",
            "-u",
            invoker,
            "--",
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "--untracked-files=no",
        ]
    ).stdout.strip()
    if dirty:
        raise HotfixError("reviewed tracked tree is dirty")
    tracked = run(
        [
            "/usr/sbin/runuser",
            "-u",
            invoker,
            "--",
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--error-unmatch",
            str(EXPECTED_HELPER),
        ],
        check=False,
    )
    if tracked.returncode != 0:
        raise HotfixError("executing helper is not tracked")
    return repo


def service_snapshot(service: str) -> dict[str, str]:
    props = [
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "NRestarts",
        "ExecMainStatus",
        "MainPID",
        "InvocationID",
    ]
    out = run(
        ["systemctl", "show", service, *[f"--property={p}" for p in props]]
    ).stdout
    value: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            key, raw = line.split("=", 1)
            value[key] = raw
    if set(value) != set(props):
        raise HotfixError(f"incomplete systemd snapshot for {service}: {value}")
    return value


def require_service_running(service: str) -> dict[str, str]:
    snap = service_snapshot(service)
    if (
        snap["LoadState"] != "loaded"
        or snap["ActiveState"] != "active"
        or snap["SubState"] != "running"
        or snap["ExecMainStatus"] != "0"
        or not snap["MainPID"].isdigit()
        or int(snap["MainPID"]) <= 0
        or not snap["InvocationID"]
    ):
        raise HotfixError(f"required service is not healthy: {service}: {snap}")
    return snap


def require_reconcile_controller_frozen() -> dict[str, str]:
    snap = service_snapshot(CONTROLLER_SERVICE)
    if (
        snap["LoadState"] != "loaded"
        or snap["ActiveState"] != "inactive"
        or snap["SubState"] != "dead"
        or snap["MainPID"] != "0"
    ):
        raise HotfixError(
            "automatic reconcile controller is not frozen: "
            f"{CONTROLLER_SERVICE}: {snap}"
        )
    return snap


def require_controller_baseline() -> dict[str, dict[str, str]]:
    observed: dict[str, dict[str, str]] = {}
    cpu = service_snapshot(RESEARCH_CPU)
    expected_cpu = {
        "LoadState": "loaded",
        "ActiveState": "inactive",
        "SubState": "dead",
        "UnitFileState": "enabled",
        "NRestarts": "12411",
        "ExecMainStatus": "1",
    }
    if any(cpu[key] != value for key, value in expected_cpu.items()):
        raise HotfixError(f"research-engine CPU preservation mismatch: {cpu}")
    observed[RESEARCH_CPU] = cpu

    for service in HEALTHY_CONTROLLERS:
        snap = service_snapshot(service)
        expected = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        if any(snap[key] != value for key, value in expected.items()):
            raise HotfixError(
                f"healthy controller baseline mismatch: {service}: {snap}"
            )
        observed[service] = snap
    return observed


def require_controller_dependency_graph() -> list[str]:
    proc = run(
        ["systemctl", "show", CONTROLLER_SERVICE, "--property=Requires", "--value"]
    )
    requires = sorted(value for value in proc.stdout.split() if value)
    if ROOT_SERVICE not in requires:
        raise HotfixError(
            "reconcile controller dependency graph does not require root "
            f"reconciler: {requires}"
        )
    return requires


def restart_root_without_dependency_propagation() -> None:
    run(
        [
            "systemctl",
            "--job-mode=ignore-dependencies",
            "restart",
            ROOT_SERVICE,
        ]
    )


def require_candidate_dormant() -> dict[str, str]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = registry.get("projects", {}).get("workspace-control")
    if not isinstance(entry, dict):
        raise HotfixError("workspace-control registry entry missing")
    if entry.get("activation_state") != "MIGRATION_CANDIDATE_NOT_INSTALLED":
        raise HotfixError("workspace-control registry state is not migration candidate")
    if manifest.get("project_id") != "workspace-control":
        raise HotfixError("workspace-control manifest identity mismatch")
    if manifest.get("status") != "MIGRATION_CANDIDATE_NOT_INSTALLED":
        raise HotfixError("workspace-control manifest state is not migration candidate")
    route = manifest.get("routes", {}).get("control-validation", {})
    if route.get("activation_state") != "PLANNED_NOT_BOUND":
        raise HotfixError("workspace-control route is not PLANNED_NOT_BOUND")

    active = run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            "workspace-ci-workspace-control-*.service",
        ],
        check=False,
    )
    if active.returncode != 0:
        raise HotfixError(
            "unable to inspect workspace-control execution units: "
            f"rc={active.returncode} stderr={active.stderr.strip()}"
        )
    for line in active.stdout.splitlines():
        parts = line.split()
        if (
            len(parts) >= 4
            and parts[1] == "loaded"
            and parts[2] in {"active", "activating", "deactivating"}
        ):
            raise HotfixError(f"workspace-control execution is active: {line}")
    return {
        "registry_state": entry["activation_state"],
        "manifest_state": manifest["status"],
        "route_state": route["activation_state"],
    }


def require_successful_diagnose_and_cursor() -> tuple[str, str]:
    receipt = json.loads(DIAGNOSE_RECEIPT.read_text(encoding="utf-8"))
    identity = receipt.get("identity", {})
    command = identity.get("command", {})
    result = receipt.get("result", {})
    if receipt.get("status") != "COMPLETED":
        raise HotfixError("preactivation diagnose receipt is not COMPLETED")
    if receipt.get("automatic_workflow_triggered") is not False:
        raise HotfixError("diagnose automatic workflow flag mismatch")
    if identity.get("comment_id") != EXPECTED_COMMENT_ID:
        raise HotfixError("diagnose receipt comment identity mismatch")
    if identity.get("command_sha256") != EXPECTED_COMMAND_SHA256:
        raise HotfixError("diagnose receipt command digest mismatch")
    if (
        identity.get("repository") != "adamtrott78/workspace-control"
        or identity.get("actor") != "adamtrott78"
    ):
        raise HotfixError("diagnose receipt source identity mismatch")
    if command != {
        "action": "diagnose",
        "lane": "cpu",
        "project_id": "workspace-control",
        "quarantine_receipt_id": None,
    }:
        raise HotfixError("diagnose receipt command mismatch")
    if (
        result.get("status") != "PASS"
        or result.get("operation") != "DIAGNOSE_LANE"
        or result.get("observation_only") is not True
        or result.get("service_active") is not False
        or result.get("active_project_units") != []
    ):
        raise HotfixError("preactivation diagnose result is not clean observation-only PASS")

    cursor = json.loads(CURSOR.read_text(encoding="utf-8"))
    if cursor.get("last_seen_comment_id") != EXPECTED_COMMENT_ID:
        raise HotfixError("maintenance cursor is not at successful diagnose comment")
    return sha256_path(DIAGNOSE_RECEIPT), canonical_sha256(cursor)


def socket_listener_ready(path: pathlib.Path) -> bool:
    if not path.is_socket():
        return False
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(SOCKET_POLL_SECONDS)
    try:
        conn.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        conn.close()


def wait_socket() -> None:
    deadline = time.monotonic() + SOCKET_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if socket_listener_ready(ROOT_SOCKET):
            return
        snap = service_snapshot(ROOT_SERVICE)
        if snap["ActiveState"] != "active":
            raise HotfixError(
                f"root reconciler exited before socket readiness: {snap}"
            )
        time.sleep(SOCKET_POLL_SECONDS)
    raise HotfixError("root reconciler socket listener readiness timeout")


def atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    fd, name = tempfile.mkstemp(
        prefix=f".{path.name}.hotfix-",
        dir=str(path.parent),
    )
    tmp = pathlib.Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("ERROR=ROOT_REQUIRED_RUN_VIA_SUDO")
        return 70
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        print("ERROR=RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT")
        return 70
    pwd.getpwnam(invoker)

    repo = attest_source(args.expected_head, invoker)
    source = repo / SOURCE_SERVICE
    source_bytes = source.read_bytes()
    source_sha = sha256_bytes(source_bytes)

    if sha256_path(INSTALLED_SERVICE) != EXPECTED_OLD_SERVICE_SHA256:
        raise HotfixError(
            "installed reconciler is not the exact reviewed pre-hotfix version"
        )

    root_before = require_service_running(ROOT_SERVICE)
    reconcile_controller_before = require_reconcile_controller_frozen()
    controller_requires = require_controller_dependency_graph()
    controllers_before = require_controller_baseline()
    candidate_before = require_candidate_dormant()
    receipt_hash, cursor_hash = require_successful_diagnose_and_cursor()
    old_bytes = INSTALLED_SERVICE.read_bytes()
    old_mode = INSTALLED_SERVICE.stat().st_mode & 0o777

    replaced = False
    try:
        atomic_write(INSTALLED_SERVICE, source_bytes, old_mode)
        replaced = True
        restart_root_without_dependency_propagation()
        wait_socket()

        if sha256_path(INSTALLED_SERVICE) != source_sha:
            raise HotfixError("installed reconciler hotfix digest mismatch")
        root_after = require_service_running(ROOT_SERVICE)
        reconcile_controller_after = require_reconcile_controller_frozen()
        if reconcile_controller_after != reconcile_controller_before:
            raise HotfixError(
                "automatic reconcile controller state/generation changed during hotfix"
            )
        if require_controller_dependency_graph() != controller_requires:
            raise HotfixError(
                "reconcile controller dependency graph changed during hotfix"
            )
        controllers_after = require_controller_baseline()
        candidate_after = require_candidate_dormant()
        receipt_hash_after, cursor_hash_after = require_successful_diagnose_and_cursor()
        if receipt_hash_after != receipt_hash or cursor_hash_after != cursor_hash:
            raise HotfixError(
                "successful diagnose receipt/cursor content changed during hotfix"
            )
        if controllers_after != controllers_before:
            raise HotfixError("project controller state changed during hotfix")
        if candidate_after != candidate_before:
            raise HotfixError("workspace-control candidate state changed during hotfix")

        result = {
            "schema_version": 1,
            "status": "PREACTIVATION_RECONCILER_DELTA_HOTFIX_INSTALLED",
            "source_head": args.expected_head,
            "source_sha256": source_sha,
            "old_installed_sha256": EXPECTED_OLD_SERVICE_SHA256,
            "installed_sha256": sha256_path(INSTALLED_SERVICE),
            "mutation": {
                "file": str(INSTALLED_SERVICE),
                "systemctl": [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    ROOT_SERVICE,
                ],
            },
            "root_before": root_before,
            "root_after": root_after,
            "reconcile_controller_before": reconcile_controller_before,
            "reconcile_controller_after": reconcile_controller_after,
            "project_controllers": controllers_after,
            "workspace_control": candidate_after,
            "diagnose_receipt_sha256": receipt_hash_after,
            "cursor_canonical_sha256": cursor_hash_after,
            "automatic_workflow_triggered": False,
        }
        print(
            "P1_PREACTIVATION_RECONCILER_DELTA_HOTFIX_RECEIPT="
            + json.dumps(result, sort_keys=True)
        )
        return 0
    except Exception as original:
        if replaced:
            print("P1_PREACTIVATION_RECONCILER_DELTA_HOTFIX_ROLLBACK=BEGIN")
            try:
                atomic_write(INSTALLED_SERVICE, old_bytes, old_mode)
                restart_root_without_dependency_propagation()
                wait_socket()
                if sha256_path(INSTALLED_SERVICE) != EXPECTED_OLD_SERVICE_SHA256:
                    raise HotfixError("rollback digest mismatch")
                require_service_running(ROOT_SERVICE)
                reconcile_controller_rollback = require_reconcile_controller_frozen()
                if reconcile_controller_rollback != reconcile_controller_before:
                    raise HotfixError(
                        "rollback changed automatic reconcile controller state/generation"
                    )
                if require_controller_dependency_graph() != controller_requires:
                    raise HotfixError(
                        "rollback changed reconcile controller dependency graph"
                    )
                if require_controller_baseline() != controllers_before:
                    raise HotfixError("rollback changed project controller state")
                if require_candidate_dormant() != candidate_before:
                    raise HotfixError(
                        "rollback changed workspace-control candidate state"
                    )
                receipt_hash_after, cursor_hash_after = (
                    require_successful_diagnose_and_cursor()
                )
                if receipt_hash_after != receipt_hash or cursor_hash_after != cursor_hash:
                    raise HotfixError(
                        "rollback changed successful diagnose receipt/cursor content"
                    )
            except Exception as rollback:
                print(
                    "P1_PREACTIVATION_RECONCILER_DELTA_HOTFIX_ROLLBACK=INCOMPLETE"
                )
                raise HotfixError(
                    "reconciler hotfix failed and rollback was incomplete: "
                    f"original={original}; rollback={rollback}"
                ) from original
            print("P1_PREACTIVATION_RECONCILER_DELTA_HOTFIX_ROLLBACK=COMPLETE")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
