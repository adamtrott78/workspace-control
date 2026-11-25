#!/usr/bin/env python3
"""Transactional live refresh for PADataset scientific runtime ceilings.

This helper changes only the two already-active PADataset scientific root
resource envelopes from 4h/14400s to 390min/23400s. It requires a quiescent
provisioner, exact source provenance, exact predecessor receipts, and a
root-owned one-shot operator authorization. It never changes workflow, model,
data, GPU, controller-policy, or admission semantics.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
import pathlib
import re
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
RECONCILER_INSTALLED = reconciler.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = reconciler.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
DUAL_ACTIVE = reconciler.PADATASET_SCIENTIFIC_DUAL_ACTIVE_RECEIPT
LANEA_WORKFLOW_ACTIVE = reconciler.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT
LANEB_WORKFLOW_ACTIVE = reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_ACTIVE_RECEIPT
ACTIVE_RECEIPT = reconciler.PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH_ACTIVE_RECEIPT

STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific/runtime-ceiling-refresh-v1")
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = STATE_ROOT / "authority-consumption"
OPERATION = "REFRESH_PADATASET_SCIENTIFIC_RUNTIME_CEILING_V1"

LANE_A = reconciler.PADATASET_SCIENTIFIC_TARGET_CLASS
LANE_B = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_CLASS
TARGETS = (LANE_A, LANE_B)
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
OLD_SECONDS = reconciler.PADATASET_SCIENTIFIC_PREVIOUS_RUNTIME_SECONDS
NEW_SECONDS = reconciler.PADATASET_SCIENTIFIC_RUNTIME_SECONDS
OLD_SYSTEMD = reconciler.PADATASET_SCIENTIFIC_PREVIOUS_SYSTEMD_RUNTIME
NEW_SYSTEMD = reconciler.PADATASET_SCIENTIFIC_SYSTEMD_RUNTIME
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class RuntimeCeilingRefreshError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeCeilingRefreshError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeCeilingRefreshError(f"{path}: expected object")
    return value


def _sha(raw: bytes) -> str:
    return base._sha(raw)


def _sha_file(path: pathlib.Path) -> str:
    return base._sha_file(path)


def _target_units() -> list[str]:
    return [f"workspace-ci-v3-controller@{class_id}.service" for class_id in TARGETS]


def _normalize_target(row: dict[str, Any], *, expected_seconds: int, expected_systemd: str) -> dict[str, Any]:
    value = copy.deepcopy(row)
    value.pop("control_plane_generation_sha256", None)
    value.pop("root_envelope_sha256", None)
    resource = value.get("resource_class")
    systemd = value.get("systemd_profile")
    if not isinstance(resource, dict) or not isinstance(systemd, dict):
        raise RuntimeCeilingRefreshError("scientific resource/systemd envelope missing")
    if resource.get("max_runtime_seconds") != expected_seconds:
        raise RuntimeCeilingRefreshError("scientific resource runtime ceiling mismatch")
    if systemd.get("RuntimeMaxSec") != expected_systemd:
        raise RuntimeCeilingRefreshError("scientific systemd runtime ceiling mismatch")
    resource.pop("max_runtime_seconds", None)
    systemd.pop("RuntimeMaxSec", None)
    systemd.pop("note", None)
    return value


def _validate_delta(
    current: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    current_classes = current.get("runner_classes")
    candidate_classes = candidate.get("runner_classes")
    if not isinstance(current_classes, dict) or not isinstance(candidate_classes, dict):
        raise RuntimeCeilingRefreshError("runner class map missing")
    if set(current_classes) != set(candidate_classes):
        raise RuntimeCeilingRefreshError("runner class set drift")
    if current.get("host_resource_policy") != candidate.get("host_resource_policy"):
        raise RuntimeCeilingRefreshError("host resource policy drift")
    if current.get("upstream_pins") != candidate.get("upstream_pins"):
        raise RuntimeCeilingRefreshError("upstream pin drift")

    previous: dict[str, str] = {}
    updated: dict[str, str] = {}
    changed: set[str] = set()
    for class_id in sorted(current_classes):
        old = current_classes[class_id]
        new = candidate_classes[class_id]
        old_digest = old.get("root_envelope_sha256")
        new_digest = new.get("root_envelope_sha256")
        if (
            not isinstance(old_digest, str)
            or SHA64.fullmatch(old_digest) is None
            or not isinstance(new_digest, str)
            or SHA64.fullmatch(new_digest) is None
        ):
            raise RuntimeCeilingRefreshError(f"invalid root envelope: {class_id}")
        previous[class_id] = old_digest
        updated[class_id] = new_digest

        if class_id in TARGETS:
            old_norm = _normalize_target(
                old,
                expected_seconds=OLD_SECONDS,
                expected_systemd=OLD_SYSTEMD,
            )
            new_norm = _normalize_target(
                new,
                expected_seconds=NEW_SECONDS,
                expected_systemd=NEW_SYSTEMD,
            )
            if old_norm != new_norm:
                raise RuntimeCeilingRefreshError(
                    f"scientific candidate changed more than runtime ceiling: {class_id}"
                )
            if old_digest == new_digest:
                raise RuntimeCeilingRefreshError(
                    f"scientific runtime ceiling did not change envelope: {class_id}"
                )
            changed.add(class_id)
        else:
            old_norm = copy.deepcopy(old)
            new_norm = copy.deepcopy(new)
            old_norm.pop("control_plane_generation_sha256", None)
            new_norm.pop("control_plane_generation_sha256", None)
            if old_norm != new_norm:
                raise RuntimeCeilingRefreshError(
                    f"candidate changed unrelated runner class: {class_id}"
                )
            if old_digest != new_digest:
                raise RuntimeCeilingRefreshError(
                    f"unrelated runner envelope changed: {class_id}"
                )
    if changed != set(TARGETS):
        raise RuntimeCeilingRefreshError("runtime ceiling target set mismatch")
    return previous, updated


def _validate_executor(current: dict[str, Any], candidate: dict[str, Any]) -> None:
    for key in ("execution_actions", "maintenance_actions", "executor_policy_sha256"):
        if current.get(key) != candidate.get(key):
            raise RuntimeCeilingRefreshError(f"executor semantics drift: {key}")


def _validate_compatibility(
    current: list[Any],
    candidate: list[Any],
    envelope_map: dict[str, str],
) -> None:
    def keyed(rows: list[Any]) -> dict[tuple[str, str], dict[str, Any]]:
        out: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeCeilingRefreshError("compatibility row invalid")
            key = (str(row.get("project_id")), str(row.get("route_id")))
            out[key] = copy.deepcopy(row)
        return out

    old = keyed(current)
    new = keyed(candidate)
    if set(old) != set(new):
        raise RuntimeCeilingRefreshError("compatibility route set drift")
    for key in old:
        a = old[key]
        b = new[key]
        class_id = str(a.get("target_runner_class_id"))
        if class_id != str(b.get("target_runner_class_id")):
            raise RuntimeCeilingRefreshError("compatibility target class drift")
        if class_id in TARGETS:
            if b.get("root_envelope_sha256") != envelope_map[class_id]:
                raise RuntimeCeilingRefreshError("compatibility target envelope mismatch")
            a.pop("root_envelope_sha256", None)
            b.pop("root_envelope_sha256", None)
        if a != b:
            raise RuntimeCeilingRefreshError(f"compatibility semantic drift: {key}")


def _prepare(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    systemd: Any,
) -> dict[str, Any]:
    try:
        repo_root = base._exact_repo(repo_root, expected_head)
        reconciler.verify_installed(BASE_MANIFEST)
        base._require_provisioner_active(systemd)
        base._require_provisioner_socket()
        base._require_quiescent(systemd)
    except (base.ScientificActivationError, reconciler.ReconcileError) as exc:
        raise RuntimeCeilingRefreshError(str(exc)) from exc

    if ACTIVE_RECEIPT.exists():
        raise RuntimeCeilingRefreshError("runtime ceiling refresh is already active")
    for path, label in (
        (DUAL_ACTIVE, "dual-lane active receipt"),
        (LANEA_WORKFLOW_ACTIVE, "lane-A timeout360 refresh receipt"),
        (LANEB_WORKFLOW_ACTIVE, "lane-B timeout360 refresh receipt"),
    ):
        if not path.is_file():
            raise RuntimeCeilingRefreshError(f"{label} missing")

    dual_raw = DUAL_ACTIVE.read_bytes()
    lane_a_raw = LANEA_WORKFLOW_ACTIVE.read_bytes()
    lane_b_raw = LANEB_WORKFLOW_ACTIVE.read_bytes()
    dual = _load(DUAL_ACTIVE)
    if dual.get("phase") != "ACTIVE":
        raise RuntimeCeilingRefreshError("dual-lane predecessor is not ACTIVE")

    current_root = _load(ROOT_POLICY)
    if current_root.get("root_policy_sha256") != dual.get("root_policy_sha256"):
        raise RuntimeCeilingRefreshError("live root/dual receipt provenance mismatch")
    current_executor = _load(EXECUTOR_ACTIONS)
    current_compatibility = json.loads(COMPATIBILITY_MATRIX.read_text(encoding="utf-8"))
    current_overlay = _load(DEPLOYMENT_OVERLAY)

    compiled = compiler.compile_policy(repo_root)
    candidate_root = compiled["root_projection"]
    previous_envelopes, candidate_envelopes = _validate_delta(
        current_root,
        candidate_root,
    )
    _validate_executor(current_executor, compiled["executor_projection"])
    if not isinstance(current_compatibility, list):
        raise RuntimeCeilingRefreshError("live compatibility matrix is not a list")
    _validate_compatibility(
        current_compatibility,
        compiled["compatibility_matrix"],
        candidate_envelopes,
    )

    overlay = copy.deepcopy(current_overlay)
    overlay["catalog_generation_sha256"] = compiled["catalog_generation_sha256"]
    artifacts = {
        ROOT_POLICY: (base._canonical(candidate_root), 0o644),
        EXECUTOR_ACTIONS: (base._canonical(compiled["executor_projection"]), 0o644),
        COMPATIBILITY_MATRIX: (base._canonical(compiled["compatibility_matrix"]), 0o644),
        DEPLOYMENT_OVERLAY: (base._canonical(overlay), 0o644),
    }

    predecessor = dual.get("managed_artifact_overrides")
    if not isinstance(predecessor, dict):
        raise RuntimeCeilingRefreshError("dual-lane managed override map missing")
    overrides: dict[str, dict[str, str]] = {}
    for path, (raw, mode) in artifacts.items():
        destination = str(path)
        binding = predecessor.get(destination)
        if not isinstance(binding, dict):
            raise RuntimeCeilingRefreshError(
                f"dual-lane predecessor does not manage {destination}"
            )
        actual = _sha_file(path)
        if binding.get("sha256") != actual:
            raise RuntimeCeilingRefreshError(
                f"live predecessor digest drift: {destination}"
            )
        if binding.get("mode") != f"{mode:04o}":
            raise RuntimeCeilingRefreshError(
                f"live predecessor mode drift: {destination}"
            )
        overrides[destination] = {
            "prior_sha256": actual,
            "sha256": _sha(raw),
            "mode": f"{mode:04o}",
        }

    receipt = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH",
        "phase": "ACTIVE",
        "source_head": expected_head,
        "dual_active_receipt_sha256": _sha(dual_raw),
        "lane_a_workflow_refresh_receipt_sha256": _sha(lane_a_raw),
        "lane_b_workflow_refresh_receipt_sha256": _sha(lane_b_raw),
        "lane_a_class_id": LANE_A,
        "lane_b_class_id": LANE_B,
        "previous_root_policy_sha256": current_root["root_policy_sha256"],
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "root_policy_sha256": candidate_root["root_policy_sha256"],
        "previous_root_envelope_sha256": previous_envelopes,
        "root_envelope_sha256": candidate_envelopes,
        "previous_runtime_max_seconds": OLD_SECONDS,
        "runtime_max_seconds": NEW_SECONDS,
        "previous_systemd_runtime": OLD_SYSTEMD,
        "systemd_runtime": NEW_SYSTEMD,
        "managed_artifact_overrides": overrides,
    }

    expected_authority = {
        "source_head": expected_head,
        "dual_active_receipt_sha256": receipt["dual_active_receipt_sha256"],
        "lane_a_workflow_refresh_receipt_sha256": receipt[
            "lane_a_workflow_refresh_receipt_sha256"
        ],
        "lane_b_workflow_refresh_receipt_sha256": receipt[
            "lane_b_workflow_refresh_receipt_sha256"
        ],
        "current_root_policy_sha256": receipt["previous_root_policy_sha256"],
        "candidate_root_policy_sha256": receipt["root_policy_sha256"],
        "previous_runtime_max_seconds": OLD_SECONDS,
        "runtime_max_seconds": NEW_SECONDS,
    }
    return {
        "repo_root": repo_root,
        "compiled": compiled,
        "artifacts": artifacts,
        "receipt": receipt,
        "expected_authority": expected_authority,
        "current_root": current_root,
    }


def _consume_authority(value: dict[str, Any], raw: bytes) -> None:
    base._ensure_private_dir(AUTHORITY_ROOT)
    marker = AUTHORITY_ROOT / f"{value['authorization_id']}.json"
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(
            base._canonical(
                {
                    "schema_version": 1,
                    "authorization_id": value["authorization_id"],
                    "operation": value["operation"],
                    "authority_sha256": _sha(raw),
                    "consumed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(marker, 0, 0)


def refresh(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    authority_path: pathlib.Path,
    systemd: Any | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise RuntimeCeilingRefreshError("runtime ceiling refresh requires root")
    systemd = systemd or base.RealSystemd()
    prepared = _prepare(
        repo_root=repo_root,
        expected_head=expected_head,
        systemd=systemd,
    )
    try:
        authority, authority_raw = base._load_authority(
            authority_path,
            operation=OPERATION,
            expected=prepared["expected_authority"],
        )
    except base.ScientificActivationError as exc:
        raise RuntimeCeilingRefreshError(str(exc)) from exc

    live_root = prepared["current_root"]
    class_ids = sorted(live_root["runner_classes"])
    target_units = _target_units()
    non_target = [x for x in class_ids if x not in TARGETS]
    target_before = {
        unit: systemd.show(unit)
        for unit in target_units
    }
    for unit, state in target_before.items():
        if state.get("ActiveState") != "active" or state.get("SubState") != "running":
            raise RuntimeCeilingRefreshError(f"scientific controller is not active: {unit}")
    non_target_before = base._controller_snapshot(systemd, non_target)

    manifest_raw = BASE_MANIFEST.read_bytes()
    manifest = _load(BASE_MANIFEST)
    candidate_reconciler = (
        prepared["repo_root"] / "scripts/lambda_ci_v3_reconciler.py"
    ).read_bytes()
    reconciler_override = base._new_reconciler_override(
        source_head=expected_head,
        base_manifest=manifest,
        base_manifest_raw=manifest_raw,
        candidate_raw=candidate_reconciler,
    )

    base._ensure_private_dir(STATE_ROOT)
    base._ensure_private_dir(TX_ROOT)
    base._ensure_private_dir(AUTHORITY_ROOT)
    tx_dir = TX_ROOT / f"refresh-{uuid.uuid4()}"
    base._ensure_private_dir(tx_dir)
    mutation_paths = [
        *sorted(prepared["artifacts"], key=str),
        RECONCILER_INSTALLED,
        RECONCILER_OVERRIDE,
        ACTIVE_RECEIPT,
    ]
    backups = base._backup_paths(tx_dir, mutation_paths)
    tx_path = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH_TRANSACTION",
        "phase": "PREPARED",
        "source_head": expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": _sha(authority_raw),
        "previous_root_policy_sha256": prepared["receipt"][
            "previous_root_policy_sha256"
        ],
        "candidate_root_policy_sha256": prepared["receipt"]["root_policy_sha256"],
        "target_controller_snapshot_before": target_before,
        "non_target_controller_snapshot_before": non_target_before,
        "backups": backups,
    }
    base._atomic_json(tx_path, tx)
    _consume_authority(authority, authority_raw)

    stopped_targets: list[str] = []
    provisioner_stopped = False
    try:
        # Stop admission sources first, then re-prove zero work before swapping root policy.
        for unit in target_units:
            systemd.stop(unit)
            stopped_targets.append(unit)
        base._require_quiescent(systemd)
        systemd.stop(PROVISIONER_UNIT)
        provisioner_stopped = True
        base._require_quiescent(systemd)

        for path, (raw, mode) in prepared["artifacts"].items():
            base._atomic_file(path, raw, mode)
        base._atomic_file(RECONCILER_INSTALLED, candidate_reconciler, 0o755)
        base._atomic_json(RECONCILER_OVERRIDE, reconciler_override)
        base._atomic_json(ACTIVE_RECEIPT, prepared["receipt"])

        systemd.start(PROVISIONER_UNIT)
        provisioner_stopped = False
        base._require_provisioner_active(systemd)
        base._require_provisioner_socket()
        for unit in target_units:
            systemd.start(unit)
        stopped_targets.clear()

        for unit in target_units:
            state = systemd.show(unit)
            if state.get("ActiveState") != "active" or state.get("SubState") != "running":
                raise RuntimeCeilingRefreshError(
                    f"scientific controller failed to restart: {unit}"
                )

        non_target_after = base._controller_snapshot(systemd, non_target)
        base._require_controller_snapshot_preserved(
            non_target_before,
            non_target_after,
        )
        reconciler.verify_installed(BASE_MANIFEST)

        live_after = _load(ROOT_POLICY)
        for class_id in TARGETS:
            row = live_after["runner_classes"][class_id]
            if row["resource_class"]["max_runtime_seconds"] != NEW_SECONDS:
                raise RuntimeCeilingRefreshError(
                    f"live resource runtime ceiling did not update: {class_id}"
                )
            if row["systemd_profile"]["RuntimeMaxSec"] != NEW_SYSTEMD:
                raise RuntimeCeilingRefreshError(
                    f"live systemd runtime ceiling did not update: {class_id}"
                )

        tx["phase"] = "COMMITTED_ACTIVE"
        tx["non_target_controller_snapshot_after"] = non_target_after
        tx["runtime_ceiling_receipt_sha256"] = _sha_file(ACTIVE_RECEIPT)
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        return tx_path
    except BaseException as exc:
        try:
            if not provisioner_stopped:
                systemd.stop(PROVISIONER_UNIT)
            for unit in target_units:
                try:
                    systemd.stop(unit)
                except BaseException:
                    pass
            base._restore_paths(backups)
            systemd.start(PROVISIONER_UNIT)
            for unit in target_units:
                systemd.start(unit)
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path)
    parser.add_argument("--print-authority-bindings", action="store_true")
    args = parser.parse_args()

    systemd = base.RealSystemd()
    if args.print_authority_bindings:
        if args.authorization_receipt is not None:
            raise RuntimeCeilingRefreshError(
                "--authorization-receipt is invalid with --print-authority-bindings"
            )
        prepared = _prepare(
            repo_root=args.repo_root,
            expected_head=args.expected_head,
            systemd=systemd,
        )
        print(json.dumps(prepared["expected_authority"], indent=2, sort_keys=True))
        return 0
    if args.authorization_receipt is None:
        raise RuntimeCeilingRefreshError("--authorization-receipt is required")

    receipt = refresh(
        repo_root=args.repo_root,
        expected_head=args.expected_head,
        authority_path=args.authorization_receipt,
        systemd=systemd,
    )
    print("PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH=PASS")
    print(f"VALIDATED_HEAD={args.expected_head}")
    print(f"RUNTIME_MAX_SECONDS={NEW_SECONDS}")
    print(f"SYSTEMD_RUNTIME={NEW_SYSTEMD}")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeCeilingRefreshError as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        raise SystemExit(2)
