#!/usr/bin/env python3
"""Local root provisioner service for Lambda CI P5.

The service has no GitHub credential and accepts only strict project/profile/JIT
requests over a root-owned Unix socket from ci-controller.
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
import threading
from typing import Any, Callable

import lambda_ci_provisioner as policy
import lambda_ci_runtime as runtime

DEFAULT_SOCKET = pathlib.Path("/run/workspace-ci/provisioner.sock")
DEFAULT_STATE = pathlib.Path("/var/lib/workspace-ci/provisioner")
MAX_REQUEST_BYTES = 192 * 1024


class ServiceError(RuntimeError):
    pass


class StateStore:
    def __init__(self, root: pathlib.Path):
        self.root = root

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

    def path(self, request_id: str) -> pathlib.Path:
        return self.root / f"{request_id}.json"

    def claim(self, request_id: str, metadata: dict[str, Any]) -> bool:
        self.ensure()
        path = self.path(request_id)
        payload = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return True

    def update(self, request_id: str, metadata: dict[str, Any]) -> None:
        self.ensure()
        path = self.path(request_id)
        tmp = self.root / f".{request_id}.{os.getpid()}.tmp"
        tmp.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)


class ProvisionerService:
    def __init__(
        self,
        *,
        manifest: dict[str, Any],
        profiles: dict[str, Any],
        pins: dict[str, Any],
        state_store: StateStore,
        controller_uid: int,
        launcher: Callable[[Any, dict[str, Any]], dict[str, Any]] = runtime.launch_cpu_runner,
    ):
        self.manifest = manifest
        self.profiles = profiles
        self.pins = pins
        self.state_store = state_store
        self.controller_uid = controller_uid
        self.launcher = launcher
        self._lock = threading.Lock()
        self._active: set[str] = set()

    def _nonsecret_record(self, req, status: str, **extra: Any) -> dict[str, Any]:
        record = {
            "schema_version": 1,
            "request_id": req.request_id,
            "project_id": req.project_id,
            "profile": req.profile,
            "runner_name": req.runner_name,
            "status": status,
        }
        record.update(extra)
        return record

    def _worker(self, req, spec: dict[str, Any]) -> None:
        try:
            result = self.launcher(req, spec)
            record = self._nonsecret_record(req, "COMPLETED", result=result)
        except Exception as exc:
            record = self._nonsecret_record(
                req,
                "FAILED",
                error_type=type(exc).__name__,
                error=str(exc),
            )
        finally:
            with self._lock:
                self._active.discard(req.request_id)
        self.state_store.update(req.request_id, record)

    def handle_request(self, data: dict[str, Any], *, peer_uid: int) -> dict[str, Any]:
        if peer_uid != self.controller_uid:
            raise ServiceError("peer UID is not ci-controller")

        req = policy.validate_request(data, self.manifest)
        if req.profile != "cpu-test":
            raise ServiceError("P5 pilot provisioner enables cpu-test only")

        spec = policy.build_launch_spec(req, self.manifest, self.profiles, self.pins)
        concurrency = int(self.manifest["concurrency"])

        with self._lock:
            if len(self._active) >= concurrency:
                return {
                    "schema_version": 1,
                    "status": "BUSY",
                    "request_id": req.request_id,
                }

            accepted = self._nonsecret_record(req, "ACCEPTED")
            if not self.state_store.claim(req.request_id, accepted):
                return {
                    "schema_version": 1,
                    "status": "DUPLICATE",
                    "request_id": req.request_id,
                }

            self._active.add(req.request_id)
            thread = threading.Thread(
                target=self._worker,
                args=(req, spec),
                name=f"workspace-ci-{req.request_id}",
                daemon=True,
            )
            thread.start()

        return accepted


def peer_uid(conn: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise ServiceError("SO_PEERCRED is required")
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def read_request(conn: socket.socket) -> dict[str, Any]:
    handle = conn.makefile("rb")
    line = handle.readline(MAX_REQUEST_BYTES + 1)
    if not line:
        raise ServiceError("empty request")
    if len(line) > MAX_REQUEST_BYTES:
        raise ServiceError("request exceeds transport size limit")
    if handle.readline(2):
        raise ServiceError("exactly one JSON object is allowed")
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ServiceError("request is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ServiceError("request must be a JSON object")
    return data


def serve(
    service: ProvisionerService,
    *,
    socket_path: pathlib.Path = DEFAULT_SOCKET,
    socket_group: str = "workspace-ci-controller",
) -> None:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()

    group = grp.getgrnam(socket_group)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    os.chown(socket_path, 0, group.gr_gid)
    os.chmod(socket_path, 0o660)
    server.listen(8)

    try:
        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    response = service.handle_request(
                        read_request(conn),
                        peer_uid=peer_uid(conn),
                    )
                except Exception as exc:
                    response = {
                        "schema_version": 1,
                        "status": "REJECTED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                conn.sendall((json.dumps(response, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        server.close()
        if socket_path.exists():
            socket_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", type=pathlib.Path, default=DEFAULT_SOCKET)
    parser.add_argument("--state-dir", type=pathlib.Path, default=DEFAULT_STATE)
    parser.add_argument("--manifest", type=pathlib.Path, default=policy.DEFAULT_MANIFEST)
    parser.add_argument("--profiles", type=pathlib.Path, default=policy.DEFAULT_PROFILES)
    parser.add_argument("--pins", type=pathlib.Path, default=policy.DEFAULT_PINS)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise ServiceError("provisioner service must run as root")

    controller = pwd.getpwnam("ci-controller")
    store = StateStore(args.state_dir)
    service = ProvisionerService(
        manifest=policy._load(args.manifest),
        profiles=policy._load(args.profiles),
        pins=policy._load(args.pins),
        state_store=store,
        controller_uid=controller.pw_uid,
    )
    serve(service, socket_path=args.socket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
