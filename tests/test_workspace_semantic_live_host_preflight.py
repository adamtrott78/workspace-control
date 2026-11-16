#!/usr/bin/env python3
"""Read-only, content-free Lambda host preflight for semantic execution.

This test is intentionally diagnostic rather than promotional. It runs only on
the bounded workspace-control self-hosted runner and reports booleans/fixed
service-state fields. It does not print tailnet identity, user identity, DSNs,
credentials, process command lines, environment values, or arbitrary paths.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import unittest


RUNNER = os.environ.get("RUNNER_NAME", "")
ON_BOUNDED_RUNNER = RUNNER.startswith("lambda-workspace-control-")


def _run(argv: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        },
    )


def _systemd_state(unit: str) -> dict[str, object]:
    cp = _run(
        [
            "/usr/bin/systemctl",
            "show",
            unit,
            "--no-pager",
            "--property=LoadState",
            "--property=ActiveState",
            "--property=SubState",
        ]
    )
    values: dict[str, str] = {}
    if cp.returncode == 0:
        for line in cp.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                if key in {"LoadState", "ActiveState", "SubState"}:
                    values[key] = value
    return {
        "query_rc": cp.returncode,
        "load": values.get("LoadState"),
        "active": values.get("ActiveState"),
        "sub": values.get("SubState"),
    }


def _tcp_open(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        return sock.connect_ex(("127.0.0.1", port)) == 0
    finally:
        sock.close()


def _tailscale_status() -> dict[str, object]:
    binary = shutil.which("tailscale")
    if binary is None:
        return {
            "cli_present": False,
            "status_rc": None,
            "json_parseable": False,
            "backend_state": None,
            "self_online": None,
        }
    cp = _run([binary, "status", "--json"], timeout=5)
    parsed = None
    try:
        parsed = json.loads(cp.stdout) if cp.returncode == 0 else None
    except json.JSONDecodeError:
        parsed = None
    self_state = parsed.get("Self") if isinstance(parsed, dict) else None
    return {
        "cli_present": True,
        "status_rc": cp.returncode,
        "json_parseable": isinstance(parsed, dict),
        "backend_state": (
            parsed.get("BackendState")
            if isinstance(parsed, dict)
            else None
        ),
        "self_online": (
            self_state.get("Online")
            if isinstance(self_state, dict)
            else None
        ),
    }


def _tailscale_serve_status() -> dict[str, object]:
    binary = shutil.which("tailscale")
    if binary is None:
        return {
            "query_rc": None,
            "json_parseable": False,
            "web_config_present": False,
            "tcp_config_present": False,
        }
    cp = _run([binary, "serve", "status", "--json"], timeout=5)
    parsed = None
    try:
        parsed = json.loads(cp.stdout) if cp.returncode == 0 else None
    except json.JSONDecodeError:
        parsed = None
    return {
        "query_rc": cp.returncode,
        "json_parseable": isinstance(parsed, dict),
        "web_config_present": bool(
            parsed.get("Web")
            if isinstance(parsed, dict)
            else False
        ),
        "tcp_config_present": bool(
            parsed.get("TCP")
            if isinstance(parsed, dict)
            else False
        ),
    }


@unittest.skipUnless(
    ON_BOUNDED_RUNNER,
    "semantic live-host preflight runs only on bounded workspace-control runner",
)
class SemanticLiveHostPreflight(unittest.TestCase):
    def test_content_free_host_capabilities(self) -> None:
        pg_isready = shutil.which("pg_isready")
        pg_ready_rc = None
        if pg_isready is not None:
            pg_ready_rc = _run(
                [
                    pg_isready,
                    "-h",
                    "127.0.0.1",
                    "-p",
                    "5432",
                    "-t",
                    "2",
                ],
                timeout=4,
            ).returncode

        report = {
            "schema": "workspace-semantic-live-host-preflight.v1",
            "runner_class": "lambda-workspace-control",
            "postgres": {
                "psql_present": shutil.which("psql") is not None,
                "pg_isready_present": pg_isready is not None,
                "postgres_binary_present": (
                    shutil.which("postgres") is not None
                ),
                "tcp_5432_open": _tcp_open(5432),
                "pg_isready_rc": pg_ready_rc,
                "units": {
                    "postgresql.service": _systemd_state(
                        "postgresql.service"
                    ),
                    "postgresql@17-main.service": _systemd_state(
                        "postgresql@17-main.service"
                    ),
                    "postgresql-17.service": _systemd_state(
                        "postgresql-17.service"
                    ),
                },
            },
            "tailscale": {
                **_tailscale_status(),
                "tailscaled_unit": _systemd_state(
                    "tailscaled.service"
                ),
                "serve": _tailscale_serve_status(),
            },
            "operator_bridge": {
                "tcp_8765_open": _tcp_open(8765),
            },
        }

        serialized = json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
        )
        print("SEMANTIC_LIVE_HOST_PREFLIGHT=" + serialized)

        # Contract checks only: diagnostics may legitimately report
        # unavailable dependencies. Do not convert absence into fake success.
        self.assertNotIn("loginName", serialized)
        self.assertNotIn("TailscaleIPs", serialized)
        self.assertNotIn("postgresql://", serialized)
        self.assertNotIn("SEMANTIC_EXECUTION_POSTGRES_DSN", serialized)
        self.assertNotIn("WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN", serialized)


if __name__ == "__main__":
    unittest.main()
