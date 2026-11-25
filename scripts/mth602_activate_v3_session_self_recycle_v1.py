#!/usr/bin/env python3
"""Safe operator bootstrap for the MTH602 v3 controller session self-recycle repair."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid


def run(args: list[str]) -> str:
    proc = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if proc.returncode:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def exact_repo(repo_root: pathlib.Path, expected_head: str) -> pathlib.Path:
    root = repo_root.resolve()
    if run(["git", "-C", str(root), "rev-parse", "HEAD"]) != expected_head:
        raise RuntimeError("source head mismatch")
    if run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=normal"]):
        raise RuntimeError("source checkout is dirty")
    return root


def find_go(repo_root: pathlib.Path) -> str:
    module = repo_root / "controller" / "lambda-ci-controller"
    candidates = [
        "/opt/workspace-ci/go/1.26.3/bin/go",
        shutil.which("go1.26.3"),
        shutil.which("go1.26"),
        "/usr/local/go/bin/go",
        shutil.which("go"),
        "/usr/bin/go",
    ]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        path = str(pathlib.Path(candidate).resolve())
        if path in seen or not pathlib.Path(path).is_file():
            continue
        seen.add(path)
        probe = subprocess.run(
            [path, "-C", str(module), "list", "-m"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "GOTOOLCHAIN": "local"},
            check=False,
        )
        if probe.returncode == 0:
            print(f"GO_TOOLCHAIN_SELECTED={path}")
            return path
    raise RuntimeError("no installed Go compiler can parse the exact controller module")


def root_phase(repo_root: pathlib.Path, expected_head: str) -> None:
    if os.geteuid() != 0:
        raise RuntimeError("root phase requires uid 0")

    root = exact_repo(repo_root, expected_head)
    scripts = root / "scripts"
    sys.path.insert(0, str(scripts))
    import lambda_ci_v3_live_controller_repair_v1 as repair
    import lambda_ci_v3_reconciler as reconciler

    reconciler.verify_installed(repair.BASE_MANIFEST)
    root_policy, _ = repair.load(repair.ROOT_POLICY)
    units = repair.controller_units(root_policy)
    before = repair.snapshot_controllers(units)
    active_before = [
        cid for cid, state in before.items()
        if state.get("ActiveState") == "active" and state.get("SubState") == "running"
    ]
    if repair.TARGET_CLASS not in active_before:
        raise RuntimeError("scientific controller lane A is not active/running")

    repair.require_root_services()

    # Critical pre-stop gate: prove there is no live/held root work before
    # touching any controller process. The generic helper will re-prove this
    # after quiescing, closing the admission race.
    repair.require_no_live_provisioner_records()
    repair.require_no_transients(units)

    go_bin = find_go(root)
    current_binary = repair.CONTROLLER_BINARY.read_bytes()
    current_sha = repair.sha(current_binary)
    candidate_binary = repair.build_candidate(root, go_bin)
    candidate_sha = repair.sha(candidate_binary)
    if current_sha == candidate_sha:
        print("MTH602_V3_SESSION_SELF_RECYCLE=ALREADY_ACTIVE")
        print(f"CONTROLLER_SOURCE_HEAD={expected_head}")
        print(f"CONTROLLER_SHA256={candidate_sha}")
        return

    manifest, manifest_raw = repair.load(repair.BASE_MANIFEST)
    previous_refresh, previous_refresh_raw = repair.load(repair.CONTROLLER_REFRESH)
    if (
        previous_refresh.get("mode") != repair.MODE
        or previous_refresh.get("phase") != "ACTIVE"
        or previous_refresh.get("controller_binary_sha256") != current_sha
    ):
        raise RuntimeError("current controller refresh receipt is not a valid active predecessor")

    base_head = manifest.get("source_head")
    root_policy_sha = manifest.get("root_policy_sha256")
    if not isinstance(base_head, str) or repair.SHA40.fullmatch(base_head) is None:
        raise RuntimeError("base manifest source head invalid")
    if not isinstance(root_policy_sha, str) or repair.SHA64.fullmatch(root_policy_sha) is None:
        raise RuntimeError("root policy digest invalid")

    work = pathlib.Path(tempfile.mkdtemp(prefix="mth602-v3-session-self-recycle-", dir="/run"))
    os.chown(work, 0, 0)
    os.chmod(work, 0o700)
    authority_path = work / "authority.json"
    now = datetime.now(timezone.utc)
    authority = {
        "schema_version": 1,
        "authority": "workspace-control-operator",
        "operation": "REFRESH_V3_CONTROLLER_BINARY_LIVE_V1",
        "authorization_id": str(uuid.uuid4()),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "source_head": expected_head,
        "base_source_head": base_head,
        "base_install_manifest_sha256": repair.sha(manifest_raw),
        "root_policy_sha256": root_policy_sha,
        "current_controller_sha256": current_sha,
        "candidate_controller_sha256": candidate_sha,
        "previous_controller_refresh_sha256": repair.sha(previous_refresh_raw),
        "previous_controller_source_head": previous_refresh.get("controller_source_head"),
    }
    repair.atomic_json(authority_path, authority)

    cmd = [
        "/usr/bin/python3",
        str(scripts / "lambda_ci_v3_live_controller_repair_v1.py"),
        "--expected-head", expected_head,
        "--authorization-receipt", str(authority_path),
        "--go-bin", go_bin,
    ]
    proc = subprocess.run(cmd, text=True, check=False)
    if proc.returncode:
        # The generic helper is transactional after authority consumption, but
        # a pre-consume failure after it stops controllers used to leave them
        # inactive. Restore exactly the previously-active set here.
        for cid in active_before:
            state = repair.systemd(units[cid])
            if state.get("ActiveState") != "active":
                subprocess.run(["systemctl", "start", units[cid]], check=False)
                repair.wait_state(units[cid], "active")
        after_failure = repair.snapshot_controllers(units)
        for cid in active_before:
            state = after_failure[cid]
            if state.get("ActiveState") != "active" or state.get("SubState") != "running":
                raise RuntimeError(
                    f"controller repair failed and restore failed for {cid}"
                )
        repair.require_root_services()
        raise RuntimeError(f"controller repair helper failed with exit {proc.returncode}")

    active, _ = repair.load(repair.CONTROLLER_REFRESH)
    if (
        active.get("phase") != "ACTIVE"
        or active.get("controller_source_head") != expected_head
        or active.get("controller_binary_sha256") != candidate_sha
    ):
        raise RuntimeError("postverify active controller refresh receipt mismatch")

    after = repair.snapshot_controllers(units)
    for cid in active_before:
        state = after[cid]
        if state.get("ActiveState") != "active" or state.get("SubState") != "running":
            raise RuntimeError(f"postverify controller not active/running: {cid}")

    print("MTH602_V3_SESSION_SELF_RECYCLE=PASS")
    print(f"CONTROLLER_SOURCE_HEAD={expected_head}")
    print(f"CONTROLLER_SHA256={candidate_sha}")
    print("ACTIVE_CONTROLLERS=" + ",".join(active_before))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--root-phase", action="store_true")
    args = parser.parse_args()

    exact_repo(args.repo_root, args.expected_head)
    if args.root_phase:
        root_phase(args.repo_root, args.expected_head)
        return 0

    if os.geteuid() == 0:
        raise RuntimeError("launch user phase without sudo")
    run(["sudo", "-v"])
    proc = subprocess.run(
        [
            "sudo", "/usr/bin/python3",
            str((args.repo_root / "scripts" / pathlib.Path(__file__).name).resolve()),
            "--repo-root", str(args.repo_root.resolve()),
            "--expected-head", args.expected_head,
            "--root-phase",
        ],
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
