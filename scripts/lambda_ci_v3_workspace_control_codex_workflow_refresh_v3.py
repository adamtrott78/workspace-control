#!/usr/bin/env python3
"""One-shot third refresh of only the live Workspace Control Codex workflow blob.

This helper is repository candidate code only until separately reviewed root
authority exists. It preserves the already-live control-small route, root
policy, overlay, capacity, GPU authority, and control-validation binding.
"""

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

import lambda_ci_v3_reconciler as candidate


BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
TARGET_CLASS = candidate.WORKSPACE_CONTROL_CODEX_TARGET_CLASS
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_POLICY = pathlib.Path(candidate.WORKSPACE_CONTROL_CODEX_CONTROLLER_DESTINATION)
ACTIVE_ROUTE = candidate.WORKSPACE_CONTROL_CODEX_ROUTE_ACTIVE_RECEIPT
PRIOR_REFRESH_ACTIVE = candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT
REFRESH_ACTIVE = candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT
INSTALLED_RECONCILER = candidate.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = candidate.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
PROVISIONER_STATE = pathlib.Path("/var/lib/workspace-ci/v3/provisioner")
TARGET_LEDGER = pathlib.Path("/var/lib/workspace-ci/v3/controller/state") / TARGET_CLASS
STATE_ROOT = (
    pathlib.Path("/var/lib/workspace-ci/v3/workspace-control")
    / "codex-bootstrap-route"
    / "workflow-refresh-v3"
)
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = STATE_ROOT / "authority-consumption"
OLD_BLOB = candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V2_BLOB
NEW_BLOB = candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB
WORKFLOW_PATH = candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_PATH
ACTIVE_RECORD_STATES = {"RESERVED", "PREPARING", "ACCEPTED", "RUNNING"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
AUTHORITY_MAX_SECONDS = 30 * 60


class RefreshError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RefreshError(f"{path}: expected JSON object")
    return value, raw


def parse_time(raw: Any, label: str) -> datetime:
    if not isinstance(raw, str):
        raise RefreshError(f"{label} missing")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RefreshError(f"{label} invalid") from exc
    if value.tzinfo is None:
        raise RefreshError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def require_root_private(path: pathlib.Path) -> bytes:
    st = path.stat()
    if (
        not stat.S_ISREG(st.st_mode)
        or st.st_uid != 0
        or st.st_gid != 0
        or stat.S_IMODE(st.st_mode) != 0o600
    ):
        raise RefreshError(f"root-private file metadata invalid: {path}")
    return path.read_bytes()


def exact_repo(repo: pathlib.Path, expected: str) -> pathlib.Path:
    if SHA40.fullmatch(expected) is None:
        raise RefreshError("expected source head invalid")
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if head != expected:
        raise RefreshError(f"source head mismatch: {head} != {expected}")
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        ],
        text=True,
    )
    if dirty.strip():
        raise RefreshError("source checkout is dirty")
    actual_blob = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", f"HEAD:{WORKFLOW_PATH}"],
        text=True,
    ).strip()
    if actual_blob != NEW_BLOB:
        raise RefreshError(
            f"source workflow blob mismatch: {actual_blob} != {NEW_BLOB}"
        )
    return repo.resolve()


def systemd(unit: str) -> dict[str, str]:
    proc = subprocess.run(
        [
            "systemctl",
            "show",
            unit,
            "-p",
            "LoadState",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
            "-p",
            "MainPID",
            "-p",
            "NRestarts",
            "-p",
            "InvocationID",
            "-p",
            "UnitFileState",
            "--no-pager",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RefreshError(
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
        raise RefreshError(
            f"systemctl {' '.join(args)} failed: {proc.stderr.strip()[:512]}"
        )


def require_roots() -> None:
    provisioner = systemd(PROVISIONER_UNIT)
    if (
        provisioner.get("ActiveState") != "active"
        or provisioner.get("SubState") != "running"
    ):
        raise RefreshError("shared provisioner is not active/running")
    reconciler = systemd(RECONCILER_UNIT)
    if (
        reconciler.get("ActiveState") != "active"
        or reconciler.get("SubState") != "exited"
        or reconciler.get("MainPID") not in {"", "0"}
    ):
        raise RefreshError("reconciler must be active/exited with no process")


def controller_snapshots() -> dict[str, dict[str, str]]:
    root, _ = load(ROOT_POLICY)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise RefreshError("installed class set invalid")
    return {
        class_id: systemd(f"workspace-ci-v3-controller@{class_id}.service")
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
        raise RefreshError("non-target controller set changed")
    for class_id in before:
        for field in fields:
            if before[class_id].get(field) != after[class_id].get(field):
                raise RefreshError(
                    f"non-target controller changed: {class_id} {field}"
                )


def require_target_quiescent() -> None:
    if TARGET_LEDGER.exists():
        for path in sorted(TARGET_LEDGER.glob("scheduler-*.json")):
            value = json.loads(path.read_text())
            if value.get("state") not in {"COMPLETED", "FAILED", "CANCELED"}:
                raise RefreshError(
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
                raise RefreshError(
                    f"target provisioner record holds capacity: {path.name}"
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
        raise RefreshError("failed to enumerate transient units")
    prefix = f"workspace-ci-v3-{TARGET_CLASS}-"
    for line in proc.stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        unit = fields[0]
        if unit.startswith(prefix):
            state = systemd(unit)
            if state.get("ActiveState") in {
                "active",
                "activating",
                "reloading",
            }:
                raise RefreshError(f"target transient still active: {unit}")


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


def policy_digest(policy: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in policy.items()
        if key not in {
            "control_plane_generation_sha256",
            "controller_policy_sha256",
        }
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def build_refreshed_policy(current: dict[str, Any]) -> dict[str, Any]:
    workflows = current.get("trusted_workflows")
    if not isinstance(workflows, list) or len(workflows) != 2:
        raise RefreshError("current Workspace Control workflow set invalid")
    by_route = {
        row.get("route_id"): row
        for row in workflows
        if isinstance(row, dict)
    }
    if set(by_route) != {"control-validation", "codex-bootstrap"}:
        raise RefreshError("current Workspace Control workflow identities invalid")

    validation = by_route["control-validation"]
    codex = by_route["codex-bootstrap"]
    if (
        validation.get("path")
        != candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_PATH
        or validation.get("blob_sha")
        != candidate.WORKSPACE_CONTROL_VALIDATION_WORKFLOW_BLOB
    ):
        raise RefreshError("control-validation predecessor drift")
    if (
        codex.get("path") != WORKFLOW_PATH
        or codex.get("blob_sha") != OLD_BLOB
        or codex.get("compile_time_job_key") != "codex-bootstrap"
        or codex.get("compile_time_top_level_job_count") != 1
        or codex.get("allowed_events") != ["issue_comment"]
        or codex.get("allowed_actor_logins") != ["adamtrott78"]
    ):
        raise RefreshError("Codex workflow predecessor drift")

    refreshed = copy.deepcopy(current)
    refreshed_by_route = {
        row["route_id"]: row for row in refreshed["trusted_workflows"]
    }
    refreshed_by_route["codex-bootstrap"]["blob_sha"] = NEW_BLOB
    refreshed["controller_policy_sha256"] = policy_digest(refreshed)

    changed = {
        key
        for key in set(current) | set(refreshed)
        if current.get(key) != refreshed.get(key)
    }
    if changed != {"trusted_workflows", "controller_policy_sha256"}:
        raise RefreshError("workflow refresh changed non-controller-local fields")
    return refreshed


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
            raise RefreshError(
                f"current reconciler override mismatch: {key}"
            )
    return value, raw


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
        raise RefreshError("authority keys drift")
    if (
        value["schema_version"] != 1
        or value["authority"] != "workspace-control-operator"
        or value["operation"]
        != "REFRESH_WORKSPACE_CONTROL_CODEX_WORKFLOW_V3"
    ):
        raise RefreshError("authority identity invalid")
    auth_id = value["authorization_id"]
    if (
        not isinstance(auth_id, str)
        or UUID_RE.fullmatch(auth_id) is None
        or str(uuid.UUID(auth_id)) != auth_id
    ):
        raise RefreshError("authorization id invalid")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise RefreshError(f"authority binding mismatch: {key}")
    issued = parse_time(value["issued_at"], "issued_at")
    expires = parse_time(value["expires_at"], "expires_at")
    now = datetime.now(timezone.utc)
    if (
        not (issued <= now <= expires)
        or (expires - issued).total_seconds() > AUTHORITY_MAX_SECONDS
    ):
        raise RefreshError("authority validity window invalid")
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


def require_target_inactive() -> dict[str, str]:
    state = systemd(TARGET_UNIT)
    if (
        state.get("ActiveState") != "inactive"
        or state.get("MainPID") not in {"", "0"}
    ):
        raise RefreshError("target controller is not proven inactive")
    return state


def require_target_active() -> dict[str, str]:
    state = systemd(TARGET_UNIT)
    if (
        state.get("ActiveState") != "active"
        or state.get("SubState") != "running"
        or state.get("UnitFileState") != "enabled"
    ):
        raise RefreshError("target controller is not active/running/enabled")
    return state


def require_predecessor_unchanged(
    *,
    root_policy_raw: bytes,
    active_route_raw: bytes,
    prior_refresh_raw: bytes,
    policy_raw: bytes,
    reconciler_raw: bytes,
    reconciler_override_raw: bytes,
    others_before: dict[str, dict[str, str]],
) -> None:
    if ROOT_POLICY.read_bytes() != root_policy_raw:
        raise RefreshError("root policy changed before workflow refresh mutation")
    if ACTIVE_ROUTE.read_bytes() != active_route_raw:
        raise RefreshError("active Codex route receipt changed before mutation")
    if PRIOR_REFRESH_ACTIVE.read_bytes() != prior_refresh_raw:
        raise RefreshError("Codex workflow refresh v2 receipt changed before mutation")
    if TARGET_POLICY.read_bytes() != policy_raw:
        raise RefreshError("target controller policy changed before mutation")
    if INSTALLED_RECONCILER.read_bytes() != reconciler_raw:
        raise RefreshError("installed reconciler changed before mutation")
    if RECONCILER_OVERRIDE.read_bytes() != reconciler_override_raw:
        raise RefreshError("reconciler override changed before mutation")
    if REFRESH_ACTIVE.exists():
        raise RefreshError("Codex workflow refresh appeared concurrently")
    require_snapshot_same(others_before, controller_snapshots())


def stop_target_close_quiescence_and_write_first_policy(
    *,
    root_policy_raw: bytes,
    active_route_raw: bytes,
    prior_refresh_raw: bytes,
    policy_raw: bytes,
    reconciler_raw: bytes,
    reconciler_override_raw: bytes,
    others_before: dict[str, dict[str, str]],
    refreshed_policy_raw: bytes,
    mutation_state: dict[str, bool],
) -> None:
    run_systemctl("stop", TARGET_UNIT)
    require_target_inactive()
    require_target_quiescent()
    require_predecessor_unchanged(
        root_policy_raw=root_policy_raw,
        active_route_raw=active_route_raw,
        prior_refresh_raw=prior_refresh_raw,
        policy_raw=policy_raw,
        reconciler_raw=reconciler_raw,
        reconciler_override_raw=reconciler_override_raw,
        others_before=others_before,
    )
    require_target_quiescent()
    mutation_state["started"] = True
    atomic_file(TARGET_POLICY, refreshed_policy_raw, 0o644)


def verify_predecessor_restored(
    *,
    root_policy_raw: bytes,
    active_route_raw: bytes,
    prior_refresh_raw: bytes,
    policy_raw: bytes,
    reconciler_raw: bytes,
    reconciler_override_raw: bytes,
    others_before: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    if ROOT_POLICY.read_bytes() != root_policy_raw:
        raise RefreshError("rollback root policy digest mismatch")
    if ACTIVE_ROUTE.read_bytes() != active_route_raw:
        raise RefreshError("rollback active-route receipt mismatch")
    if PRIOR_REFRESH_ACTIVE.read_bytes() != prior_refresh_raw:
        raise RefreshError("rollback v2 refresh receipt mismatch")
    if TARGET_POLICY.read_bytes() != policy_raw:
        raise RefreshError("rollback target policy bytes mismatch")
    if INSTALLED_RECONCILER.read_bytes() != reconciler_raw:
        raise RefreshError("rollback reconciler bytes mismatch")
    if RECONCILER_OVERRIDE.read_bytes() != reconciler_override_raw:
        raise RefreshError("rollback reconciler override bytes mismatch")
    if REFRESH_ACTIVE.exists():
        raise RefreshError("rollback refresh v3 receipt still present")

    target_after = require_target_active()
    require_roots()
    require_target_quiescent()
    others_after = controller_snapshots()
    require_snapshot_same(others_before, others_after)
    candidate.verify_installed(BASE_MANIFEST)
    return target_after, others_after


def recover_pre_mutation_failure(
    *,
    root_policy_raw: bytes,
    active_route_raw: bytes,
    prior_refresh_raw: bytes,
    policy_raw: bytes,
    reconciler_raw: bytes,
    reconciler_override_raw: bytes,
    others_before: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    require_target_inactive()
    require_predecessor_unchanged(
        root_policy_raw=root_policy_raw,
        active_route_raw=active_route_raw,
        prior_refresh_raw=prior_refresh_raw,
        policy_raw=policy_raw,
        reconciler_raw=reconciler_raw,
        reconciler_override_raw=reconciler_override_raw,
        others_before=others_before,
    )
    run_systemctl("start", TARGET_UNIT)
    return verify_predecessor_restored(
        root_policy_raw=root_policy_raw,
        active_route_raw=active_route_raw,
        prior_refresh_raw=prior_refresh_raw,
        policy_raw=policy_raw,
        reconciler_raw=reconciler_raw,
        reconciler_override_raw=reconciler_override_raw,
        others_before=others_before,
    )


def rollback_after_mutation(
    *,
    root_policy_raw: bytes,
    active_route_raw: bytes,
    prior_refresh_raw: bytes,
    policy_raw: bytes,
    reconciler_raw: bytes,
    reconciler_override_raw: bytes,
    reconciler_mode: int,
    others_before: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    current = systemd(TARGET_UNIT)
    if current.get("ActiveState") != "inactive":
        run_systemctl("stop", TARGET_UNIT)
    require_target_inactive()

    atomic_file(TARGET_POLICY, policy_raw, 0o644)
    try:
        REFRESH_ACTIVE.unlink()
    except FileNotFoundError:
        pass
    atomic_file(RECONCILER_OVERRIDE, reconciler_override_raw, 0o600)
    atomic_file(INSTALLED_RECONCILER, reconciler_raw, reconciler_mode)

    if TARGET_POLICY.read_bytes() != policy_raw:
        raise RefreshError("rollback target policy restore failed")
    if INSTALLED_RECONCILER.read_bytes() != reconciler_raw:
        raise RefreshError("rollback reconciler restore failed")
    if RECONCILER_OVERRIDE.read_bytes() != reconciler_override_raw:
        raise RefreshError("rollback reconciler override restore failed")
    if REFRESH_ACTIVE.exists():
        raise RefreshError("rollback refresh v3 receipt removal failed")
    if ROOT_POLICY.read_bytes() != root_policy_raw:
        raise RefreshError("rollback root policy changed")
    if ACTIVE_ROUTE.read_bytes() != active_route_raw:
        raise RefreshError("rollback active-route receipt changed")
    if PRIOR_REFRESH_ACTIVE.read_bytes() != prior_refresh_raw:
        raise RefreshError("rollback v2 refresh receipt changed")

    candidate.verify_installed(BASE_MANIFEST)
    run_systemctl("start", TARGET_UNIT)
    return verify_predecessor_restored(
        root_policy_raw=root_policy_raw,
        active_route_raw=active_route_raw,
        prior_refresh_raw=prior_refresh_raw,
        policy_raw=policy_raw,
        reconciler_raw=reconciler_raw,
        reconciler_override_raw=reconciler_override_raw,
        others_before=others_before,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RefreshError("Codex workflow refresh requires root")

    repo = exact_repo(args.repo_root, args.expected_head)
    require_roots()
    require_target_quiescent()

    # Full currently installed state must be accepted before mutation.
    candidate.verify_installed(BASE_MANIFEST)

    if REFRESH_ACTIVE.exists():
        raise RefreshError("Codex workflow refresh v3 already exists")
    active, active_raw = load(ACTIVE_ROUTE)
    root_policy_raw = ROOT_POLICY.read_bytes()
    if (
        active.get("mode")
        != "V3_WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_OVERRIDE"
        or active.get("phase") != "ACTIVE"
        or active.get("target_class_id") != TARGET_CLASS
        or active.get("workflow_path") != WORKFLOW_PATH
        or active.get("workflow_blob_sha")
        != candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_INITIAL_BLOB
    ):
        raise RefreshError("live Codex route predecessor binding invalid")

    prior_v1 = candidate._workspace_control_codex_workflow_refresh(active)
    if prior_v1 is None:
        raise RefreshError("Codex workflow refresh v1 predecessor is absent")
    prior = candidate._workspace_control_codex_workflow_refresh_v2(
        active,
        prior_v1,
    )
    if prior is None:
        raise RefreshError("Codex workflow refresh v2 predecessor is absent")
    prior_refresh_raw = PRIOR_REFRESH_ACTIVE.read_bytes()
    if prior.get("workflow_blob_sha") != OLD_BLOB:
        raise RefreshError("Codex workflow refresh v2 predecessor blob drift")

    target_before = systemd(TARGET_UNIT)
    if (
        target_before.get("ActiveState") != "active"
        or target_before.get("SubState") != "running"
        or target_before.get("UnitFileState") != "enabled"
    ):
        raise RefreshError("target controller is not active/running/enabled")
    others_before = controller_snapshots()

    current_policy, current_policy_raw = load(TARGET_POLICY)
    if (
        sha(current_policy_raw)
        != prior.get("controller_policy_file_sha256")
        or current_policy.get("controller_policy_sha256")
        != prior.get("controller_policy_sha256")
    ):
        raise RefreshError("live target policy does not match refresh v2 receipt")
    refreshed_policy = build_refreshed_policy(current_policy)
    refreshed_policy_raw = canonical(refreshed_policy)

    manifest, manifest_raw = load(BASE_MANIFEST)
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
            "git",
            "-C",
            str(repo),
            "hash-object",
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
        "active_route_receipt_sha256": sha(active_raw),
        "previous_refresh_receipt_sha256": sha(prior_refresh_raw),
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "previous_controller_policy_sha256":
            current_policy["controller_policy_sha256"],
        "controller_policy_sha256":
            refreshed_policy["controller_policy_sha256"],
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "controller_policy_file_sha256": sha(refreshed_policy_raw),
        "target_class_id": TARGET_CLASS,
    }
    authority, authority_raw = validate_authority(
        args.authorization_receipt,
        expected_authority,
    )

    refresh = {
        "schema_version": 1,
        "mode": "V3_WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3",
        "phase": "ACTIVE",
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "active_route_receipt_sha256": sha(active_raw),
        "previous_refresh_receipt_sha256": sha(prior_refresh_raw),
        "target_class_id": TARGET_CLASS,
        "workflow_path": WORKFLOW_PATH,
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "previous_controller_policy_sha256":
            current_policy["controller_policy_sha256"],
        "controller_policy_sha256":
            refreshed_policy["controller_policy_sha256"],
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "controller_policy_file_sha256": sha(refreshed_policy_raw),
    }

    ensure_dir(TX_ROOT)
    tx_id = str(uuid.uuid4())
    tx_dir = TX_ROOT / f"refresh-{tx_id}"
    ensure_dir(tx_dir)
    tx_path = tx_dir / "receipt.json"
    backups = {
        "policy": current_policy_raw,
        "reconciler": old_reconciler,
        "reconciler_override": old_reconciler_override_raw,
    }
    tx = {
        "schema_version": 1,
        "mode": "V3_WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3_TRANSACTION",
        "phase": "PREPARED",
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": sha(authority_raw),
        "active_route_receipt_sha256": sha(active_raw),
        "previous_refresh_receipt_sha256": sha(prior_refresh_raw),
        "previous_workflow_blob_sha": OLD_BLOB,
        "workflow_blob_sha": NEW_BLOB,
        "target_controller_before": target_before,
        "existing_controller_snapshot": others_before,
        "previous_controller_policy_file_sha256": sha(current_policy_raw),
        "controller_policy_file_sha256": sha(refreshed_policy_raw),
    }
    atomic_json(tx_path, tx)
    consume_authority(authority, authority_raw)

    mutation_state = {"started": False}
    reconciler_mode = int(str(reconciler_entry.get("mode")), 8)
    try:
        stop_target_close_quiescence_and_write_first_policy(
            root_policy_raw=root_policy_raw,
            active_route_raw=active_raw,
            prior_refresh_raw=prior_refresh_raw,
            policy_raw=current_policy_raw,
            reconciler_raw=old_reconciler,
            reconciler_override_raw=old_reconciler_override_raw,
            others_before=others_before,
            refreshed_policy_raw=refreshed_policy_raw,
            mutation_state=mutation_state,
        )

        atomic_json(REFRESH_ACTIVE, refresh)
        atomic_json(RECONCILER_OVERRIDE, new_reconciler_override)
        atomic_file(
            INSTALLED_RECONCILER,
            new_reconciler,
            reconciler_mode,
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
            raise RefreshError(
                "installed reconciler verification failed: "
                + proc.stderr.strip()[:1024]
            )

        tx["phase"] = "POLICY_INSTALLED_CONTROLLER_STOPPED"
        atomic_json(tx_path, tx)

        run_systemctl("start", TARGET_UNIT)
        target_after = require_target_active()
        require_roots()
        require_target_quiescent()
        others_after = controller_snapshots()
        require_snapshot_same(others_before, others_after)
        candidate.verify_installed(BASE_MANIFEST)

        tx.update({
            "phase": "COMMITTED_ACTIVE_CODEX_WORKFLOW_REFRESH_V3",
            "mutation_performed": mutation_state["started"],
            "refresh_receipt_sha256": sha(REFRESH_ACTIVE.read_bytes()),
            "controller_policy_file_sha256": sha(TARGET_POLICY.read_bytes()),
            "reconciler_sha256": sha(INSTALLED_RECONCILER.read_bytes()),
            "target_controller_after": target_after,
            "existing_controller_snapshot_after": others_after,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(tx_path, tx)
        print("WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3=PASS")
        print(f"TRANSACTION_RECEIPT={tx_path}")
        return 0
    except BaseException as exc:
        rollback_error: BaseException | None = None
        try:
            if mutation_state["started"]:
                target_restored, others_restored = rollback_after_mutation(
                    root_policy_raw=root_policy_raw,
                    active_route_raw=active_raw,
                    prior_refresh_raw=prior_refresh_raw,
                    policy_raw=backups["policy"],
                    reconciler_raw=backups["reconciler"],
                    reconciler_override_raw=backups["reconciler_override"],
                    reconciler_mode=reconciler_mode,
                    others_before=others_before,
                )
                tx["phase"] = "ROLLED_BACK_PREVIOUS_CODEX_WORKFLOW_V3"
            else:
                target_restored, others_restored = recover_pre_mutation_failure(
                    root_policy_raw=root_policy_raw,
                    active_route_raw=active_raw,
                    prior_refresh_raw=prior_refresh_raw,
                    policy_raw=backups["policy"],
                    reconciler_raw=backups["reconciler"],
                    reconciler_override_raw=backups["reconciler_override"],
                    others_before=others_before,
                )
                tx["phase"] = "FAILED_PRE_MUTATION_RESTORED"
            tx["rollback_completed"] = True
            tx["mutation_performed"] = mutation_state["started"]
            tx["target_controller_after_rollback"] = target_restored
            tx["existing_controller_snapshot_after_rollback"] = others_restored
        except BaseException as rollback_exc:
            rollback_error = rollback_exc
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["mutation_performed"] = mutation_state["started"]
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(tx_path, tx)
        if rollback_error is not None:
            raise RefreshError(
                f"refresh failed and rollback is incomplete: {rollback_error}"
            ) from exc
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RefreshError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
