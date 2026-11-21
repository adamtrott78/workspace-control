#!/usr/bin/env python3
"""Operator-only one-shot launcher for the authorized MTH602 lane-A L2O trust refresh.

This wrapper does not widen authority. Running it as root is the operator action.
It performs a fresh zero-work preflight, creates root-private one-use receipts
bound to the exact reviewed candidate, then invokes the bounded refresh helper.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import uuid

import lambda_ci_v3_reconciler as candidate
import lambda_ci_v3_padataset_scientific_workflow_refresh_v1 as base
import lambda_ci_v3_padataset_scientific_workflow_refresh_v2 as refresh

EXPECTED_SOURCE_HEAD = "613c0cc8295a521396e794af9f221ff7665e3275"
EXPECTED_PAD_MAIN = "34e150ae4fe349889a054aa2c12d33393cf64f66"
EXPECTED_WORKFLOW_BLOB = "bca2eabe3afe70ec3115391e5a6c24daefd1498b"
EXPECTED_CONFIRM = "MERGE_PR39_AND_ACTIVATE_GPU0_L2O"
REPOSITORY = "adamtrott78/PADataset"
WORKFLOW_NAME = "PADataset Lambda Scientific Single GPU"
SCALE_SET_ID = 5


class OperatorGateError(RuntimeError):
    pass


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def gh_json(path: str):
    proc = subprocess.run(
        ["gh", "api", path],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise OperatorGateError(f"gh api failed: {path}: {proc.stderr.strip()[:800]}")
    return json.loads(proc.stdout)


def root_private_json(path: pathlib.Path, value: dict) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as h:
        h.write(raw)
        h.flush()
        os.fsync(h.fileno())
    os.chown(path, 0, 0)
    return raw


def exact_repo(repo_root: pathlib.Path) -> pathlib.Path:
    root = repo_root.resolve()
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != EXPECTED_SOURCE_HEAD:
        raise OperatorGateError(f"candidate head mismatch: {head}")
    dirty = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=normal"],
        text=True,
    )
    if dirty.strip():
        raise OperatorGateError("candidate checkout is dirty")
    return root


def github_preflight():
    ref = gh_json(f"repos/{REPOSITORY}/git/ref/heads/main")
    main_sha = ref["object"]["sha"]
    if main_sha != EXPECTED_PAD_MAIN:
        raise OperatorGateError(f"PADataset main drift: {main_sha}")

    wf = gh_json(
        f"repos/{REPOSITORY}/contents/.github/workflows/lambda-ci-scientific.yml?ref={main_sha}"
    )
    if wf.get("sha") != EXPECTED_WORKFLOW_BLOB:
        raise OperatorGateError(f"lane-A workflow blob drift: {wf.get('sha')}")

    runs = gh_json(f"repos/{REPOSITORY}/actions/runs?event=issue_comment&per_page=100")
    active = [
        x for x in runs.get("workflow_runs", [])
        if x.get("name") == WORKFLOW_NAME
        and x.get("status") in {"requested", "queued", "pending", "waiting", "in_progress"}
    ]
    if active:
        raise OperatorGateError(
            "lane-A has active workflow runs: "
            + ",".join(str(x.get("id")) for x in active)
        )
    return main_sha


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=pathlib.Path, required=True)
    p.add_argument("--operator-confirm", required=True)
    args = p.parse_args()

    if os.geteuid() != 0:
        raise OperatorGateError("operator launcher requires root")
    if args.operator_confirm != EXPECTED_CONFIRM:
        raise OperatorGateError("operator confirmation marker mismatch")
    if not os.environ.get("GH_TOKEN"):
        raise OperatorGateError("GH_TOKEN is required for fresh GitHub preflight")

    repo = exact_repo(args.repo_root)
    github_preflight()

    # Fail closed on any live-state drift before creating authority.
    candidate.verify_installed(refresh.BASE_MANIFEST)
    refresh.require_roots()
    refresh.require_target_quiescent()

    target = base.systemd(refresh.TARGET_UNIT)
    if (
        target.get("ActiveState") != "active"
        or target.get("SubState") != "running"
        or target.get("UnitFileState") != "enabled"
    ):
        raise OperatorGateError("lane-A controller is not active/running/enabled")

    # Bind preflight to exact live identifiers expected by the reviewed helper.
    tmp = pathlib.Path("/tmp") / f"mth602-lanea-refresh-v2-{uuid.uuid4()}"
    tmp.mkdir(mode=0o700)
    os.chown(tmp, 0, 0)
    preflight_path = tmp / "preflight.json"
    authority_path = tmp / "authority.json"

    now = datetime.now(timezone.utc)
    preflight = {
        "schema_version": 1,
        "mode": "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_PREFLIGHT",
        "repository": REPOSITORY,
        "padataset_main_sha": EXPECTED_PAD_MAIN,
        "workflow_path": candidate.PADATASET_SCIENTIFIC_WORKFLOW_PATH,
        "workflow_blob_sha": EXPECTED_WORKFLOW_BLOB,
        "scale_set_name": candidate.PADATASET_SCIENTIFIC_TARGET_SCALE_SET,
        "assigned_jobs": 0,
        "running_jobs": 0,
        "active_workflow_runs": 0,
        "scale_set_id": SCALE_SET_ID,
        "confirmed_at": now.isoformat(),
    }
    preflight_raw = root_private_json(preflight_path, preflight)

    dual, dual_raw = base.load(refresh.DUAL_ACTIVE)
    prior, prior_raw = base.load(refresh.PRIOR_REFRESH_ACTIVE)
    if dual.get("phase") != "ACTIVE":
        raise OperatorGateError("dual-lane active receipt is not ACTIVE")
    if (
        prior.get("mode") != "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH"
        or prior.get("phase") != "ACTIVE"
        or prior.get("workflow_blob_sha") != refresh.OLD_BLOB
    ):
        raise OperatorGateError("lane-A v1 predecessor receipt drift")

    current_policy, _ = base.load(refresh.TARGET_POLICY)
    refreshed_policy = refresh.build_refreshed_policy(current_policy)

    authority = {
        "schema_version": 1,
        "authority": "workspace-control-operator",
        "operation": "REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V2",
        "authorization_id": str(uuid.uuid4()),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "source_head": EXPECTED_SOURCE_HEAD,
        "dual_active_receipt_sha256": sha(dual_raw),
        "prior_refresh_receipt_sha256": sha(prior_raw),
        "preflight_confirmation_sha256": sha(preflight_raw),
        "previous_workflow_blob_sha": refresh.OLD_BLOB,
        "workflow_blob_sha": refresh.NEW_BLOB,
        "padataset_main_sha": refresh.PAD_MAIN,
        "previous_controller_policy_sha256": current_policy["controller_policy_sha256"],
        "controller_policy_sha256": refreshed_policy["controller_policy_sha256"],
        "target_class_id": refresh.TARGET_CLASS,
    }
    root_private_json(authority_path, authority)

    rc = refresh.main_from_operator(
        repo_root=repo,
        expected_head=EXPECTED_SOURCE_HEAD,
        preflight_confirmation=preflight_path,
        authorization_receipt=authority_path,
    ) if hasattr(refresh, "main_from_operator") else None

    if rc is None:
        cmd = [
            "/usr/bin/python3",
            str(repo / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v2.py"),
            "--repo-root", str(repo),
            "--expected-head", EXPECTED_SOURCE_HEAD,
            "--preflight-confirmation", str(preflight_path),
            "--authorization-receipt", str(authority_path),
        ]
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        print(proc.stdout, end="")
        if proc.returncode:
            if proc.stderr:
                print(proc.stderr, end="", file=__import__("sys").stderr)
            raise OperatorGateError(f"refresh helper failed rc={proc.returncode}")

    candidate.verify_installed(refresh.BASE_MANIFEST)
    installed = json.loads(refresh.TARGET_POLICY.read_text())
    wf = installed.get("trusted_workflows") or []
    if len(wf) != 1 or wf[0].get("blob_sha") != EXPECTED_WORKFLOW_BLOB:
        raise OperatorGateError("postverify lane-A workflow binding mismatch")

    state = base.systemd(refresh.TARGET_UNIT)
    if state.get("ActiveState") != "active" or state.get("SubState") != "running":
        raise OperatorGateError("postverify lane-A controller not active/running")

    print("MTH602_LANEA_L2O_REFRESH_V2_POSTVERIFY=PASS")
    print(f"WORKFLOW_BLOB={EXPECTED_WORKFLOW_BLOB}")
    print(f"CONTROLLER_POLICY_SHA256={installed['controller_policy_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OperatorGateError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
