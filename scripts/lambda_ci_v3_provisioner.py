#!/usr/bin/env python3
"""Root-owned capacity provider for the Lambda CI v3 runner-class protocol.

This service intentionally has no GitHub credential and accepts no caller-selected
runner class, resource class, GPU, execution profile, model, runtime, route, PR,
or candidate identity.  The authenticated Unix peer UID is mapped to exactly one
compiled runner class and all launch authority comes from that root projection.

The protocol is two phase:
    RESERVE -> controller creates GitHub JIT config -> LAUNCH
with STATUS/CANCEL for crash recovery.

Raw JIT bytes are never written to persistent state.  During LAUNCH they are
placed only in the v3 runtime tmpfs, mode 0600, for the deterministic root-owned
supervisor to consume and unlink before invoking the existing hardened runner
runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import re
import socket
import struct
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import lambda_ci_runtime as runtime
import lambda_ci_v3_spec as v3spec


DEFAULT_SOCKET = pathlib.Path("/run/workspace-ci/v3/provisioner.sock")
DEFAULT_STATE = pathlib.Path("/var/lib/workspace-ci/v3/provisioner")
DEFAULT_JIT_ROOT = pathlib.Path("/run/workspace-ci/v3/provisioner/jit")
DEFAULT_ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
DEFAULT_SOCKET_GROUP = "workspace-ci-v3-provisioner"
MAX_REQUEST_BYTES = 192 * 1024
MAX_JIT_BYTES = 174764
RECONCILE_GRACE_SECONDS = 30
HEX64 = re.compile(r"^[0-9a-f]{64}$")
RUNNER_NAME = re.compile(r"^lambda-[A-Za-z0-9._-]{3,127}$")
ACTIVE_STATES = frozenset({"RESERVED", "PREPARING", "ACCEPTED"})
TERMINAL_STATES = frozenset({"COMPLETED", "FAILED", "CANCELED", "EXPIRED"})


class V3ServiceError(RuntimeError):
    pass


class RequestTransportError(V3ServiceError):
    """Connection-local malformed input that must not terminate the service."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise V3ServiceError("stored timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _valid_request_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value.lower()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise V3ServiceError(f"{path}: expected JSON object")
    return value


class StateStore:
    """Atomic non-secret state plus tmpfs-only raw JIT handoff."""

    def __init__(self, root: pathlib.Path, jit_root: pathlib.Path):
        self.root = root
        self.jit_root = jit_root

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        self.jit_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.jit_root, 0o700)

    def record_path(self, request_id: str) -> pathlib.Path:
        if not _valid_request_id(request_id):
            raise V3ServiceError("invalid request id for state path")
        return self.root / f"{request_id}.json"

    def read(self, request_id: str) -> dict[str, Any] | None:
        path = self.record_path(request_id)
        if not path.exists():
            return None
        return _load_json(path)

    def records(self) -> dict[str, dict[str, Any]]:
        self.ensure()
        found: dict[str, dict[str, Any]] = {}
        for path in sorted(self.root.glob("*.json")):
            if path.name.startswith("_"):
                continue
            request_id = path.stem
            if not _valid_request_id(request_id):
                raise V3ServiceError(f"unexpected state filename: {path.name}")
            value = _load_json(path)
            if value.get("request_id") != request_id:
                raise V3ServiceError(f"state identity mismatch: {path.name}")
            found[request_id] = value
        return found

    def write(self, record: dict[str, Any]) -> None:
        self.ensure()
        request_id = record.get("request_id")
        if not _valid_request_id(request_id):
            raise V3ServiceError("state record request_id invalid")
        path = self.record_path(request_id)
        tmp = self.root / f".{request_id}.{os.getpid()}.{threading.get_ident()}.tmp"
        payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
        with tmp.open("w", encoding="utf-8") as handle:
            os.chmod(tmp, 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)

    @property
    def quarantine_path(self) -> pathlib.Path:
        return self.root / "_class-quarantine.json"

    def quarantines(self) -> dict[str, dict[str, Any]]:
        path = self.quarantine_path
        if not path.exists():
            return {}
        value = _load_json(path)
        if value.get("schema_version") != 1:
            raise V3ServiceError("class quarantine schema version invalid")
        classes = value.get("classes")
        if not isinstance(classes, dict):
            raise V3ServiceError("class quarantine classes invalid")
        return classes

    def quarantine(
        self,
        runner_class_id: str,
        *,
        request_id: str,
        reason: str,
        now: datetime,
    ) -> None:
        self.ensure()
        current = self.quarantines()
        current[runner_class_id] = {
            "status": "QUARANTINED",
            "request_id": request_id,
            "reason": reason,
            "updated_at": _iso(now),
        }
        payload = {
            "schema_version": 1,
            "classes": current,
        }
        tmp = self.root / f"._class-quarantine.{os.getpid()}.tmp"
        with tmp.open("w", encoding="utf-8") as handle:
            os.chmod(tmp, 0o600)
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.quarantine_path)

    def jit_path(self, request_id: str) -> pathlib.Path:
        if not _valid_request_id(request_id):
            raise V3ServiceError("invalid request id for JIT path")
        return self.jit_root / f"{request_id}.jit"

    def write_jit(self, request_id: str, jit_config: str) -> pathlib.Path:
        self.ensure()
        raw = jit_config.encode("utf-8")
        if not raw or len(raw) > MAX_JIT_BYTES:
            raise V3ServiceError("JIT config size invalid")
        path = self.jit_path(request_id)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise V3ServiceError("JIT handoff already exists") from exc
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        return path

    def consume_jit(self, request_id: str) -> str:
        path = self.jit_path(request_id)
        raw = path.read_bytes()
        path.unlink()
        if not raw or len(raw) > MAX_JIT_BYTES:
            raise V3ServiceError("JIT handoff size invalid")
        return raw.decode("utf-8")

    def remove_jit(self, request_id: str) -> None:
        path = self.jit_path(request_id)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def build_controller_uid_map(
    root_projection: dict[str, Any],
    *,
    resolver: Callable[[str], int] | None = None,
) -> dict[str, int]:
    """Resolve every immutable controller user to a unique numeric SO_PEERCRED UID."""

    if resolver is None:
        resolver = lambda user: pwd.getpwnam(user).pw_uid
    result: dict[str, int] = {}
    seen: dict[int, str] = {}
    classes = root_projection.get("runner_classes")
    if not isinstance(classes, dict) or not classes:
        raise V3ServiceError("root projection runner_classes missing")
    for class_id, cls in sorted(classes.items()):
        peer = cls.get("controller_peer")
        user = peer.get("unix_user") if isinstance(peer, dict) else None
        if not isinstance(user, str) or not user:
            raise V3ServiceError(f"{class_id}: controller unix user missing")
        uid = int(resolver(user))
        if uid <= 0:
            raise V3ServiceError(f"{class_id}: controller UID must be non-root positive")
        if uid in seen:
            raise V3ServiceError(
                f"controller UID {uid} maps to both {seen[uid]} and {class_id}"
            )
        seen[uid] = class_id
        result[class_id] = uid
    return result


def _default_unit_probe(unit_name: str) -> bool | None:
    proc = subprocess.run(
        [
            "systemctl",
            "show",
            unit_name,
            "--property=LoadState",
            "--value",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    state = proc.stdout.strip()
    if state == "not-found":
        return False
    if state:
        return True
    return None


class V3Provisioner:
    """Durable root authority for one host's v3 capacity protocol."""

    def __init__(
        self,
        *,
        root_projection: dict[str, Any],
        state_store: StateStore,
        root_policy_path: pathlib.Path | None = None,
        controller_uid_by_class: dict[str, int] | None = None,
        clock: Callable[[], datetime] = _utcnow,
        start_supervisor: Callable[[dict[str, Any], pathlib.Path], None] | None = None,
        unit_probe: Callable[[str], bool | None] | None = _default_unit_probe,
    ):
        self.root = json.loads(json.dumps(root_projection))
        self.store = state_store
        self.root_policy_path = root_policy_path
        self.clock = clock
        self.unit_probe = unit_probe
        self._lock = threading.RLock()

        root_sha = self.root.get("root_policy_sha256")
        if not isinstance(root_sha, str) or HEX64.fullmatch(root_sha) is None:
            raise V3ServiceError("root_policy_sha256 invalid")
        self.classes = self.root.get("runner_classes")
        if not isinstance(self.classes, dict) or not self.classes:
            raise V3ServiceError("root projection runner_classes missing")

        if controller_uid_by_class is None:
            controller_uid_by_class = build_controller_uid_map(self.root)
        if set(controller_uid_by_class) != set(self.classes):
            raise V3ServiceError("controller UID map does not cover exactly the runner classes")
        self.uid_to_class: dict[int, str] = {}
        for class_id, raw_uid in controller_uid_by_class.items():
            uid = int(raw_uid)
            if uid <= 0:
                raise V3ServiceError("controller UID must be non-root positive")
            if uid in self.uid_to_class:
                raise V3ServiceError("controller UID maps to multiple runner classes")
            self.uid_to_class[uid] = class_id

        if start_supervisor is None:
            start_supervisor = self._start_supervisor
        self.start_supervisor = start_supervisor
        self.store.ensure()
        with self._lock:
            self._refresh_locked(reconcile=True)

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise V3ServiceError("clock must return timezone-aware datetime")
        return value.astimezone(timezone.utc)

    def _ttl_seconds(self) -> int:
        ttl = int(
            self.root["host_resource_policy"]["reservation_policy"]["ttl_seconds"]
        )
        if ttl <= 0:
            raise V3ServiceError("reservation TTL must be positive")
        return ttl

    def _class_for_uid(self, peer_uid: int) -> tuple[str, dict[str, Any]] | None:
        class_id = self.uid_to_class.get(int(peer_uid))
        if class_id is None:
            return None
        return class_id, self.classes[class_id]

    @staticmethod
    def _supervisor_unit(request_id: str) -> str:
        digest = hashlib.sha256(request_id.encode("ascii")).hexdigest()[:20]
        return f"workspace-ci-v3-supervisor-{digest}.service"

    @staticmethod
    def _receipt_status(record: dict[str, Any]) -> str:
        state = record["state"]
        if state == "RESERVED":
            return "RESERVED"
        if state in {"PREPARING", "ACCEPTED"}:
            return "ACCEPTED"
        if state == "EXPIRED":
            return "CANCELED"
        if state in {"COMPLETED", "FAILED", "CANCELED"}:
            return state
        raise V3ServiceError(f"unsupported record state {state!r}")

    @staticmethod
    def _external_status(record: dict[str, Any]) -> str:
        state = record["state"]
        if state == "EXPIRED":
            return "CANCELED"
        if state in {
            "RESERVED",
            "PREPARING",
            "ACCEPTED",
            "COMPLETED",
            "FAILED",
            "CANCELED",
        }:
            return state
        raise V3ServiceError(f"unsupported record state {state!r}")

    def _active_or_held(self, record: dict[str, Any]) -> bool:
        return record.get("state") in ACTIVE_STATES or record.get("resource_hold") is True

    def _refresh_locked(self, *, reconcile: bool) -> dict[str, dict[str, Any]]:
        now = self._now()
        records = self.store.records()

        changed: list[dict[str, Any]] = []
        for record in records.values():
            if self._active_or_held(record):
                class_id = record.get("runner_class_id")
                cls = self.classes.get(class_id)
                if cls is None:
                    raise V3ServiceError("active durable record references unknown runner class")
                if record.get("root_policy_sha256") != self.root["root_policy_sha256"]:
                    raise V3ServiceError("active durable record root policy binding mismatch")
                if record.get("root_envelope_sha256") != cls["root_envelope_sha256"]:
                    raise V3ServiceError("active durable record root envelope binding mismatch")

            if record.get("state") == "RESERVED":
                expires = _parse_time(record.get("reservation_expires_at"))
                if expires is not None and now >= expires:
                    record["state"] = "EXPIRED"
                    record["reservation_expires_at"] = None
                    record["updated_at"] = _iso(now)
                    record["resource_hold"] = False
                    changed.append(record)

            if reconcile and record.get("state") in {"PREPARING", "ACCEPTED"}:
                updated = _parse_time(record.get("updated_at"))
                age = (now - updated).total_seconds() if updated is not None else 0
                if age >= RECONCILE_GRACE_SECONDS and self.unit_probe is not None:
                    supervisor = record.get("supervisor_unit")
                    runner = record.get("runner_unit")
                    probes = []
                    for unit in (supervisor, runner):
                        if isinstance(unit, str) and unit:
                            probes.append(self.unit_probe(unit))
                    if probes and all(value is False for value in probes):
                        record["state"] = "FAILED"
                        record["reservation_expires_at"] = None
                        record["updated_at"] = _iso(now)
                        self.store.remove_jit(record["request_id"])
                        if record.get("supervisor_started") is True:
                            record["failure_reason"] = "SUPERVISOR_AND_RUNNER_UNIT_MISSING"
                            record["cleanup_verified"] = False
                            record["resource_hold"] = True
                            self.store.quarantine(
                                record["runner_class_id"],
                                request_id=record["request_id"],
                                reason=record["failure_reason"],
                                now=now,
                            )
                        else:
                            record["failure_reason"] = "PREPARING_BEFORE_SUPERVISOR_START"
                            record["cleanup_verified"] = True
                            record["resource_hold"] = False
                        changed.append(record)

        for record in changed:
            self.store.write(record)
        if changed:
            records = self.store.records()
        return records

    def _allocation_view(
        self,
        records: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        active = [record for record in records.values() if self._active_or_held(record)]
        resources: dict[str, str] = {}
        for record in active:
            for resource in record.get("reserved_resources", []):
                owner = resources.get(resource)
                if owner is not None and owner != record["request_id"]:
                    raise V3ServiceError(
                        f"durable resource ledger conflict {resource}: {owner} vs {record['request_id']}"
                    )
                resources[resource] = record["request_id"]
        return active, resources

    def _can_allocate(
        self,
        *,
        class_id: str,
        cls: dict[str, Any],
        records: dict[str, dict[str, Any]],
    ) -> bool:
        active, resources = self._allocation_view(records)
        host_max = int(
            self.root["host_resource_policy"]["migration_mode"]["host_max_active_runners"]
        )
        if len(active) >= host_max:
            return False

        project_id = cls["project_id"]
        project_max = int(cls["project_max_active_runners"])
        if sum(item["project_id"] == project_id for item in active) >= project_max:
            return False

        class_max = int(cls["max_runners"])
        if sum(item["runner_class_id"] == class_id for item in active) >= class_max:
            return False

        return not any(
            resource in resources for resource in cls["exclusive_resource_claims"]
        )

    def _response(
        self,
        operation: str,
        status: str,
        request_id: str,
        **extra: Any,
    ) -> dict[str, Any]:
        result = {
            "schema_version": 3,
            "operation": f"{operation}_RESULT",
            "status": status,
            "request_id": request_id,
        }
        result.update({key: value for key, value in extra.items() if value is not None})
        return result

    def _error(
        self,
        operation: str,
        request_id: str,
        *,
        status: str,
        code: str,
        message: str,
    ) -> dict[str, Any]:
        return self._response(
            operation,
            status,
            request_id,
            error_code=code,
            error=message[:2048],
        )

    def _validate_shape(
        self,
        request: Any,
    ) -> tuple[str, str] | tuple[None, str]:
        if not isinstance(request, dict):
            return None, "request must be a JSON object"
        operation = request.get("operation")
        if operation not in {"RESERVE", "LAUNCH", "STATUS", "CANCEL"}:
            return None, "operation unsupported"
        request_id = request.get("request_id")
        if not _valid_request_id(request_id):
            return operation, "request_id must be canonical UUID"
        if request.get("schema_version") != 3:
            return operation, "schema_version must be 3"

        required = {
            "RESERVE": {"schema_version", "operation", "request_id", "runner_name"},
            "LAUNCH": {
                "schema_version",
                "operation",
                "request_id",
                "runner_name",
                "jit_config",
            },
            "STATUS": {"schema_version", "operation", "request_id"},
            "CANCEL": {"schema_version", "operation", "request_id"},
        }[operation]
        if set(request) != required:
            return operation, "request fields differ from exact v3 operation schema"
        return operation, request_id

    def handle(self, peer_uid: int, request: Any) -> dict[str, Any]:
        with self._lock:
            shape = self._validate_shape(request)
            operation = shape[0]
            if operation is None:
                raise RequestTransportError(shape[1])
            request_id_or_error = shape[1]
            request_id = request.get("request_id")
            if not _valid_request_id(request_id):
                request_id = "00000000-0000-0000-0000-000000000000"
            if not _valid_request_id(request_id_or_error):
                return self._error(
                    operation,
                    request_id,
                    status="INVALID_REQUEST",
                    code="INVALID_REQUEST",
                    message=request_id_or_error,
                )

            peer = self._class_for_uid(peer_uid)
            if peer is None:
                return self._error(
                    operation,
                    request_id,
                    status="UNAUTHORIZED_PEER"
                    if operation in {"RESERVE", "LAUNCH"} else "MISSING",
                    code="UNAUTHORIZED_PEER",
                    message="peer UID is not mapped to a v3 runner class",
                )
            class_id, cls = peer

            if operation == "RESERVE":
                return self._reserve(class_id, cls, request)
            if operation == "LAUNCH":
                return self._launch(class_id, cls, request)
            if operation == "STATUS":
                return self._status(class_id, request)
            return self._cancel(class_id, request)

    def _validate_runner_name(
        self,
        cls: dict[str, Any],
        runner_name: Any,
    ) -> str | None:
        if not isinstance(runner_name, str) or RUNNER_NAME.fullmatch(runner_name) is None:
            return "runner_name malformed"
        if not runner_name.startswith(cls["runner_prefix"]):
            return "runner_name does not match immutable class prefix"
        return None

    def _reserve(
        self,
        class_id: str,
        cls: dict[str, Any],
        request: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = request["request_id"]
        error = self._validate_runner_name(cls, request["runner_name"])
        if error is not None:
            return self._error(
                "RESERVE",
                request_id,
                status="INVALID_REQUEST",
                code="RUNNER_NAME_INVALID",
                message=error,
            )

        records = self._refresh_locked(reconcile=True)
        existing = records.get(request_id)
        if existing is not None:
            if (
                existing.get("runner_class_id") != class_id
                or existing.get("runner_name") != request["runner_name"]
            ):
                return self._error(
                    "RESERVE",
                    request_id,
                    status="INVALID_REQUEST",
                    code="REPLAY_CONFLICT",
                    message="request_id replay differs from durable reservation identity",
                )
            return self._response(
                "RESERVE",
                "DUPLICATE",
                request_id,
                receipt_status=self._receipt_status(existing),
                reservation_expires_at=existing.get("reservation_expires_at"),
            )

        if class_id in self.store.quarantines():
            return self._response("RESERVE", "CLASS_QUARANTINED", request_id)

        if not self._can_allocate(class_id=class_id, cls=cls, records=records):
            return self._response("RESERVE", "BUSY", request_id)

        now = self._now()
        record = {
            "schema_version": 1,
            "request_id": request_id,
            "peer_uid": self.uid_to_class_inverse(class_id),
            "controller_user": cls["controller_peer"]["unix_user"],
            "runner_class_id": class_id,
            "project_id": cls["project_id"],
            "runner_name": request["runner_name"],
            "state": "RESERVED",
            "reserved_resources": list(cls["exclusive_resource_claims"]),
            "reservation_expires_at": _iso(
                now + timedelta(seconds=self._ttl_seconds())
            ),
            "root_policy_sha256": self.root["root_policy_sha256"],
            "root_envelope_sha256": cls["root_envelope_sha256"],
            "jit_sha256": None,
            "supervisor_unit": None,
            "supervisor_started": False,
            "runner_unit": None,
            "cleanup_verified": False,
            "resource_hold": False,
            "failure_reason": None,
            "created_at": _iso(now),
            "updated_at": _iso(now),
        }
        self.store.write(record)
        return self._response(
            "RESERVE",
            "RESERVED",
            request_id,
            reservation_expires_at=record["reservation_expires_at"],
        )

    def uid_to_class_inverse(self, class_id: str) -> int:
        for uid, mapped in self.uid_to_class.items():
            if mapped == class_id:
                return uid
        raise V3ServiceError("runner class has no controller UID")

    def _launch(
        self,
        class_id: str,
        cls: dict[str, Any],
        request: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = request["request_id"]
        error = self._validate_runner_name(cls, request["runner_name"])
        if error is not None:
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="RUNNER_NAME_INVALID",
                message=error,
            )
        jit = request["jit_config"]
        if not isinstance(jit, str) or not jit or len(jit.encode("utf-8")) > MAX_JIT_BYTES:
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="JIT_CONFIG_INVALID",
                message="jit_config must be non-empty and within the v3 transport bound",
            )

        records = self._refresh_locked(reconcile=True)
        record = records.get(request_id)
        if record is None or record.get("runner_class_id") != class_id:
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="RESERVATION_MISSING",
                message="LAUNCH requires a reservation owned by this controller class",
            )
        if record.get("runner_name") != request["runner_name"]:
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="REPLAY_CONFLICT",
                message="runner_name differs from reservation",
            )
        if record["state"] in {"PREPARING", "ACCEPTED"}:
            return self._response(
                "LAUNCH",
                "DUPLICATE",
                request_id,
                receipt_status="ACCEPTED",
            )
        if record["state"] == "EXPIRED":
            return self._response("LAUNCH", "RESERVATION_EXPIRED", request_id)
        if record["state"] in {"COMPLETED", "FAILED", "CANCELED"}:
            return self._response(
                "LAUNCH",
                "DUPLICATE",
                request_id,
                receipt_status=self._receipt_status(record),
            )
        if record["state"] != "RESERVED":
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="STATE_INVALID",
                message=f"cannot LAUNCH from {record['state']}",
            )

        expires = _parse_time(record.get("reservation_expires_at"))
        now = self._now()
        if expires is None or now >= expires:
            record["state"] = "EXPIRED"
            record["reservation_expires_at"] = None
            record["updated_at"] = _iso(now)
            self.store.write(record)
            return self._response("LAUNCH", "RESERVATION_EXPIRED", request_id)

        try:
            _, launch_spec = v3spec.build_launch_spec(
                root_projection=self.root,
                runner_class_id=class_id,
                request_id=request_id,
                runner_name=request["runner_name"],
                jit_config=jit,
            )
        except Exception as exc:
            return self._error(
                "LAUNCH",
                request_id,
                status="INVALID_REQUEST",
                code="ROOT_LAUNCH_SPEC_INVALID",
                message=f"root launch spec rejected: {type(exc).__name__}: {exc}",
            )

        record["state"] = "PREPARING"
        record["reservation_expires_at"] = None
        record["jit_sha256"] = hashlib.sha256(jit.encode("utf-8")).hexdigest()
        record["supervisor_unit"] = self._supervisor_unit(request_id)
        record["runner_unit"] = launch_spec["unit_name"]
        record["updated_at"] = _iso(now)
        self.store.write(record)

        try:
            jit_path = self.store.write_jit(request_id, jit)
            self.start_supervisor(record, jit_path)
            record["supervisor_started"] = True
            record["updated_at"] = _iso(self._now())
            self.store.write(record)
        except Exception as exc:
            self.store.remove_jit(request_id)
            record["state"] = "FAILED"
            record["cleanup_verified"] = True
            record["resource_hold"] = False
            record["failure_reason"] = "SUPERVISOR_START_FAILED"
            record["updated_at"] = _iso(self._now())
            self.store.write(record)
            return self._error(
                "LAUNCH",
                request_id,
                status="FAILED",
                code="SUPERVISOR_START_FAILED",
                message=f"root supervisor start failed: {type(exc).__name__}: {exc}",
            )

        return self._response("LAUNCH", "PREPARING", request_id)

    def _status(
        self,
        class_id: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = request["request_id"]
        records = self._refresh_locked(reconcile=True)
        record = records.get(request_id)
        if record is None or record.get("runner_class_id") != class_id:
            return self._response("STATUS", "MISSING", request_id)
        return self._response(
            "STATUS",
            self._external_status(record),
            request_id,
            runner_name=record.get("runner_name"),
            reservation_expires_at=record.get("reservation_expires_at"),
        )

    def _cancel(
        self,
        class_id: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = request["request_id"]
        records = self._refresh_locked(reconcile=True)
        record = records.get(request_id)
        if record is None or record.get("runner_class_id") != class_id:
            return self._response("CANCEL", "MISSING", request_id)
        if record["state"] == "RESERVED":
            record["state"] = "CANCELED"
            record["reservation_expires_at"] = None
            record["updated_at"] = _iso(self._now())
            self.store.write(record)
            return self._response("CANCEL", "CANCELED", request_id)
        if record["state"] in TERMINAL_STATES:
            return self._response("CANCEL", "ALREADY_TERMINAL", request_id)
        return self._response("CANCEL", "NOT_CANCELABLE", request_id)

    def _start_supervisor(
        self,
        record: dict[str, Any],
        jit_path: pathlib.Path,
    ) -> None:
        if self.root_policy_path is None:
            raise V3ServiceError("root policy path required for production supervisor")
        script = pathlib.Path(__file__).resolve()
        command = [
            "systemd-run",
            "--unit",
            record["supervisor_unit"],
            "--collect",
            "--property=Type=exec",
            "--property=NoNewPrivileges=yes",
            "--property=PrivateTmp=yes",
            sys.executable,
            str(script),
            "--worker",
            "--root-policy",
            str(self.root_policy_path),
            "--state-dir",
            str(self.store.root),
            "--jit-root",
            str(self.store.jit_root),
            "--request-id",
            record["request_id"],
        ]
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise V3ServiceError(
                f"systemd-run rc={proc.returncode}: {proc.stderr.strip()}"
            )


def _worker_update(
    store: StateStore,
    record: dict[str, Any],
    *,
    state: str,
    cleanup_verified: bool,
    resource_hold: bool,
    failure_reason: str | None,
) -> None:
    record["state"] = state
    record["cleanup_verified"] = cleanup_verified
    record["resource_hold"] = resource_hold
    record["failure_reason"] = failure_reason
    record["updated_at"] = _iso(_utcnow())
    store.write(record)


def run_worker(
    *,
    root_projection: dict[str, Any],
    state_store: StateStore,
    request_id: str,
    launcher: Callable[[Any, dict[str, Any]], dict[str, Any]] = runtime.launch_runner,
    unit_probe: Callable[[str], bool | None] | None = _default_unit_probe,
) -> int:
    """Consume one tmpfs JIT handoff and execute the immutable root launch spec."""

    record = state_store.read(request_id)
    if record is None or record.get("state") != "PREPARING":
        raise V3ServiceError("worker requires PREPARING durable record")

    class_id = record.get("runner_class_id")
    cls = root_projection.get("runner_classes", {}).get(class_id)
    if (
        root_projection.get("root_policy_sha256") != record.get("root_policy_sha256")
        or not isinstance(cls, dict)
        or cls.get("root_envelope_sha256") != record.get("root_envelope_sha256")
    ):
        state_store.remove_jit(request_id)
        _worker_update(
            state_store,
            record,
            state="FAILED",
            cleanup_verified=True,
            resource_hold=False,
            failure_reason="ROOT_POLICY_BINDING_MISMATCH",
        )
        return 1

    jit = state_store.consume_jit(request_id)
    digest = hashlib.sha256(jit.encode("utf-8")).hexdigest()
    if digest != record.get("jit_sha256"):
        _worker_update(
            state_store,
            record,
            state="FAILED",
            cleanup_verified=True,
            resource_hold=False,
            failure_reason="JIT_DIGEST_MISMATCH",
        )
        return 1

    request, spec = v3spec.build_launch_spec(
        root_projection=root_projection,
        runner_class_id=record["runner_class_id"],
        request_id=request_id,
        runner_name=record["runner_name"],
        jit_config=jit,
    )
    jit = ""

    result: dict[str, Any] = {}
    error: list[BaseException] = []

    def target() -> None:
        try:
            result["receipt"] = launcher(request, spec)
        except BaseException as exc:
            error.append(exc)

    thread = threading.Thread(target=target, name=f"v3-runner-{request_id}", daemon=False)
    thread.start()

    deadline = time.monotonic() + RECONCILE_GRACE_SECONDS
    while thread.is_alive() and time.monotonic() < deadline:
        if unit_probe is not None and unit_probe(spec["unit_name"]) is True:
            record["state"] = "ACCEPTED"
            record["updated_at"] = _iso(_utcnow())
            state_store.write(record)
            break
        time.sleep(0.05)

    thread.join()

    if not error:
        _worker_update(
            state_store,
            record,
            state="COMPLETED",
            cleanup_verified=True,
            resource_hold=False,
            failure_reason=None,
        )
        return 0

    exc = error[0]
    cleanup_failed = isinstance(exc, runtime.RuntimeCleanupError)
    reason = f"{type(exc).__name__}: {exc}"[:2048]
    _worker_update(
        state_store,
        record,
        state="FAILED",
        cleanup_verified=not cleanup_failed,
        resource_hold=cleanup_failed,
        failure_reason=reason,
    )
    if cleanup_failed:
        state_store.quarantine(
            record["runner_class_id"],
            request_id=request_id,
            reason="RUNTIME_CLEANUP_FAILED",
            now=_utcnow(),
        )
    return 1


def peer_uid(conn: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise V3ServiceError("SO_PEERCRED is required")
    raw = conn.getsockopt(
        socket.SOL_SOCKET,
        socket.SO_PEERCRED,
        struct.calcsize("3i"),
    )
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def read_request(conn: socket.socket) -> dict[str, Any]:
    handle = conn.makefile("rb")
    line = handle.readline(MAX_REQUEST_BYTES + 1)
    if not line:
        raise RequestTransportError("empty request")
    if len(line) > MAX_REQUEST_BYTES:
        raise RequestTransportError("request exceeds transport size limit")
    if handle.readline(2):
        raise RequestTransportError("exactly one JSON object is allowed")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise RequestTransportError("request is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RequestTransportError("request must be a JSON object")
    return value


def serve(
    service: V3Provisioner,
    *,
    socket_path: pathlib.Path = DEFAULT_SOCKET,
    socket_group: str = DEFAULT_SOCKET_GROUP,
) -> None:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(socket_path.parent, 0o711)
    try:
        socket_path.unlink()
    except FileNotFoundError:
        pass

    import grp

    gid = grp.getgrnam(socket_group).gr_gid
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o660)
        os.chown(socket_path, 0, gid)
        server.listen(64)
        while True:
            conn, _ = server.accept()
            with conn:
                uid = peer_uid(conn)
                try:
                    request = read_request(conn)
                    response = service.handle(uid, request)
                except RequestTransportError as exc:
                    response = {
                        "schema_version": 3,
                        "transport_status": "ERROR",
                        "error": f"{type(exc).__name__}: {exc}"[:2048],
                    }
                conn.sendall(
                    (json.dumps(response, sort_keys=True) + "\n").encode("utf-8")
                )
    finally:
        server.close()
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-policy", type=pathlib.Path, default=DEFAULT_ROOT_POLICY)
    parser.add_argument("--state-dir", type=pathlib.Path, default=DEFAULT_STATE)
    parser.add_argument("--jit-root", type=pathlib.Path, default=DEFAULT_JIT_ROOT)
    parser.add_argument("--socket", type=pathlib.Path, default=DEFAULT_SOCKET)
    parser.add_argument("--socket-group", default=DEFAULT_SOCKET_GROUP)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--request-id")
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise V3ServiceError("v3 provisioner must run as root")

    root_projection = _load_json(args.root_policy)
    store = StateStore(args.state_dir, args.jit_root)
    if args.worker:
        if not _valid_request_id(args.request_id):
            raise V3ServiceError("--worker requires canonical --request-id")
        return run_worker(
            root_projection=root_projection,
            state_store=store,
            request_id=args.request_id,
        )

    service = V3Provisioner(
        root_projection=root_projection,
        state_store=store,
        root_policy_path=args.root_policy,
    )
    serve(service, socket_path=args.socket, socket_group=args.socket_group)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
