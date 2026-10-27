#!/usr/bin/env python3
"""One-shot recovery for controllers failed by rollback-time startup cancellation.

This helper is intentionally narrower than bootstrap. It performs no file
installation, reconciliation, policy change, activation, or workspace-control
mutation. It restores exactly the three non-CPU project controllers whose
fresh starts were canceled when rollback stopped their shared provisioner
during the 2026-10-27 P1 maintenance-socket incident.
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
EXPECTED_HELPER_RELATIVE_PATH = pathlib.Path(
    "scripts/lambda_ci_p1_restore_rollback_failed_controllers.py"
)
START_STABILITY_SECONDS = 2

RESEARCH_CPU = "workspace-ci-controller@research-engine-cpu.service"
TARGETS = [
    "workspace-ci-controller@research-engine-gpu.service",
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
]
SHARED_REQUIRED = [
    "workspace-ci-provisioner.service",
    "workspace-ci-reconciler.service",
    "workspace-ci-reconcile-controller.service",
]

EXPECTED_CPU = {
    "LoadState": "loaded",
    "ActiveState": "inactive",
    "SubState": "dead",
    "UnitFileState": "enabled",
    "NRestarts": "12411",
    "ExecMainStatus": "1",
}
EXPECTED_TARGET = {
    "LoadState": "loaded",
    "ActiveState": "failed",
    "SubState": "failed",
    "UnitFileState": "enabled",
    "NRestarts": "0",
    "ExecMainStatus": "1",
}


class RecoveryError(RuntimeError):
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
        raise RecoveryError(
            f"command failed rc={proc.returncode}: {command!r}: "
            + proc.stderr.strip()
        )
    return proc


def snapshot(service: str) -> dict[str, str]:
    argv = ["systemctl", "show", service, "--no-pager"]
    for prop in (
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "NRestarts",
        "ExecMainStatus",
    ):
        argv.extend(["-p", prop])
    proc = run(argv, check=False)
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out


def attest_reviewed_source(
    expected_head: str,
    invoker: str,
) -> tuple[pathlib.Path, str]:
    executing_helper = pathlib.Path(__file__).resolve()
    try:
        repo = executing_helper.parents[1]
    except IndexError as exc:
        raise RecoveryError(
            "executing helper is not inside the reviewed repository layout"
        ) from exc

    expected_helper = (repo / EXPECTED_HELPER_RELATIVE_PATH).resolve()
    if executing_helper != expected_helper:
        raise RecoveryError(
            "executing helper is outside the reviewed tracked helper path: "
            f"actual={executing_helper} expected={expected_helper}"
        )

    git_root = pathlib.Path(
        run(
            ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
            user=invoker,
        ).stdout.strip()
    ).resolve()
    if git_root != repo:
        raise RecoveryError(
            f"executing helper repository root mismatch: derived={repo} git={git_root}"
        )

    tracked = run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--error-unmatch",
            "--",
            EXPECTED_HELPER_RELATIVE_PATH.as_posix(),
        ],
        check=False,
        user=invoker,
    )
    if tracked.returncode != 0:
        raise RecoveryError("executing helper is not tracked at reviewed path")

    head = run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        user=invoker,
    ).stdout.strip()
    if head != expected_head:
        raise RecoveryError(
            f"unexpected source HEAD: actual={head} expected={expected_head}"
        )

    dirty = run(
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
    if dirty:
        raise RecoveryError("tracked reviewed source is dirty:\n" + dirty)

    return repo, head


def no_active_project_execution() -> None:
    proc = run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            "workspace-ci-research-engine-*.service",
            "workspace-ci-padataset-*.service",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RecoveryError(
            "unable to inspect project execution units: "
            f"rc={proc.returncode}: {proc.stderr.strip()}"
        )
    active = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] in {
            "active",
            "activating",
            "deactivating",
        }:
            active.append(line)
    if active:
        raise RecoveryError(
            "project execution is active; refusing controller recovery:\n"
            + "\n".join(active)
        )


def _require_shared_healthy() -> dict[str, dict[str, str]]:
    shared: dict[str, dict[str, str]] = {}
    for service in SHARED_REQUIRED:
        state = snapshot(service)
        shared[service] = state
        if (
            state.get("LoadState") != "loaded"
            or state.get("ActiveState") != "active"
            or state.get("SubState") != "running"
            or state.get("ExecMainStatus") != "0"
            or state.get("NRestarts") != "0"
        ):
            raise RecoveryError(
                f"shared control service is not in the accepted healthy state: "
                f"{service}: " + json.dumps(state, sort_keys=True)
            )
    return shared


def validate_pre_recovery_state() -> dict[str, Any]:
    no_active_project_execution()
    shared = _require_shared_healthy()

    cpu = snapshot(RESEARCH_CPU)
    if cpu != EXPECTED_CPU:
        raise RecoveryError(
            "research-engine CPU changed from the accepted quiesced incident state: "
            + json.dumps({"expected": EXPECTED_CPU, "actual": cpu}, sort_keys=True)
        )

    targets: dict[str, dict[str, str]] = {}
    for service in TARGETS:
        state = snapshot(service)
        targets[service] = state
        if state != EXPECTED_TARGET:
            raise RecoveryError(
                f"rollback-failed controller changed from the accepted incident "
                f"state: {service}: "
                + json.dumps(
                    {"expected": EXPECTED_TARGET, "actual": state},
                    sort_keys=True,
                )
            )

    return {"shared": shared, "cpu": cpu, "targets": targets}


def recover() -> dict[str, Any]:
    before = validate_pre_recovery_state()

    run(["systemctl", "start", *TARGETS])
    time.sleep(START_STABILITY_SECONDS)

    after: dict[str, dict[str, str]] = {}
    for service in TARGETS:
        state = snapshot(service)
        after[service] = state
        if not (
            state.get("LoadState") == "loaded"
            and state.get("UnitFileState") in {"enabled", "enabled-runtime"}
            and state.get("ActiveState") == "active"
            and state.get("SubState") == "running"
            and state.get("ExecMainStatus") == "0"
            and state.get("NRestarts") == "0"
        ):
            raise RecoveryError(
                f"controller did not restore to stable active/running: {service}: "
                + json.dumps(state, sort_keys=True)
            )

    cpu_after = snapshot(RESEARCH_CPU)
    if cpu_after != EXPECTED_CPU:
        raise RecoveryError(
            "research-engine CPU changed during non-CPU recovery: "
            + json.dumps(
                {"expected": EXPECTED_CPU, "actual": cpu_after},
                sort_keys=True,
            )
        )

    shared_after = _require_shared_healthy()
    no_active_project_execution()

    return {
        "status": "ROLLBACK_FAILED_CONTROLLERS_RESTORED",
        "mutation": {"command": ["systemctl", "start", *TARGETS]},
        "before": before,
        "after": after,
        "research_cpu": cpu_after,
        "shared_after": shared_after,
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

    repo, head = attest_reviewed_source(args.expected_head, invoker)
    print(f"repo={repo}")
    print(f"head={head}")
    receipt = recover()
    print(
        "P1_ROLLBACK_FAILED_CONTROLLER_RECOVERY_RECEIPT="
        + json.dumps(receipt, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecoveryError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
