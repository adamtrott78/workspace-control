#!/usr/bin/env python3
"""Narrow post-cutover repair for shared PADataset runtime-root traversal.

Only the three shared parent directories used by both scientific runner UIDs are
changed. They remain owned by ci-padataset:ci-padataset and become 0710:
owner rwx, shared project group execute-only, no world access. Per-request
children remain 0700 and are still UID-isolated.
"""
from __future__ import annotations

import argparse
import grp
import os
import pathlib
import pwd
import stat

ROOT_MODES = {
    pathlib.Path("/srv/workspace-ci/padataset/jobs"): 0o750,
    pathlib.Path("/srv/workspace-ci/padataset/staging-cache"): 0o710,
    pathlib.Path("/srv/workspace-ci/padataset/logs"): 0o710,
}


class RepairError(RuntimeError):
    pass


def verify() -> None:
    owner = pwd.getpwnam("ci-padataset")
    group = grp.getgrnam("ci-padataset")
    lane_b = pwd.getpwnam("ci-padataset-2")
    if lane_b.pw_gid != group.gr_gid:
        raise RepairError("lane-B primary group mismatch")
    for path, expected_mode in ROOT_MODES.items():
        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RepairError(f"ownership mismatch: {path}")
        if stat.S_IMODE(st.st_mode) != expected_mode:
            raise RepairError(
                f"mode mismatch {stat.S_IMODE(st.st_mode):04o} != "
                f"{expected_mode:04o}: {path}"
            )


def repair() -> None:
    if os.geteuid() != 0:
        raise RepairError("repair requires root")
    owner = pwd.getpwnam("ci-padataset")
    group = grp.getgrnam("ci-padataset")
    lane_b = pwd.getpwnam("ci-padataset-2")
    if lane_b.pw_gid != group.gr_gid:
        raise RepairError("lane-B primary group mismatch")

    for path, expected_mode in ROOT_MODES.items():
        if not path.is_dir():
            raise RepairError(f"required shared root missing: {path}")
        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RepairError(f"unexpected pre-repair ownership: {path}")
        mode = stat.S_IMODE(st.st_mode)
        if mode not in {0o700, 0o710}:
            raise RepairError(f"unexpected pre-repair mode {mode:04o}: {path}")

    for path, expected_mode in ROOT_MODES.items():
        os.chmod(path, 0o710)

    verify()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
    else:
        repair()

    print("PADATASET_SHARED_RUNTIME_ROOT_REPAIR=PASS")
    print("JOBS_MODE=0750")
    print("STAGING_CACHE_MODE=0710")
    print("LOGS_MODE=0710")
    print("OWNER=ci-padataset")
    print("GROUP=ci-padataset")
    print("LANE_B_GROUP_TRAVERSE=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RepairError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
