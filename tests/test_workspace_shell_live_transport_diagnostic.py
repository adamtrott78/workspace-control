#!/usr/bin/env python3
"""Live diagnostic for Workspace Shell isolation on the Lambda host.

Runs only on the bounded lambda-workspace-control runner. It performs read-only
systemd observations and verifies that the sibling workspace-control runner
cannot connect to the private Workspace Shell loopback frontend. The actual MCP
transport is accepted separately through the dedicated tunnel/plugin path.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import unittest


UNITS = (
    "workspace-shell-job-launcher.service",
    "workspace-shell-root-broker.service",
    "workspace-shell-mcp.service",
    "workspace-shell-tunnel.service",
)

SHOW_PROPERTIES = (
    "Id",
    "LoadState",
    "ActiveState",
    "SubState",
    "Result",
    "MainPID",
    "ExecMainPID",
    "ExecMainCode",
    "ExecMainStatus",
    "NRestarts",
    "User",
    "Group",
    "StatusText",
    "ActiveEnterTimestamp",
    "ExecMainStartTimestamp",
    "FragmentPath",
)


def systemctl_show(unit: str) -> dict[str, str]:
    cp = subprocess.run(
        [
            "/usr/bin/systemctl",
            "show",
            unit,
            "--no-pager",
            *[f"--property={name}" for name in SHOW_PROPERTIES],
        ],
        check=False,
        text=True,
        capture_output=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    if cp.returncode != 0:
        raise AssertionError(
            f"systemctl show failed for {unit}: rc={cp.returncode} stderr={cp.stderr.strip()}"
        )
    observed: dict[str, str] = {}
    for line in cp.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in SHOW_PROPERTIES:
            observed[key] = value
    return observed


def systemctl_enabled(unit: str) -> tuple[int, str]:
    cp = subprocess.run(
        ["/usr/bin/systemctl", "is-enabled", unit],
        check=False,
        text=True,
        capture_output=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    return cp.returncode, cp.stdout.strip()


@unittest.skipUnless(
    os.environ.get("RUNNER_NAME", "").startswith("lambda-workspace-control"),
    "live Workspace Shell diagnostic runs only on bounded Lambda workspace-control runner",
)
class WorkspaceShellLiveTransportDiagnostic(unittest.TestCase):
    def test_live_transport_substrate(self) -> None:
        report: dict[str, object] = {
            "schema": "workspace-shell-live-transport-diagnostic.v1",
            "runner_name": os.environ.get("RUNNER_NAME"),
            "units": {},
            "frontend_tcp_8797": None,
        }

        failures: list[str] = []
        for unit in UNITS:
            state = systemctl_show(unit)
            enabled_rc, enabled_state = systemctl_enabled(unit)
            report["units"][unit] = {
                **state,
                "is_enabled_rc": enabled_rc,
                "is_enabled": enabled_state,
            }

            if state.get("LoadState") != "loaded":
                failures.append(f"{unit}: LoadState={state.get('LoadState')!r}")
            if state.get("ActiveState") != "active":
                failures.append(f"{unit}: ActiveState={state.get('ActiveState')!r}")
            if state.get("SubState") != "running":
                failures.append(f"{unit}: SubState={state.get('SubState')!r}")
            if enabled_state != "disabled":
                failures.append(f"{unit}: boot state={enabled_state!r}")

        try:
            with socket.create_connection(("127.0.0.1", 8797), timeout=2):
                report["frontend_tcp_8797"] = "UNEXPECTEDLY_REACHABLE"
                failures.append(
                    "workspace-control sibling runner unexpectedly reached private Workspace Shell loopback TCP 8797"
                )
        except OSError as exc:
            report["frontend_tcp_8797"] = f"ISOLATED:{type(exc).__name__}:{exc}"

        print(
            "WORKSPACE_SHELL_LIVE_DIAGNOSTIC="
            + json.dumps(report, sort_keys=True, separators=(",", ":"))
        )

        self.assertFalse(failures, " ; ".join(failures))


if __name__ == "__main__":
    unittest.main()
