#!/usr/bin/env python3
"""Third one-shot refresh of PADataset scientific lane-A trusted-workflow authority."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
import pathlib
import re
import subprocess
import uuid
from typing import Any

import lambda_ci_v3_reconciler as candidate
import lambda_ci_v3_padataset_scientific_workflow_refresh_v1 as base


BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
TARGET_CLASS = candidate.PADATASET_SCIENTIFIC_TARGET_CLASS
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_POLICY = pathlib.Path("/etc/workspace-ci/v3/controllers") / f"{TARGET_CLASS}.json"
DUAL_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_ACTIVE_RECEIPT
PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT
REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT
INSTALLED_RECONCILER = candidate.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = candidate.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
PROVISIONER_STATE = pathlib.Path("/var/lib/workspace-ci/v3/provisioner")
TARGET_LEDGER = pathlib.Path("/var/lib/workspace-ci/v3/controller/state") / TARGET_CLASS
STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific/workflow-refresh-v3")
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific/authority-consumption-v3")
OLD_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_BLOB
NEW_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_BLOB
PAD_MAIN = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_PAD_MAIN
WORKFLOW_PATH = candidate.PADATASET_SCIENTIFIC_WORKFLOW_PATH
ACTIVE_RECORD_STATES = {"RESERVED", "JIT_REGISTERED", "PREPARING", "ACCEPTED", "RUNNING"}
AUTHORITY_MAX_SECONDS = 30 * 60
PREFLIGHT_MAX_SECONDS = 15 * 60
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class WorkflowRefreshV3Error(RuntimeError):
    pass


def controller_snapshots() -> dict[str, dict[str, str]]:
    root, _ = base.load(ROOT_POLICY)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise WorkflowRefreshV3Error("installed lane-A class set invalid")
    return {
        cid: base.systemd(f"workspace-ci-v3-controller@{cid}.service")
        for cid in sorted(classes)
        if cid != TARGET_CLASS
    }


def require_snapshot_same(
    before: dict[str, dict[str, str]],
    after: dict[str, dict[str, str]],
) -> None:
    fields = (
        "LoadState",
        "ActiveState",
        "SubState",
        "MainPID",
        "NRestarts",
        "InvocationID",
        "UnitFileState",
    )
    if set(before) != set(after):
        raise WorkflowRefreshV3Error("non-target controller set changed")
    for class_id in before:
        for field in fields:
            if before[class_id].get(field) != after[class_id].get(field):
                raise WorkflowRefreshV3Error(
                    f"non-target controller changed: {class_id} {field}"
                )


def require_roots() -> None:
    p = base.systemd(PROVISIONER_UNIT)
    if p.get("ActiveState") != "active" or p.get("SubState") != "running":
        raise WorkflowRefreshV3Error("shared provisioner is not active/running")
    r = base.systemd(RECONCILER_UNIT)
    if (
        r.get("ActiveState") != "active"
        or r.get("SubState") != "exited"
        or r.get("MainPID") not in {"", "0"}
    ):
        raise WorkflowRefreshV3Error(
            "reconciler must be active/exited with no running process"
        )


def require_target_quiescent() -> None:
    if TARGET_LEDGER.exists():
        for path in sorted(TARGET_LEDGER.glob("scheduler-*.json")):
            value = json.loads(path.read_text())
            if value.get("state") not in {"COMPLETED", "FAILED", "CANCELED"}:
                raise WorkflowRefreshV3Error(
                    f"lane-A controller has nonterminal ledger record: {path.name}"
                )
    if PROVISIONER_STATE.exists():
        for path in sorted(PROVISIONER_STATE.glob("*.json")):
            if path.name.startswith("_"):
                continue
            value = json.loads(path.read_text())
            if value.get("runner_class_id") != TARGET_CLASS:
                continue
            if (
                value.get("state") in ACTIVE_RECORD_STATES
                or value.get("resource_hold") is True
            ):
                raise WorkflowRefreshV3Error(
                    f"lane-A provisioner record still holds capacity: {path.name}"
                )
    proc = subprocess.run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--type=service",
            "--plain",
            "--no-legend",
            "--no-pager",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise WorkflowRefreshV3Error("failed to enumerate transient units")
    prefix = f"workspace-ci-v3-{TARGET_CLASS}-"
    for line in proc.stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        unit = fields[0]
        if not unit.startswith(prefix):
            continue
        state = base.systemd(unit)
        if state.get("ActiveState") in {"active", "activating", "reloading"}:
            raise WorkflowRefreshV3Error(f"lane-A transient still active: {unit}")


def validate_preflight(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = base.require_root_private(path)
    value = json.loads(raw)
    required = {
        "schema_version": 1,
        "mode": "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_PREFLIGHT",
        "repository": "adamtrott78/PADataset",
        "padataset_main_sha": PAD_MAIN,
        "workflow_path": WORKFLOW_PATH,
        "workflow_blob_sha": NEW_BLOB,
        "scale_set_name": candidate.PADATASET_SCIENTIFIC_TARGET_SCALE_SET,
        "assigned_jobs": 0,
        "running_jobs": 0,
        "active_workflow_runs": 0,
    }
    if not isinstance(value, dict):
        raise WorkflowRefreshV3Error("lane-A refresh preflight must be object")
    for key, expected in required.items():
        if value.get(key) != expected:
            raise WorkflowRefreshV3Error(
                f"lane-A refresh preflight mismatch: {key}"
            )
    if not isinstance(value.get("scale_set_id"), int) or value["scale_set_id"] <= 0:
        raise WorkflowRefreshV3Error("lane-A scale_set_id invalid")
    allowed = set(required) | {"scale_set_id", "confirmed_at"}
    if set(value) != allowed:
        raise WorkflowRefreshV3Error("lane-A refresh preflight keys drift")
    confirmed = base.parse_time(value.get("confirmed_at"), "confirmed_at")
    age = (datetime.now(timezone.utc) - confirmed).total_seconds()
    if age < 0 or age > PREFLIGHT_MAX_SECONDS:
        raise WorkflowRefreshV3Error("lane-A refresh preflight stale")
    return value, raw


def validate_authority(
    path: pathlib.Path,
    expected: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    raw = base.require_root_private(path)
    value = json.loads(raw)
    required = {
        "schema_version",
        "authority",
        "operation",
        "authorization_id",
        "issued_at",
        "expires_at",
        *expected.keys(),
    }
    if not isinstance(value, dict) or set(value) != required:
        raise WorkflowRefreshV3Error("lane-A refresh authority keys drift")
    if (
        value["schema_version"] != 1
        or value["authority"] != "workspace-control-operator"
        or value["operation"]
        != "REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V3"
    ):
        raise WorkflowRefreshV3Error("lane-A refresh authority identity invalid")
    aid = value["authorization_id"]
    if (
        not isinstance(aid, str)
        or UUID_RE.fullmatch(aid) is None
        or str(uuid.UUID(aid)) != aid
    ):
        raise WorkflowRefreshV3Error("lane-A refresh authorization id invalid")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise WorkflowRefreshV3Error(
                f"lane-A refresh authority binding mismatch: {key}"
            )
    issued = base.parse_time(value["issued_at"], "issued_at")
    expires = base.parse_time(value["expires_at"], "expires_at")
    now = datetime.now(timezone.utc)
    if not (issued <= now <= expires):
        raise WorkflowRefreshV3Error("lane-A refresh authority not currently valid")
    if (expires - issued).total_seconds() > AUTHORITY_MAX_SECONDS:
        raise WorkflowRefreshV3Error("lane-A refresh authority window too wide")
    return value, raw


def consume_authority(value: dict[str, Any], raw: bytes) -> pathlib.Path:
    base.ensure_dir(AUTHORITY_ROOT)
    marker = AUTHORITY_ROOT / f"{value['authorization_id']}.json"
    record = {
        "schema_version": 1,
        "authorization_id": value["authorization_id"],
        "operation": value["operation"],
        "authority_sha256": base.sha(raw),
        "consumed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise WorkflowRefreshV3Error(
            "lane-A refresh authorization already consumed"
        ) from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(base.canonical(record))
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(marker, 0, 0)
    return marker


def build_refreshed_policy(current: dict[str, Any]) -> dict[str, Any]:
    workflows = current.get("trusted_workflows")
    if not isinstance(workflows, list) or len(workflows) != 1:
        raise WorkflowRefreshV3Error("lane-A trusted workflow set invalid")
    workflow = workflows[0]
    required = {
        "route_id": "scientific-single-gpu",
        "path": WORKFLOW_PATH,
        "default_branch": "main",
        "blob_sha": OLD_BLOB,
        "compile_time_job_key": "padataset-scientific",
        "compile_time_top_level_job_count": 1,
        "allowed_events": ["issue_comment"],
        "allowed_actor_logins": ["adamtrott78"],
    }
    if workflow != required:
        raise WorkflowRefreshV3Error(
            "lane-A workflow binding is not the accepted predecessor"
        )
    refreshed = copy.deepcopy(current)
    refreshed_workflow = copy.deepcopy(workflow)
    refreshed_workflow["blob_sha"] = NEW_BLOB
    refreshed["trusted_workflows"] = [refreshed_workflow]
    refreshed["controller_policy_sha256"] = base.policy_digest(refreshed)
    return refreshed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--preflight-confirmation", type=pathlib.Path, required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise WorkflowRefreshV3Error("lane-A workflow refresh requires root")

    repo = base.exact_repo(args.repo_root, args.expected_head)
    require_roots()
    require_target_quiescent()

    candidate.verify_installed(BASE_MANIFEST)

    target_before = base.systemd(TARGET_UNIT)
    if (
        target_before.get("ActiveState") != "active"
        or target_before.get("SubState") != "running"
        or target_before.get("UnitFileState") != "enabled"
    ):
        raise WorkflowRefreshV3Error(
            "lane-A target controller is not active/running/enabled"
        )
    others_before = controller_snapshots()

    _, preflight_raw = validate_preflight(args.preflight_confirmation)
    dual, dual_raw = base.load(DUAL_ACTIVE)
    prior_refresh, prior_refresh_raw = base.load(PRIOR_REFRESH_ACTIVE)
    if dual.get("phase") != "ACTIVE":
        raise WorkflowRefreshV3Error("dual-lane activation predecessor is not ACTIVE")
    if (
        prior_refresh.get("mode")
        != "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2"
        or prior_refresh.get("phase") != "ACTIVE"
        or prior_refresh.get("workflow_blob_sha") != OLD_BLOB
        or prior_refresh.get("previous_workflow_blob_sha")
        != candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_BLOB
    ):
        raise WorkflowRefreshV3Error(
            "lane-A workflow refresh v2 predecessor binding invalid"
        )
    if REFRESH_ACTIVE.exists():
        raise WorkflowRefreshV3Error("lane-A workflow refresh v3 already exists")

    current_policy, current_policy_raw = base.load(TARGET_POLICY)
    if (
        current_policy.get("controller_policy_sha256")
        != prior_refresh.get("controller_policy_sha256")
    ):
        raise WorkflowRefreshV3Error(
            "lane-A current controller policy does not match refresh v2"
        )
    refreshed_policy = build_refreshed_policy(current_policy)
    refreshed_policy_raw = base.canonical(refreshed_policy)

    manifest, manifest_raw = base.load(BASE_MANIFEST)
    old_rec = INSTALLED_RECONCILER.read_bytes()
    old_rec_sha = base.sha(old_rec)
    _, old_rec_override_raw = base.current_reconciler_override(
        manifest,
        manifest_raw,
        old_rec_sha,
    )
    new_rec = (repo / "scripts/lambda_ci_v3_reconciler.py").read_bytes()
    new_rec_sha = base.sha(new_rec)
    rec_blob = subprocess.check_output(
        ["git", "-C", str(repo), "hash-object", "scripts/lambda_ci_v3_reconciler.py"],
        text=True,
    ).strip()
    entries = {str(e["destination"]): e for e in manifest["entries"]}
    rec_entry = entries[str(INSTALLED_RECONCILER)]
    new_rec_override = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": base.sha(manifest_raw),
        "base_reconciler_sha256": rec_entry.get("sha256"),
        "reconciler_sha256": new_rec_sha,
        "reconciler_mode": str(rec_entry.get("mode")),
        "reconciler_source_head": args.expected_head,
        "reconciler_git_blob": rec_blob,
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }

    expected_authority = {
        "source_head": args.expected_head,
        "dual_active_receipt_sha256": base.sha(dual_raw),
        "prior_refresh_receipt_sha256": base.sha(prior_refresh_raw),
        "preflight_confirmation_sha256": base.sha(preflight_raw),
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "padataset_main_sha": PAD_MAIN,
        "previous_controller_policy_sha256":
            current_policy["controller_policy_sha256"],
        "controller_policy_sha256":
            refreshed_policy["controller_policy_sha256"],
        "target_class_id": TARGET_CLASS,
    }
    authority, authority_raw = validate_authority(
        args.authorization_receipt,
        expected_authority,
    )

    refresh = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3",
        "phase": "ACTIVE",
        "source_head": args.expected_head,
        "dual_active_receipt_sha256": base.sha(dual_raw),
        "prior_refresh_receipt_sha256": base.sha(prior_refresh_raw),
        "target_class_id": TARGET_CLASS,
        "workflow_path": WORKFLOW_PATH,
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "padataset_main_sha": PAD_MAIN,
        "previous_controller_policy_sha256":
            current_policy["controller_policy_sha256"],
        "controller_policy_sha256":
            refreshed_policy["controller_policy_sha256"],
        "controller_policy_file_sha256": base.sha(refreshed_policy_raw),
    }

    base.ensure_dir(TX_ROOT)
    tx_id = str(uuid.uuid4())
    tx_dir = TX_ROOT / f"refresh-{tx_id}"
    base.ensure_dir(tx_dir)
    tx_path = tx_dir / "receipt.json"
    backups = {
        "policy": current_policy_raw,
        "reconciler": old_rec,
        "reconciler_override": old_rec_override_raw,
    }
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_TRANSACTION",
        "phase": "PREPARED",
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": base.sha(authority_raw),
        "preflight_confirmation_sha256": base.sha(preflight_raw),
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "target_controller_before": target_before,
        "existing_controller_snapshot": others_before,
    }
    base.atomic_json(tx_path, tx)
    consume_authority(authority, authority_raw)

    target_stopped = False
    try:
        base.run_systemctl("stop", TARGET_UNIT)
        target_stopped = True
        stopped = base.systemd(TARGET_UNIT)
        if stopped.get("ActiveState") != "inactive":
            raise WorkflowRefreshV3Error("lane-A controller did not stop")

        base.atomic_file(TARGET_POLICY, refreshed_policy_raw, 0o644)
        base.atomic_json(REFRESH_ACTIVE, refresh)
        base.atomic_json(RECONCILER_OVERRIDE, new_rec_override)
        base.atomic_file(
            INSTALLED_RECONCILER,
            new_rec,
            int(str(rec_entry.get("mode")), 8),
        )

        candidate.verify_installed(BASE_MANIFEST)
        proc = subprocess.run(
            [
                "/usr/bin/python3",
                str(INSTALLED_RECONCILER),
                "--verify-installed",
                "--manifest",
                str(BASE_MANIFEST),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode:
            raise WorkflowRefreshV3Error(
                "installed reconciler verification failed: "
                + proc.stderr.strip()[:1024]
            )

        base.run_systemctl("start", TARGET_UNIT)
        target_stopped = False
        target_after = base.systemd(TARGET_UNIT)
        if (
            target_after.get("ActiveState") != "active"
            or target_after.get("SubState") != "running"
            or target_after.get("UnitFileState") != "enabled"
        ):
            raise WorkflowRefreshV3Error(
                "lane-A controller did not return active/running/enabled"
            )
        require_roots()
        require_target_quiescent()
        others_after = controller_snapshots()
        require_snapshot_same(others_before, others_after)
        candidate.verify_installed(BASE_MANIFEST)

        tx.update(
            {
                "phase": "COMMITTED_ACTIVE_WORKFLOW_REFRESH_V2",
                "refresh_receipt_sha256": base.sha(REFRESH_ACTIVE.read_bytes()),
                "controller_policy_file_sha256": base.sha(TARGET_POLICY.read_bytes()),
                "reconciler_sha256": base.sha(INSTALLED_RECONCILER.read_bytes()),
                "target_controller_after": target_after,
                "existing_controller_snapshot_after": others_after,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        base.atomic_json(tx_path, tx)
        print("PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2=PASS")
        print(f"TRANSACTION_RECEIPT={tx_path}")
        return 0
    except BaseException as exc:
        try:
            if not target_stopped:
                subprocess.run(["systemctl", "stop", TARGET_UNIT], check=False)
            base.atomic_file(TARGET_POLICY, backups["policy"], 0o644)
            try:
                REFRESH_ACTIVE.unlink()
            except FileNotFoundError:
                pass
            base.atomic_file(
                RECONCILER_OVERRIDE,
                backups["reconciler_override"],
                0o600,
            )
            base.atomic_file(
                INSTALLED_RECONCILER,
                backups["reconciler"],
                int(str(rec_entry.get("mode")), 8),
            )
            subprocess.run(["systemctl", "start", TARGET_UNIT], check=False)
            rollback_state = base.systemd(TARGET_UNIT)
            if (
                rollback_state.get("ActiveState") != "active"
                or rollback_state.get("SubState") != "running"
                or rollback_state.get("UnitFileState") != "enabled"
            ):
                raise WorkflowRefreshV3Error(
                    "rollback lane-A controller did not return active/running/enabled"
                )
            candidate.verify_installed(BASE_MANIFEST)
            require_roots()
            require_target_quiescent()
            rollback_others = controller_snapshots()
            require_snapshot_same(others_before, rollback_others)
            tx["phase"] = "ROLLED_BACK_TO_WORKFLOW_REFRESH_V2"
            tx["rollback_completed"] = True
            tx["rollback_target_controller_after"] = rollback_state
            tx["rollback_existing_controller_snapshot_after"] = rollback_others
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        base.atomic_json(tx_path, tx)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowRefreshV3Error as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
