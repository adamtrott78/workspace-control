#!/usr/bin/env python3
"""One-command operator bootstrap for the validated v3 REST-backfill liveness repair."""

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
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def exact_repo(repo_root: pathlib.Path, expected_head: str) -> pathlib.Path:
    root = repo_root.resolve()
    head = run(["git", "-C", str(root), "rev-parse", "HEAD"])
    if head != expected_head:
        raise RuntimeError(f"source head mismatch: {head} != {expected_head}")
    dirty = run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=normal"]
    )
    if dirty:
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
    failures: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        path = str(pathlib.Path(candidate).resolve())
        if path in seen or not pathlib.Path(path).is_file():
            continue
        seen.add(path)
        version = subprocess.run(
            [path, "version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        label = (version.stdout or version.stderr).strip()
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
            print(f"GO_TOOLCHAIN_VERSION={label}")
            return path
        failures.append(
            f"{path}: {label or 'version unavailable'}: "
            f"{probe.stderr.strip()[-512:] or 'module probe failed'}"
        )
    raise RuntimeError(
        "no installed Go compiler can parse the exact controller module; "
        + " | ".join(failures)
    )


EQUIVALENT_ACTIVE_CONTROLLER_SOURCES = {
    # Previously validated and live controller-only repair.  The controller
    # production source blobs at this head are identical to the PR #658
    # candidate, and equality of the built binary digest is still required
    # before this no-op path can be accepted.
    "45bcf7caa14778baeb014d702064b4a0bfa50d94": {
        "controller_go_blob": "59753977cb2b77d8308b58f311784da366de63bd",
        "main_go_blob": "18abac983e389069b1f988792dbea42628486c09",
    },
}


def verify_equivalent_active_source(
    repo_root: pathlib.Path,
    previous_source_head: object,
) -> str:
    if not isinstance(previous_source_head, str):
        raise RuntimeError("active controller source head is not a string")
    binding = EQUIVALENT_ACTIVE_CONTROLLER_SOURCES.get(previous_source_head)
    if binding is None:
        raise RuntimeError(
            "candidate digest already installed from an unreviewed source head: "
            + previous_source_head
        )
    controller_blob = run(
        [
            "git",
            "-C",
            str(repo_root),
            "rev-parse",
            "HEAD:controller/lambda-ci-controller/v3/controller.go",
        ]
    )
    main_blob = run(
        [
            "git",
            "-C",
            str(repo_root),
            "rev-parse",
            "HEAD:controller/lambda-ci-controller/v3/main.go",
        ]
    )
    if controller_blob != binding["controller_go_blob"]:
        raise RuntimeError("candidate controller.go blob differs from reviewed equivalent source")
    if main_blob != binding["main_go_blob"]:
        raise RuntimeError("candidate main.go blob differs from reviewed equivalent source")
    return previous_source_head



def root_phase(repo_root: pathlib.Path, expected_head: str) -> None:
    if os.geteuid() != 0:
        raise RuntimeError("root phase requires uid 0")
    root = exact_repo(repo_root, expected_head)
    scripts = root / "scripts"
    sys.path.insert(0, str(scripts))

    import lambda_ci_v3_live_controller_repair_v1 as repair
    import lambda_ci_v3_reconciler as reconciler

    reconciler.verify_installed(repair.BASE_MANIFEST)
    manifest, manifest_raw = repair.load(repair.BASE_MANIFEST)
    root_policy, _ = repair.load(repair.ROOT_POLICY)
    units = repair.controller_units(root_policy)
    before = repair.snapshot_controllers(units)
    active_before = [
        cid for cid, state in before.items()
        if state.get("ActiveState") == "active"
    ]
    if repair.TARGET_CLASS not in active_before:
        raise RuntimeError("PADataset scientific lane A is not active before bootstrap")
    repair.require_root_services()

    current_binary = repair.CONTROLLER_BINARY.read_bytes()
    current_sha = repair.sha(current_binary)
    go_bin = find_go(root)
    candidate_binary = repair.build_candidate(root, go_bin)
    candidate_sha = repair.sha(candidate_binary)

    previous_refresh, previous_refresh_raw = repair.load(repair.CONTROLLER_REFRESH)
    if (
        previous_refresh.get("mode") != repair.MODE
        or previous_refresh.get("phase") != "ACTIVE"
        or previous_refresh.get("controller_binary_sha256") != current_sha
    ):
        raise RuntimeError("current controller refresh receipt is not a valid active predecessor")

    if current_sha == candidate_sha:
        previous_source_head = previous_refresh.get("controller_source_head")
        if previous_source_head == expected_head:
            print("MTH602_V3_REST_BACKFILL_BOOTSTRAP=ALREADY_ACTIVE")
            print(f"CONTROLLER_SOURCE_HEAD={expected_head}")
            print(f"CONTROLLER_SHA256={candidate_sha}")
            print("ACTIVE_CONTROLLERS=" + ",".join(active_before))
            return

        equivalent_source = verify_equivalent_active_source(root, previous_source_head)
        after = repair.snapshot_controllers(units)
        for cid in active_before:
            state = after[cid]
            if state.get("ActiveState") != "active" or state.get("SubState") != "running":
                raise RuntimeError(
                    f"equivalent-active postverify controller not active/running: {cid}"
                )
        repair.require_root_services()
        print("MTH602_V3_REST_BACKFILL_BOOTSTRAP=ALREADY_ACTIVE_EQUIVALENT")
        print(f"CONTROLLER_SOURCE_HEAD={equivalent_source}")
        print(f"CANDIDATE_SOURCE_HEAD={expected_head}")
        print(f"CONTROLLER_SHA256={candidate_sha}")
        print("ACTIVE_CONTROLLERS=" + ",".join(active_before))
        return

    base_sha = repair.sha(manifest_raw)
    root_policy_sha = manifest.get("root_policy_sha256")
    base_head = manifest.get("source_head")
    if not isinstance(base_head, str) or repair.SHA40.fullmatch(base_head) is None:
        raise RuntimeError("base manifest source head invalid")
    if not isinstance(root_policy_sha, str) or repair.SHA64.fullmatch(root_policy_sha) is None:
        raise RuntimeError("root policy digest invalid")

    expected = {
        "source_head": expected_head,
        "base_source_head": base_head,
        "base_install_manifest_sha256": base_sha,
        "root_policy_sha256": root_policy_sha,
        "current_controller_sha256": current_sha,
        "candidate_controller_sha256": candidate_sha,
        "previous_controller_refresh_sha256": repair.sha(previous_refresh_raw),
        "previous_controller_source_head": previous_refresh.get("controller_source_head"),
    }

    work = pathlib.Path(tempfile.mkdtemp(prefix="mth602-v3-rest-backfill-", dir="/run"))
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
        **expected,
    }
    repair.atomic_json(authority_path, authority)

    cmd = [
        "/usr/bin/python3",
        str(scripts / "lambda_ci_v3_live_controller_repair_v1.py"),
        "--expected-head",
        expected_head,
        "--authorization-receipt",
        str(authority_path),
        "--go-bin",
        go_bin,
    ]
    proc = subprocess.run(cmd, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"controller repair helper failed with exit {proc.returncode}")

    active, _ = repair.load(repair.CONTROLLER_REFRESH)
    if (
        active.get("mode") != repair.MODE
        or active.get("phase") != "ACTIVE"
        or active.get("controller_source_head") != expected_head
        or active.get("controller_binary_sha256") != candidate_sha
    ):
        raise RuntimeError("postverify active controller refresh receipt mismatch")

    after = repair.snapshot_controllers(units)
    for cid in active_before:
        state = after[cid]
        if state.get("ActiveState") != "active" or state.get("SubState") != "running":
            raise RuntimeError(f"postverify controller not active/running: {cid}")
    repair.require_root_services()

    print("MTH602_V3_REST_BACKFILL_BOOTSTRAP=PASS")
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
            "sudo",
            "/usr/bin/python3",
            str((args.repo_root / "scripts" / pathlib.Path(__file__).name).resolve()),
            "--repo-root",
            str(args.repo_root.resolve()),
            "--expected-head",
            args.expected_head,
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
