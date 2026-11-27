#!/usr/bin/env python3
"""Activate only the Workspace Control Codex bootstrap route on control-small."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import tempfile
import uuid
from typing import Any

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_reconciler as candidate

BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
OVERLAY = pathlib.Path("/etc/workspace-ci/v3/deployment-overlay.json")
TARGET_CLASS = candidate.WORKSPACE_CONTROL_CODEX_TARGET_CLASS
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_POLICY = pathlib.Path(candidate.WORKSPACE_CONTROL_CODEX_CONTROLLER_DESTINATION)
ACTIVE_ROUTE_RECEIPT = candidate.WORKSPACE_CONTROL_CODEX_ROUTE_ACTIVE_RECEIPT
INSTALLED_RECONCILER = candidate.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = candidate.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
PRODUCTION_ACTIVE = candidate.PRODUCTION_CUTOVER_ACTIVE_RECEIPT
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
PROVISIONER_STATE = pathlib.Path("/var/lib/workspace-ci/v3/provisioner")
TARGET_LEDGER = pathlib.Path("/var/lib/workspace-ci/v3/controller/state") / TARGET_CLASS
STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/workspace-control/codex-bootstrap-route")
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = STATE_ROOT / "authority-consumption"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
AUTHORITY_MAX_SECONDS = 30 * 60
ACTIVE_RECORD_STATES = {"RESERVED", "PREPARING", "ACCEPTED", "RUNNING"}


class RouteActivationError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RouteActivationError(f"{path}: expected JSON object")
    return value, raw


def parse_time(raw: Any, label: str) -> datetime:
    if not isinstance(raw, str):
        raise RouteActivationError(f"{label} missing")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RouteActivationError(f"{label} invalid") from exc
    if value.tzinfo is None:
        raise RouteActivationError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def require_root_private(path: pathlib.Path) -> bytes:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_gid != 0:
        raise RouteActivationError(f"root-private file metadata invalid: {path}")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise RouteActivationError(f"root-private file mode invalid: {path}")
    return path.read_bytes()


def exact_repo(repo: pathlib.Path, expected: str) -> pathlib.Path:
    if SHA40.fullmatch(expected) is None:
        raise RouteActivationError("expected source head invalid")
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if head != expected:
        raise RouteActivationError(f"source head mismatch: {head} != {expected}")
    dirty = subprocess.check_output(
        [
            "git", "-C", str(repo), "status", "--porcelain=v1",
            "--untracked-files=normal",
        ],
        text=True,
    )
    if dirty.strip():
        raise RouteActivationError("source checkout is dirty")
    return repo.resolve()


def systemd(unit: str) -> dict[str, str]:
    proc = subprocess.run(
        [
            "systemctl", "show", unit,
            "-p", "LoadState",
            "-p", "ActiveState",
            "-p", "SubState",
            "-p", "MainPID",
            "-p", "NRestarts",
            "-p", "InvocationID",
            "-p", "UnitFileState",
            "--no-pager",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RouteActivationError(
            f"systemctl show failed: {unit}: {proc.stderr.strip()[:512]}"
        )
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out


def run_systemctl(*args: str) -> None:
    proc = subprocess.run(
        ["systemctl", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RouteActivationError(
            f"systemctl {' '.join(args)} failed: {proc.stderr.strip()[:512]}"
        )


def require_roots() -> None:
    provisioner = systemd(PROVISIONER_UNIT)
    if (
        provisioner.get("ActiveState") != "active"
        or provisioner.get("SubState") != "running"
    ):
        raise RouteActivationError("shared provisioner is not active/running")
    reconciler = systemd(RECONCILER_UNIT)
    if (
        reconciler.get("ActiveState") != "active"
        or reconciler.get("SubState") != "exited"
        or reconciler.get("MainPID") not in {"", "0"}
    ):
        raise RouteActivationError(
            "reconciler must be active/exited with no running process"
        )


def controller_snapshots() -> dict[str, dict[str, str]]:
    root, _ = load(ROOT_POLICY)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise RouteActivationError("installed class set invalid")
    return {
        class_id: systemd(
            f"workspace-ci-v3-controller@{class_id}.service"
        )
        for class_id in sorted(classes)
        if class_id != TARGET_CLASS
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
        raise RouteActivationError("non-target controller set changed")
    for class_id in before:
        for field in fields:
            if before[class_id].get(field) != after[class_id].get(field):
                raise RouteActivationError(
                    f"non-target controller changed: {class_id} {field}"
                )


def require_target_quiescent() -> None:
    if TARGET_LEDGER.exists():
        for path in sorted(TARGET_LEDGER.glob("scheduler-*.json")):
            value = json.loads(path.read_text())
            if value.get("state") not in {"COMPLETED", "FAILED", "CANCELED"}:
                raise RouteActivationError(
                    f"target controller has nonterminal ledger record: {path.name}"
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
                raise RouteActivationError(
                    f"target provisioner record still holds capacity: {path.name}"
                )
    proc = subprocess.run(
        [
            "systemctl", "list-units", "--all", "--type=service",
            "--plain", "--no-legend", "--no-pager",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RouteActivationError("failed to enumerate transient units")
    prefix = f"workspace-ci-v3-{TARGET_CLASS}-"
    for line in proc.stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        unit = fields[0]
        if not unit.startswith(prefix):
            continue
        state = systemd(unit)
        if state.get("ActiveState") in {"active", "activating", "reloading"}:
            raise RouteActivationError(f"target transient still active: {unit}")


def ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, 0, 0)
    os.chmod(path, 0o700)


def atomic_file(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = pathlib.Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.replace(tmp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    atomic_file(path, canonical(value), 0o600)


def current_reconciler_override(
    manifest: dict[str, Any],
    manifest_raw: bytes,
    actual_sha: str,
) -> tuple[dict[str, Any], bytes]:
    value, raw = load(RECONCILER_OVERRIDE)
    entries = {str(entry["destination"]): entry for entry in manifest["entries"]}
    entry = entries[str(INSTALLED_RECONCILER)]
    required = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha(manifest_raw),
        "base_reconciler_sha256": entry.get("sha256"),
        "reconciler_sha256": actual_sha,
        "reconciler_mode": str(entry.get("mode")),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            raise RouteActivationError(
                f"current reconciler override mismatch: {key}"
            )
    return value, raw


def _controller_policy_digest(policy: dict[str, Any]) -> str:
    return compiler.sha256_object(
        {
            key: value
            for key, value in policy.items()
            if key
            not in {
                "control_plane_generation_sha256",
                "controller_policy_sha256",
            }
        }
    )


def build_candidate_policy(
    *,
    repo: pathlib.Path,
    installed_root: dict[str, Any],
    current_policy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Add only the Codex trusted workflow to the installed controller policy.

    Root authority is not reconstructed from current repository inputs here.
    The reconciler has already attested the complete installed effective
    generation, including scientific/runtime390 successors. This transaction
    does not write root-policy.json, so the route candidate is built from the
    installed control-small controller policy and changes only its trusted
    workflow set plus the derived controller-policy digest.
    """
    classes = installed_root.get("runner_classes")
    if not isinstance(classes, dict):
        raise RouteActivationError("installed root runner classes missing")
    target_root = classes.get(TARGET_CLASS)
    if not isinstance(target_root, dict):
        raise RouteActivationError(
            "installed Workspace Control control-small root class missing"
        )

    root_bindings = {
        "runner_class_id": TARGET_CLASS,
        "project_id": "workspace-control",
        "repository": "adamtrott78/workspace-control",
        "scale_set_name": candidate.WORKSPACE_CONTROL_CODEX_TARGET_SCALE_SET,
        "max_runners": 1,
        "project_max_active_runners": 1,
    }
    for key, expected in root_bindings.items():
        if target_root.get(key) != expected:
            raise RouteActivationError(
                f"installed control-small root binding drift: {key}"
            )
    if target_root.get("exclusive_resource_claims") != []:
        raise RouteActivationError(
            "installed control-small unexpectedly owns exclusive resources"
        )

    policy_root_bindings = {
        "runner_class_id": target_root["runner_class_id"],
        "repository": target_root["repository"],
        "scale_set_name": target_root["scale_set_name"],
        "runner_prefix": target_root["runner_prefix"],
        "max_runners": target_root["max_runners"],
    }
    for key, expected in policy_root_bindings.items():
        if current_policy.get(key) != expected:
            raise RouteActivationError(
                f"installed control-small controller/root mismatch: {key}"
            )

    current_workflows = current_policy.get("trusted_workflows")
    if not isinstance(current_workflows, list) or len(current_workflows) != 1:
        raise RouteActivationError(
            "current Workspace Control workflow predecessor invalid"
        )
    current = current_workflows[0]
    if (
        not isinstance(current, dict)
        or current.get("route_id") != "control-validation"
        or current.get("path")
        != candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_PATH
        or current.get("blob_sha")
        != candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_BLOB
    ):
        raise RouteActivationError(
            "current Workspace Control workflow binding drift"
        )

    compiled = compiler.compile_policy(repo)
    compiled_policy = compiled["controller_projections"].get(TARGET_CLASS)
    if not isinstance(compiled_policy, dict):
        raise RouteActivationError(
            "compiled Workspace Control control-small policy missing"
        )
    for key in (
        "schema_version",
        "runner_class_id",
        "repository",
        "scale_set_name",
        "runner_prefix",
        "max_runners",
    ):
        if compiled_policy.get(key) != current_policy.get(key):
            raise RouteActivationError(
                f"compiled Codex route changed controller structure: {key}"
            )

    compiled_workflows = compiled_policy.get("trusted_workflows")
    if not isinstance(compiled_workflows, list) or len(compiled_workflows) != 2:
        raise RouteActivationError(
            "compiled Codex route workflow set invalid"
        )
    by_route = {
        row.get("route_id"): row
        for row in compiled_workflows
        if isinstance(row, dict)
    }
    if set(by_route) != {"control-validation", "codex-bootstrap"}:
        raise RouteActivationError(
            "compiled Codex route workflow identities invalid"
        )
    if by_route["control-validation"] != current:
        raise RouteActivationError(
            "compiled Codex route changed control-validation binding"
        )
    codex = by_route["codex-bootstrap"]
    if (
        codex.get("path") != candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_PATH
        or codex.get("blob_sha")
        != candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB
    ):
        raise RouteActivationError(
            "Codex bootstrap trusted-workflow binding invalid"
        )

    refreshed = copy.deepcopy(current_policy)
    refreshed["trusted_workflows"] = [
        copy.deepcopy(by_route[route_id])
        for route_id in sorted(by_route)
    ]
    # Preserve the installed control-plane generation. Only the trusted
    # workflow set and its derived controller-policy digest change.
    refreshed["controller_policy_sha256"] = _controller_policy_digest(
        refreshed
    )

    changed_keys = {
        key
        for key in set(current_policy) | set(refreshed)
        if current_policy.get(key) != refreshed.get(key)
    }
    if changed_keys != {"trusted_workflows", "controller_policy_sha256"}:
        raise RouteActivationError(
            "Codex bootstrap candidate changed non-controller-local fields"
        )
    return refreshed, installed_root

def build_overlay(current: dict[str, Any]) -> dict[str, Any]:
    refreshed = copy.deepcopy(current)
    classes = refreshed.get("classes")
    routes = refreshed.get("routes")
    if not isinstance(classes, dict) or not isinstance(routes, dict):
        raise RouteActivationError("installed overlay shape invalid")
    target = classes.get(TARGET_CLASS)
    if not isinstance(target, dict):
        raise RouteActivationError("target class absent from overlay")
    if target.get("controller_state") != "ACTIVE":
        raise RouteActivationError("target controller overlay is not ACTIVE")
    validation = routes.get("workspace-control:control-validation")
    if (
        not isinstance(validation, dict)
        or validation.get("admission_state") != "ENABLED"
    ):
        raise RouteActivationError(
            "control-validation route predecessor is not ENABLED"
        )
    existing = routes.get(candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE)
    if existing is not None and existing.get("admission_state") == "ENABLED":
        raise RouteActivationError("Codex bootstrap route is already enabled")
    refreshed["routes"][candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE] = {
        "admission_state": "ENABLED",
        "source": (
            "root-attested Workspace Control Codex bootstrap route activation"
        ),
    }
    return refreshed


def validate_authority(
    path: pathlib.Path,
    expected: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    raw = require_root_private(path)
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
        raise RouteActivationError("authority keys drift")
    if (
        value["schema_version"] != 1
        or value["authority"] != "workspace-control-operator"
        or value["operation"]
        != "ACTIVATE_WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_V1"
    ):
        raise RouteActivationError("authority identity invalid")
    auth_id = value["authorization_id"]
    if (
        not isinstance(auth_id, str)
        or UUID_RE.fullmatch(auth_id) is None
        or str(uuid.UUID(auth_id)) != auth_id
    ):
        raise RouteActivationError("authorization id invalid")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise RouteActivationError(
                f"authority binding mismatch: {key}"
            )
    issued = parse_time(value["issued_at"], "issued_at")
    expires = parse_time(value["expires_at"], "expires_at")
    now = datetime.now(timezone.utc)
    if (
        not (issued <= now <= expires)
        or (expires - issued).total_seconds() > AUTHORITY_MAX_SECONDS
    ):
        raise RouteActivationError("authority validity window invalid")
    return value, raw


def consume_authority(value: dict[str, Any], raw: bytes) -> pathlib.Path:
    ensure_dir(AUTHORITY_ROOT)
    marker = AUTHORITY_ROOT / f"{value['authorization_id']}.json"
    record = {
        "schema_version": 1,
        "authorization_id": value["authorization_id"],
        "operation": value["operation"],
        "authority_sha256": sha(raw),
        "consumed_at": datetime.now(timezone.utc).isoformat(),
    }
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(canonical(record))
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(marker, 0, 0)
    return marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RouteActivationError("Codex route activation requires root")

    repo = exact_repo(args.repo_root, args.expected_head)
    require_roots()
    require_target_quiescent()

    # The new verifier must accept the current layered live state before mutation.
    candidate.verify_installed(BASE_MANIFEST)

    target_before = systemd(TARGET_UNIT)
    if (
        target_before.get("ActiveState") != "active"
        or target_before.get("SubState") != "running"
        or target_before.get("UnitFileState") != "enabled"
    ):
        raise RouteActivationError(
            "Workspace Control target controller is not active/running/enabled"
        )
    others_before = controller_snapshots()

    if ACTIVE_ROUTE_RECEIPT.exists():
        raise RouteActivationError("Codex bootstrap route override already exists")

    manifest, manifest_raw = load(BASE_MANIFEST)
    installed_root, _ = load(ROOT_POLICY)
    production, production_raw = load(PRODUCTION_ACTIVE)
    if (
        production.get("mode") != "V3_PRODUCTION_CUTOVER_OVERRIDE"
        or production.get("phase") != "ACTIVE"
    ):
        raise RouteActivationError("production cutover predecessor invalid")

    current_policy, current_policy_raw = load(TARGET_POLICY)
    current_overlay, current_overlay_raw = load(OVERLAY)
    production_overrides = candidate._production_cutover_overrides(
        manifest_raw,
        manifest,
    )
    production_policy_file = production_overrides.get(str(TARGET_POLICY))
    if production_policy_file != sha(current_policy_raw):
        raise RouteActivationError(
            "current Workspace Control policy is not production predecessor"
        )

    candidate_policy, _ = build_candidate_policy(
        repo=repo,
        installed_root=installed_root,
        current_policy=current_policy,
    )
    candidate_policy_raw = canonical(candidate_policy)
    candidate_overlay = build_overlay(current_overlay)
    candidate_overlay_raw = canonical(candidate_overlay)

    old_reconciler = INSTALLED_RECONCILER.read_bytes()
    old_reconciler_sha = sha(old_reconciler)
    _, old_reconciler_override_raw = current_reconciler_override(
        manifest,
        manifest_raw,
        old_reconciler_sha,
    )
    new_reconciler = (
        repo / "scripts/lambda_ci_v3_reconciler.py"
    ).read_bytes()
    new_reconciler_sha = sha(new_reconciler)
    reconciler_blob = subprocess.check_output(
        [
            "git", "-C", str(repo), "hash-object",
            "scripts/lambda_ci_v3_reconciler.py",
        ],
        text=True,
    ).strip()
    entries = {str(entry["destination"]): entry for entry in manifest["entries"]}
    reconciler_entry = entries[str(INSTALLED_RECONCILER)]
    new_reconciler_override = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha(manifest_raw),
        "base_reconciler_sha256": reconciler_entry.get("sha256"),
        "reconciler_sha256": new_reconciler_sha,
        "reconciler_mode": str(reconciler_entry.get("mode")),
        "reconciler_source_head": args.expected_head,
        "reconciler_git_blob": reconciler_blob,
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }

    expected_authority = {
        "source_head": args.expected_head,
        "base_install_manifest_sha256": sha(manifest_raw),
        "production_active_receipt_sha256": sha(production_raw),
        "root_policy_sha256": installed_root.get("root_policy_sha256"),
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "controller_policy_file_sha256": sha(candidate_policy_raw),
        "previous_overlay_file_sha256": sha(current_overlay_raw),
        "overlay_file_sha256": sha(candidate_overlay_raw),
        "previous_reconciler_sha256": old_reconciler_sha,
        "reconciler_sha256": new_reconciler_sha,
        "workflow_blob_sha": candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
        "target_class_id": TARGET_CLASS,
    }
    authority, authority_raw = validate_authority(
        args.authorization_receipt,
        expected_authority,
    )

    active_receipt = {
        "schema_version": 1,
        "mode": "V3_WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha(manifest_raw),
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "base_root_policy_sha256": manifest.get("root_policy_sha256"),
        "root_policy_sha256": installed_root.get("root_policy_sha256"),
        "target_class_id": TARGET_CLASS,
        "target_route_key": candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE,
        "target_scale_set_name":
            candidate.WORKSPACE_CONTROL_CODEX_TARGET_SCALE_SET,
        "workflow_path": candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_PATH,
        "workflow_blob_sha": candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
        "control_validation_workflow_path":
            candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_PATH,
        "control_validation_workflow_blob_sha":
            candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_BLOB,
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "previous_controller_policy_sha256":
            current_policy["controller_policy_sha256"],
        "controller_policy_sha256":
            candidate_policy["controller_policy_sha256"],
        "controller_policy_file_sha256": sha(candidate_policy_raw),
        "previous_overlay_file_sha256": sha(current_overlay_raw),
        "overlay_file_sha256": sha(candidate_overlay_raw),
    }

    ensure_dir(TX_ROOT)
    tx_id = str(uuid.uuid4())
    tx_dir = TX_ROOT / f"activation-{tx_id}"
    ensure_dir(tx_dir)
    tx_path = tx_dir / "receipt.json"
    backups = {
        "policy": current_policy_raw,
        "overlay": current_overlay_raw,
        "reconciler": old_reconciler,
        "reconciler_override": old_reconciler_override_raw,
    }
    tx = {
        "schema_version": 1,
        "mode": "V3_WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_TRANSACTION",
        "phase": "PREPARED",
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": sha(authority_raw),
        "production_active_receipt_sha256": sha(production_raw),
        "target_controller_before": target_before,
        "existing_controller_snapshot": others_before,
        "base_root_policy_sha256": manifest.get("root_policy_sha256"),
        "root_policy_sha256": installed_root.get("root_policy_sha256"),
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "controller_policy_file_sha256": sha(candidate_policy_raw),
        "previous_overlay_file_sha256": sha(current_overlay_raw),
        "overlay_file_sha256": sha(candidate_overlay_raw),
        "workflow_blob_sha": candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
    }
    atomic_json(tx_path, tx)
    consume_authority(authority, authority_raw)

    target_stopped = False
    try:
        run_systemctl("stop", TARGET_UNIT)
        target_stopped = True
        stopped = systemd(TARGET_UNIT)
        if stopped.get("ActiveState") != "inactive":
            raise RouteActivationError(
                "Workspace Control controller did not stop"
            )

        atomic_file(TARGET_POLICY, candidate_policy_raw, 0o644)
        atomic_file(OVERLAY, candidate_overlay_raw, 0o644)
        atomic_json(ACTIVE_ROUTE_RECEIPT, active_receipt)
        atomic_json(RECONCILER_OVERRIDE, new_reconciler_override)
        atomic_file(
            INSTALLED_RECONCILER,
            new_reconciler,
            int(str(reconciler_entry.get("mode")), 8),
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
            raise RouteActivationError(
                "installed reconciler verification failed: "
                + proc.stderr.strip()[:1024]
            )

        tx["phase"] = "POLICY_INSTALLED_CONTROLLER_STOPPED"
        atomic_json(tx_path, tx)

        run_systemctl("start", TARGET_UNIT)
        target_stopped = False
        target_after = systemd(TARGET_UNIT)
        if (
            target_after.get("ActiveState") != "active"
            or target_after.get("SubState") != "running"
            or target_after.get("UnitFileState") != "enabled"
        ):
            raise RouteActivationError(
                "Workspace Control controller did not return active/running/enabled"
            )
        require_roots()
        others_after = controller_snapshots()
        require_snapshot_same(others_before, others_after)
        candidate.verify_installed(BASE_MANIFEST)

        tx.update({
            "phase": "COMMITTED_ACTIVE_CODEX_BOOTSTRAP_ROUTE",
            "active_route_receipt_sha256":
                sha(ACTIVE_ROUTE_RECEIPT.read_bytes()),
            "controller_policy_file_sha256": sha(TARGET_POLICY.read_bytes()),
            "overlay_file_sha256": sha(OVERLAY.read_bytes()),
            "reconciler_sha256": sha(INSTALLED_RECONCILER.read_bytes()),
            "target_controller_after": target_after,
            "existing_controller_snapshot_after": others_after,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(tx_path, tx)
        print("WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_ACTIVATION=PASS")
        print(f"TRANSACTION_RECEIPT={tx_path}")
        return 0
    except BaseException as exc:
        try:
            if not target_stopped:
                subprocess.run(["systemctl", "stop", TARGET_UNIT], check=False)
            atomic_file(TARGET_POLICY, backups["policy"], 0o644)
            atomic_file(OVERLAY, backups["overlay"], 0o644)
            try:
                ACTIVE_ROUTE_RECEIPT.unlink()
            except FileNotFoundError:
                pass
            atomic_file(
                RECONCILER_OVERRIDE,
                backups["reconciler_override"],
                0o600,
            )
            atomic_file(
                INSTALLED_RECONCILER,
                backups["reconciler"],
                int(str(reconciler_entry.get("mode")), 8),
            )
            subprocess.run(["systemctl", "start", TARGET_UNIT], check=False)
            tx["phase"] = "ROLLED_BACK_PREVIOUS_ROUTE_STATE"
            tx["rollback_completed"] = True
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(tx_path, tx)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouteActivationError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
