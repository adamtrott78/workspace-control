#!/usr/bin/env python3
"""One-command operator launcher for the validated PADataset lane-B refresh-v9."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import uuid

EXPECTED_PAD_MAIN = "7cfe0ab61cc16785f4d267273b48a63361c595dd"
EXPECTED_WORKFLOW_BLOB = "6753795041090a5331a80354f59945be006ac889"
WORKFLOW_FILE = "lambda-ci-scientific-2.yml"
REPOSITORY = "adamtrott78/PADataset"


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


def provider_zero_work() -> None:
    main_sha = run(
        ["gh", "api", f"repos/{REPOSITORY}/branches/main", "--jq", ".commit.sha"]
    )
    if main_sha != EXPECTED_PAD_MAIN:
        raise RuntimeError(f"PADataset main moved: {main_sha} != {EXPECTED_PAD_MAIN}")

    blob = run(
        [
            "gh",
            "api",
            f"repos/{REPOSITORY}/contents/.github/workflows/{WORKFLOW_FILE}?ref=main",
            "--jq",
            ".sha",
        ]
    )
    if blob != EXPECTED_WORKFLOW_BLOB:
        raise RuntimeError(
            f"lane-B workflow blob mismatch: {blob} != {EXPECTED_WORKFLOW_BLOB}"
        )

    for status in ("queued", "in_progress"):
        raw = run(
            [
                "gh",
                "api",
                f"repos/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/runs?status={status}&per_page=100",
            ]
        )
        data = json.loads(raw)
        count = int(data.get("total_count", -1))
        if count != 0:
            ids = [str(x.get("id")) for x in data.get("workflow_runs", [])]
            raise RuntimeError(
                f"lane-B provider not quiescent: status={status} total_count={count} ids={','.join(ids)}"
            )
    print("LANEB_PROVIDER_ZERO_WORK=PASS")
    print(f"PAD_MAIN={main_sha}")
    print(f"LANEB_WORKFLOW_BLOB={blob}")


def root_phase(repo_root: pathlib.Path, expected_head: str) -> None:
    if os.geteuid() != 0:
        raise RuntimeError("root phase requires uid 0")
    root = exact_repo(repo_root, expected_head)
    scripts = root / "scripts"
    sys.path.insert(0, str(scripts))

    import lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9 as helper

    if helper.PAD_MAIN != EXPECTED_PAD_MAIN:
        raise RuntimeError("helper PAD_MAIN binding mismatch")
    if helper.NEW_BLOB != EXPECTED_WORKFLOW_BLOB:
        raise RuntimeError("helper workflow blob binding mismatch")

    helper.require_roots()
    helper.require_target_quiescent()

    dual, dual_raw = helper.base.load(helper.DUAL_ACTIVE)
    prior, prior_raw = helper.base.load(helper.PRIOR_REFRESH_ACTIVE)
    current_policy, _ = helper.base.load(helper.TARGET_POLICY)

    scale_set_id = dual.get("scale_set_id")
    if not isinstance(scale_set_id, int) or scale_set_id <= 0:
        raise RuntimeError("live lane-B activation receipt lacks valid scale_set_id")

    refreshed_policy = helper.build_refreshed_policy(current_policy)
    refreshed_policy_raw = helper.base.canonical(refreshed_policy)

    work = pathlib.Path(
        tempfile.mkdtemp(prefix="mth602-laneb-v9-", dir="/run")
    )
    os.chown(work, 0, 0)
    os.chmod(work, 0o700)
    preflight_path = work / "preflight.json"
    authority_path = work / "authority.json"

    now = datetime.now(timezone.utc)
    preflight = {
        "schema_version": 1,
        "mode": "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_PREFLIGHT",
        "repository": REPOSITORY,
        "padataset_main_sha": EXPECTED_PAD_MAIN,
        "workflow_path": helper.WORKFLOW_PATH,
        "workflow_blob_sha": EXPECTED_WORKFLOW_BLOB,
        "scale_set_name": helper.candidate.PADATASET_SCIENTIFIC_DUAL_TARGET_SCALE_SET,
        "scale_set_id": scale_set_id,
        "assigned_jobs": 0,
        "running_jobs": 0,
        "active_workflow_runs": 0,
        "confirmed_at": now.isoformat(),
    }
    helper.base.atomic_json(preflight_path, preflight)
    preflight_raw = preflight_path.read_bytes()

    expected_authority = {
        "source_head": expected_head,
        "dual_active_receipt_sha256": helper.base.sha(dual_raw),
        "prior_refresh_receipt_sha256": helper.base.sha(prior_raw),
        "preflight_confirmation_sha256": helper.base.sha(preflight_raw),
        "previous_workflow_blob_sha": helper.OLD_BLOB,
        "workflow_blob_sha": helper.NEW_BLOB,
        "padataset_main_sha": helper.PAD_MAIN,
        "previous_controller_policy_sha256": current_policy[
            "controller_policy_sha256"
        ],
        "controller_policy_sha256": refreshed_policy[
            "controller_policy_sha256"
        ],
        "target_class_id": helper.TARGET_CLASS,
    }
    authority = {
        "schema_version": 1,
        "authority": "workspace-control-operator",
        "operation": "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V9",
        "authorization_id": str(uuid.uuid4()),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        **expected_authority,
    }
    helper.base.atomic_json(authority_path, authority)

    cmd = [
        "/usr/bin/python3",
        str(scripts / "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py"),
        "--repo-root",
        str(root),
        "--expected-head",
        expected_head,
        "--preflight-confirmation",
        str(preflight_path),
        "--authorization-receipt",
        str(authority_path),
    ]
    proc = subprocess.run(cmd, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"refresh-v8 helper failed with exit {proc.returncode}")

    active, _ = helper.base.load(helper.REFRESH_ACTIVE)
    if active.get("workflow_blob_sha") != EXPECTED_WORKFLOW_BLOB:
        raise RuntimeError("postverify active receipt workflow blob mismatch")
    policy, _ = helper.base.load(helper.TARGET_POLICY)
    workflows = policy.get("trusted_workflows")
    if (
        not isinstance(workflows, list)
        or len(workflows) != 1
        or workflows[0].get("blob_sha") != EXPECTED_WORKFLOW_BLOB
    ):
        raise RuntimeError("postverify controller policy workflow blob mismatch")
    state = helper.base.systemd(helper.TARGET_UNIT)
    if state.get("ActiveState") != "active" or state.get("SubState") != "running":
        raise RuntimeError("postverify lane-B controller is not active/running")

    print("MTH602_LANEB_REFRESH_V9_POSTVERIFY=PASS")
    print(f"CONTROLLER_POLICY_SHA256={policy.get('controller_policy_sha256')}")
    print(f"TRUSTED_WORKFLOW_BLOB={EXPECTED_WORKFLOW_BLOB}")


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
    provider_zero_work()
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
