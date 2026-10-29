#!/usr/bin/env python3
"""One-time rollback-safe activation for controller reliability hardening v1.

This helper installs only the independently reviewed controller reliability payload:
- rebuilt lambda-ci-controller binary;
- generic workspace-ci-controller@.service unit;
- root lambda_ci_maintenance_service.py.

It preserves research-engine/cpu inactive state, restarts only controllers that were
healthy/live at the frozen preflight plus the broken research-engine/gpu lane, never
clears quarantine, never triggers workflows, and never restores retry authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from typing import Any

GO_BIN = pathlib.Path("/opt/workspace-ci/go/1.26.3/bin/go")
EXPECTED_HELPER = pathlib.Path(
    "scripts/lambda_ci_controller_reliability_activation_v1.py"
)
PAYLOAD_SOURCE_HEAD = "7524612dfb96e24f45a969b761858b2f71409fc4"
EXPECTED_SOURCE_BLOBS = {
    "controller/lambda-ci-controller/main.go":
        "7ed009e3602460650909ce1e7b713d8c3b84b66b",
    "controller/lambda-ci-controller/attestation.go":
        "4d16f9668173c2ac04e30bf09ea6814e09dd9c51",
    "controller/lambda-ci-controller/go.mod":
        "c0a743bec472b0ab0996679a9d86dc409db79104",
    "templates/lambda-ci/workspace-ci-controller@.service.in":
        "1cbc879695bd2b4f9f3d1e24f68eb5aa6e641ef2",
    "scripts/lambda_ci_maintenance_service.py":
        "034489492a2405fabeff36532c6643d801b44954",
}
EXPECTED_OLD_SHA256 = {
    "/opt/workspace-ci/controller/lambda-ci-controller":
        "6acd290f2312f0908d17443a2f5ee8d31711fbdb3f0bf9318171e9edd0ddee12",
    "/etc/systemd/system/workspace-ci-controller@.service":
        "3b77df48549a0972ca4b1f207b09067808cb8f1eed1ca9d967511df74d7be16f",
    "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py":
        "59395404e8a174fefbde32657e6215c87a4170f539c85fc8aa5e2295883f6e6d",
}
CONTROLLER_BINARY = pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller")
CONTROLLER_UNIT = pathlib.Path("/etc/systemd/system/workspace-ci-controller@.service")
MAINTENANCE_SERVICE = pathlib.Path(
    "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py"
)
MAINTENANCE_SOCKET = pathlib.Path("/run/workspace-ci/maintenance/maintenance.sock")
ACTIVATION_ROOT = pathlib.Path(
    "/var/lib/workspace-ci/maintenance/controller-reliability-activation-v1"
)
RECEIPT_PATH = ACTIVATION_ROOT / "activation-receipt.json"
BACKUP_ROOT = ACTIVATION_ROOT / "backup"
GPU_STATE = pathlib.Path(
    "/var/lib/workspace-ci/controller/state/research-engine-gpu"
)

RESEARCH_CPU = "workspace-ci-controller@research-engine-cpu.service"
RESEARCH_GPU = "workspace-ci-controller@research-engine-gpu.service"
PAD_CPU = "workspace-ci-controller@padataset-cpu.service"
PAD_GPU = "workspace-ci-controller@padataset-gpu.service"
WORKSPACE_CPU = "workspace-ci-controller@workspace-control-cpu.service"
MAINT_ROOT = "workspace-ci-maintenance.service"
MAINT_CONTROLLER = "workspace-ci-maintenance-controller.service"

HEALTHY_CONTROLLERS = [PAD_CPU, PAD_GPU, WORKSPACE_CPU]
ACTIVE_AFTER_INSTALL = [PAD_CPU, PAD_GPU, WORKSPACE_CPU, RESEARCH_GPU]

EXPECTED_QUARANTINE = {
    "schema_version": 1,
    "receipt_id": "a7880e15-b29c-4b2b-bccd-3a34745f9ded",
    "status": "ASSIGNMENT_DIVERGENCE_QUARANTINED",
    "project_id": "research-engine",
    "lane": "gpu",
    "scale_set_name": "lambda-research-engine-gpu",
    "scale_set_id": 3,
    "total_assigned_jobs": 1,
    "reconstructable_jobs": 0,
    "active_count": 0,
    "pending_count": 0,
    "reason": "github_assigned_count_exceeds_complete_reconstructable_jobs",
}
EXPECTED_READY = {
    "schema_version": 1,
    "receipt_id": "3eeffae8-2bd0-4344-b89f-02afbf1a445b",
    "status": "READY_FOR_SINGLE_RETRY",
    "project_id": "research-engine",
    "lane": "gpu",
    "scale_set_name": "lambda-research-engine-gpu",
    "old_scale_set_id": 2,
    "new_scale_set_id": 3,
    "reset_generation": "c00a10e3-1907-56e7-9e19-099fa0268d5e",
    "automatic_workflow_triggered": False,
}

STABILITY_SECONDS = 20
MAINTENANCE_STABILITY_SECONDS = 5


class ActivationError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    check: bool = True,
    user: str | None = None,
    env: dict[str, str] | None = None,
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
        env=env,
    )
    if check and proc.returncode != 0:
        raise ActivationError(
            f"command failed rc={proc.returncode}: {command!r}: "
            f"{proc.stderr.strip()}"
        )
    return proc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActivationError(f"invalid required JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ActivationError(f"required JSON is not an object: {path}")
    return value


def exact_subset(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    mismatches = {
        key: {"actual": actual.get(key), "expected": value}
        for key, value in expected.items()
        if actual.get(key) != value
    }
    if mismatches:
        raise ActivationError(f"{label} mismatch: {json.dumps(mismatches, sort_keys=True)}")


def attest_source(expected_head: str, invoker: str) -> pathlib.Path:
    helper = pathlib.Path(__file__).resolve()
    repo = helper.parents[1]
    if helper != (repo / EXPECTED_HELPER).resolve():
        raise ActivationError("helper is outside reviewed tracked path")
    prefix = ["/usr/sbin/runuser", "-u", invoker, "--", "git", "-C", str(repo)]
    top = run([*prefix, "rev-parse", "--show-toplevel"]).stdout.strip()
    if pathlib.Path(top).resolve() != repo:
        raise ActivationError("repository top-level mismatch")
    head = run([*prefix, "rev-parse", "HEAD"]).stdout.strip()
    if head != expected_head:
        raise ActivationError(f"HEAD mismatch: actual={head} expected={expected_head}")
    symbolic = run([*prefix, "symbolic-ref", "-q", "HEAD"], check=False)
    if symbolic.returncode == 0:
        raise ActivationError("activation requires detached HEAD")
    if symbolic.returncode != 1:
        raise ActivationError("unable to prove detached HEAD")
    dirty = run(
        [*prefix, "status", "--porcelain=v1", "--untracked-files=no"]
    ).stdout.strip()
    if dirty:
        raise ActivationError("reviewed tracked checkout is dirty")
    if run(
        [*prefix, "ls-files", "--error-unmatch", str(EXPECTED_HELPER)],
        check=False,
    ).returncode != 0:
        raise ActivationError("activation helper is not tracked")

    for path, expected_blob in EXPECTED_SOURCE_BLOBS.items():
        reviewed_blob = run(
            [*prefix, "rev-parse", f"{PAYLOAD_SOURCE_HEAD}:{path}"]
        ).stdout.strip()
        head_blob = run([*prefix, "rev-parse", f"HEAD:{path}"]).stdout.strip()
        if reviewed_blob != expected_blob or head_blob != expected_blob:
            raise ActivationError(
                f"source blob mismatch for {path}: "
                f"reviewed={reviewed_blob} head={head_blob} expected={expected_blob}"
            )
    return repo


def service_snapshot(service: str) -> dict[str, str]:
    props = [
        "LoadState", "UnitFileState", "ActiveState", "SubState", "Result",
        "ExecMainCode", "ExecMainStatus", "NRestarts", "MainPID",
        "InvocationID", "Restart",
    ]
    argv = ["systemctl", "show", service, "--no-pager"]
    for prop in props:
        argv.extend(["-p", prop])
    out = run(argv, check=False).stdout
    value: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            key, raw = line.split("=", 1)
            value[key] = raw
    if set(value) != set(props):
        raise ActivationError(f"incomplete service snapshot for {service}: {value}")
    return value


def is_running(snap: dict[str, str]) -> bool:
    return (
        snap["LoadState"] == "loaded"
        and snap["ActiveState"] == "active"
        and snap["SubState"] == "running"
        and snap["ExecMainStatus"] == "0"
        and snap["MainPID"].isdigit()
        and int(snap["MainPID"]) > 0
    )


def require_running(service: str) -> dict[str, str]:
    snap = service_snapshot(service)
    if not is_running(snap):
        raise ActivationError(f"required service is not running: {service}: {snap}")
    return snap


def require_inactive_research_cpu() -> dict[str, str]:
    snap = service_snapshot(RESEARCH_CPU)
    expected = {
        "LoadState": "loaded",
        "UnitFileState": "enabled",
        "ActiveState": "inactive",
        "SubState": "dead",
        "Result": "exit-code",
        "ExecMainCode": "1",
        "ExecMainStatus": "1",
        "NRestarts": "12411",
        "MainPID": "0",
        "Restart": "on-failure",
    }
    exact_subset(snap, expected, "research-engine cpu baseline")
    return snap


def require_old_gpu_loop() -> dict[str, str]:
    snap = service_snapshot(RESEARCH_GPU)
    if (
        snap["LoadState"] != "loaded"
        or snap["UnitFileState"] != "enabled"
        or snap["Result"] != "exit-code"
        or snap["Restart"] != "on-failure"
        or snap["ActiveState"] not in {"activating", "active"}
        or snap["SubState"] not in {"auto-restart", "running"}
    ):
        raise ActivationError(f"research-engine gpu baseline drift: {snap}")
    try:
        restarts = int(snap["NRestarts"])
    except ValueError as exc:
        raise ActivationError("gpu NRestarts is invalid") from exc
    if restarts < 14276:
        raise ActivationError(f"gpu restart count regressed unexpectedly: {restarts}")
    return snap


def active_execution_units() -> list[str]:
    out: list[str] = []
    for project in ("research-engine", "padataset", "workspace-control"):
        proc = run(
            [
                "systemctl", "list-units", "--all", "--plain", "--no-legend",
                "--no-pager", f"workspace-ci-{project}-*.service",
            ],
            check=False,
        )
        if proc.returncode not in {0, 1}:
            raise ActivationError(f"unable to inspect execution units for {project}")
        for line in proc.stdout.splitlines():
            parts = line.split()
            if (
                len(parts) >= 4
                and parts[1] == "loaded"
                and parts[2] in {"active", "activating", "deactivating"}
            ):
                out.append(line)
    return out


def require_no_active_execution() -> None:
    units = active_execution_units()
    if units:
        raise ActivationError(
            "project execution is active; refusing controller activation: "
            + json.dumps(units)
        )


def require_installed_baseline() -> dict[str, str]:
    actual: dict[str, str] = {}
    for raw, expected in EXPECTED_OLD_SHA256.items():
        path = pathlib.Path(raw)
        if not path.is_file():
            raise ActivationError(f"required installed file is missing: {path}")
        digest = sha256_path(path)
        actual[raw] = digest
        if digest != expected:
            raise ActivationError(
                f"installed baseline drift: {path}: actual={digest} expected={expected}"
            )
    return actual


def require_recovery_baseline() -> dict[str, Any]:
    quarantine = read_json(GPU_STATE / "quarantine.json")
    ready = read_json(GPU_STATE / "ready-for-single-retry.json")
    exact_subset(quarantine, EXPECTED_QUARANTINE, "gpu quarantine")
    exact_subset(ready, EXPECTED_READY, "gpu ready gate")
    pending = list(GPU_STATE.glob("reset-pending-*.json"))
    if pending:
        raise ActivationError(f"unexpected reset-pending receipts: {pending}")
    if (GPU_STATE / "reset-zero-observation.json").exists():
        raise ActivationError("unexpected reset-zero-observation.json")
    return {"quarantine": quarantine, "ready": ready}


def wait_socket(path: pathlib.Path, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_socket():
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.25)
            try:
                client.connect(str(path))
                return
            except OSError:
                pass
            finally:
                client.close()
        time.sleep(0.1)
    raise ActivationError(f"socket did not become ready: {path}")


def stable_running(service: str, seconds: int) -> dict[str, Any]:
    first = require_running(service)
    time.sleep(seconds)
    second = require_running(service)
    if first["NRestarts"] != second["NRestarts"]:
        raise ActivationError(
            f"service restart count changed during stability window: {service}: "
            f"{first['NRestarts']} -> {second['NRestarts']}"
        )
    return {"first": first, "second": second, "settle_seconds": seconds}


def git_text(repo: pathlib.Path, invoker: str, path: str) -> str:
    return run(
        ["git", "-C", str(repo), "show", f"HEAD:{path}"],
        user=invoker,
    ).stdout


def build_controller(repo: pathlib.Path, invoker: str) -> pathlib.Path:
    if not GO_BIN.is_file():
        raise ActivationError("isolated Go toolchain missing")
    version = run([str(GO_BIN), "env", "GOVERSION"]).stdout.strip()
    if version != "go1.26.3":
        raise ActivationError(f"Go version drift: {version}")
    root = pathlib.Path(tempfile.mkdtemp(prefix="workspace-ci-controller-hardening-"))
    work = root / "src"
    work.mkdir()
    for rel in (
        "controller/lambda-ci-controller/main.go",
        "controller/lambda-ci-controller/attestation.go",
        "controller/lambda-ci-controller/go.mod",
    ):
        (work / pathlib.Path(rel).name).write_text(
            git_text(repo, invoker, rel),
            encoding="utf-8",
        )
    controller = pwd.getpwnam("ci-controller")
    for current, dirs, files in os.walk(root):
        os.chown(current, controller.pw_uid, controller.pw_gid)
        for name in dirs:
            os.chown(os.path.join(current, name), controller.pw_uid, controller.pw_gid)
        for name in files:
            os.chown(os.path.join(current, name), controller.pw_uid, controller.pw_gid)
    os.chmod(root, 0o700)
    out = work / "lambda-ci-controller"
    env = {
        "PATH": "/opt/workspace-ci/go/1.26.3/bin:/usr/bin:/bin",
        "HOME": "/var/lib/workspace-ci/controller",
        "GOCACHE": str(work / ".gocache"),
        "GOMODCACHE": str(work / ".gomodcache"),
    }
    run(
        [
            str(GO_BIN), "-C", str(work), "build", "-mod=mod", "-trimpath",
            "-o", str(out), ".",
        ],
        user="ci-controller",
        env=env,
    )
    if not out.is_file():
        raise ActivationError("controller build produced no binary")
    return out


def atomic_install(raw: bytes, path: pathlib.Path, mode: int) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.activation-", dir=path.parent)
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


def save_backups() -> dict[str, Any]:
    if ACTIVATION_ROOT.exists():
        if RECEIPT_PATH.exists():
            raise ActivationError("activation receipt already exists; refusing replay")
    ACTIVATION_ROOT.mkdir(parents=True, exist_ok=True)
    os.chown(ACTIVATION_ROOT, 0, 0)
    os.chmod(ACTIVATION_ROOT, 0o700)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    os.chown(BACKUP_ROOT, 0, 0)
    os.chmod(BACKUP_ROOT, 0o700)

    manifest: dict[str, Any] = {"files": {}}
    for path in (CONTROLLER_BINARY, CONTROLLER_UNIT, MAINTENANCE_SERVICE):
        raw = path.read_bytes()
        backup = BACKUP_ROOT / hashlib.sha256(str(path).encode()).hexdigest()
        backup.write_bytes(raw)
        os.chown(backup, 0, 0)
        os.chmod(backup, 0o600)
        manifest["files"][str(path)] = {
            "backup": str(backup),
            "sha256": sha256_bytes(raw),
            "mode": path.stat().st_mode & 0o777,
        }
    return manifest


def restore_backups(manifest: dict[str, Any]) -> None:
    for raw, record in manifest["files"].items():
        path = pathlib.Path(raw)
        backup = pathlib.Path(record["backup"])
        data = backup.read_bytes()
        if sha256_bytes(data) != record["sha256"]:
            raise ActivationError(f"backup integrity mismatch: {path}")
        atomic_install(data, path, int(record["mode"]))
    run(["systemctl", "daemon-reload"])


def preflight(repo: pathlib.Path) -> dict[str, Any]:
    installed = require_installed_baseline()
    research_cpu = require_inactive_research_cpu()
    gpu = require_old_gpu_loop()
    healthy = {
        service: require_running(service)
        for service in HEALTHY_CONTROLLERS
    }
    maintenance = {
        MAINT_ROOT: require_running(MAINT_ROOT),
        MAINT_CONTROLLER: require_running(MAINT_CONTROLLER),
    }
    wait_socket(MAINTENANCE_SOCKET, timeout=3.0)
    require_no_active_execution()
    recovery = require_recovery_baseline()
    return {
        "installed": installed,
        "research_cpu": research_cpu,
        "gpu": gpu,
        "healthy_controllers": healthy,
        "maintenance": maintenance,
        "recovery": recovery,
    }


def require_post_activation_recovery() -> dict[str, Any]:
    quarantine = read_json(GPU_STATE / "quarantine.json")
    exact_subset(quarantine, EXPECTED_QUARANTINE, "post-activation quarantine")
    ready = read_json(GPU_STATE / "ready-for-single-retry.json")
    expected = {
        "status": "RECOVERY_RETRY_INVALIDATED",
        "previous_status": "READY_FOR_SINGLE_RETRY",
        "receipt_id": EXPECTED_READY["receipt_id"],
        "project_id": "research-engine",
        "lane": "gpu",
        "scale_set_name": "lambda-research-engine-gpu",
        "old_scale_set_id": 2,
        "new_scale_set_id": 3,
        "reset_generation": EXPECTED_READY["reset_generation"],
        "invalidated_by_quarantine_receipt_id": EXPECTED_QUARANTINE["receipt_id"],
    }
    exact_subset(ready, expected, "post-activation retry gate")
    if list(GPU_STATE.glob("reset-pending-*.json")):
        raise ActivationError("reset-pending state appeared during activation")
    return {"quarantine": quarantine, "retry_gate": ready}


def write_receipt(value: dict[str, Any]) -> None:
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".activation-receipt-", dir=ACTIVATION_ROOT)
    tmp = pathlib.Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.chmod(tmp, 0o600)
        os.replace(tmp, RECEIPT_PATH)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def activate(
    repo: pathlib.Path,
    expected_head: str,
    invoker: str,
    before: dict[str, Any],
) -> dict[str, Any]:
    built = build_controller(repo, invoker)
    candidate_sha = sha256_path(built)
    source_unit = git_text(
        repo,
        invoker,
        "templates/lambda-ci/workspace-ci-controller@.service.in",
    ).encode("utf-8")
    source_maintenance = git_text(
        repo,
        invoker,
        "scripts/lambda_ci_maintenance_service.py",
    ).encode("utf-8")
    backup = save_backups()

    mutation_started = False
    try:
        # Stop the known crash-looping lane first. Healthy lanes continue serving
        # until the new binary/unit are atomically installed.
        run(["systemctl", "stop", RESEARCH_GPU])
        run(["systemctl", "reset-failed", RESEARCH_GPU], check=False)
        mutation_started = True

        atomic_install(built.read_bytes(), CONTROLLER_BINARY, 0o755)
        atomic_install(source_unit, CONTROLLER_UNIT, 0o644)
        atomic_install(source_maintenance, MAINTENANCE_SERVICE, 0o755)
        run(["systemctl", "daemon-reload"])

        # Root maintenance loads the new ownership/stability semantics.
        run(["systemctl", "restart", MAINT_ROOT])
        wait_socket(MAINTENANCE_SOCKET)
        maintenance_root = stable_running(MAINT_ROOT, MAINTENANCE_STABILITY_SECONDS)
        maintenance_controller = require_running(MAINT_CONTROLLER)

        # Restart only previously healthy/live controller lanes.
        controllers: dict[str, Any] = {}
        for service in HEALTHY_CONTROLLERS:
            run(["systemctl", "reset-failed", service], check=False)
            run(["systemctl", "restart", service])

        # Start the repaired GPU lane last. Startup must invalidate the stale
        # retry gate while preserving quarantine and refusing acquisition.
        run(["systemctl", "reset-failed", RESEARCH_GPU], check=False)
        run(["systemctl", "start", RESEARCH_GPU])

        for service in ACTIVE_AFTER_INSTALL:
            controllers[service] = stable_running(service, STABILITY_SECONDS)

        # Research CPU was inactive before activation and must remain so.
        research_cpu_after = require_inactive_research_cpu()
        require_no_active_execution()

        recovery_after = require_post_activation_recovery()

        if sha256_path(CONTROLLER_BINARY) != candidate_sha:
            raise ActivationError("installed controller digest differs from built candidate")
        if CONTROLLER_UNIT.read_bytes() != source_unit:
            raise ActivationError("installed controller unit differs from reviewed source")
        if MAINTENANCE_SERVICE.read_bytes() != source_maintenance:
            raise ActivationError("installed maintenance service differs from reviewed source")

        receipt = {
            "schema_version": 1,
            "status": "CONTROLLER_RELIABILITY_ACTIVATED",
            "source_head": expected_head,
            "payload_source_head": PAYLOAD_SOURCE_HEAD,
            "candidate_controller_sha256": candidate_sha,
            "installed_controller_sha256": sha256_path(CONTROLLER_BINARY),
            "installed_controller_unit_sha256": sha256_path(CONTROLLER_UNIT),
            "installed_maintenance_service_sha256": sha256_path(MAINTENANCE_SERVICE),
            "preflight": before,
            "post_activation": {
                "controllers": controllers,
                "research_cpu": research_cpu_after,
                "maintenance_root": maintenance_root,
                "maintenance_controller": maintenance_controller,
                "recovery": recovery_after,
            },
            "automatic_workflow_triggered": False,
            "quarantine_cleared": False,
            "retry_authority_restored": False,
            "scientific_execution_started": False,
        }
        write_receipt(receipt)
        return receipt
    except Exception as exc:
        rollback_errors: list[str] = []
        if mutation_started:
            try:
                # Contain the affected GPU lane while rolling bytes back.
                run(["systemctl", "stop", RESEARCH_GPU], check=False)
                restore_backups(backup)
                run(["systemctl", "restart", MAINT_ROOT])
                wait_socket(MAINTENANCE_SOCKET)
                require_running(MAINT_ROOT)
                for service in HEALTHY_CONTROLLERS:
                    run(["systemctl", "reset-failed", service], check=False)
                    run(["systemctl", "restart", service])
                    require_running(service)
                require_inactive_research_cpu()
                require_no_active_execution()
                if service_snapshot(RESEARCH_GPU)["ActiveState"] != "inactive":
                    raise ActivationError("rollback failed to contain research-engine gpu")
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            raise ActivationError(
                "activation failed and rollback was incomplete: "
                f"original={type(exc).__name__}:{exc}; "
                f"rollback={'; '.join(rollback_errors)}"
            ) from exc
        raise ActivationError(
            "activation failed; old files restored, healthy lanes restored, "
            "research-engine gpu left stopped: "
            f"{type(exc).__name__}:{exc}"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--apply", action="store_true")
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
    before = preflight(repo)
    if not args.apply:
        print(
            "CONTROLLER_RELIABILITY_ACTIVATION_PREFLIGHT="
            + json.dumps(before, sort_keys=True)
        )
        return 0

    receipt = activate(repo, args.expected_head, invoker, before)
    print(
        "CONTROLLER_RELIABILITY_ACTIVATION_RECEIPT="
        + json.dumps(receipt, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
