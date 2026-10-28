#!/usr/bin/env python3
"""Install the reviewed legacy-state-root equivalence hotfix only."""

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

EXPECTED_HELPER = pathlib.Path(
    "scripts/lambda_ci_p1_install_legacy_state_root_equivalence_hotfix.py"
)
SOURCE_ROOT = pathlib.Path("scripts/lambda_ci_reconciler.py")

INSTALLED_ROOT = pathlib.Path(
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"
)
INSTALLED_RECONCILE_CONTROLLER = pathlib.Path(
    "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py"
)
INSTALLED_ONE_SHOT_UNIT = pathlib.Path(
    "/etc/systemd/system/workspace-ci-reconcile-controller-once.service"
)
INSTALLED_CONTROLLER_BINARY = pathlib.Path(
    "/opt/workspace-ci/controller/lambda-ci-controller"
)

RECONCILE_CONTROLLER_STATE = pathlib.Path(
    "/var/lib/workspace-ci/reconcile-controller"
)
LAST_REJECTED = RECONCILE_CONTROLLER_STATE / "last-rejected.json"
ARCHIVED_REJECTED = (
    RECONCILE_CONTROLLER_STATE
    / "last-rejected.pre-legacy-state-root-equivalence-hotfix.json"
)

ROOT_SERVICE = "workspace-ci-reconciler.service"
AUTO_CONTROLLER = "workspace-ci-reconcile-controller.service"
ONE_SHOT = "workspace-ci-reconcile-controller-once.service"
WORKSPACE_CPU = "workspace-ci-controller@workspace-control-cpu.service"
PRESERVED = [
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
    "workspace-ci-controller@research-engine-cpu.service",
    "workspace-ci-controller@research-engine-gpu.service",
]
ROOT_SOCKET = pathlib.Path("/run/workspace-ci/reconciler.sock")

EXPECTED_POLICY_SHA = "e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91"
EXPECTED_REQUEST_ID = "94e3e5ae-d1a7-541b-9185-7acb5c5b7103"
EXPECTED_WORKFLOW_RUN_ID = 40587498629
EXPECTED_OLD_ROOT_SHA256 = (
    "865cedf8f0d437f4e67f0d04d748e16d70fbc162708248dbef038b8afb4d29bd"
)
EXPECTED_RECONCILE_CONTROLLER_SHA256 = (
    "09130c0d8c8a83339b2110cb4a7163b2abd7d5ea18d423083b8437db038df34a"
)
EXPECTED_ONE_SHOT_UNIT_SHA256 = (
    "6e32ccf001161e17fdd3ad01abadfb44f57576b4d46ae9c3ebc102fb935fa69b"
)
EXPECTED_CONTROLLER_BINARY_SHA256 = (
    "6acd290f2312f0908d17443a2f5ee8d31711fbdb3f0bf9318171e9edd0ddee12"
)

EXPECTED_AUTO = {
    "LoadState": "loaded",
    "ActiveState": "inactive",
    "SubState": "dead",
    "UnitFileState": "enabled",
    "NRestarts": "0",
    "ExecMainStatus": "15",
    "MainPID": "0",
    "InvocationID": "294fcee8ea1548f8863d17680f21cf92",
}
EXPECTED_ONE_SHOT = {
    "LoadState": "loaded",
    "ActiveState": "failed",
    "SubState": "failed",
    "UnitFileState": "static",
    "NRestarts": "0",
    "ExecMainStatus": "70",
    "MainPID": "0",
    "InvocationID": "9659518ca16b4596a6936d72bd5e1e34",
}
EXPECTED_WORKSPACE_CPU = {
    "LoadState": "loaded",
    "ActiveState": "inactive",
    "SubState": "dead",
    "UnitFileState": "disabled",
    "NRestarts": "0",
    "ExecMainStatus": "0",
    "MainPID": "0",
    "InvocationID": "",
}
EXPECTED_SIBLINGS = {
    "workspace-ci-controller@padataset-cpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433911",
        "InvocationID": "264b5b8d1ff847d1873ebabdd0f466fd",
    },
    "workspace-ci-controller@padataset-gpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433913",
        "InvocationID": "a2c4a67262dc488a97929cf77cf83805",
    },
    "workspace-ci-controller@research-engine-cpu.service": {
        "LoadState": "loaded",
        "ActiveState": "inactive",
        "SubState": "dead",
        "UnitFileState": "enabled",
        "NRestarts": "12411",
        "ExecMainStatus": "1",
        "MainPID": "0",
        "InvocationID": "fdb8c54f1bf34556942f7137dac4fe92",
    },
    "workspace-ci-controller@research-engine-gpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433914",
        "InvocationID": "b79c01d618f4492c8630994f1d301ba8",
    },
}


class HotfixError(RuntimeError):
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
        raise HotfixError(
            f"command failed rc={proc.returncode}: {argv!r}: {proc.stderr.strip()}"
        )
    return proc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def attest_source(expected_head: str, invoker: str) -> pathlib.Path:
    helper = pathlib.Path(__file__).resolve()
    repo = helper.parents[1]
    if helper != (repo / EXPECTED_HELPER).resolve():
        raise HotfixError("executing helper is outside reviewed tracked path")
    prefix = ["/usr/sbin/runuser", "-u", invoker, "--", "git", "-C", str(repo)]
    if run([*prefix, "rev-parse", "--show-toplevel"]).stdout.strip() != str(repo):
        raise HotfixError("reviewed repository top-level mismatch")
    head = run([*prefix, "rev-parse", "HEAD"]).stdout.strip()
    if head != expected_head:
        raise HotfixError(
            f"HEAD mismatch: actual={head} expected={expected_head}"
        )
    if run(
        [*prefix, "status", "--porcelain=v1", "--untracked-files=no"]
    ).stdout.strip():
        raise HotfixError("reviewed tracked tree is dirty")
    if run(
        [*prefix, "ls-files", "--error-unmatch", str(EXPECTED_HELPER)],
        check=False,
    ).returncode != 0:
        raise HotfixError("executing helper is not tracked")
    return repo


def snapshot(service: str) -> dict[str, str]:
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
            key, item = line.split("=", 1)
            value[key] = item
    if set(value) != set(props):
        raise HotfixError(f"incomplete service snapshot: {service}: {value}")
    return value


def require_snapshot(service: str, expected: dict[str, str]) -> dict[str, str]:
    actual = snapshot(service)
    if actual != expected:
        raise HotfixError(
            f"service snapshot mismatch for {service}: "
            f"actual={actual} expected={expected}"
        )
    return actual


def require_root_healthy() -> dict[str, str]:
    value = snapshot(ROOT_SERVICE)
    if (
        value["LoadState"] != "loaded"
        or value["ActiveState"] != "active"
        or value["SubState"] != "running"
        or value["ExecMainStatus"] != "0"
        or value["MainPID"] == "0"
    ):
        raise HotfixError(f"root reconciler is not healthy: {value}")
    return value


def validate_rejected_marker(raw: bytes) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HotfixError("last-rejected marker is invalid JSON") from exc
    if not isinstance(value, dict):
        raise HotfixError("last-rejected marker must be object")
    if value.get("status") != "REJECTED":
        raise HotfixError("last-rejected status mismatch")
    if value.get("commit_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected policy SHA mismatch")
    if value.get("approved_policy_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected approved policy SHA mismatch")
    if value.get("observed_main_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected observed main SHA mismatch")
    if value.get("policy_equivalent_to_observed_main") is not True:
        raise HotfixError("last-rejected policy equivalence mismatch")
    if value.get("request_id") != EXPECTED_REQUEST_ID:
        raise HotfixError("last-rejected request ID mismatch")
    if value.get("workflow_run_id") != EXPECTED_WORKFLOW_RUN_ID:
        raise HotfixError("last-rejected workflow run mismatch")
    response = value.get("response")
    if not isinstance(response, dict):
        raise HotfixError("last-rejected response missing")
    if response.get("status") != "REJECTED":
        raise HotfixError("last-rejected root response status mismatch")
    if response.get("error_type") != "ReconcileError":
        raise HotfixError("last-rejected root error type mismatch")
    error = response.get("error")
    required_fragments = [
        "derived controller transaction differs from reviewed expected transaction",
        "workspace-ci-controller@padataset-cpu.service",
        "workspace-ci-controller@padataset-gpu.service",
        "workspace-ci-controller@research-engine-cpu.service",
        "workspace-ci-controller@research-engine-gpu.service",
        "workspace-ci-controller@workspace-control-cpu.service",
    ]
    if not isinstance(error, str) or any(
        fragment not in error for fragment in required_fragments
    ):
        raise HotfixError("last-rejected root error does not match reviewed rejection")
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
    raise HotfixError("root reconciler AF_UNIX socket is not ready")


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
    one_shot_before: dict[str, str],
    workspace_before: dict[str, str],
    siblings_before: dict[str, dict[str, str]],
) -> None:
    if snapshot(AUTO_CONTROLLER) != auto_before:
        raise HotfixError("automatic reconcile-controller changed")
    if snapshot(ONE_SHOT) != one_shot_before:
        raise HotfixError("one-shot reconcile-controller changed")
    if snapshot(WORKSPACE_CPU) != workspace_before:
        raise HotfixError("workspace-control CPU changed")
    for service, before in siblings_before.items():
        if snapshot(service) != before:
            raise HotfixError(f"preserved sibling changed: {service}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise HotfixError("installer must run as root via sudo")
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        raise HotfixError("installer requires a non-root sudo invoker")
    pwd.getpwnam(invoker)

    repo = attest_source(args.expected_head, invoker)
    source_root = (repo / SOURCE_ROOT).read_bytes()

    if sha256_path(INSTALLED_ROOT) != EXPECTED_OLD_ROOT_SHA256:
        raise HotfixError("installed root reconciler baseline mismatch")
    if (
        sha256_path(INSTALLED_RECONCILE_CONTROLLER)
        != EXPECTED_RECONCILE_CONTROLLER_SHA256
    ):
        raise HotfixError("installed reconcile-controller baseline mismatch")
    if sha256_path(INSTALLED_ONE_SHOT_UNIT) != EXPECTED_ONE_SHOT_UNIT_SHA256:
        raise HotfixError("installed one-shot unit baseline mismatch")
    if sha256_path(INSTALLED_CONTROLLER_BINARY) != EXPECTED_CONTROLLER_BINARY_SHA256:
        raise HotfixError("installed project-controller binary baseline mismatch")

    if not LAST_REJECTED.is_file():
        raise HotfixError("expected rejected one-shot marker is absent")
    if ARCHIVED_REJECTED.exists():
        raise HotfixError("rejected one-shot archive already exists")
    rejected_raw = LAST_REJECTED.read_bytes()
    rejected = validate_rejected_marker(rejected_raw)

    root_before = require_root_healthy()
    auto_before = require_snapshot(AUTO_CONTROLLER, EXPECTED_AUTO)
    one_shot_before = require_snapshot(ONE_SHOT, EXPECTED_ONE_SHOT)
    workspace_before = require_snapshot(WORKSPACE_CPU, EXPECTED_WORKSPACE_CPU)
    siblings_before = {
        service: require_snapshot(service, expected)
        for service, expected in EXPECTED_SIBLINGS.items()
    }

    old_root = INSTALLED_ROOT.read_bytes()
    rollback_armed = True
    rejected_archived = False
    try:
        atomic_write(INSTALLED_ROOT, source_root, 0o755)
        run([
            "systemctl",
            "--job-mode=ignore-dependencies",
            "restart",
            ROOT_SERVICE,
        ])
        wait_socket()
        root_after = require_root_healthy()
        certify_preserved(
            auto_before,
            one_shot_before,
            workspace_before,
            siblings_before,
        )
        if sha256_path(INSTALLED_ROOT) != sha256_bytes(source_root):
            raise HotfixError("root reconciler install digest mismatch")

        os.replace(LAST_REJECTED, ARCHIVED_REJECTED)
        rejected_archived = True
        if LAST_REJECTED.exists():
            raise HotfixError("last-rejected marker still present after archive")
        if ARCHIVED_REJECTED.read_bytes() != rejected_raw:
            raise HotfixError("archived rejected marker bytes mismatch")

        receipt = {
            "schema_version": 1,
            "status": "P1_LEGACY_STATE_ROOT_EQUIVALENCE_HOTFIX_INSTALLED",
            "source_head": args.expected_head,
            "installed_root_sha256": sha256_bytes(source_root),
            "controller_binary_sha256": sha256_path(INSTALLED_CONTROLLER_BINARY),
            "reconcile_controller_sha256": sha256_path(
                INSTALLED_RECONCILE_CONTROLLER
            ),
            "one_shot_unit_sha256": sha256_path(INSTALLED_ONE_SHOT_UNIT),
            "rejected_request": {
                "request_id": rejected["request_id"],
                "commit_sha": rejected["commit_sha"],
                "workflow_run_id": rejected["workflow_run_id"],
                "status": rejected["status"],
                "archived_path": str(ARCHIVED_REJECTED),
                "archived_sha256": sha256_bytes(rejected_raw),
            },
            "root_before": root_before,
            "root_after": root_after,
            "automatic_reconcile_controller": auto_before,
            "one_shot_controller": one_shot_before,
            "workspace_control_cpu": workspace_before,
            "preserved_siblings": siblings_before,
            "activation_performed": False,
            "retry_performed": False,
            "automatic_workflow_triggered": False,
        }
        print(
            "P1_LEGACY_STATE_ROOT_EQUIVALENCE_HOTFIX_RECEIPT="
            + json.dumps(receipt, sort_keys=True)
        )
        return 0
    except Exception as exc:
        if not rollback_armed:
            raise
        rollback_errors: list[str] = []
        try:
            atomic_write(INSTALLED_ROOT, old_root, 0o755)
            if rejected_archived:
                if LAST_REJECTED.exists():
                    raise HotfixError(
                        "cannot restore rejected marker because destination exists"
                    )
                os.replace(ARCHIVED_REJECTED, LAST_REJECTED)
            run([
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                ROOT_SERVICE,
            ])
            wait_socket()
            require_root_healthy()
            certify_preserved(
                auto_before,
                one_shot_before,
                workspace_before,
                siblings_before,
            )
            if INSTALLED_ROOT.read_bytes() != old_root:
                raise HotfixError("rollback did not restore exact old root bytes")
            if LAST_REJECTED.read_bytes() != rejected_raw:
                raise HotfixError("rollback did not restore exact rejected marker")
            if ARCHIVED_REJECTED.exists():
                raise HotfixError("rollback left rejected archive behind")
        except Exception as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            raise HotfixError(
                "legacy-state-root hotfix failed and rollback incomplete: "
                f"original={type(exc).__name__}:{exc}; "
                f"rollback={'; '.join(rollback_errors)}"
            ) from exc
        raise HotfixError(
            "legacy-state-root hotfix failed and rollback completed: "
            f"{type(exc).__name__}:{exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
