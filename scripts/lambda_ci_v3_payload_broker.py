#!/usr/bin/env python3
"""One-shot payload executor for v3 offline model classes.

The broker is started by the root runtime in a private network namespace. It
accepts exactly one request from the owning online runner unit over AF_UNIX,
verifies the peer PID belongs to that exact runner systemd unit, and executes
only the root-bound promoted-runtime Python. No caller environment is accepted.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import struct
import subprocess
from typing import Any


MAX_REQUEST_BYTES = 64 * 1024
MAX_ARG_COUNT = 256
MAX_ARG_BYTES = 32 * 1024
MAX_OUTPUT_FRAME = 64 * 1024
SAFE_ENV_KEYS = frozenset(
    {
        "PATH", "HOME", "TMPDIR", "PYTHONNOUSERSITE",
        "HF_HOME", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
        "HF_HUB_DISABLE_TELEMETRY", "DO_NOT_TRACK", "VLLM_NO_USAGE_STATS",
        "CUDA_VISIBLE_DEVICES", "P5_GPU_TARGET_UUID", "P5_GPU_TARGET_UUIDS",
        "P5_GPU_SELECTED_DEVICE", "P5_GPU_SELECTED_DEVICES",
        "P5_GPU_DENIED_DEVICES", "P5_GPU_SUPPORT_DEVICES",
        "P5_MODEL_ID", "P5_MODEL_OBJECT_ID", "P5_MODEL_OBJECT_ROOT",
        "P5_MODEL_PATH", "P5_MODEL_REPOSITORY",
        "P5_MODEL_REVISION", "P5_MODEL_TREE_SHA256",
        "P5_MODEL_MANIFEST_SHA256", "P5_MODEL_DESCRIPTOR_SHA256",
        "P5_MODEL_PROMOTION_RECEIPT_SHA256", "P5_EXPANDED_RUNTIME",
        "P5_EXPANDED_RUNTIME_PYTHON", "P5_EXPANDED_RUNTIME_RECEIPT",
        "P5_EXPANDED_RUNTIME_TREE_SHA256",
        "P5_EXPANDED_RUNTIME_MANIFEST_SHA256", "P5_EXPANDED_RUNTIME_OBJECT",
        "GLOO_SOCKET_IFNAME", "NCCL_SOCKET_IFNAME",
    }
)


class PayloadBrokerError(RuntimeError):
    pass


def _recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = conn.recv(remaining)
        if not chunk:
            raise PayloadBrokerError("unexpected EOF")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_request(conn: socket.socket) -> dict[str, Any]:
    size = struct.unpack("!I", _recv_exact(conn, 4))[0]
    if size <= 0 or size > MAX_REQUEST_BYTES:
        raise PayloadBrokerError("request size invalid")
    try:
        value = json.loads(_recv_exact(conn, size))
    except Exception as exc:
        raise PayloadBrokerError("request JSON invalid") from exc
    if not isinstance(value, dict) or set(value) != {"argv", "cwd"}:
        raise PayloadBrokerError("request keys invalid")
    return value


def _send_frame(conn: socket.socket, raw: bytes) -> None:
    if len(raw) > MAX_OUTPUT_FRAME:
        raise PayloadBrokerError("output frame too large")
    conn.sendall(struct.pack("!I", len(raw)) + raw)


def _send_terminal(conn: socket.socket, returncode: int) -> None:
    conn.sendall(struct.pack("!Ii", 0, int(returncode)))


def peer_credentials(conn: socket.socket) -> tuple[int, int, int]:
    if not hasattr(socket, "SO_PEERCRED"):
        raise PayloadBrokerError("SO_PEERCRED required")
    raw = conn.getsockopt(
        socket.SOL_SOCKET,
        socket.SO_PEERCRED,
        struct.calcsize("3i"),
    )
    return struct.unpack("3i", raw)


def peer_in_expected_unit(
    pid: int,
    expected_unit: str,
    *,
    proc_root: pathlib.Path = pathlib.Path("/proc"),
) -> bool:
    if pid <= 0 or not expected_unit.endswith(".service"):
        return False
    try:
        raw = (proc_root / str(pid) / "cgroup").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return False
    for line in raw.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        if expected_unit in pathlib.PurePosixPath(parts[2]).parts:
            return True
    return False


def _inside(path: pathlib.Path, roots: tuple[pathlib.Path, ...]) -> bool:
    resolved = path.resolve(strict=True)
    if not resolved.is_dir():
        return False
    for root in roots:
        try:
            resolved.relative_to(root.resolve(strict=True))
            return True
        except ValueError:
            continue
    return False


def validate_request(
    request: dict[str, Any],
    *,
    runtime_python: pathlib.Path,
    allowed_cwd_roots: tuple[pathlib.Path, ...],
) -> tuple[list[str], pathlib.Path]:
    argv = request.get("argv")
    cwd_raw = request.get("cwd")
    if not isinstance(argv, list) or not argv or len(argv) > MAX_ARG_COUNT:
        raise PayloadBrokerError("argv invalid")
    if any(
        not isinstance(value, str)
        or not value
        or "\x00" in value
        or len(value.encode("utf-8")) > MAX_ARG_BYTES
        for value in argv
    ):
        raise PayloadBrokerError("argv member invalid")
    runtime = runtime_python.resolve(strict=True)
    if pathlib.Path(argv[0]).resolve(strict=True) != runtime:
        raise PayloadBrokerError(
            "payload executable is not root-bound runtime Python"
        )
    if not isinstance(cwd_raw, str) or not pathlib.Path(cwd_raw).is_absolute():
        raise PayloadBrokerError("cwd must be absolute")
    cwd = pathlib.Path(cwd_raw)
    if not _inside(cwd, allowed_cwd_roots):
        raise PayloadBrokerError("cwd escapes root-owned payload roots")
    return list(argv), cwd.resolve(strict=True)


def safe_environment(source: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in source.items() if key in SAFE_ENV_KEYS}


def serve_once(
    *,
    socket_path: pathlib.Path,
    expected_uid: int,
    expected_runner_unit: str,
    runtime_python: pathlib.Path,
    allowed_cwd_roots: tuple[pathlib.Path, ...],
) -> int:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        socket_path.unlink()
    except FileNotFoundError:
        pass
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        server.listen(1)
        conn, _ = server.accept()
        with conn:
            pid, uid, _gid = peer_credentials(conn)
            if uid != expected_uid:
                raise PayloadBrokerError("peer UID mismatch")
            if not peer_in_expected_unit(pid, expected_runner_unit):
                raise PayloadBrokerError("peer PID is not in expected runner unit")
            request = _recv_request(conn)
            argv, cwd = validate_request(
                request,
                runtime_python=runtime_python,
                allowed_cwd_roots=allowed_cwd_roots,
            )
            proc = subprocess.Popen(
                argv,
                cwd=str(cwd),
                env=safe_environment(dict(os.environ)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                bufsize=0,
                close_fds=True,
            )
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(MAX_OUTPUT_FRAME)
                if not chunk:
                    break
                _send_frame(conn, chunk)
            returncode = proc.wait()
            _send_terminal(conn, returncode)
            return int(returncode)
    finally:
        server.close()
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", type=pathlib.Path, required=True)
    parser.add_argument("--expected-uid", type=int, required=True)
    parser.add_argument("--expected-runner-unit", required=True)
    parser.add_argument("--runtime-python", type=pathlib.Path, required=True)
    parser.add_argument("--job-root", type=pathlib.Path, required=True)
    parser.add_argument("--staging-root", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != args.expected_uid:
        raise PayloadBrokerError(
            "broker effective UID differs from root-bound project identity"
        )
    return serve_once(
        socket_path=args.socket,
        expected_uid=args.expected_uid,
        expected_runner_unit=args.expected_runner_unit,
        runtime_python=args.runtime_python,
        allowed_cwd_roots=(args.job_root, args.staging_root),
    )


if __name__ == "__main__":
    raise SystemExit(main())
