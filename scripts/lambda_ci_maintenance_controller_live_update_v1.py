#!/usr/bin/env python3
"""Transactional live update for the Workspace CI maintenance controller.

This updater changes exactly one installed file:
  /opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py

It does not mutate GitHub scale sets, project controllers, v3 services, workflow
state, credentials, quarantine files, or retry authority. It exists solely to
deploy the reviewed RFC3339 nanosecond timestamp parser repair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone


EXPECTED_OLD_GIT_BLOB = "4b5ec97754c83e4b01103dea9c2f84112b3d6110"
EXPECTED_CANDIDATE_GIT_BLOB = "f994992cb3e4713c1e0a165c18de459fa44dac74"
SERVICE = "workspace-ci-maintenance-controller.service"
INSTALLED = Path(
    "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py"
)
CANDIDATE_REL = Path("scripts/lambda_ci_maintenance_controller.py")
UPDATE_ROOT = Path("/var/lib/workspace-ci/maintenance-controller/updates")


class UpdateError(RuntimeError):
    pass


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise UpdateError(
            f"command failed rc={proc.returncode}: {' '.join(argv)}: "
            f"{proc.stderr.strip()}"
        )
    return proc


def git_blob(path: Path) -> str:
    return run(["git", "hash-object", str(path)]).stdout.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def service_state() -> dict[str, str]:
    proc = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "--no-pager",
            "--property=LoadState,ActiveState,SubState,MainPID,NRestarts,"
            "ExecMainCode,ExecMainStatus,Result,UnitFileState",
        ]
    )
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def require_running(state: dict[str, str], label: str) -> None:
    if (
        state.get("LoadState") != "loaded"
        or state.get("ActiveState") != "active"
        or state.get("SubState") != "running"
        or not state.get("MainPID", "").isdigit()
        or int(state["MainPID"]) <= 0
    ):
        raise UpdateError(f"{label}: maintenance controller not active/running: {state}")


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise UpdateError("must run as root")
    if len(args.expected_head) != 40 or any(c not in "0123456789abcdef" for c in args.expected_head):
        raise UpdateError("--expected-head must be a full lowercase Git SHA")

    repo_hint = Path.cwd().resolve()
    repo = Path(
        run(
            [
                "git",
                "-c",
                f"safe.directory={repo_hint}",
                "rev-parse",
                "--show-toplevel",
            ]
        ).stdout.strip()
    ).resolve()
    git_prefix = ["git", "-c", f"safe.directory={repo}", "-C", str(repo)]
    observed_head = run(git_prefix + ["rev-parse", "HEAD"]).stdout.strip()
    if observed_head != args.expected_head:
        raise UpdateError(
            f"checkout HEAD mismatch: expected {args.expected_head}, observed {observed_head}"
        )
    if run(
        git_prefix + ["status", "--porcelain=v1", "--untracked-files=normal"]
    ).stdout.strip():
        raise UpdateError("checkout is dirty")

    candidate = repo / CANDIDATE_REL
    if git_blob(candidate) != EXPECTED_CANDIDATE_GIT_BLOB:
        raise UpdateError("candidate maintenance-controller blob mismatch")
    if not INSTALLED.is_file() or INSTALLED.is_symlink():
        raise UpdateError("installed maintenance controller is missing or symlinked")
    if git_blob(INSTALLED) != EXPECTED_OLD_GIT_BLOB:
        raise UpdateError("installed maintenance-controller blob is not the reviewed prestate")

    st = INSTALLED.stat()
    if st.st_uid != 0 or st.st_gid != 0:
        raise UpdateError("installed maintenance controller must be root:root")
    if stat.S_IMODE(st.st_mode) != 0o755:
        raise UpdateError("installed maintenance controller mode must be 0755")

    run([sys.executable, "-m", "py_compile", str(candidate)])
    pre = service_state()
    require_running(pre, "preflight")

    update_dir = UPDATE_ROOT / args.expected_head
    if update_dir.exists():
        raise UpdateError(f"update directory already exists: {update_dir}")
    backup_dir = update_dir / "backup"
    backup_dir.mkdir(parents=True, mode=0o700)
    os.chmod(update_dir, 0o700)
    os.chmod(backup_dir, 0o700)

    backup = backup_dir / INSTALLED.name
    shutil.copy2(INSTALLED, backup)
    os.chown(backup, 0, 0)
    os.chmod(backup, 0o755)

    receipt_path = update_dir / "receipt.json"
    started = False
    committed = False

    try:
        atomic_json(
            receipt_path,
            {
                "schema": "workspace-ci-maintenance-controller-live-update.v1",
                "status": "PREPARED",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "expected_head": args.expected_head,
                "installed_pre_blob": EXPECTED_OLD_GIT_BLOB,
                "candidate_blob": EXPECTED_CANDIDATE_GIT_BLOB,
                "pre_service_state": pre,
            },
        )

        run(["systemctl", "stop", SERVICE])
        started = True

        tmp_install = INSTALLED.with_name(INSTALLED.name + ".candidate")
        shutil.copyfile(candidate, tmp_install)
        os.chown(tmp_install, 0, 0)
        os.chmod(tmp_install, 0o755)
        os.replace(tmp_install, INSTALLED)

        if git_blob(INSTALLED) != EXPECTED_CANDIDATE_GIT_BLOB:
            raise UpdateError("installed candidate blob mismatch after replacement")

        run(["systemctl", "start", SERVICE])
        time.sleep(2.0)
        first = service_state()
        require_running(first, "post-start first sample")
        time.sleep(2.0)
        second = service_state()
        require_running(second, "post-start second sample")
        if first.get("MainPID") != second.get("MainPID"):
            raise UpdateError("maintenance controller PID changed during stability window")
        if first.get("NRestarts") != second.get("NRestarts"):
            raise UpdateError("maintenance controller restart count changed during stability window")

        receipt = {
            "schema": "workspace-ci-maintenance-controller-live-update.v1",
            "status": "PASS",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "expected_head": args.expected_head,
            "installed_pre_blob": EXPECTED_OLD_GIT_BLOB,
            "installed_post_blob": git_blob(INSTALLED),
            "installed_post_sha256": sha256(INSTALLED),
            "pre_service_state": pre,
            "post_service_state": second,
            "scope": [
                str(INSTALLED),
                SERVICE,
            ],
            "explicit_non_effects": [
                "no GitHub workflow mutation",
                "no scale-set mutation",
                "no project-controller mutation",
                "no v3 service mutation",
                "no credential mutation",
                "no quarantine/retry-state mutation",
            ],
        }
        atomic_json(receipt_path, receipt)
        committed = True
        print("MAINTENANCE_CONTROLLER_LIVE_UPDATE=PASS")
        print(f"VALIDATED_HEAD={args.expected_head}")
        print(f"INSTALLED_BLOB={receipt['installed_post_blob']}")
        print(f"UPDATE_RECEIPT={receipt_path}")
        return 0
    finally:
        if started and not committed:
            try:
                run(["systemctl", "stop", SERVICE], check=False)
                shutil.copy2(backup, INSTALLED)
                os.chown(INSTALLED, 0, 0)
                os.chmod(INSTALLED, 0o755)
                run(["systemctl", "start", SERVICE], check=False)
                time.sleep(1.0)
                rollback_state = service_state()
                atomic_json(
                    receipt_path,
                    {
                        "schema": "workspace-ci-maintenance-controller-live-update.v1",
                        "status": "ROLLED_BACK",
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "expected_head": args.expected_head,
                        "restored_blob": git_blob(INSTALLED),
                        "service_state": rollback_state,
                    },
                )
            except Exception as rollback_error:
                print(
                    f"ROLLBACK_ERROR={type(rollback_error).__name__}:{rollback_error}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
