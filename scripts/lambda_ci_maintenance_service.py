#!/usr/bin/env python3
"""Bounded root maintenance service for Workspace CI P1.

This daemon is intentionally not a general remote administration interface.
The unprivileged L0 maintenance controller may request only a finite set of
typed operations. Project paths and systemd units are always derived from the
root-installed project registry.
"""

from __future__ import annotations

import argparse
import grp
import json
import os
import pathlib
import pwd
import socket
import struct
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

MAX_REQUEST_BYTES = 64 * 1024
REQUEST_TIMEOUT_SECONDS = 5
ALLOWED_OPERATIONS = {
    "DIAGNOSE_LANE",
    "RESTART_CONTROLLER",
    "QUIESCE_LANE_FOR_RECOVERY",
    "RESUME_LANE_AFTER_RESET",
}


class MaintenanceError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, sort_keys=True) + "\n"
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_text(raw, encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)


def _run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise MaintenanceError(
            f"command failed rc={proc.returncode}: {argv[0]}: {proc.stderr.strip()}"
        )
    return proc


def _service_active(service: str) -> bool:
    return _run(["systemctl", "is-active", "--quiet", service], check=False).returncode == 0


def _service_inactive(service: str) -> bool:
    return _run(["systemctl", "is-active", "--quiet", service], check=False).returncode != 0


def peer_uid(conn: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise MaintenanceError("SO_PEERCRED is required")
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def read_request(conn: socket.socket) -> dict[str, Any]:
    handle = conn.makefile("rb")
    line = handle.readline(MAX_REQUEST_BYTES + 1)
    if not line:
        raise MaintenanceError("empty maintenance request")
    if len(line) > MAX_REQUEST_BYTES:
        raise MaintenanceError("maintenance request exceeds transport limit")
    if handle.readline(2):
        raise MaintenanceError("exactly one maintenance JSON object is allowed")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise MaintenanceError("maintenance request is invalid JSON") from exc
    if not isinstance(value, dict):
        raise MaintenanceError("maintenance request must be object")
    return value


def _validate_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise MaintenanceError("maintenance request must be object")
    expected = {
        "schema_version",
        "request_id",
        "operation",
        "project_id",
        "lane",
        "quarantine_receipt_id",
        "reset_generation",
    }
    if set(request) != expected:
        raise MaintenanceError("maintenance request keys mismatch")
    if request["schema_version"] != 1:
        raise MaintenanceError("maintenance schema_version must be 1")
    try:
        uuid.UUID(str(request["request_id"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MaintenanceError("maintenance request_id must be UUID") from exc
    operation = request["operation"]
    if operation not in ALLOWED_OPERATIONS:
        raise MaintenanceError("maintenance operation is unsupported")
    project_id = request["project_id"]
    lane = request["lane"]
    if not isinstance(project_id, str) or not project_id:
        raise MaintenanceError("project_id is invalid")
    if lane not in {"cpu", "gpu"}:
        raise MaintenanceError("lane is invalid")
    quarantine = request["quarantine_receipt_id"]
    generation = request["reset_generation"]
    for name, value in (
        ("quarantine_receipt_id", quarantine),
        ("reset_generation", generation),
    ):
        if value is not None:
            try:
                uuid.UUID(str(value))
            except (ValueError, TypeError, AttributeError) as exc:
                raise MaintenanceError(f"{name} must be UUID or null") from exc
    if operation in {"DIAGNOSE_LANE", "RESTART_CONTROLLER"}:
        if quarantine is not None or generation is not None:
            raise MaintenanceError("diagnose/restart accept no recovery identifiers")
    elif operation == "QUIESCE_LANE_FOR_RECOVERY":
        if quarantine is None:
            raise MaintenanceError("quiesce requires quarantine_receipt_id")
    elif operation == "RESUME_LANE_AFTER_RESET":
        if quarantine is None or generation is None:
            raise MaintenanceError("resume requires quarantine_receipt_id and reset_generation")
    return dict(request)


def _load_registry(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaintenanceError("installed project registry unavailable") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise MaintenanceError("installed project registry invalid")
    return value


def derive_target(
    registry: dict[str, Any],
    project_id: str,
    lane: str,
    *,
    controller_state_root: pathlib.Path,
) -> dict[str, Any]:
    projects = registry.get("projects")
    if not isinstance(projects, dict):
        raise MaintenanceError("installed registry projects invalid")
    entry = projects.get(project_id)
    if not isinstance(entry, dict):
        raise MaintenanceError("project is not installed in registry")
    lanes = entry.get("lanes")
    if not isinstance(lanes, list) or lane not in lanes:
        raise MaintenanceError("lane is not registered for project")
    if entry.get("activation_state") != "ACTIVE":
        raise MaintenanceError("maintenance target project is not active")
    service = f"workspace-ci-controller@{project_id}-{lane}.service"
    state_dir = controller_state_root / f"{project_id}-{lane}"
    return {
        "project_id": project_id,
        "lane": lane,
        "service": service,
        "state_dir": state_dir,
    }


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaintenanceError(f"required state unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise MaintenanceError(f"required state invalid: {path.name}")
    return value


def _quarantine_state(
    target: dict[str, Any],
    quarantine_id: str,
    reset_generation: str | None,
) -> tuple[pathlib.Path, dict[str, Any]]:
    state_dir: pathlib.Path = target["state_dir"]
    candidates = [state_dir / "quarantine.json"]
    if reset_generation is not None:
        candidates = [
            state_dir / f"reset-pending-{reset_generation}.json",
            state_dir / "ready-for-single-retry.json",
            *candidates,
        ]
    for path in candidates:
        if not path.is_file():
            continue
        value = _read_json(path)
        if value.get("receipt_id") != quarantine_id:
            continue
        if value.get("project_id") != target["project_id"] or value.get("lane") != target["lane"]:
            raise MaintenanceError("quarantine target identity mismatch")
        return path, value
    raise MaintenanceError("matching quarantine receipt not found")


def _active_project_units(project_id: str) -> list[str]:
    pattern = f"workspace-ci-{project_id}-*.service"
    proc = _run(
        ["systemctl", "list-units", "--all", "--plain", "--no-legend", "--no-pager", pattern],
        check=False,
    )
    if proc.returncode not in {0, 1}:
        raise MaintenanceError("unable to inspect project execution units")
    active: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        unit, load, active_state, sub = parts[:4]
        if load == "loaded" and active_state in {"active", "activating", "deactivating"}:
            active.append(f"{unit}:{active_state}:{sub}")
    return sorted(active)


def _receipt_identity(request: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "operation": request["operation"],
        "project_id": target["project_id"],
        "lane": target["lane"],
        "service": target["service"],
        "quarantine_receipt_id": request["quarantine_receipt_id"],
        "reset_generation": request["reset_generation"],
    }


def _mutating_receipt(
    request: dict[str, Any],
    target: dict[str, Any],
    *,
    receipts_dir: pathlib.Path,
    mutation: callable,
) -> dict[str, Any]:
    receipts_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipts_dir / f"{request['request_id']}.json"
    identity = _receipt_identity(request, target)
    if receipt_path.is_file():
        prior = _read_json(receipt_path)
        if prior.get("identity") != identity:
            raise MaintenanceError("maintenance request_id replay identity mismatch")
        if prior.get("status") == "COMPLETED":
            return prior
        raise MaintenanceError("stored maintenance receipt is non-terminal")
    in_progress = {
        "schema_version": 1,
        "status": "IN_PROGRESS",
        "identity": identity,
        "timestamp_utc": _utc_now(),
    }
    _atomic_json(receipt_path, in_progress)
    result = mutation()
    receipt = {
        "schema_version": 1,
        "status": "COMPLETED",
        "identity": identity,
        "timestamp_utc": _utc_now(),
        "result": result,
    }
    _atomic_json(receipt_path, receipt)
    return receipt


def apply_request(
    request: dict[str, Any],
    *,
    registry_path: pathlib.Path,
    controller_state_root: pathlib.Path,
    receipts_dir: pathlib.Path,
) -> dict[str, Any]:
    request = _validate_request(request)
    registry = _load_registry(registry_path)
    target = derive_target(
        registry,
        request["project_id"],
        request["lane"],
        controller_state_root=controller_state_root,
    )
    service = target["service"]
    operation = request["operation"]

    if operation == "DIAGNOSE_LANE":
        quarantine = None
        qpath = target["state_dir"] / "quarantine.json"
        if qpath.is_file():
            quarantine = _read_json(qpath)
        reset_pending = [
            _read_json(path)
            for path in sorted(target["state_dir"].glob("reset-pending-*.json"))
        ]
        ready_path = target["state_dir"] / "ready-for-single-retry.json"
        ready = _read_json(ready_path) if ready_path.is_file() else None
        return {
            "schema_version": 1,
            "status": "PASS",
            "operation": operation,
            "project_id": target["project_id"],
            "lane": target["lane"],
            "service": service,
            "service_active": _service_active(service),
            "active_project_units": _active_project_units(target["project_id"]),
            "quarantine": quarantine,
            "reset_pending": reset_pending,
            "ready_for_single_retry": ready,
        }

    if operation == "RESTART_CONTROLLER":
        def restart() -> dict[str, Any]:
            _run(["systemctl", "restart", service])
            if not _service_active(service):
                raise MaintenanceError("controller did not become active")
            return {"service_active": True}
        return _mutating_receipt(
            request, target, receipts_dir=receipts_dir, mutation=restart
        )

    if operation == "QUIESCE_LANE_FOR_RECOVERY":
        qpath, quarantine = _quarantine_state(
            target,
            request["quarantine_receipt_id"],
            request["reset_generation"],
        )
        def quiesce() -> dict[str, Any]:
            _run(["systemctl", "stop", service])
            if not _service_inactive(service):
                raise MaintenanceError("controller did not stop")
            active_units = _active_project_units(target["project_id"])
            if active_units:
                raise MaintenanceError(
                    "project execution still active while quiescing: "
                    + ",".join(active_units)
                )
            state_path = qpath
            if (
                request["reset_generation"] is not None
                and qpath.name == "ready-for-single-retry.json"
            ):
                pending = (
                    target["state_dir"]
                    / f"reset-pending-{request['reset_generation']}.json"
                )
                pending_state = dict(quarantine)
                pending_state["status"] = "RECOVERY_SCALESET_RESET_PENDING"
                pending_state["reset_generation"] = request["reset_generation"]
                pending_state["old_scale_set_id"] = quarantine.get(
                    "old_scale_set_id",
                    quarantine.get("scale_set_id"),
                )
                pending_state["reset_requiesced_at"] = _utc_now()
                _atomic_json(pending, pending_state)
                qpath.unlink()
                state_path = pending
            return {
                "service_active": False,
                "quarantine_state_path": str(state_path),
                "quarantine_scale_set_id": quarantine.get(
                    "scale_set_id",
                    quarantine.get("new_scale_set_id"),
                ),
                "local_execution_absent": True,
            }
        return _mutating_receipt(
            request, target, receipts_dir=receipts_dir, mutation=quiesce
        )

    if operation == "RESUME_LANE_AFTER_RESET":
        qpath, quarantine = _quarantine_state(
            target,
            request["quarantine_receipt_id"],
            request["reset_generation"],
        )
        generation = request["reset_generation"]
        pending = target["state_dir"] / f"reset-pending-{generation}.json"
        if pending.exists():
            prior = _read_json(pending)
            if prior.get("receipt_id") != quarantine.get("receipt_id"):
                raise MaintenanceError("reset generation identity mismatch")
        def resume() -> dict[str, Any]:
            archived_previous_recovery = None
            if qpath.name == "quarantine.json":
                ready_path = target["state_dir"] / "ready-for-single-retry.json"
                if ready_path.is_file():
                    prior_ready = _read_json(ready_path)
                    if prior_ready.get("status") != "RECOVERY_RETRY_COMPLETED":
                        raise MaintenanceError(
                            "previous recovery generation is not terminal"
                        )
                    prior_generation = prior_ready.get("reset_generation")
                    try:
                        uuid.UUID(str(prior_generation))
                    except (ValueError, TypeError, AttributeError) as exc:
                        raise MaintenanceError(
                            "previous recovery generation identity is invalid"
                        ) from exc
                    history_path = (
                        target["state_dir"]
                        / f"recovery-history-{prior_generation}.json"
                    )
                    if history_path.is_file():
                        if _read_json(history_path) != prior_ready:
                            raise MaintenanceError(
                                "previous recovery history replay mismatch"
                            )
                        ready_path.unlink()
                    else:
                        ready_path.replace(history_path)
                    archived_previous_recovery = str(history_path)

                pending_state = dict(quarantine)
                pending_state["status"] = "RECOVERY_SCALESET_RESET_PENDING"
                pending_state["reset_generation"] = generation
                pending_state["old_scale_set_id"] = quarantine.get("scale_set_id")
                pending_state["reset_started_at"] = _utc_now()
                _atomic_json(pending, pending_state)
                qpath.unlink()
            _run(["systemctl", "start", service])
            if not _service_active(service):
                raise MaintenanceError("controller did not become active")
            return {
                "service_active": True,
                "reset_generation": generation,
                "archived_quarantine_path": str(pending),
                "old_scale_set_id": quarantine.get(
                    "old_scale_set_id",
                    quarantine.get("scale_set_id"),
                ),
                "controller_remains_recovery_quarantined": True,
                "archived_previous_recovery": archived_previous_recovery,
            }
        return _mutating_receipt(
            request, target, receipts_dir=receipts_dir, mutation=resume
        )

    raise MaintenanceError("maintenance operation is unsupported")


def serve(
    *,
    socket_path: pathlib.Path,
    socket_group: str,
    controller_uid: int,
    registry_path: pathlib.Path,
    controller_state_root: pathlib.Path,
    state_dir: pathlib.Path,
) -> None:
    group = grp.getgrnam(socket_group)
    receipts_dir = state_dir / "receipts"
    state_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir.mkdir(parents=True, exist_ok=True)
    os.chown(state_dir, 0, 0)
    os.chown(receipts_dir, 0, 0)
    os.chmod(state_dir, 0o700)
    os.chmod(receipts_dir, 0o700)

    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        os.chown(socket_path.parent, 0, group.gr_gid)
    os.chmod(socket_path.parent, 0o750)
    if socket_path.exists():
        socket_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    os.chown(socket_path, 0, group.gr_gid)
    os.chmod(socket_path, 0o660)
    server.listen(8)
    try:
        while True:
            conn, _ = server.accept()
            with conn:
                conn.settimeout(REQUEST_TIMEOUT_SECONDS)
                try:
                    if peer_uid(conn) != controller_uid:
                        raise MaintenanceError("peer UID is not ci-maintenance")
                    request = read_request(conn)
                    response = apply_request(
                        request,
                        registry_path=registry_path,
                        controller_state_root=controller_state_root,
                        receipts_dir=receipts_dir,
                    )
                    wrapper = {
                        "schema_version": 1,
                        "status": "PASS",
                        "request_id": request.get("request_id"),
                        "receipt": response,
                    }
                except Exception as exc:
                    wrapper = {
                        "schema_version": 1,
                        "status": "REJECTED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                try:
                    conn.sendall((json.dumps(wrapper, sort_keys=True) + "\n").encode("utf-8"))
                except (BrokenPipeError, ConnectionResetError):
                    pass
    finally:
        server.close()
        if socket_path.exists():
            socket_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument(
        "--socket",
        type=pathlib.Path,
        default=pathlib.Path("/run/workspace-ci/maintenance/maintenance.sock"),
    )
    parser.add_argument("--socket-group", default="workspace-ci-maintenance")
    parser.add_argument("--controller-user", default="ci-maintenance")
    parser.add_argument(
        "--registry",
        type=pathlib.Path,
        default=pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json"),
    )
    parser.add_argument(
        "--controller-state-root",
        type=pathlib.Path,
        default=pathlib.Path("/var/lib/workspace-ci/controller/state"),
    )
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path("/var/lib/workspace-ci/maintenance"),
    )
    args = parser.parse_args()
    if not args.serve:
        raise MaintenanceError("live maintenance is accepted only through --serve root socket")
    controller = pwd.getpwnam(args.controller_user)
    serve(
        socket_path=args.socket,
        socket_group=args.socket_group,
        controller_uid=controller.pw_uid,
        registry_path=args.registry,
        controller_state_root=args.controller_state_root,
        state_dir=args.state_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
