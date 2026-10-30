#!/usr/bin/env python3
"""Client for the v3 offline payload broker.

The client sends argv + cwd only. It never serializes the runner environment,
GitHub token, JIT config, workflow metadata, or repository credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import struct
import sys


MAX_REQUEST_BYTES = 64 * 1024
MAX_OUTPUT_FRAME = 64 * 1024


class PayloadClientError(RuntimeError):
    pass


def _recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = conn.recv(remaining)
        if not chunk:
            raise PayloadClientError("unexpected broker EOF")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def execute(socket_path: pathlib.Path, argv: list[str], cwd: pathlib.Path) -> int:
    if not argv:
        raise PayloadClientError("payload argv is empty")
    request = json.dumps(
        {"argv": argv, "cwd": str(cwd.resolve(strict=True))},
        separators=(",", ":"),
    ).encode("utf-8")
    if len(request) > MAX_REQUEST_BYTES:
        raise PayloadClientError("payload request exceeds transport bound")
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.connect(str(socket_path))
        conn.sendall(struct.pack("!I", len(request)) + request)
        conn.shutdown(socket.SHUT_WR)
        while True:
            size = struct.unpack("!I", _recv_exact(conn, 4))[0]
            if size == 0:
                return struct.unpack("!i", _recv_exact(conn, 4))[0]
            if size > MAX_OUTPUT_FRAME:
                raise PayloadClientError("broker output frame exceeds bound")
            raw = _recv_exact(conn, size)
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", type=pathlib.Path)
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    socket_path = args.socket
    if socket_path is None:
        raw = os.environ.get("P5_PAYLOAD_EXEC_SOCKET", "")
        if not raw:
            raise PayloadClientError("P5_PAYLOAD_EXEC_SOCKET is missing")
        socket_path = pathlib.Path(raw)
    argv = list(args.argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    return execute(socket_path, argv, pathlib.Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
