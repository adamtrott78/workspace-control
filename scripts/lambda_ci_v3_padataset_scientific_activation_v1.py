#!/usr/bin/env python3
"""Additive live-v3 activation for the dedicated PADataset scientific class.

This transaction never replays the historical v2->v3 cutover.

Phase A (EXPAND_INACTIVE) proves the currently installed v3 generation is a
strict nine-class predecessor of the reviewed ten-class repository policy,
quiesces only the shared root provisioner, installs the exact additive
configuration, restarts only the provisioner, and leaves the scientific class
INSTALLED/INACTIVE with its route DISABLED.

Phase B (ACTIVATE) consumes separate authority and a fresh root-owned GitHub /
runtime preflight confirmation, then starts/enables only the scientific class
controller and flips only its overlay class/route state.

Existing class controllers are never stopped or restarted by this helper.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import grp
import hashlib
import json
import os
import pathlib
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import uuid
from typing import Any, Protocol

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_reconciler as reconciler


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

TARGET_CLASS = reconciler.PADATASET_SCIENTIFIC_TARGET_CLASS
TARGET_ROUTE = reconciler.PADATASET_SCIENTIFIC_TARGET_ROUTE
TARGET_SCALE_SET = reconciler.PADATASET_SCIENTIFIC_TARGET_SCALE_SET
TARGET_CONTROLLER_USER = "ci-ctl-pad-science"
TARGET_CONTROLLER_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_CONTROLLER_POLICY = (
    pathlib.Path("/etc/workspace-ci/v3/controllers") / f"{TARGET_CLASS}.json"
)
TARGET_CONTROLLER_DROPIN = (
    pathlib.Path("/etc/systemd/system")
    / f"workspace-ci-v3-controller@{TARGET_CLASS}.service.d"
    / "identity.conf"
)
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
PROVISIONER_SOCKET = pathlib.Path("/run/workspace-ci/v3/provisioner.sock")
PROVISIONER_SOCKET_GROUP = "workspace-ci-v3-provisioner"
PROVISIONER_STATE = pathlib.Path("/var/lib/workspace-ci/v3/provisioner")
SCIENTIFIC_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific")
ACTIVE_RECEIPT = reconciler.PADATASET_SCIENTIFIC_ACTIVE_RECEIPT
TRANSACTION_ROOT = SCIENTIFIC_ROOT / "transactions"
AUTHORITY_ROOT = SCIENTIFIC_ROOT / "authority-consumption"
RECONCILER_INSTALLED = reconciler.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = reconciler.RECONCILER_OVERRIDE_ACTIVE_RECEIPT

WORKFLOW_PATH = reconciler.PADATASET_SCIENTIFIC_WORKFLOW_PATH
WORKFLOW_BLOB = reconciler.PADATASET_SCIENTIFIC_WORKFLOW_BLOB
RUNTIME_MANIFEST = reconciler.PADATASET_SCIENTIFIC_RUNTIME_MANIFEST
RUNTIME_TREE = reconciler.PADATASET_SCIENTIFIC_RUNTIME_TREE
BASE_PYTHON_SHA = reconciler.PADATASET_SCIENTIFIC_BASE_PYTHON_SHA
DATA_PROFILE = reconciler.PADATASET_SCIENTIFIC_DATA_PROFILE
DATA_DIGEST = reconciler.PADATASET_SCIENTIFIC_DATA_DIGEST

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
ACTIVE_RECORD_STATES = {"RESERVED", "PREPARING", "ACCEPTED"}
AUTHORITY_MAX_SECONDS = 30 * 60
PREFLIGHT_MAX_SECONDS = 15 * 60


class ScientificActivationError(RuntimeError):
    pass


class Systemd(Protocol):
    def show(self, unit: str) -> dict[str, str]: ...
    def start(self, unit: str) -> None: ...
    def stop(self, unit: str) -> None: ...
    def enable(self, unit: str) -> None: ...
    def disable(self, unit: str) -> None: ...
    def list_units(self) -> list[str]: ...


class RealSystemd:
    @staticmethod
    def _run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and proc.returncode != 0:
            raise ScientificActivationError(
                f"command failed rc={proc.returncode}: {' '.join(argv)}: "
                f"{proc.stderr.strip()[:512]}"
            )
        return proc

    def show(self, unit: str) -> dict[str, str]:
        proc = self._run(
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
            ]
        )
        out: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                out[key] = value
        return out

    def start(self, unit: str) -> None:
        self._run(["systemctl", "start", unit])

    def stop(self, unit: str) -> None:
        self._run(["systemctl", "stop", unit])

    def enable(self, unit: str) -> None:
        self._run(["systemctl", "enable", unit])

    def disable(self, unit: str) -> None:
        self._run(["systemctl", "disable", unit], check=False)

    def list_units(self) -> list[str]:
        proc = self._run(
            [
                "systemctl",
                "list-units",
                "--all",
                "--type=service",
                "--plain",
                "--no-legend",
                "--no-pager",
            ]
        )
        return [line.split()[0] for line in proc.stdout.splitlines() if line.split()]


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScientificActivationError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise ScientificActivationError(f"{path}: expected JSON object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: pathlib.Path) -> str:
    return _sha(path.read_bytes())


def _atomic_file(path: pathlib.Path, raw: bytes, mode: int) -> None:
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
        dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _atomic_json(path: pathlib.Path, value: dict[str, Any], mode: int = 0o600) -> None:
    _atomic_file(path, _canonical(value), mode)


def _ensure_private_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, 0, 0)
    os.chmod(path, 0o700)


def _require_root_private_file(path: pathlib.Path) -> bytes:
    st = path.stat()
    if (
        not stat.S_ISREG(st.st_mode)
        or st.st_uid != 0
        or st.st_gid != 0
        or stat.S_IMODE(st.st_mode) != 0o600
    ):
        raise ScientificActivationError(
            f"root authority/preflight file metadata invalid: {path}"
        )
    return path.read_bytes()


def _parse_time(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScientificActivationError(f"{field} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ScientificActivationError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _validate_window(
    payload: dict[str, Any],
    *,
    issued_key: str,
    expires_key: str,
    max_seconds: int,
) -> None:
    now = datetime.now(timezone.utc)
    issued = _parse_time(payload.get(issued_key), issued_key)
    expires = _parse_time(payload.get(expires_key), expires_key)
    if expires <= issued:
        raise ScientificActivationError("authority/preflight expiry precedes issuance")
    if (expires - issued).total_seconds() > max_seconds:
        raise ScientificActivationError("authority/preflight lifetime exceeds maximum")
    if issued > now or expires <= now:
        raise ScientificActivationError("authority/preflight is not currently valid")


def _exact_repo(repo_root: pathlib.Path, expected_head: str) -> pathlib.Path:
    if SHA40.fullmatch(expected_head) is None:
        raise ScientificActivationError("expected head must be a full lowercase Git SHA")
    repo_root = repo_root.resolve()
    observed = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if observed != expected_head:
        raise ScientificActivationError(
            f"source head mismatch: {observed} != {expected_head}"
        )
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        ],
        text=True,
    )
    if dirty.strip():
        raise ScientificActivationError("source checkout is dirty")
    return repo_root


def _base_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ScientificActivationError("base manifest entries missing")
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ScientificActivationError("base manifest entry invalid")
        destination = entry.get("destination")
        if not isinstance(destination, str) or destination in out:
            raise ScientificActivationError("base manifest destination invalid/duplicate")
        out[destination] = entry
    return out


def _semantic_class(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key != "control_plane_generation_sha256"
    }


def _validate_target_root(target: dict[str, Any]) -> None:
    required = {
        "runner_class_id": TARGET_CLASS,
        "project_id": "padataset",
        "repository": "adamtrott78/PADataset",
        "scale_set_name": TARGET_SCALE_SET,
        "runner_prefix": "lambda-padataset-scientific-single-gpu-",
        "execution_contract_id": "scientific-single-gpu-v1",
    }
    for key, expected in required.items():
        if target.get(key) != expected:
            raise ScientificActivationError(f"target root binding mismatch: {key}")
    if target.get("controller_peer") != {"unix_user": TARGET_CONTROLLER_USER}:
        raise ScientificActivationError("target controller identity mismatch")
    runtime = target.get("bindings", {}).get("runtime")
    if not isinstance(runtime, dict):
        raise ScientificActivationError("target runtime binding missing")
    expected_runtime = {
        "runtime_id": "padataset-dnns-v1",
        "manifest_identity_sha256": RUNTIME_MANIFEST,
        "tree_digest_sha256": RUNTIME_TREE,
        "base_python_path": "/usr/bin/python3.12",
        "base_python_sha256": BASE_PYTHON_SHA,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            raise ScientificActivationError(f"target runtime binding mismatch: {key}")
    data = runtime.get("scientific_data")
    if not isinstance(data, dict):
        raise ScientificActivationError("target scientific data binding missing")
    if data.get("profile_id") != DATA_PROFILE:
        raise ScientificActivationError("target scientific data profile mismatch")
    if data.get("tree_digest_sha256") != DATA_DIGEST:
        raise ScientificActivationError("target scientific data digest mismatch")


def _validate_exact_superset(
    current_root: dict[str, Any],
    candidate_root: dict[str, Any],
) -> dict[str, str]:
    current_classes = current_root.get("runner_classes")
    candidate_classes = candidate_root.get("runner_classes")
    if not isinstance(current_classes, dict) or not isinstance(candidate_classes, dict):
        raise ScientificActivationError("runner class maps missing")
    if TARGET_CLASS in current_classes:
        raise ScientificActivationError("scientific target already exists in current root policy")
    if set(candidate_classes) != set(current_classes) | {TARGET_CLASS}:
        raise ScientificActivationError("candidate runner classes are not exact +1 superset")
    if current_root.get("host_resource_policy") != candidate_root.get("host_resource_policy"):
        raise ScientificActivationError("candidate host resource policy drift")
    if current_root.get("upstream_pins") != candidate_root.get("upstream_pins"):
        raise ScientificActivationError("candidate upstream pins drift")

    preserved: dict[str, str] = {}
    for class_id, current in current_classes.items():
        candidate = candidate_classes[class_id]
        if _semantic_class(current) != _semantic_class(candidate):
            raise ScientificActivationError(
                f"pre-existing runner class authority drift: {class_id}"
            )
        digest = current.get("root_envelope_sha256")
        if not isinstance(digest, str) or SHA64.fullmatch(digest) is None:
            raise ScientificActivationError(
                f"pre-existing root envelope digest invalid: {class_id}"
            )
        preserved[class_id] = digest
    _validate_target_root(candidate_classes[TARGET_CLASS])
    return preserved


def _candidate_generation(
    repo_root: pathlib.Path,
    current_root: dict[str, Any],
    current_overlay: dict[str, Any],
) -> tuple[dict[str, Any], dict[pathlib.Path, tuple[bytes, int]], dict[str, str]]:
    compiled = compiler.compile_policy(repo_root)
    candidate_root = compiled["root_projection"]
    preserved = _validate_exact_superset(current_root, candidate_root)

    if TARGET_CLASS in current_overlay.get("classes", {}):
        raise ScientificActivationError("scientific class already exists in live overlay")
    if TARGET_ROUTE in current_overlay.get("routes", {}):
        raise ScientificActivationError("scientific route already exists in live overlay")

    template = _load(repo_root / OVERLAY_TEMPLATE_REL)
    target_state = copy.deepcopy(template["classes"][TARGET_CLASS])
    target_state["install_state"] = "INSTALLED"
    target_state["controller_state"] = "INACTIVE"
    target_state["containment"] = {"state": "CLEAR", "source": None}
    route_state = copy.deepcopy(template["routes"][TARGET_ROUTE])
    route_state["admission_state"] = "DISABLED"
    route_state["source"] = "PADataset scientific additive install: activation pending"

    overlay = copy.deepcopy(current_overlay)
    overlay["catalog_generation_sha256"] = compiled["catalog_generation_sha256"]
    overlay["classes"][TARGET_CLASS] = target_state
    overlay["routes"][TARGET_ROUTE] = route_state

    migration = _load(repo_root / MIGRATION_PLAN_REL)
    target_policy = compiled["controller_projections"][TARGET_CLASS]
    if target_policy.get("runner_class_id") != TARGET_CLASS:
        raise ScientificActivationError("compiled target controller class mismatch")
    if target_policy.get("scale_set_name") != TARGET_SCALE_SET:
        raise ScientificActivationError("compiled target scale set mismatch")
    workflows = target_policy.get("trusted_workflows")
    if (
        not isinstance(workflows, list)
        or len(workflows) != 1
        or workflows[0].get("route_id") != "scientific-single-gpu"
        or workflows[0].get("path") != WORKFLOW_PATH
        or workflows[0].get("blob_sha") != WORKFLOW_BLOB
    ):
        raise ScientificActivationError("compiled target workflow binding drift")

    artifacts: dict[pathlib.Path, tuple[bytes, int]] = {
        ROOT_POLICY: (_canonical(candidate_root), 0o644),
        EXECUTOR_ACTIONS: (_canonical(compiled["executor_projection"]), 0o644),
        COMPATIBILITY_MATRIX: (_canonical(compiled["compatibility_matrix"]), 0o644),
        DEPLOYMENT_OVERLAY: (_canonical(overlay), 0o644),
        SYSUSERS: (reconciler.render_sysusers(compiled, migration).encode(), 0o644),
        TMPFILES: (reconciler.render_tmpfiles(compiled, migration).encode(), 0o644),
        TARGET_CONTROLLER_POLICY: (_canonical(target_policy), 0o644),
        TARGET_CONTROLLER_DROPIN: (
            reconciler.render_controller_dropin(
                TARGET_CLASS,
                candidate_root["runner_classes"][TARGET_CLASS],
                migration,
            ).encode(),
            0o644,
        ),
    }
    return compiled, artifacts, preserved


def _current_records(state_root: pathlib.Path = PROVISIONER_STATE) -> list[dict[str, Any]]:
    if not state_root.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(state_root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ScientificActivationError(f"invalid provisioner record: {path}") from exc
        if not isinstance(value, dict):
            raise ScientificActivationError(f"invalid provisioner record object: {path}")
        out.append(value)
    return out


def _active_or_held_records(state_root: pathlib.Path = PROVISIONER_STATE) -> list[str]:
    out: list[str] = []
    for record in _current_records(state_root):
        if (
            record.get("state") in ACTIVE_RECORD_STATES
            or record.get("resource_hold") is True
        ):
            out.append(str(record.get("request_id", "<unknown>")))
    return sorted(out)


def _active_transients(systemd: Systemd) -> list[str]:
    runner = re.compile(r"^workspace-ci-v3-.+-[0-9a-f]{8}-[0-9a-f-]{27}\.service$")
    supervisor = re.compile(r"^workspace-ci-v3-supervisor-[0-9a-f]{20}\.service$")
    out: list[str] = []
    for unit in systemd.list_units():
        if not (runner.fullmatch(unit) or supervisor.fullmatch(unit)):
            continue
        state = systemd.show(unit)
        if state.get("ActiveState") in {"active", "activating", "reloading"}:
            out.append(unit)
    return sorted(out)


def _require_quiescent(systemd: Systemd) -> None:
    records = _active_or_held_records()
    if records:
        raise ScientificActivationError(
            f"shared provisioner has active/held records: {records}"
        )
    transients = _active_transients(systemd)
    if transients:
        raise ScientificActivationError(f"v3 transients remain: {transients}")


def _controller_snapshot(
    systemd: Systemd,
    class_ids: list[str],
) -> dict[str, dict[str, str]]:
    return {
        class_id: systemd.show(f"workspace-ci-v3-controller@{class_id}.service")
        for class_id in sorted(class_ids)
    }


def _require_controller_snapshot_preserved(
    before: dict[str, dict[str, str]],
    after: dict[str, dict[str, str]],
) -> None:
    if set(before) != set(after):
        raise ScientificActivationError("existing controller snapshot class set drift")
    fields = (
        "LoadState",
        "ActiveState",
        "SubState",
        "MainPID",
        "NRestarts",
        "InvocationID",
        "UnitFileState",
    )
    for class_id in sorted(before):
        for field in fields:
            if before[class_id].get(field) != after[class_id].get(field):
                raise ScientificActivationError(
                    f"existing controller changed during scientific transaction: "
                    f"{class_id} {field}"
                )


def _require_provisioner_active(systemd: Systemd) -> None:
    state = systemd.show(PROVISIONER_UNIT)
    if state.get("ActiveState") != "active" or state.get("SubState") != "running":
        raise ScientificActivationError("shared v3 provisioner is not active/running")


def _require_provisioner_socket() -> None:
    st = PROVISIONER_SOCKET.lstat()
    if not stat.S_ISSOCK(st.st_mode):
        raise ScientificActivationError("v3 provisioner path is not a Unix socket")
    if st.st_uid != 0:
        raise ScientificActivationError("v3 provisioner socket is not root-owned")
    expected_gid = grp.getgrnam(PROVISIONER_SOCKET_GROUP).gr_gid
    if st.st_gid != expected_gid:
        raise ScientificActivationError("v3 provisioner socket group mismatch")
    if stat.S_IMODE(st.st_mode) != 0o660:
        raise ScientificActivationError("v3 provisioner socket mode mismatch")


def _load_authority(
    path: pathlib.Path,
    *,
    operation: str,
    expected: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    raw = _require_root_private_file(path)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScientificActivationError("authority receipt JSON invalid") from exc
    if not isinstance(value, dict):
        raise ScientificActivationError("authority receipt must be an object")
    required = {
        "schema_version",
        "authority",
        "operation",
        "authorization_id",
        "issued_at",
        "expires_at",
        *expected.keys(),
    }
    if set(value) != required:
        raise ScientificActivationError("authority receipt keys drift")
    if value["schema_version"] != 1 or value["authority"] != "workspace-control-operator":
        raise ScientificActivationError("authority receipt identity invalid")
    if value["operation"] != operation:
        raise ScientificActivationError("authority operation mismatch")
    auth_id = value["authorization_id"]
    if (
        not isinstance(auth_id, str)
        or UUID_RE.fullmatch(auth_id) is None
        or str(uuid.UUID(auth_id)) != auth_id
    ):
        raise ScientificActivationError("authorization id invalid")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ScientificActivationError(f"authority binding mismatch: {key}")
    _validate_window(
        value,
        issued_key="issued_at",
        expires_key="expires_at",
        max_seconds=AUTHORITY_MAX_SECONDS,
    )
    return value, raw


def _consume_authority(payload: dict[str, Any], raw: bytes) -> pathlib.Path:
    _ensure_private_dir(AUTHORITY_ROOT)
    marker = AUTHORITY_ROOT / f"{payload['authorization_id']}.json"
    record = {
        "schema_version": 1,
        "authorization_id": payload["authorization_id"],
        "operation": payload["operation"],
        "authority_sha256": _sha(raw),
        "consumed_at": datetime.now(timezone.utc).isoformat(),
    }
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(_canonical(record))
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(marker, 0, 0)
    return marker


def _build_scientific_receipt(
    *,
    source_head: str,
    base_manifest: dict[str, Any],
    base_manifest_raw: bytes,
    compiled: dict[str, Any],
    artifacts: dict[pathlib.Path, tuple[bytes, int]],
    preserved: dict[str, str],
    production_overrides: dict[str, str],
    phase: str,
    installed_inactive_overlay_sha256: str,
) -> dict[str, Any]:
    base_entries = _base_entries(base_manifest)
    overrides: dict[str, dict[str, str]] = {}
    for destination in sorted(reconciler.PADATASET_SCIENTIFIC_OVERRIDE_DESTINATIONS):
        path = pathlib.Path(destination)
        raw, mode = artifacts[path]
        base = base_entries.get(destination)
        if base is None:
            raise ScientificActivationError(
                f"scientific override destination is not base-managed: {destination}"
            )
        prior = production_overrides.get(destination, str(base.get("sha256", "")))
        if not path.is_file() or _sha_file(path) != prior:
            raise ScientificActivationError(
                f"effective pre-expansion artifact does not match attested prior digest: {path}"
            )
        overrides[destination] = {
            "prior_sha256": prior,
            "sha256": _sha(raw),
            "mode": f"{mode:04o}",
        }

    additions: dict[str, dict[str, str]] = {}
    for destination in sorted(reconciler.PADATASET_SCIENTIFIC_ADDITION_DESTINATIONS):
        path = pathlib.Path(destination)
        raw, mode = artifacts[path]
        if path.exists():
            raise ScientificActivationError(
                f"scientific managed addition already exists: {path}"
            )
        additions[destination] = {
            "sha256": _sha(raw),
            "mode": f"{mode:04o}",
        }

    target_policy = compiled["controller_projections"][TARGET_CLASS]
    return {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_ADDITIVE_OVERRIDE",
        "phase": phase,
        "base_source_head": base_manifest.get("source_head"),
        "base_install_manifest_sha256": _sha(base_manifest_raw),
        "base_root_policy_sha256": base_manifest.get("root_policy_sha256"),
        "source_head": source_head,
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "target_scale_set_name": TARGET_SCALE_SET,
        "target_controller_policy_sha256": target_policy["controller_policy_sha256"],
        "trusted_workflow_blob_sha": WORKFLOW_BLOB,
        "runtime_manifest_identity_sha256": RUNTIME_MANIFEST,
        "runtime_tree_digest_sha256": RUNTIME_TREE,
        "base_python_sha256": BASE_PYTHON_SHA,
        "scientific_data_profile_id": DATA_PROFILE,
        "scientific_data_tree_digest_sha256": DATA_DIGEST,
        "installed_inactive_overlay_sha256": installed_inactive_overlay_sha256,
        "preserved_root_envelope_sha256": preserved,
        "prior_production_overrides": production_overrides,
        "managed_artifact_overrides": overrides,
        "managed_artifact_additions": additions,
    }


def _new_reconciler_override(
    *,
    source_head: str,
    base_manifest: dict[str, Any],
    base_manifest_raw: bytes,
    candidate_raw: bytes,
) -> dict[str, Any]:
    entries = _base_entries(base_manifest)
    destination = str(RECONCILER_INSTALLED)
    entry = entries.get(destination)
    if entry is None:
        raise ScientificActivationError("base manifest does not manage reconciler")
    return {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": base_manifest.get("source_head"),
        "base_install_manifest_sha256": _sha(base_manifest_raw),
        "base_reconciler_sha256": entry.get("sha256"),
        "reconciler_sha256": _sha(candidate_raw),
        "reconciler_mode": str(entry.get("mode")),
        "reconciler_source_head": source_head,
        "root_policy_sha256": base_manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }


def _backup_paths(
    tx_dir: pathlib.Path,
    paths: list[pathlib.Path],
) -> dict[str, dict[str, Any]]:
    backup_root = tx_dir / "backup"
    _ensure_private_dir(backup_root)
    out: dict[str, dict[str, Any]] = {}
    for index, path in enumerate(paths):
        row: dict[str, Any] = {"existed": path.exists()}
        if path.exists():
            st = path.stat()
            backup = backup_root / f"{index:03d}"
            shutil.copyfile(path, backup)
            os.chown(backup, 0, 0)
            os.chmod(backup, 0o600)
            row.update(
                {
                    "backup": str(backup),
                    "mode": stat.S_IMODE(st.st_mode),
                    "sha256": _sha_file(path),
                }
            )
        out[str(path)] = row
    return out


def _restore_paths(backups: dict[str, dict[str, Any]]) -> None:
    for raw_path, row in backups.items():
        path = pathlib.Path(raw_path)
        if row["existed"]:
            backup = pathlib.Path(row["backup"])
            _atomic_file(path, backup.read_bytes(), int(row["mode"]))
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def _run_root_tool(argv: list[str]) -> None:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise ScientificActivationError(
            f"root setup command failed rc={proc.returncode}: {' '.join(argv)}: "
            f"{proc.stderr.strip()[:512]}"
        )


def expand_inactive(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    authority_path: pathlib.Path,
    systemd: Systemd | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise ScientificActivationError("scientific expansion requires root")
    if ACTIVE_RECEIPT.exists():
        raise ScientificActivationError("scientific additive generation already installed")
    systemd = systemd or RealSystemd()
    repo_root = _exact_repo(repo_root, expected_head)

    reconciler.verify_installed(BASE_MANIFEST)
    base_raw = BASE_MANIFEST.read_bytes()
    base = _load(BASE_MANIFEST)
    current_root = _load(ROOT_POLICY)
    current_overlay = _load(DEPLOYMENT_OVERLAY)
    if current_root.get("root_policy_sha256") != base.get("root_policy_sha256"):
        raise ScientificActivationError(
            "pre-expansion root policy is not the immutable base generation"
        )

    compiled, artifacts, preserved = _candidate_generation(
        repo_root,
        current_root,
        current_overlay,
    )
    production_overrides = reconciler._production_cutover_overrides(base_raw, base)
    inactive_overlay_sha = _sha(artifacts[DEPLOYMENT_OVERLAY][0])
    scientific_receipt = _build_scientific_receipt(
        source_head=expected_head,
        base_manifest=base,
        base_manifest_raw=base_raw,
        compiled=compiled,
        artifacts=artifacts,
        preserved=preserved,
        production_overrides=production_overrides,
        phase="INSTALLED_INACTIVE",
        installed_inactive_overlay_sha256=inactive_overlay_sha,
    )

    expected_authority = {
        "source_head": expected_head,
        "base_install_manifest_sha256": _sha(base_raw),
        "current_root_policy_sha256": current_root["root_policy_sha256"],
        "candidate_root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
    }
    authority, authority_raw = _load_authority(
        authority_path,
        operation="EXPAND_PADATASET_SCIENTIFIC_V3_INACTIVE",
        expected=expected_authority,
    )

    existing_class_ids = sorted(current_root["runner_classes"])
    controller_before = _controller_snapshot(systemd, existing_class_ids)
    _require_provisioner_active(systemd)
    _require_quiescent(systemd)

    candidate_reconciler = (repo_root / "scripts/lambda_ci_v3_reconciler.py").read_bytes()
    new_reconciler_override = _new_reconciler_override(
        source_head=expected_head,
        base_manifest=base,
        base_manifest_raw=base_raw,
        candidate_raw=candidate_reconciler,
    )

    _ensure_private_dir(SCIENTIFIC_ROOT)
    _ensure_private_dir(TRANSACTION_ROOT)
    _ensure_private_dir(AUTHORITY_ROOT)
    tx_id = str(uuid.uuid4())
    tx_dir = TRANSACTION_ROOT / f"expand-{tx_id}"
    _ensure_private_dir(tx_dir)

    mutation_paths = [
        *sorted(artifacts, key=str),
        RECONCILER_INSTALLED,
        RECONCILER_OVERRIDE,
        ACTIVE_RECEIPT,
    ]
    backups = _backup_paths(tx_dir, mutation_paths)
    tx_receipt = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_EXPANSION",
        "phase": "PREPARED",
        "source_head": expected_head,
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": _sha(authority_raw),
        "base_install_manifest_sha256": _sha(base_raw),
        "previous_root_policy_sha256": current_root["root_policy_sha256"],
        "expanded_root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "existing_controller_snapshot": controller_before,
        "backups": backups,
    }
    _atomic_json(tx_receipt, tx)
    _consume_authority(authority, authority_raw)

    provisioner_started_on_new_generation = False
    try:
        systemd.stop(PROVISIONER_UNIT)
        state = systemd.show(PROVISIONER_UNIT)
        if state.get("ActiveState") not in {"inactive", "failed"}:
            raise ScientificActivationError("shared provisioner did not stop")
        _require_quiescent(systemd)

        for destination, (raw, mode) in artifacts.items():
            _atomic_file(destination, raw, mode)
        _atomic_json(ACTIVE_RECEIPT, scientific_receipt)
        _atomic_json(RECONCILER_OVERRIDE, new_reconciler_override)
        base_reconciler_mode = int(
            str(_base_entries(base)[str(RECONCILER_INSTALLED)]["mode"]),
            8,
        )
        _atomic_file(RECONCILER_INSTALLED, candidate_reconciler, base_reconciler_mode)

        _run_root_tool(["systemd-sysusers", str(SYSUSERS)])
        _run_root_tool(["systemd-tmpfiles", "--create", str(TMPFILES)])
        _run_root_tool(["systemctl", "daemon-reload"])

        # The candidate verifier must accept the fully staged effective
        # generation before the shared provisioner is restarted.
        reconciler.verify_installed(BASE_MANIFEST)

        systemd.start(PROVISIONER_UNIT)
        provisioner_started_on_new_generation = True
        _require_provisioner_active(systemd)
        _require_provisioner_socket()

        controller_after = _controller_snapshot(systemd, existing_class_ids)
        _require_controller_snapshot_preserved(controller_before, controller_after)
        reconciler.verify_installed(BASE_MANIFEST)

        tx["phase"] = "COMMITTED_INSTALLED_INACTIVE"
        tx["active_receipt_sha256"] = _sha_file(ACTIVE_RECEIPT)
        tx["existing_controller_snapshot_after"] = controller_after
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(tx_receipt, tx)
        return tx_receipt
    except BaseException as exc:
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        if not provisioner_started_on_new_generation:
            try:
                _restore_paths(backups)
                _run_root_tool(["systemctl", "daemon-reload"])
                systemd.start(PROVISIONER_UNIT)
                tx["phase"] = "ROLLED_BACK_PRESTART"
                tx["rollback_completed"] = True
            except BaseException as rollback_exc:
                tx["phase"] = "ROLLBACK_INCOMPLETE"
                tx["rollback_completed"] = False
                tx["rollback_error"] = str(rollback_exc)
        else:
            # Once the expanded provisioner has accepted the new root policy,
            # automatic rollback could race a fresh reservation from an
            # already-live controller. Preserve the safe target-inactive state
            # and require explicit diagnosis instead.
            tx["phase"] = "EXPANDED_NEEDS_REVIEW"
            tx["rollback_completed"] = False
        _atomic_json(tx_receipt, tx)
        raise


def _validate_preflight(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = _require_root_private_file(path)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScientificActivationError("activation preflight JSON invalid") from exc
    if not isinstance(value, dict):
        raise ScientificActivationError("activation preflight must be object")
    required = {
        "schema_version": 1,
        "mode": "PADATASET_SCIENTIFIC_ACTIVATION_PREFLIGHT_CONFIRMED",
        "repository": "adamtrott78/PADataset",
        "workflow_path": WORKFLOW_PATH,
        "workflow_blob_sha": WORKFLOW_BLOB,
        "active_workflow_runs": 0,
        "scale_set_name": TARGET_SCALE_SET,
        "assigned_jobs": 0,
        "running_jobs": 0,
        "runtime_manifest_identity_sha256": RUNTIME_MANIFEST,
        "runtime_tree_digest_sha256": RUNTIME_TREE,
        "base_python_sha256": BASE_PYTHON_SHA,
        "scientific_data_profile_id": DATA_PROFILE,
        "scientific_data_tree_digest_sha256": DATA_DIGEST,
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            raise ScientificActivationError(f"activation preflight mismatch: {key}")
    scale_set_id = value.get("scale_set_id")
    if not isinstance(scale_set_id, int) or scale_set_id <= 0:
        raise ScientificActivationError("activation preflight scale_set_id invalid")
    confirmed_at = _parse_time(value.get("confirmed_at"), "confirmed_at")
    now = datetime.now(timezone.utc)
    age = (now - confirmed_at).total_seconds()
    if age < 0 or age > PREFLIGHT_MAX_SECONDS:
        raise ScientificActivationError("activation preflight is stale")
    allowed_keys = set(required) | {"scale_set_id", "confirmed_at"}
    if set(value) != allowed_keys:
        raise ScientificActivationError("activation preflight keys drift")
    return value, raw


def activate(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    authority_path: pathlib.Path,
    preflight_path: pathlib.Path,
    systemd: Systemd | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise ScientificActivationError("scientific activation requires root")
    systemd = systemd or RealSystemd()
    repo_root = _exact_repo(repo_root, expected_head)
    reconciler.verify_installed(BASE_MANIFEST)

    inactive_receipt_raw = ACTIVE_RECEIPT.read_bytes()
    inactive_receipt = _load(ACTIVE_RECEIPT)
    if inactive_receipt.get("phase") != "INSTALLED_INACTIVE":
        raise ScientificActivationError("scientific effective generation is not inactive")
    if inactive_receipt.get("source_head") != expected_head:
        raise ScientificActivationError("scientific effective generation source head mismatch")

    preflight, preflight_raw = _validate_preflight(preflight_path)
    expected_authority = {
        "source_head": expected_head,
        "scientific_active_receipt_sha256": _sha(inactive_receipt_raw),
        "preflight_confirmation_sha256": _sha(preflight_raw),
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "target_scale_set_name": TARGET_SCALE_SET,
        "trusted_workflow_blob_sha": WORKFLOW_BLOB,
        "runtime_manifest_identity_sha256": RUNTIME_MANIFEST,
        "scientific_data_tree_digest_sha256": DATA_DIGEST,
    }
    authority, authority_raw = _load_authority(
        authority_path,
        operation="ACTIVATE_PADATASET_SCIENTIFIC_V3",
        expected=expected_authority,
    )

    target_before = systemd.show(TARGET_CONTROLLER_UNIT)
    if target_before.get("ActiveState") in {"active", "activating", "reloading"}:
        raise ScientificActivationError("scientific target controller is already active")
    if target_before.get("UnitFileState") == "enabled":
        raise ScientificActivationError("scientific target controller is already enabled")

    root_policy = _load(ROOT_POLICY)
    existing_ids = sorted(set(root_policy["runner_classes"]) - {TARGET_CLASS})
    existing_before = _controller_snapshot(systemd, existing_ids)
    _require_provisioner_active(systemd)
    _require_provisioner_socket()

    overlay = _load(DEPLOYMENT_OVERLAY)
    target_state = overlay.get("classes", {}).get(TARGET_CLASS)
    route_state = overlay.get("routes", {}).get(TARGET_ROUTE)
    if (
        not isinstance(target_state, dict)
        or target_state.get("install_state") != "INSTALLED"
        or target_state.get("controller_state") != "INACTIVE"
        or not isinstance(route_state, dict)
        or route_state.get("admission_state") != "DISABLED"
    ):
        raise ScientificActivationError("scientific inactive overlay precondition failed")

    active_overlay = copy.deepcopy(overlay)
    active_overlay["classes"][TARGET_CLASS]["controller_state"] = "ACTIVE"
    active_overlay["routes"][TARGET_ROUTE]["admission_state"] = "ENABLED"
    active_overlay["routes"][TARGET_ROUTE]["source"] = (
        "PADataset scientific additive activation accepted"
    )
    active_overlay_raw = _canonical(active_overlay)

    active_receipt = copy.deepcopy(inactive_receipt)
    active_receipt["phase"] = "ACTIVE"
    active_receipt["managed_artifact_overrides"][str(DEPLOYMENT_OVERLAY)][
        "sha256"
    ] = _sha(active_overlay_raw)
    active_receipt["activation_authorization_id"] = authority["authorization_id"]
    active_receipt["activation_preflight_sha256"] = _sha(preflight_raw)
    active_receipt["scale_set_id"] = preflight["scale_set_id"]

    _ensure_private_dir(TRANSACTION_ROOT)
    _ensure_private_dir(AUTHORITY_ROOT)
    tx_id = str(uuid.uuid4())
    tx_dir = TRANSACTION_ROOT / f"activate-{tx_id}"
    _ensure_private_dir(tx_dir)
    backups = _backup_paths(tx_dir, [DEPLOYMENT_OVERLAY, ACTIVE_RECEIPT])
    tx_receipt = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_SCIENTIFIC_ACTIVATION",
        "phase": "PREPARED",
        "source_head": expected_head,
        "target_class_id": TARGET_CLASS,
        "target_route_key": TARGET_ROUTE,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": _sha(authority_raw),
        "preflight_confirmation_sha256": _sha(preflight_raw),
        "existing_controller_snapshot": existing_before,
        "backups": backups,
    }
    _atomic_json(tx_receipt, tx)
    _consume_authority(authority, authority_raw)

    target_started = False
    target_enabled = False
    try:
        _atomic_file(DEPLOYMENT_OVERLAY, active_overlay_raw, 0o644)
        _atomic_json(ACTIVE_RECEIPT, active_receipt)
        reconciler.verify_installed(BASE_MANIFEST)

        systemd.start(TARGET_CONTROLLER_UNIT)
        target_started = True
        target = systemd.show(TARGET_CONTROLLER_UNIT)
        if target.get("ActiveState") != "active" or target.get("SubState") != "running":
            raise ScientificActivationError("scientific target controller did not start")
        systemd.enable(TARGET_CONTROLLER_UNIT)
        target_enabled = True

        existing_after = _controller_snapshot(systemd, existing_ids)
        _require_controller_snapshot_preserved(existing_before, existing_after)
        _require_provisioner_active(systemd)
        _require_provisioner_socket()
        reconciler.verify_installed(BASE_MANIFEST)

        tx["phase"] = "COMMITTED_ACTIVE"
        tx["active_receipt_sha256"] = _sha_file(ACTIVE_RECEIPT)
        tx["target_controller_state"] = systemd.show(TARGET_CONTROLLER_UNIT)
        tx["existing_controller_snapshot_after"] = existing_after
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(tx_receipt, tx)
        return tx_receipt
    except BaseException as exc:
        if target_enabled:
            systemd.disable(TARGET_CONTROLLER_UNIT)
        if target_started:
            try:
                systemd.stop(TARGET_CONTROLLER_UNIT)
            except BaseException:
                pass
        try:
            _restore_paths(backups)
            reconciler.verify_installed(BASE_MANIFEST)
            tx["phase"] = "ROLLED_BACK_TO_INSTALLED_INACTIVE"
            tx["rollback_completed"] = True
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(tx_receipt, tx)
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
            raise ScientificActivationError(
                "--preflight-confirmation is only valid with --activate"
            )
        receipt = expand_inactive(
            repo_root=args.repo_root,
            expected_head=args.expected_head,
            authority_path=args.authorization_receipt,
        )
        print("PADATASET_SCIENTIFIC_V3_EXPAND_INACTIVE=PASS")
        print(f"TRANSACTION_RECEIPT={receipt}")
        return 0

    if args.preflight_confirmation is None:
        raise ScientificActivationError("--activate requires --preflight-confirmation")
    receipt = activate(
        repo_root=args.repo_root,
        expected_head=args.expected_head,
        authority_path=args.authorization_receipt,
        preflight_path=args.preflight_confirmation,
    )
    print("PADATASET_SCIENTIFIC_V3_ACTIVATE=PASS")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScientificActivationError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
