#!/usr/bin/env python3
"""Transactional live update for stale-quarantine recovery.

This updater changes exactly two installed files:
  /opt/workspace-ci/controller/lambda-ci-controller
  /opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py

It does not itself mutate GitHub scale sets, workflows, credentials, quarantine
state, retry authority, v3 services, or Workspace Shell. It only installs the
exact validated controller + maintenance-controller pair that understands the
narrow DELETE_STALE_QUARANTINED recovery operation.

The legacy workspace-control controller's pre-update active/inactive state is
preserved. The maintenance controller must remain active and stable.
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
import tempfile
import time
from datetime import datetime, timezone


EXPECTED_OLD_CONTROLLER_REVISION = "3e8a231483413ba3a16d405ba61b55d0ab9ff3aa"
EXPECTED_MAIN_BLOB = "7ef485a14ab6092ee4bea79e701e7fca6e562821"
EXPECTED_GOMOD_BLOB = "c6eac3f02843fbe5d384594b7ff1e60806a1ba14"
EXPECTED_GOSUM_BLOB = "9bbeb18130880f5ff5e9cbf2b247493c80f8cfa1"
EXPECTED_OLD_MAINTENANCE_BLOB = "44234db6ceac33f42406731ec190f8de65ecf3f4"
EXPECTED_NEW_MAINTENANCE_BLOB = "4c451faa19d785b0bbab04b93f1ab78529048ed5"

CONTROLLER_SERVICE = "workspace-ci-controller@workspace-control-cpu.service"
MAINTENANCE_SERVICE = "workspace-ci-maintenance-controller.service"
INSTALLED_CONTROLLER = Path("/opt/workspace-ci/controller/lambda-ci-controller")
INSTALLED_MAINTENANCE = Path(
    "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py"
)
CONTROLLER_DIR_REL = Path("controller/lambda-ci-controller")
MAINTENANCE_REL = Path("scripts/lambda_ci_maintenance_controller.py")
UPDATE_ROOT = Path("/var/lib/workspace-ci/maintenance-controller/updates")


class UpdateError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
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
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def service_state(service: str) -> dict[str, str]:
    proc = run(
        [
            "systemctl",
            "show",
            service,
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


def is_running(state: dict[str, str]) -> bool:
    return (
        state.get("LoadState") == "loaded"
        and state.get("ActiveState") == "active"
        and state.get("SubState") == "running"
        and state.get("MainPID", "").isdigit()
        and int(state["MainPID"]) > 0
    )


def require_running(state: dict[str, str], label: str) -> None:
    if not is_running(state):
        raise UpdateError(f"{label} is not active/running: {state}")


def go_vcs_revision(binary: Path, go_bin: str) -> str:
    proc = run([go_bin, "version", "-m", str(binary)])
    for line in proc.stdout.splitlines():
        marker = "vcs.revision="
        if marker in line:
            return line.split(marker, 1)[1].strip()
    raise UpdateError(f"binary has no Go vcs.revision build setting: {binary}")


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def require_root_owned_0755(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise UpdateError(f"{label} is missing or symlinked: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0:
        raise UpdateError(f"{label} must be root:root: {path}")
    if stat.S_IMODE(st.st_mode) != 0o755:
        raise UpdateError(f"{label} mode must be 0755: {path}")


def restore_service_state(service: str, should_run: bool) -> None:
    run(["systemctl", "reset-failed", service], check=False)
    if should_run:
        run(["systemctl", "start", service])
    else:
        run(["systemctl", "stop", service], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise UpdateError("must run as root")
    if (
        len(args.expected_head) != 40
        or any(c not in "0123456789abcdef" for c in args.expected_head)
    ):
        raise UpdateError("--expected-head must be a full lowercase Git SHA")

    go_bin = shutil.which("go")
    if not go_bin:
        raise UpdateError("go toolchain is unavailable")

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
            f"checkout HEAD mismatch: expected {args.expected_head}, "
            f"observed {observed_head}"
        )
    if run(
        git_prefix + ["status", "--porcelain=v1", "--untracked-files=normal"]
    ).stdout.strip():
        raise UpdateError("checkout is dirty")

    changed_controller = [
        line
        for line in run(
            git_prefix
            + [
                "diff",
                "--name-only",
                f"{EXPECTED_OLD_CONTROLLER_REVISION}..{args.expected_head}",
                "--",
                str(CONTROLLER_DIR_REL),
            ]
        ).stdout.splitlines()
        if line
    ]
    if changed_controller != [
        "controller/lambda-ci-controller/main.go",
        "controller/lambda-ci-controller/main_test.go",
    ]:
        raise UpdateError(
            "controller candidate drifted outside reviewed stale-recovery files: "
            + ",".join(changed_controller)
        )

    controller_dir = repo / CONTROLLER_DIR_REL
    maintenance_candidate = repo / MAINTENANCE_REL
    if git_blob(controller_dir / "main.go") != EXPECTED_MAIN_BLOB:
        raise UpdateError("candidate controller main.go blob mismatch")
    if git_blob(controller_dir / "go.mod") != EXPECTED_GOMOD_BLOB:
        raise UpdateError("candidate controller go.mod blob mismatch")
    if git_blob(controller_dir / "go.sum") != EXPECTED_GOSUM_BLOB:
        raise UpdateError("candidate controller go.sum blob mismatch")
    if git_blob(maintenance_candidate) != EXPECTED_NEW_MAINTENANCE_BLOB:
        raise UpdateError("candidate maintenance-controller blob mismatch")

    require_root_owned_0755(INSTALLED_CONTROLLER, "installed controller")
    require_root_owned_0755(
        INSTALLED_MAINTENANCE,
        "installed maintenance controller",
    )
    installed_revision = go_vcs_revision(INSTALLED_CONTROLLER, go_bin)
    if installed_revision != EXPECTED_OLD_CONTROLLER_REVISION:
        raise UpdateError(
            "installed controller revision is not the reviewed live prestate: "
            f"{installed_revision}"
        )
    if git_blob(INSTALLED_MAINTENANCE) != EXPECTED_OLD_MAINTENANCE_BLOB:
        raise UpdateError(
            "installed maintenance-controller blob is not reviewed hotfix-v2 prestate"
        )

    maintenance_pre = service_state(MAINTENANCE_SERVICE)
    require_running(maintenance_pre, "maintenance controller preflight")
    controller_pre = service_state(CONTROLLER_SERVICE)
    controller_was_running = is_running(controller_pre)

    run([sys.executable, "-m", "py_compile", str(maintenance_candidate)])

    build_dir = Path(tempfile.mkdtemp(prefix="workspace-ci-stale-recovery-build."))
    candidate_binary = build_dir / "lambda-ci-controller"
    try:
        run([go_bin, "test", "-mod=mod", "./..."], cwd=controller_dir)
        run(
            [go_bin, "build", "-mod=mod", "-o", str(candidate_binary), "."],
            cwd=controller_dir,
        )
        candidate_revision = go_vcs_revision(candidate_binary, go_bin)
        if candidate_revision != args.expected_head:
            raise UpdateError(
                f"candidate controller revision mismatch: {candidate_revision}"
            )

        update_dir = (
            UPDATE_ROOT / args.expected_head / "stale-quarantine-recovery"
        )
        if update_dir.exists():
            raise UpdateError(f"update directory already exists: {update_dir}")
        backup_dir = update_dir / "backup"
        backup_dir.mkdir(parents=True, mode=0o700)
        os.chmod(update_dir, 0o700)
        os.chmod(backup_dir, 0o700)

        controller_backup = backup_dir / INSTALLED_CONTROLLER.name
        maintenance_backup = backup_dir / INSTALLED_MAINTENANCE.name
        shutil.copy2(INSTALLED_CONTROLLER, controller_backup)
        shutil.copy2(INSTALLED_MAINTENANCE, maintenance_backup)
        for path in (controller_backup, maintenance_backup):
            os.chown(path, 0, 0)
            os.chmod(path, 0o755)

        receipt_path = update_dir / "receipt.json"
        mutated = False
        committed = False
        try:
            atomic_json(
                receipt_path,
                {
                    "schema":
                        "workspace-ci-stale-quarantine-recovery-live-update.v1",
                    "status": "PREPARED",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "expected_head": args.expected_head,
                    "installed_controller_revision": installed_revision,
                    "installed_maintenance_blob":
                        EXPECTED_OLD_MAINTENANCE_BLOB,
                    "candidate_controller_sha256": sha256(candidate_binary),
                    "candidate_maintenance_blob":
                        EXPECTED_NEW_MAINTENANCE_BLOB,
                    "controller_pre_state": controller_pre,
                    "maintenance_pre_state": maintenance_pre,
                },
            )

            run(["systemctl", "stop", MAINTENANCE_SERVICE])
            run(["systemctl", "stop", CONTROLLER_SERVICE], check=False)
            mutated = True

            tmp_controller = INSTALLED_CONTROLLER.with_name(
                INSTALLED_CONTROLLER.name + ".candidate"
            )
            tmp_maintenance = INSTALLED_MAINTENANCE.with_name(
                INSTALLED_MAINTENANCE.name + ".candidate"
            )
            shutil.copyfile(candidate_binary, tmp_controller)
            shutil.copyfile(maintenance_candidate, tmp_maintenance)
            for path in (tmp_controller, tmp_maintenance):
                os.chown(path, 0, 0)
                os.chmod(path, 0o755)
            os.replace(tmp_controller, INSTALLED_CONTROLLER)
            os.replace(tmp_maintenance, INSTALLED_MAINTENANCE)

            if (
                go_vcs_revision(INSTALLED_CONTROLLER, go_bin)
                != args.expected_head
            ):
                raise UpdateError(
                    "installed candidate controller revision mismatch"
                )
            if (
                git_blob(INSTALLED_MAINTENANCE)
                != EXPECTED_NEW_MAINTENANCE_BLOB
            ):
                raise UpdateError(
                    "installed candidate maintenance-controller blob mismatch"
                )

            run(["systemctl", "reset-failed", MAINTENANCE_SERVICE], check=False)
            run(["systemctl", "start", MAINTENANCE_SERVICE])
            if controller_was_running:
                run(
                    ["systemctl", "reset-failed", CONTROLLER_SERVICE],
                    check=False,
                )
                run(["systemctl", "start", CONTROLLER_SERVICE])

            time.sleep(3.0)
            maintenance_first = service_state(MAINTENANCE_SERVICE)
            require_running(
                maintenance_first,
                "maintenance controller post-start first sample",
            )
            controller_first = service_state(CONTROLLER_SERVICE)
            if controller_was_running:
                require_running(
                    controller_first,
                    "legacy controller post-start first sample",
                )
            elif is_running(controller_first):
                raise UpdateError("legacy controller unexpectedly started")

            time.sleep(3.0)
            maintenance_second = service_state(MAINTENANCE_SERVICE)
            require_running(
                maintenance_second,
                "maintenance controller post-start second sample",
            )
            controller_second = service_state(CONTROLLER_SERVICE)
            if (
                maintenance_first.get("MainPID")
                != maintenance_second.get("MainPID")
            ):
                raise UpdateError(
                    "maintenance controller PID changed during stability window"
                )
            if (
                maintenance_first.get("NRestarts")
                != maintenance_second.get("NRestarts")
            ):
                raise UpdateError(
                    "maintenance controller restart count changed during stability window"
                )
            if controller_was_running:
                require_running(
                    controller_second,
                    "legacy controller post-start second sample",
                )
                if (
                    controller_first.get("MainPID")
                    != controller_second.get("MainPID")
                ):
                    raise UpdateError(
                        "legacy controller PID changed during stability window"
                    )
                if (
                    controller_first.get("NRestarts")
                    != controller_second.get("NRestarts")
                ):
                    raise UpdateError(
                        "legacy controller restart count changed during stability window"
                    )
            elif is_running(controller_second):
                raise UpdateError(
                    "legacy controller unexpectedly running after update"
                )

            receipt = {
                "schema":
                    "workspace-ci-stale-quarantine-recovery-live-update.v1",
                "status": "PASS",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "validated_head": args.expected_head,
                "installed_controller_revision":
                    go_vcs_revision(INSTALLED_CONTROLLER, go_bin),
                "installed_controller_sha256": sha256(INSTALLED_CONTROLLER),
                "installed_maintenance_blob":
                    git_blob(INSTALLED_MAINTENANCE),
                "controller_pre_state": controller_pre,
                "controller_post_state": controller_second,
                "maintenance_pre_state": maintenance_pre,
                "maintenance_post_state": maintenance_second,
                "scope": [
                    str(INSTALLED_CONTROLLER),
                    str(INSTALLED_MAINTENANCE),
                    CONTROLLER_SERVICE,
                    MAINTENANCE_SERVICE,
                ],
                "explicit_non_effects": [
                    "no GitHub workflow mutation",
                    "no scale-set mutation",
                    "no quarantine/retry-state mutation",
                    "no credential mutation",
                    "no v3 service mutation",
                    "no Workspace Shell mutation",
                ],
            }
            atomic_json(receipt_path, receipt)
            committed = True
            print("STALE_QUARANTINE_RECOVERY_LIVE_UPDATE=PASS")
            print(f"VALIDATED_HEAD={args.expected_head}")
            print(
                "INSTALLED_CONTROLLER_REVISION="
                f"{receipt['installed_controller_revision']}"
            )
            print(
                "INSTALLED_MAINTENANCE_BLOB="
                f"{receipt['installed_maintenance_blob']}"
            )
            print(f"UPDATE_RECEIPT={receipt_path}")
            return 0
        finally:
            if mutated and not committed:
                try:
                    run(["systemctl", "stop", MAINTENANCE_SERVICE], check=False)
                    run(["systemctl", "stop", CONTROLLER_SERVICE], check=False)
                    shutil.copy2(controller_backup, INSTALLED_CONTROLLER)
                    shutil.copy2(maintenance_backup, INSTALLED_MAINTENANCE)
                    os.chown(INSTALLED_CONTROLLER, 0, 0)
                    os.chmod(INSTALLED_CONTROLLER, 0o755)
                    os.chown(INSTALLED_MAINTENANCE, 0, 0)
                    os.chmod(INSTALLED_MAINTENANCE, 0o755)
                    run(
                        ["systemctl", "reset-failed", MAINTENANCE_SERVICE],
                        check=False,
                    )
                    run(["systemctl", "start", MAINTENANCE_SERVICE], check=False)
                    restore_service_state(
                        CONTROLLER_SERVICE,
                        controller_was_running,
                    )
                    time.sleep(1.0)
                    atomic_json(
                        receipt_path,
                        {
                            "schema":
                                "workspace-ci-stale-quarantine-recovery-live-update.v1",
                            "status": "ROLLED_BACK",
                            "timestamp_utc":
                                datetime.now(timezone.utc).isoformat(),
                            "expected_head": args.expected_head,
                            "restored_controller_revision":
                                go_vcs_revision(
                                    INSTALLED_CONTROLLER,
                                    go_bin,
                                ),
                            "restored_maintenance_blob":
                                git_blob(INSTALLED_MAINTENANCE),
                            "controller_state":
                                service_state(CONTROLLER_SERVICE),
                            "maintenance_state":
                                service_state(MAINTENANCE_SERVICE),
                        },
                    )
                except Exception as rollback_error:
                    print(
                        "ROLLBACK_ERROR="
                        f"{type(rollback_error).__name__}:{rollback_error}",
                        file=sys.stderr,
                    )
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
