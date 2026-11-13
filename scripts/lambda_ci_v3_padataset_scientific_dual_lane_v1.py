#!/usr/bin/env python3
"""Drained two-phase activation for PADataset scientific lane B.

Phase A expands the already-live scientific generation from 10 to 11 classes,
raises only the host and PADataset project concurrency ceilings from 1 to 2,
and installs lane B inactive/disabled. Phase B separately activates lane B
after a fresh GitHub/scale-set/runtime preflight. Both phases require exact,
root-owned one-shot operator authority and fail closed on nonterminal work.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
import pathlib
import re
import stat
import subprocess
import uuid
from typing import Any

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_reconciler as reconciler
import lambda_ci_v3_padataset_scientific_activation_v1 as base


ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
EXECUTOR_ACTIONS = pathlib.Path("/etc/workspace-ci/v3/executor-actions.json")
COMPATIBILITY_MATRIX = pathlib.Path("/etc/workspace-ci/v3/compatibility-matrix.json")
DEPLOYMENT_OVERLAY = pathlib.Path("/etc/workspace-ci/v3/deployment-overlay.json")
SYSUSERS = pathlib.Path("/etc/sysusers.d/workspace-ci-v3.conf")
TMPFILES = pathlib.Path("/etc/tmpfiles.d/workspace-ci-v3.conf")
MIGRATION_PLAN_REL = pathlib.Path("architecture/lambda-ci-v3-migration-plan.v1.json")
OVERLAY_TEMPLATE_REL = pathlib.Path("architecture/lambda-ci-deployment-overlay.v1.json")

TARGET_CLASS = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_CLASS
TARGET_ROUTE = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_ROUTE
TARGET_SCALE_SET = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_SCALE_SET
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_POLICY = pathlib.Path("/etc/workspace-ci/v3/controllers") / f"{TARGET_CLASS}.json"
TARGET_DROPIN = (
    pathlib.Path("/etc/systemd/system")
    / f"workspace-ci-v3-controller@{TARGET_CLASS}.service.d"
    / "identity.conf"
)

PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
PROVISIONER_SOCKET = pathlib.Path("/run/workspace-ci/v3/provisioner.sock")
ACTIVE_RECEIPT = reconciler.PADATASET_SCIENTIFIC_DUAL_ACTIVE_RECEIPT
SCIENTIFIC_ACTIVE = reconciler.PADATASET_SCIENTIFIC_ACTIVE_RECEIPT
WORKFLOW_REFRESH = reconciler.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT
RECONCILER_INSTALLED = reconciler.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = reconciler.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific/dual-lane")
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = STATE_ROOT / "authority-consumption"

WORKFLOW_PATH = reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_PATH
WORKFLOW_BLOB = reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB
GPU0 = reconciler.PADATASET_SCIENTIFIC_DUAL_GPU0
GPU1 = reconciler.PADATASET_SCIENTIFIC_DUAL_GPU1
RUNTIME_MANIFEST = reconciler.PADATASET_SCIENTIFIC_RUNTIME_MANIFEST
RUNTIME_TREE = reconciler.PADATASET_SCIENTIFIC_RUNTIME_TREE
DATA_PROFILE = reconciler.PADATASET_SCIENTIFIC_DATA_PROFILE
DATA_DIGEST = reconciler.PADATASET_SCIENTIFIC_DATA_DIGEST

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
PREFLIGHT_MAX_SECONDS = 15 * 60


class DualLaneActivationError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DualLaneActivationError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise DualLaneActivationError(f"{path}: expected object")
    return value


def _sha(raw: bytes) -> str:
    return base._sha(raw)


def _sha_file(path: pathlib.Path) -> str:
    return base._sha_file(path)


def _exact_repo(repo_root: pathlib.Path, expected_head: str) -> pathlib.Path:
    try:
        return base._exact_repo(repo_root, expected_head)
    except base.ScientificActivationError as exc:
        raise DualLaneActivationError(str(exc)) from exc


def _semantic(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in policy.items()
        if key not in {"control_plane_generation_sha256", "root_envelope_sha256"}
    }


def _validate_generation(
    current_root: dict[str, Any],
    candidate_root: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    current_classes = current_root.get("runner_classes")
    candidate_classes = candidate_root.get("runner_classes")
    if not isinstance(current_classes, dict) or not isinstance(candidate_classes, dict):
        raise DualLaneActivationError("runner class maps missing")
    if TARGET_CLASS in current_classes:
        raise DualLaneActivationError("lane B already exists in current root policy")
    if set(candidate_classes) != set(current_classes) | {TARGET_CLASS}:
        raise DualLaneActivationError("candidate is not exact +1 class generation")

    current_host = current_root.get("host_resource_policy")
    candidate_host = candidate_root.get("host_resource_policy")
    if not isinstance(current_host, dict) or not isinstance(candidate_host, dict):
        raise DualLaneActivationError("host resource policy missing")
    if current_host.get("migration_mode", {}).get("host_max_active_runners") != 1:
        raise DualLaneActivationError("predecessor host max is not 1")
    if candidate_host.get("migration_mode", {}).get("host_max_active_runners") != 2:
        raise DualLaneActivationError("candidate host max is not 2")
    if current_host.get("project_limits", {}).get("padataset", {}).get("max_active_runners") != 1:
        raise DualLaneActivationError("predecessor PADataset max is not 1")
    if candidate_host.get("project_limits", {}).get("padataset", {}).get("max_active_runners") != 2:
        raise DualLaneActivationError("candidate PADataset max is not 2")
    for project in ("workspace-control", "research-engine"):
        if (
            current_host.get("project_limits", {}).get(project)
            != candidate_host.get("project_limits", {}).get(project)
        ):
            raise DualLaneActivationError(
                f"candidate widened unrelated project limit: {project}"
            )
    if current_host.get("exclusive_resources") != candidate_host.get("exclusive_resources"):
        raise DualLaneActivationError("exclusive GPU resource inventory drift")

    previous: dict[str, str] = {}
    current: dict[str, str] = {}
    for class_id, old in current_classes.items():
        new = candidate_classes[class_id]
        old_digest = old.get("root_envelope_sha256")
        new_digest = new.get("root_envelope_sha256")
        if (
            not isinstance(old_digest, str)
            or SHA64.fullmatch(old_digest) is None
            or not isinstance(new_digest, str)
            or SHA64.fullmatch(new_digest) is None
        ):
            raise DualLaneActivationError(f"invalid envelope digest: {class_id}")
        previous[class_id] = old_digest
        current[class_id] = new_digest

        old_sem = _semantic(old)
        new_sem = _semantic(new)
        if old.get("project_id") == "padataset":
            if old_sem.get("project_max_active_runners") != 1:
                raise DualLaneActivationError(
                    f"predecessor PADataset class cap drift: {class_id}"
                )
            if new_sem.get("project_max_active_runners") != 2:
                raise DualLaneActivationError(
                    f"candidate PADataset class cap drift: {class_id}"
                )
            new_sem["project_max_active_runners"] = 1
        if old_sem != new_sem:
            raise DualLaneActivationError(
                f"candidate changed pre-existing class authority: {class_id}"
            )

    target = candidate_classes[TARGET_CLASS]
    exact = {
        "runner_class_id": TARGET_CLASS,
        "project_id": "padataset",
        "repository": "adamtrott78/PADataset",
        "scale_set_name": TARGET_SCALE_SET,
        "runner_prefix": "lambda-padataset-scientific-single-gpu-2-",
        "execution_contract_id": "scientific-single-gpu-2-v1",
        "max_runners": 1,
        "project_max_active_runners": 2,
    }
    for key, expected in exact.items():
        if target.get(key) != expected:
            raise DualLaneActivationError(f"lane B target binding mismatch: {key}")
    if target.get("controller_peer") != {"unix_user": "ci-ctl-pad-science-2"}:
        raise DualLaneActivationError("lane B controller identity mismatch")
    if target.get("exclusive_resource_claims") != [f"gpu:{GPU1}"]:
        raise DualLaneActivationError("lane B GPU1 claim mismatch")
    resource = target.get("resource_class")
    if (
        not isinstance(resource, dict)
        or resource.get("gpu_uuids") != [GPU1]
        or resource.get("gpu_count") != 1
        or resource.get("execution_profile") != "gpu-scientific-single-2"
    ):
        raise DualLaneActivationError("lane B resource envelope mismatch")

    lane_a = candidate_classes.get(reconciler.PADATASET_SCIENTIFIC_TARGET_CLASS)
    if (
        not isinstance(lane_a, dict)
        or lane_a.get("exclusive_resource_claims") != [f"gpu:{GPU0}"]
    ):
        raise DualLaneActivationError("lane A GPU0 claim drift")
    current[TARGET_CLASS] = target["root_envelope_sha256"]
    return previous, current


def _candidate_artifacts(
    repo_root: pathlib.Path,
    current_root: dict[str, Any],
    current_overlay: dict[str, Any],
) -> tuple[dict[str, Any], dict[pathlib.Path, tuple[bytes, int]], dict[str, str], dict[str, str]]:
    compiled = compiler.compile_policy(repo_root)
    previous, current = _validate_generation(
        current_root,
        compiled["root_projection"],
    )
    template = _load(repo_root / OVERLAY_TEMPLATE_REL)
    if TARGET_CLASS in current_overlay.get("classes", {}):
        raise DualLaneActivationError("lane B already exists in live overlay")
    if TARGET_ROUTE in current_overlay.get("routes", {}):
        raise DualLaneActivationError("lane B route already exists in live overlay")

    overlay = copy.deepcopy(current_overlay)
    overlay["catalog_generation_sha256"] = compiled["catalog_generation_sha256"]
    target_state = copy.deepcopy(template["classes"][TARGET_CLASS])
    target_state["install_state"] = "INSTALLED"
    target_state["controller_state"] = "INACTIVE"
    target_state["containment"] = {"state": "CLEAR", "source": None}
    route_state = copy.deepcopy(template["routes"][TARGET_ROUTE])
    route_state["admission_state"] = "DISABLED"
    route_state["source"] = "PADataset scientific dual-lane install: activation pending"
    overlay["classes"][TARGET_CLASS] = target_state
    overlay["routes"][TARGET_ROUTE] = route_state

    target_policy = compiled["controller_projections"][TARGET_CLASS]
    workflows = target_policy.get("trusted_workflows")
    if (
        target_policy.get("runner_class_id") != TARGET_CLASS
        or target_policy.get("scale_set_name") != TARGET_SCALE_SET
        or not isinstance(workflows, list)
        or len(workflows) != 1
        or workflows[0].get("route_id") != "scientific-single-gpu-2"
        or workflows[0].get("path") != WORKFLOW_PATH
        or workflows[0].get("blob_sha") != WORKFLOW_BLOB
    ):
        raise DualLaneActivationError("lane B compiled controller binding drift")

    migration = _load(repo_root / MIGRATION_PLAN_REL)
    artifacts = {
        ROOT_POLICY: (base._canonical(compiled["root_projection"]), 0o644),
        EXECUTOR_ACTIONS: (base._canonical(compiled["executor_projection"]), 0o644),
        COMPATIBILITY_MATRIX: (base._canonical(compiled["compatibility_matrix"]), 0o644),
        DEPLOYMENT_OVERLAY: (base._canonical(overlay), 0o644),
        SYSUSERS: (reconciler.render_sysusers(compiled, migration).encode(), 0o644),
        TMPFILES: (reconciler.render_tmpfiles(compiled, migration).encode(), 0o644),
        TARGET_POLICY: (base._canonical(target_policy), 0o644),
        TARGET_DROPIN: (
            reconciler.render_controller_dropin(
                TARGET_CLASS,
                compiled["root_projection"]["runner_classes"][TARGET_CLASS],
                migration,
            ).encode(),
            0o644,
        ),
    }
    return compiled, artifacts, previous, current


def _build_receipt(
    *,
    source_head: str,
    compiled: dict[str, Any],
    artifacts: dict[pathlib.Path, tuple[bytes, int]],
    previous: dict[str, str],
    current: dict[str, str],
    phase: str,
) -> dict[str, Any]:
    scientific = _load(SCIENTIFIC_ACTIVE)
    if scientific.get("phase") != "ACTIVE":
        raise DualLaneActivationError("lane A scientific predecessor is not ACTIVE")
    refresh = _load(WORKFLOW_REFRESH) if WORKFLOW_REFRESH.is_file() else None

    overrides: dict[str, dict[str, str]] = {}
    predecessor = scientific.get("managed_artifact_overrides")
    if not isinstance(predecessor, dict):
        raise DualLaneActivationError("lane A predecessor override map missing")
    for destination in sorted(reconciler.PADATASET_SCIENTIFIC_DUAL_OVERRIDE_DESTINATIONS):
        path = pathlib.Path(destination)
        raw, mode = artifacts[path]
        prior = predecessor[destination]["sha256"]
        if not path.is_file() or _sha_file(path) != prior:
            raise DualLaneActivationError(
                f"live predecessor artifact does not match receipt: {path}"
            )
        overrides[destination] = {
            "prior_sha256": prior,
            "sha256": _sha(raw),
            "mode": f"{mode:04o}",
        }

    additions: dict[str, dict[str, str]] = {}
    for destination in sorted(reconciler.PADATASET_SCIENTIFIC_DUAL_ADDITION_DESTINATIONS):
        path = pathlib.Path(destination)
        raw, mode = artifacts[path]
        if path.exists():
            raise DualLaneActivationError(f"lane B managed addition exists: {path}")
        additions[destination] = {
            "sha256": _sha(raw),
            "mode": f"{mode:04o}",
        }

    target_policy = compiled["controller_projections"][TARGET_CLASS]
    return {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_DUAL_LANE_OVERRIDE",
        "phase": phase,
        "source_head": source_head,
        "scientific_active_receipt_sha256": _sha(SCIENTIFIC_ACTIVE.read_bytes()),
        "scientific_workflow_refresh_receipt_sha256": (
            _sha(WORKFLOW_REFRESH.read_bytes()) if refresh is not None else None
        ),
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "previous_root_policy_sha256": _load(ROOT_POLICY)["root_policy_sha256"],
        "root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "target_scale_set_name": TARGET_SCALE_SET,
        "target_controller_policy_sha256": target_policy["controller_policy_sha256"],
        "trusted_workflow_blob_sha": WORKFLOW_BLOB,
        "gpu0_uuid": GPU0,
        "gpu1_uuid": GPU1,
        "runtime_manifest_identity_sha256": RUNTIME_MANIFEST,
        "runtime_tree_digest_sha256": RUNTIME_TREE,
        "scientific_data_profile_id": DATA_PROFILE,
        "scientific_data_tree_digest_sha256": DATA_DIGEST,
        "installed_inactive_overlay_sha256": _sha(artifacts[DEPLOYMENT_OVERLAY][0]),
        "previous_root_envelope_sha256": previous,
        "root_envelope_sha256": current,
        "managed_artifact_overrides": overrides,
        "managed_artifact_additions": additions,
    }


def _load_authority(
    path: pathlib.Path,
    *,
    operation: str,
    expected: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    try:
        return base._load_authority(path, operation=operation, expected=expected)
    except base.ScientificActivationError as exc:
        raise DualLaneActivationError(str(exc)) from exc


def _consume_authority(value: dict[str, Any], raw: bytes) -> pathlib.Path:
    try:
        base._ensure_private_dir(AUTHORITY_ROOT)
        return base._consume_authority(value, raw)
    except base.ScientificActivationError as exc:
        raise DualLaneActivationError(str(exc)) from exc


def _validate_preflight(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = base._require_root_private_file(path)
    value = json.loads(raw)
    required = {
        "schema_version": 1,
        "mode": "PADATASET_SCIENTIFIC_DUAL_LANE_PREFLIGHT",
        "repository": "adamtrott78/PADataset",
        "workflow_path": WORKFLOW_PATH,
        "workflow_blob_sha": WORKFLOW_BLOB,
        "scale_set_name": TARGET_SCALE_SET,
        "assigned_jobs": 0,
        "running_jobs": 0,
        "active_scientific_workflow_runs": 0,
        "runtime_manifest_identity_sha256": RUNTIME_MANIFEST,
        "runtime_tree_digest_sha256": RUNTIME_TREE,
        "scientific_data_profile_id": DATA_PROFILE,
        "scientific_data_tree_digest_sha256": DATA_DIGEST,
    }
    if not isinstance(value, dict):
        raise DualLaneActivationError("dual-lane preflight must be object")
    for key, expected in required.items():
        if value.get(key) != expected:
            raise DualLaneActivationError(f"dual-lane preflight mismatch: {key}")
    if not isinstance(value.get("scale_set_id"), int) or value["scale_set_id"] <= 0:
        raise DualLaneActivationError("dual-lane scale_set_id invalid")
    confirmed = base._parse_time(value.get("confirmed_at"), "confirmed_at")
    age = (datetime.now(timezone.utc) - confirmed).total_seconds()
    if age < 0 or age > PREFLIGHT_MAX_SECONDS:
        raise DualLaneActivationError("dual-lane preflight stale")
    allowed = set(required) | {"scale_set_id", "confirmed_at", "padataset_main_sha"}
    if set(value) != allowed:
        raise DualLaneActivationError("dual-lane preflight key drift")
    if SHA40.fullmatch(str(value.get("padataset_main_sha", ""))) is None:
        raise DualLaneActivationError("dual-lane PADataset main SHA invalid")
    return value, raw


def expand_inactive(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    authority_path: pathlib.Path,
    systemd: Any | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise DualLaneActivationError("dual-lane expansion requires root")
    if ACTIVE_RECEIPT.exists():
        raise DualLaneActivationError("dual-lane generation already installed")
    repo_root = _exact_repo(repo_root, expected_head)
    systemd = systemd or base.RealSystemd()

    reconciler.verify_installed(BASE_MANIFEST)
    current_root = _load(ROOT_POLICY)
    current_overlay = _load(DEPLOYMENT_OVERLAY)
    compiled, artifacts, previous, current = _candidate_artifacts(
        repo_root, current_root, current_overlay
    )
    receipt = _build_receipt(
        source_head=expected_head,
        compiled=compiled,
        artifacts=artifacts,
        previous=previous,
        current=current,
        phase="INSTALLED_INACTIVE",
    )

    expected_authority = {
        "source_head": expected_head,
        "current_root_policy_sha256": current_root["root_policy_sha256"],
        "candidate_root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "host_max_active_runners": 2,
        "padataset_max_active_runners": 2,
        "scientific_active_receipt_sha256": receipt["scientific_active_receipt_sha256"],
        "scientific_workflow_refresh_receipt_sha256":
            receipt["scientific_workflow_refresh_receipt_sha256"],
    }
    authority, authority_raw = _load_authority(
        authority_path,
        operation="EXPAND_PADATASET_SCIENTIFIC_DUAL_LANE_V1",
        expected=expected_authority,
    )

    existing_ids = sorted(current_root["runner_classes"])
    before = base._controller_snapshot(systemd, existing_ids)
    base._require_provisioner_active(systemd)
    base._require_quiescent(systemd)

    base._ensure_private_dir(STATE_ROOT)
    base._ensure_private_dir(TX_ROOT)
    base._ensure_private_dir(AUTHORITY_ROOT)
    tx_dir = TX_ROOT / f"expand-{uuid.uuid4()}"
    base._ensure_private_dir(tx_dir)

    candidate_reconciler = (repo_root / "scripts/lambda_ci_v3_reconciler.py").read_bytes()
    manifest_raw = BASE_MANIFEST.read_bytes()
    manifest = _load(BASE_MANIFEST)
    reconciler_override = base._new_reconciler_override(
        source_head=expected_head,
        base_manifest=manifest,
        base_manifest_raw=manifest_raw,
        candidate_raw=candidate_reconciler,
    )

    mutation_paths = [
        *sorted(artifacts, key=str),
        RECONCILER_INSTALLED,
        RECONCILER_OVERRIDE,
        ACTIVE_RECEIPT,
    ]
    backups = base._backup_paths(tx_dir, mutation_paths)
    tx_path = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_DUAL_LANE_EXPANSION",
        "phase": "PREPARED",
        "source_head": expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": _sha(authority_raw),
        "existing_controller_snapshot": before,
        "backups": backups,
    }
    base._atomic_json(tx_path, tx)
    _consume_authority(authority, authority_raw)

    provisioner_stopped = False
    try:
        systemd.stop(PROVISIONER_UNIT)
        provisioner_stopped = True
        base._require_quiescent(systemd)

        for path, (raw, mode) in artifacts.items():
            base._atomic_file(path, raw, mode)
        base._atomic_file(RECONCILER_INSTALLED, candidate_reconciler, 0o755)
        base._atomic_json(RECONCILER_OVERRIDE, reconciler_override)
        base._atomic_json(ACTIVE_RECEIPT, receipt)

        base._run_root_tool(["systemd-sysusers", str(SYSUSERS)])
        base._run_root_tool(["systemd-tmpfiles", "--create", str(TMPFILES)])
        base._run_root_tool(["systemctl", "daemon-reload"])

        systemd.start(PROVISIONER_UNIT)
        provisioner_stopped = False
        base._require_provisioner_active(systemd)
        base._require_provisioner_socket()
        reconciler.verify_installed(BASE_MANIFEST)

        after = base._controller_snapshot(systemd, existing_ids)
        base._require_controller_snapshot_preserved(before, after)

        tx["phase"] = "COMMITTED_INSTALLED_INACTIVE"
        tx["active_receipt_sha256"] = _sha_file(ACTIVE_RECEIPT)
        tx["existing_controller_snapshot_after"] = after
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        return tx_path
    except BaseException as exc:
        try:
            if not provisioner_stopped:
                systemd.stop(PROVISIONER_UNIT)
            base._restore_paths(backups)
            base._run_root_tool(["systemctl", "daemon-reload"])
            systemd.start(PROVISIONER_UNIT)
            reconciler.verify_installed(BASE_MANIFEST)
            tx["phase"] = "ROLLED_BACK"
            tx["rollback_completed"] = True
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        raise


def activate(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    authority_path: pathlib.Path,
    preflight_path: pathlib.Path,
    systemd: Any | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise DualLaneActivationError("dual-lane activation requires root")
    repo_root = _exact_repo(repo_root, expected_head)
    systemd = systemd or base.RealSystemd()

    reconciler.verify_installed(BASE_MANIFEST)
    base._require_provisioner_active(systemd)
    base._require_provisioner_socket()
    base._require_quiescent(systemd)

    inactive_raw = ACTIVE_RECEIPT.read_bytes()
    inactive = _load(ACTIVE_RECEIPT)
    if inactive.get("phase") != "INSTALLED_INACTIVE":
        raise DualLaneActivationError("lane B is not installed inactive")
    if inactive.get("source_head") != expected_head:
        raise DualLaneActivationError("lane B source head mismatch")

    preflight, preflight_raw = _validate_preflight(preflight_path)
    expected_authority = {
        "source_head": expected_head,
        "dual_lane_active_receipt_sha256": _sha(inactive_raw),
        "preflight_confirmation_sha256": _sha(preflight_raw),
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "target_scale_set_name": TARGET_SCALE_SET,
        "trusted_workflow_blob_sha": WORKFLOW_BLOB,
        "padataset_main_sha": preflight["padataset_main_sha"],
    }
    authority, authority_raw = _load_authority(
        authority_path,
        operation="ACTIVATE_PADATASET_SCIENTIFIC_DUAL_LANE_V1",
        expected=expected_authority,
    )

    target_before = systemd.show(TARGET_UNIT)
    if target_before.get("ActiveState") in {"active", "activating", "reloading"}:
        raise DualLaneActivationError("lane B controller already active")
    if target_before.get("UnitFileState") == "enabled":
        raise DualLaneActivationError("lane B controller already enabled")

    root = _load(ROOT_POLICY)
    existing_ids = sorted(set(root["runner_classes"]) - {TARGET_CLASS})
    existing_before = base._controller_snapshot(systemd, existing_ids)

    overlay = _load(DEPLOYMENT_OVERLAY)
    state = overlay.get("classes", {}).get(TARGET_CLASS)
    route = overlay.get("routes", {}).get(TARGET_ROUTE)
    if (
        not isinstance(state, dict)
        or state.get("install_state") != "INSTALLED"
        or state.get("controller_state") != "INACTIVE"
        or not isinstance(route, dict)
        or route.get("admission_state") != "DISABLED"
    ):
        raise DualLaneActivationError("lane B inactive overlay precondition failed")

    active_overlay = copy.deepcopy(overlay)
    active_overlay["classes"][TARGET_CLASS]["controller_state"] = "ACTIVE"
    active_overlay["routes"][TARGET_ROUTE]["admission_state"] = "ENABLED"
    active_overlay["routes"][TARGET_ROUTE]["source"] = (
        "PADataset scientific dual-lane activation accepted"
    )
    active_overlay_raw = base._canonical(active_overlay)

    active_receipt = copy.deepcopy(inactive)
    active_receipt["phase"] = "ACTIVE"
    active_receipt["managed_artifact_overrides"][str(DEPLOYMENT_OVERLAY)][
        "sha256"
    ] = _sha(active_overlay_raw)
    active_receipt["activation_authorization_id"] = authority["authorization_id"]
    active_receipt["activation_preflight_sha256"] = _sha(preflight_raw)
    active_receipt["scale_set_id"] = preflight["scale_set_id"]
    active_receipt["padataset_main_sha"] = preflight["padataset_main_sha"]

    base._ensure_private_dir(TX_ROOT)
    tx_dir = TX_ROOT / f"activate-{uuid.uuid4()}"
    base._ensure_private_dir(tx_dir)
    backups = base._backup_paths(tx_dir, [DEPLOYMENT_OVERLAY, ACTIVE_RECEIPT])
    tx_path = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_DUAL_LANE_ACTIVATION",
        "phase": "PREPARED",
        "source_head": expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": _sha(authority_raw),
        "preflight_confirmation_sha256": _sha(preflight_raw),
        "existing_controller_snapshot": existing_before,
        "backups": backups,
    }
    base._atomic_json(tx_path, tx)
    _consume_authority(authority, authority_raw)

    started = False
    enabled = False
    try:
        base._atomic_file(DEPLOYMENT_OVERLAY, active_overlay_raw, 0o644)
        base._atomic_json(ACTIVE_RECEIPT, active_receipt)
        reconciler.verify_installed(BASE_MANIFEST)

        systemd.start(TARGET_UNIT)
        started = True
        state_now = systemd.show(TARGET_UNIT)
        if (
            state_now.get("ActiveState") != "active"
            or state_now.get("SubState") != "running"
        ):
            raise DualLaneActivationError("lane B controller failed to start")
        systemd.enable(TARGET_UNIT)
        enabled = True

        base._require_provisioner_active(systemd)
        base._require_provisioner_socket()
        existing_after = base._controller_snapshot(systemd, existing_ids)
        base._require_controller_snapshot_preserved(existing_before, existing_after)
        reconciler.verify_installed(BASE_MANIFEST)

        tx["phase"] = "COMMITTED_ACTIVE"
        tx["active_receipt_sha256"] = _sha_file(ACTIVE_RECEIPT)
        tx["target_controller_state"] = systemd.show(TARGET_UNIT)
        tx["existing_controller_snapshot_after"] = existing_after
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        return tx_path
    except BaseException as exc:
        if enabled:
            systemd.disable(TARGET_UNIT)
        if started:
            try:
                systemd.stop(TARGET_UNIT)
            except BaseException:
                pass
        try:
            base._restore_paths(backups)
            reconciler.verify_installed(BASE_MANIFEST)
            tx["phase"] = "ROLLED_BACK_TO_INSTALLED_INACTIVE"
            tx["rollback_completed"] = True
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--expand-inactive", action="store_true")
    mode.add_argument("--activate", action="store_true")
    parser.add_argument("--preflight-confirmation", type=pathlib.Path)
    args = parser.parse_args()

    if args.expand_inactive:
        if args.preflight_confirmation is not None:
            raise DualLaneActivationError(
                "--preflight-confirmation is only valid with --activate"
            )
        receipt = expand_inactive(
            repo_root=args.repo_root,
            expected_head=args.expected_head,
            authority_path=args.authorization_receipt,
        )
        print("PADATASET_SCIENTIFIC_DUAL_LANE_EXPAND_INACTIVE=PASS")
        print(f"TRANSACTION_RECEIPT={receipt}")
        return 0

    if args.preflight_confirmation is None:
        raise DualLaneActivationError("--activate requires --preflight-confirmation")
    receipt = activate(
        repo_root=args.repo_root,
        expected_head=args.expected_head,
        authority_path=args.authorization_receipt,
        preflight_path=args.preflight_confirmation,
    )
    print("PADATASET_SCIENTIFIC_DUAL_LANE_ACTIVATE=PASS")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DualLaneActivationError, base.ScientificActivationError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
