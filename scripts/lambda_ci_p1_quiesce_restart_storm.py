#!/usr/bin/env python3
"""One-shot pre-bootstrap quiesce for the pre-existing research CPU restart storm.

This helper is intentionally narrower than the P1 bootstrap installer. It does
not install files, change policy, restart a controller, reconcile anything, or
activate workspace-control. It proves the already-observed research-engine CPU
controller is still in a persistent on-failure restart storm with no local
research execution, stops exactly that one controller, and proves it remains
stably inactive/dead. The reviewed P1 bootstrap can then preserve that exact
inactive state while installing the independent L0 maintenance plane.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import pwd
import subprocess
import sys
import time
from typing import Any

RUNUSER_BIN = pathlib.Path("/usr/sbin/runuser")
RESEARCH_CPU = "workspace-ci-controller@research-engine-cpu.service"
MIN_RESTARTS = 12110
STORM_OBSERVATION_SECONDS = 6
STORM_CONFIRM_SECONDS = 6
QUIESCENT_CONFIRM_SECONDS = 6

REQUIRED_ACTIVE_SERVICES = [
    "workspace-ci-provisioner.service",
    "workspace-ci-reconciler.service",
    "workspace-ci-reconcile-controller.service",
    "workspace-ci-controller@research-engine-gpu.service",
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
]


class QuiesceError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    check: bool = True,
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = argv
    if user is not None:
        command = [str(RUNUSER_BIN), "-u", user, "--", *argv]
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise QuiesceError(
            f"command failed rc={proc.returncode}: {command!r}: "
            + proc.stderr.strip()
        )
    return proc


def service_snapshot(name: str) -> dict[str, str]:
    argv = ["systemctl", "show", name, "--no-pager"]
    for prop in (
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "NRestarts",
        "ExecMainStatus",
        "Restart",
        "Result",
    ):
        argv.extend(["-p", prop])
    proc = run(argv, check=False)
    values: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def _parse_nonnegative(raw: str | None, field: str) -> int:
    if raw is None or raw == "":
        raise QuiesceError(f"{field} missing")
    try:
        value = int(raw)
    except ValueError as exc:
        raise QuiesceError(f"{field} is not an integer") from exc
    if value < 0:
        raise QuiesceError(f"{field} is negative")
    return value


def _stable_state_predicate(state: dict[str, str]) -> bool:
    try:
        _parse_nonnegative(state.get("NRestarts"), "NRestarts")
        exit_status = _parse_nonnegative(
            state.get("ExecMainStatus"), "ExecMainStatus"
        )
    except QuiesceError:
        return False
    if (
        state.get("LoadState") != "loaded"
        or state.get("UnitFileState") not in {"enabled", "enabled-runtime"}
    ):
        return False
    active = state.get("ActiveState")
    sub = state.get("SubState")
    if active == "active":
        return sub == "running" and exit_status == 0
    if active == "inactive":
        return sub == "dead"
    if active == "failed":
        return sub == "failed" and exit_status > 0
    return False


def _restart_storm_sample(state: dict[str, str]) -> int:
    restarts = _parse_nonnegative(state.get("NRestarts"), "NRestarts")
    exit_status = _parse_nonnegative(
        state.get("ExecMainStatus"), "ExecMainStatus"
    )
    if state.get("LoadState") != "loaded":
        raise QuiesceError("research CPU unit is not loaded")
    if state.get("UnitFileState") not in {"enabled", "enabled-runtime"}:
        raise QuiesceError("research CPU unit is not enabled")
    if state.get("Restart") != "on-failure":
        raise QuiesceError("research CPU unit restart policy is not on-failure")
    if restarts < MIN_RESTARTS:
        raise QuiesceError(
            f"research CPU restart count below reviewed incident floor: "
            f"{restarts} < {MIN_RESTARTS}"
        )

    active = state.get("ActiveState")
    sub = state.get("SubState")
    if active == "active" and sub == "running":
        if exit_status != 0:
            raise QuiesceError(
                "active/running research CPU has invalid ExecMainStatus"
            )
    elif active == "activating" and sub == "auto-restart":
        if exit_status == 0:
            raise QuiesceError(
                "auto-restart research CPU has zero ExecMainStatus"
            )
    elif active == "failed" and sub == "failed":
        if exit_status == 0:
            raise QuiesceError(
                "failed research CPU has zero ExecMainStatus"
            )
    else:
        raise QuiesceError(
            "research CPU is outside reviewed restart-storm states: "
            + json.dumps(state, sort_keys=True)
        )
    return restarts


def service_active(name: str) -> bool:
    return (
        run(["systemctl", "is-active", "--quiet", name], check=False).returncode
        == 0
    )


def require_other_control_services_active() -> None:
    missing = [service for service in REQUIRED_ACTIVE_SERVICES if not service_active(service)]
    if missing:
        raise QuiesceError(
            "required non-target control services are not active: "
            + ",".join(missing)
        )


def no_active_research_execution() -> None:
    proc = run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            "workspace-ci-research-engine-*.service",
        ],
        check=False,
    )
    if proc.returncode not in {0, 1}:
        raise QuiesceError("unable to inspect research-engine execution units")
    active: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] in {
            "active",
            "activating",
            "deactivating",
        }:
            active.append(line)
    if active:
        raise QuiesceError(
            "research-engine execution is active; refusing controller quiesce:\n"
            + "\n".join(active)
        )


def prove_persistent_restart_storm() -> dict[str, Any]:
    require_other_control_services_active()
    no_active_research_execution()

    first = service_snapshot(RESEARCH_CPU)
    if _stable_state_predicate(first):
        time.sleep(STORM_OBSERVATION_SECONDS)
        stable_second = service_snapshot(RESEARCH_CPU)
        if stable_second == first and _stable_state_predicate(stable_second):
            return {
                "status": "NO_QUIESCE_REQUIRED",
                "reason": "research CPU is already exactly stable",
                "stable_state": stable_second,
            }
        first = stable_second

    first_restarts = _restart_storm_sample(first)

    time.sleep(STORM_OBSERVATION_SECONDS)
    second = service_snapshot(RESEARCH_CPU)
    second_restarts = _restart_storm_sample(second)
    if second_restarts <= first_restarts:
        raise QuiesceError(
            "research CPU restart count did not increase during storm observation: "
            + json.dumps({"first": first, "second": second}, sort_keys=True)
        )

    time.sleep(STORM_CONFIRM_SECONDS)
    third = service_snapshot(RESEARCH_CPU)
    third_restarts = _restart_storm_sample(third)
    if third_restarts <= second_restarts:
        raise QuiesceError(
            "research CPU restart count stopped increasing before mutation boundary: "
            + json.dumps(
                {"first": first, "second": second, "third": third},
                sort_keys=True,
            )
        )

    require_other_control_services_active()
    no_active_research_execution()
    return {
        "status": "PERSISTENT_RESTART_STORM",
        "first": first,
        "second": second,
        "third": third,
    }


def quiesce_and_verify() -> dict[str, Any]:
    proof = prove_persistent_restart_storm()
    if proof["status"] == "NO_QUIESCE_REQUIRED":
        return proof

    run(["systemctl", "stop", RESEARCH_CPU])

    first = service_snapshot(RESEARCH_CPU)
    if not _stable_state_predicate(first):
        raise QuiesceError(
            "research CPU did not enter a reviewed stable state after stop: "
            + json.dumps(first, sort_keys=True)
        )
    if first.get("ActiveState") != "inactive" or first.get("SubState") != "dead":
        raise QuiesceError(
            "research CPU did not become inactive/dead after stop: "
            + json.dumps(first, sort_keys=True)
        )

    time.sleep(QUIESCENT_CONFIRM_SECONDS)
    second = service_snapshot(RESEARCH_CPU)
    if second != first:
        raise QuiesceError(
            "research CPU changed after explicit quiesce: "
            + json.dumps({"first": first, "second": second}, sort_keys=True)
        )

    require_other_control_services_active()
    no_active_research_execution()
    return {
        "status": "QUIESCED_STABLE_INACTIVE",
        "mutation": {
            "command": ["systemctl", "stop", RESEARCH_CPU],
            "service": RESEARCH_CPU,
        },
        "storm_proof": proof,
        "stable_inactive_state": second,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("ERROR=ROOT_REQUIRED_RUN_VIA_SUDO", file=sys.stderr)
        return 70
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        print("ERROR=RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT", file=sys.stderr)
        return 70

    repo_proc = run(
        ["git", "rev-parse", "--show-toplevel"],
        user=invoker,
    )
    repo = pathlib.Path(repo_proc.stdout.strip()).resolve()
    head = run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        user=invoker,
    ).stdout.strip()
    if head != args.expected_head:
        raise QuiesceError(
            f"unexpected source HEAD: actual={head} expected={args.expected_head}"
        )
    tracked = run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        user=invoker,
    ).stdout.strip()
    if tracked:
        raise QuiesceError("tracked reviewed source is dirty:\n" + tracked)

    print(f"repo={repo}")
    print(f"head={head}")
    result = quiesce_and_verify()
    print("P1_RESEARCH_CPU_QUIESCE_RECEIPT=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QuiesceError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
