#!/usr/bin/env python3
"""Narrow post-cutover repair for shared PADataset runtime-root access.

The two scientific runner UIDs share the ci-padataset primary group. The GitHub
Actions listener requires read+traverse on the shared jobs parent, while cache
and log parents require traverse only. Per-request children remain 0700 and
UID-isolated.
"""
from __future__ import annotations

import argparse
import grp
import os
import pathlib
import pwd
import stat

JOBS = pathlib.Path("/srv/workspace-ci/padataset/jobs")
STAGING_CACHE = pathlib.Path("/srv/workspace-ci/padataset/staging-cache")
LOGS = pathlib.Path("/srv/workspace-ci/padataset/logs")

ROOT_MODES = {
    JOBS: 0o750,
    STAGING_CACHE: 0o710,
    LOGS: 0o710,
}

ACCEPTED_PRE_MODES = {
    JOBS: frozenset({0o700, 0o710, 0o750}),
    STAGING_CACHE: frozenset({0o700, 0o710}),
    LOGS: frozenset({0o700, 0o710}),
}


class RepairError(RuntimeError):
    pass


def _identity() -> tuple[pwd.struct_passwd, grp.struct_group]:
    owner = pwd.getpwnam("ci-padataset")
    group = grp.getgrnam("ci-padataset")
    lane_b = pwd.getpwnam("ci-padataset-2")
    if lane_b.pw_gid != group.gr_gid:
        raise RepairError("lane-B primary group mismatch")
    return owner, group


def verify() -> None:
    owner, group = _identity()

    for path, expected_mode in ROOT_MODES.items():
        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RepairError(f"ownership mismatch: {path}")
        actual_mode = stat.S_IMODE(st.st_mode)
        if actual_mode != expected_mode:
            raise RepairError(
                f"mode mismatch {actual_mode:04o} != "
                f"{expected_mode:04o}: {path}"
            )


def repair() -> None:
    if os.geteuid() != 0:
        raise RepairError("repair requires root")

    owner, group = _identity()

    for path, expected_mode in ROOT_MODES.items():
        if not path.is_dir():
            raise RepairError(f"required shared root missing: {path}")

        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RepairError(f"unexpected pre-repair ownership: {path}")

        actual_mode = stat.S_IMODE(st.st_mode)
        accepted = ACCEPTED_PRE_MODES[path]
        if actual_mode not in accepted:
            accepted_text = ",".join(f"{mode:04o}" for mode in sorted(accepted))
            raise RepairError(
                f"unexpected pre-repair mode {actual_mode:04o}; "
                f"accepted={accepted_text}: {path}"
            )

    for path, expected_mode in ROOT_MODES.items():
        os.chmod(path, expected_mode)

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
    print("LANE_B_JOBS_READ_TRAVERSE=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RepairError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
