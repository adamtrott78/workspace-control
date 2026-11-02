#!/usr/bin/env python3
"""Fail-closed Lambda CI v3 production-generation cutover transaction.

This module has two roles:
1. deterministically render the exact three accepted production workflow
   retargets plus controller policies and deployment overlays; and
2. execute the root-only host side of a production generation cutover.

It never edits GitHub itself.  The live operator must prove exact default-branch
workflow blobs before activation and exact legacy blobs before rollback.  The
root transaction never infers authority from model output or repository state:
a fresh root-owned one-shot authorization receipt is consumed before v2 is
quiesced.

Accepted production scope is intentionally frozen to:
- workspace-control-control-small-v1
- padataset-cpu-public-v1
- padataset-gpu-single-public-v1

Research CPU remains inactive.  Every Research GPU-derived class remains
inactive and inherited-contained.
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
from typing import Any, Protocol

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_migration_transaction as migration
import lambda_ci_v3_reconciler as reconciler


ROOT = pathlib.Path(__file__).resolve().parents[1]
V3_CONFIG_ROOT = pathlib.Path("/etc/workspace-ci/v3")
V3_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3")
MIGRATION_ROOT = V3_STATE_ROOT / "migration"
AUTHORITY_ROOT = V3_STATE_ROOT / "migration-authority"
PRODUCTION_OVERRIDE = V3_STATE_ROOT / "production-cutover" / "active.json"
BASE_MANIFEST = V3_CONFIG_ROOT / "install-manifest.json"
PROVISIONER_STATE = V3_STATE_ROOT / "provisioner"
CONTROLLER_STATE_ROOT = V3_STATE_ROOT / "controller" / "state"
AUTHORITY_MAX_LIFETIME_SECONDS = 30 * 60
TERMINAL_CONTROLLER_STATES = {"COMPLETED", "FAILED", "CANCELED"}

ALL_CLASSES = (
    "workspace-control-control-small-v1",
    "padataset-cpu-public-v1",
    "padataset-gpu-single-public-v1",
    "research-cpu-public-v1",
    "research-gpu-single-public-v1",
    "research-gpu-single-runtime-v1",
    "research-model-single-offline-v1",
    "research-model-dual-offline-v1",
    "research-model-dual-public-v1",
)
ACCEPTED_CLASSES = (
    "workspace-control-control-small-v1",
    "padataset-cpu-public-v1",
    "padataset-gpu-single-public-v1",
)
ACCEPTED_V3_UNITS = tuple(
    f"workspace-ci-v3-controller@{class_id}.service"
    for class_id in ACCEPTED_CLASSES
)
ROOT_UNITS = (
    migration.V3_RECONCILER_UNIT,
    migration.V3_PROVISIONER_UNIT,
)

ROUTES: dict[str, dict[str, str]] = {
    "workspace-control:control-validation": {
        "project_id": "workspace-control",
        "route_id": "control-validation",
        "repository": "adamtrott78/workspace-control",
        "path": ".github/workflows/lambda-ci-workspace-control-validation.yml",
        "legacy_scale_set_name": "lambda-workspace-control",
        "target_scale_set_name": "lambda-workspace-control-control-small",
        "runner_class_id": "workspace-control-control-small-v1",
        "legacy_controller_key": "workspace-control-cpu",
    },
    "padataset:cpu-ci": {
        "project_id": "padataset",
        "route_id": "cpu-ci",
        "repository": "adamtrott78/PADataset",
        "path": ".github/workflows/lambda-ci-cpu.yml",
        "legacy_scale_set_name": "lambda-padataset",
        "target_scale_set_name": "lambda-padataset-cpu-public",
        "runner_class_id": "padataset-cpu-public-v1",
        "legacy_controller_key": "padataset-cpu",
    },
    "padataset:gpu-ci": {
        "project_id": "padataset",
        "route_id": "gpu-ci",
        "repository": "adamtrott78/PADataset",
        "path": ".github/workflows/lambda-ci-gpu.yml",
        "legacy_scale_set_name": "lambda-padataset-gpu",
        "target_scale_set_name": "lambda-padataset-gpu-single-public",
        "runner_class_id": "padataset-gpu-single-public-v1",
        "legacy_controller_key": "padataset-gpu",
    },
}


class CutoverError(RuntimeError):
    pass


class Systemd(Protocol):
    def active(self, unit: str) -> bool: ...
    def enabled(self, unit: str) -> bool: ...
    def start(self, unit: str) -> None: ...
    def stop(self, unit: str) -> None: ...
    def enable(self, unit: str) -> None: ...
    def disable(self, unit: str) -> None: ...
    def list_units(self) -> list[str]: ...


class RealSystemd:
    def _run(
        self,
        argv: list[str],
        *,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and proc.returncode != 0:
            raise CutoverError(
                f"command failed rc={proc.returncode}: {' '.join(argv)}: "
                f"{proc.stderr.strip()[:512]}"
            )
        return proc

    def active(self, unit: str) -> bool:
        return self._run(
            ["systemctl", "is-active", "--quiet", unit],
            check=False,
        ).returncode == 0

    def enabled(self, unit: str) -> bool:
        return self._run(
            ["systemctl", "is-enabled", "--quiet", unit],
            check=False,
        ).returncode == 0

    def start(self, unit: str) -> None:
        self._run(["systemctl", "start", unit])

    def stop(self, unit: str) -> None:
        self._run(["systemctl", "stop", unit])

    def enable(self, unit: str) -> None:
        self._run(["systemctl", "enable", unit])

    def disable(self, unit: str) -> None:
        self._run(["systemctl", "disable", unit])

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
        return [
            line.split()[0]
            for line in proc.stdout.splitlines()
            if line.split()
        ]


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CutoverError(f"{path}: expected JSON object")
    return value


def _ensure_private_dir(path: pathlib.Path) -> None:
    if path.exists():
        st = path.stat()
        if not stat.S_ISDIR(st.st_mode):
            raise CutoverError(f"private state path is not a directory: {path}")
        if st.st_uid != os.geteuid() or st.st_gid != os.getegid():
            raise CutoverError(f"private state ownership invalid: {path}")
        if stat.S_IMODE(st.st_mode) != 0o700:
            raise CutoverError(f"private state mode invalid: {path}")
        return
    path.mkdir(parents=True, mode=0o700)
    os.chmod(path, 0o700)


def _atomic_write(path: pathlib.Path, raw: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = pathlib.Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
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


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _retarget_workflow(
    raw: bytes,
    *,
    legacy_scale_set_name: str,
    target_scale_set_name: str,
) -> bytes:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CutoverError("workflow is not UTF-8") from exc
    pattern = re.compile(
        rf"(?m)^(?P<indent>[ \t]+)runs-on:[ \t]+{re.escape(legacy_scale_set_name)}[ \t]*$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise CutoverError(
            f"expected exactly one runs-on {legacy_scale_set_name!r}, got {len(matches)}"
        )
    if re.search(
        rf"(?m)^[ \t]+runs-on:[ \t]+{re.escape(target_scale_set_name)}[ \t]*$",
        text,
    ):
        raise CutoverError("target scale set already present in workflow")
    rendered = pattern.sub(
        lambda match: (
            f"{match.group('indent')}runs-on: {target_scale_set_name}"
        ),
        text,
        count=1,
    )
    if legacy_scale_set_name == "lambda-workspace-control":
        old_go = (
            "          (\n"
            "            cd controller/lambda-ci-controller\n"
            "            go test -mod=mod ./...\n"
            "          )\n"
        )
        if old_go in rendered:
            pinned_go = (
                "          go_archive=\"$RUNNER_TEMP/go1.26.3.linux-amd64.tar.gz\"\n"
                "          curl -fsSL --retry 3 -o \"$go_archive\" \\\n"
                "            \"https://go.dev/dl/go1.26.3.linux-amd64.tar.gz\"\n"
                "          printf '%s  %s\\n' \\\n"
                "            '2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556' \\\n"
                "            \"$go_archive\" | sha256sum -c -\n"
                "          tar -C \"$RUNNER_TEMP\" -xzf \"$go_archive\"\n"
                "          [[ \"$(\"$RUNNER_TEMP/go/bin/go\" env GOVERSION)\" == \"go1.26.3\" ]]\n"
                "          (\n"
                "            cd controller/lambda-ci-controller\n"
                "            \"$RUNNER_TEMP/go/bin/go\" test -mod=mod ./...\n"
                "          )\n"
            )
            rendered = rendered.replace(old_go, pinned_go, 1)
    if rendered == text:
        raise CutoverError("workflow retarget produced no byte change")
    return rendered.encode("utf-8")


def _route_evidence(
    data: dict[str, Any],
    project_id: str,
    route_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in data["workflow_evidence"]["entries"]
        if item.get("project_id") == project_id
        and item.get("route_id") == route_id
    ]
    if len(matches) != 1:
        raise CutoverError(
            f"workflow evidence not unique for {project_id}:{route_id}"
        )
    return matches[0]


def build_generation(
    repo_root: pathlib.Path,
    workflow_raw: dict[str, bytes],
    live_overlay: dict[str, Any],
    *,
    source_head: str,
) -> dict[str, Any]:
    if set(workflow_raw) != set(ROUTES):
        raise CutoverError("production workflow input set drift")
    if re.fullmatch(r"[0-9a-f]{40}", source_head) is None:
        raise CutoverError("source_head must be a full lowercase Git SHA")

    data = copy.deepcopy(compiler.load_inputs(repo_root))
    base_compiled = compiler.compile_from_inputs(copy.deepcopy(data))
    bindings: dict[str, dict[str, str]] = {}
    rendered: dict[str, bytes] = {}

    for route_key, spec in ROUTES.items():
        project = data["catalog"]["projects"][spec["project_id"]]
        route = project["routes"][spec["route_id"]]
        trusted = route["trusted_workflow"]
        evidence = _route_evidence(
            data,
            spec["project_id"],
            spec["route_id"],
        )
        raw = workflow_raw[route_key]
        old_blob = _git_blob_sha(raw)
        if trusted["blob_sha"] != old_blob:
            raise CutoverError(
                f"{route_key}: default-branch workflow blob differs from compiled base"
            )
        if evidence["workflow_blob_sha"] != old_blob:
            raise CutoverError(
                f"{route_key}: workflow evidence blob differs from compiled base"
            )
        if evidence["current_scale_set_name"] != spec["legacy_scale_set_name"]:
            raise CutoverError(f"{route_key}: legacy scale-set evidence drift")
        if evidence["target_scale_set_name"] != spec["target_scale_set_name"]:
            raise CutoverError(f"{route_key}: target scale-set evidence drift")
        if (
            base_compiled["controller_projections"][spec["runner_class_id"]][
                "scale_set_name"
            ]
            != spec["target_scale_set_name"]
        ):
            raise CutoverError(f"{route_key}: compiled target scale set drift")

        new_raw = _retarget_workflow(
            raw,
            legacy_scale_set_name=spec["legacy_scale_set_name"],
            target_scale_set_name=spec["target_scale_set_name"],
        )
        new_blob = _git_blob_sha(new_raw)
        trusted["blob_sha"] = new_blob
        evidence["workflow_blob_sha"] = new_blob
        rendered[route_key] = new_raw
        bindings[route_key] = {
            "repository": spec["repository"],
            "path": spec["path"],
            "old_blob_sha": old_blob,
            "new_blob_sha": new_blob,
            "target_scale_set_name": spec["target_scale_set_name"],
        }

    compiled = compiler.compile_from_inputs(data)
    if (
        compiled["root_projection"]["root_policy_sha256"]
        != base_compiled["root_projection"]["root_policy_sha256"]
    ):
        raise CutoverError("production workflow retarget changed root authority")

    policies = {
        class_id: compiled["controller_projections"][class_id]
        for class_id in ACCEPTED_CLASSES
    }
    for class_id, policy in policies.items():
        if len(policy["trusted_workflows"]) != 1:
            raise CutoverError(
                f"{class_id}: accepted production class must trust exactly one workflow"
            )
        route_key = next(
            key
            for key, spec in ROUTES.items()
            if spec["runner_class_id"] == class_id
        )
        if (
            policy["trusted_workflows"][0]["blob_sha"]
            != bindings[route_key]["new_blob_sha"]
        ):
            raise CutoverError(
                f"{class_id}: compiled policy did not bind retargeted workflow"
            )

    active_overlay = build_overlay(
        live_overlay,
        compiled["catalog_generation_sha256"],
        committed=False,
    )
    committed_overlay = build_overlay(
        live_overlay,
        compiled["catalog_generation_sha256"],
        committed=True,
    )

    material = {
        "source_head": source_head,
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "accepted_runner_class_ids": list(ACCEPTED_CLASSES),
        "workflow_bindings": bindings,
        "controller_policy_sha256": {
            class_id: policy["controller_policy_sha256"]
            for class_id, policy in policies.items()
        },
        "active_overlay_sha256": _sha256(_canonical(active_overlay)),
        "committed_overlay_sha256": _sha256(_canonical(committed_overlay)),
    }
    generation_sha = _sha256(_canonical(material))
    manifest = {
        "schema_version": 1,
        "mode": "V3_PRODUCTION_GENERATION",
        "production_generation_sha256": generation_sha,
        **material,
    }
    return {
        "manifest": manifest,
        "rendered_workflows": rendered,
        "controller_policies": policies,
        "active_overlay": active_overlay,
        "committed_overlay": committed_overlay,
    }


def build_overlay(
    live_overlay: dict[str, Any],
    catalog_generation_sha256: str,
    *,
    committed: bool,
) -> dict[str, Any]:
    overlay = copy.deepcopy(live_overlay)
    if overlay.get("schema_version") != 1:
        raise CutoverError("installed deployment overlay schema invalid")
    classes = overlay.get("classes")
    routes = overlay.get("routes")
    legacy = overlay.get("legacy")
    if not isinstance(classes, dict) or set(classes) != set(ALL_CLASSES):
        raise CutoverError("installed deployment overlay class set drift")
    if not isinstance(routes, dict) or set(ROUTES) - set(routes):
        raise CutoverError("installed deployment overlay route set drift")
    if not isinstance(legacy, dict):
        raise CutoverError("installed deployment overlay legacy state missing")
    for class_id, state in classes.items():
        if state.get("install_state") != "INSTALLED":
            raise CutoverError(
                f"{class_id}: production cutover requires INSTALLED class"
            )
        if class_id in ACCEPTED_CLASSES:
            state["controller_state"] = "ACTIVE"
        else:
            state["controller_state"] = "INACTIVE"
    for route_key, state in routes.items():
        state["admission_state"] = (
            "ENABLED" if route_key in ROUTES else "DISABLED"
        )
        if route_key in ROUTES:
            state["source"] = (
                "accepted v3 production generation cutover"
            )
    controllers = legacy.get("controllers")
    scale_sets = legacy.get("scale_sets")
    if not isinstance(controllers, dict) or not isinstance(scale_sets, dict):
        raise CutoverError("installed deployment overlay legacy maps missing")
    for spec in ROUTES.values():
        controller_key = spec["legacy_controller_key"]
        scale_set = spec["legacy_scale_set_name"]
        if controller_key not in controllers or scale_set not in scale_sets:
            raise CutoverError("legacy deployment overlay key drift")
        controllers[controller_key] = (
            "RETIRED" if committed else "PRESENT_INACTIVE"
        )
        scale_sets[scale_set] = (
            "RETIRED" if committed else "DRAINING"
        )
    # Research lanes are never promoted by this cutover.
    if controllers.get("research-engine-gpu") != "PRESENT_INACTIVE":
        raise CutoverError("Research GPU controller containment drift")
    for key in (
        "lambda-research-engine",
        "lambda-research-engine-gpu",
    ):
        if scale_sets.get(key) != "PRESENT":
            raise CutoverError(f"Research legacy scale-set drift: {key}")

    overlay["catalog_generation_sha256"] = catalog_generation_sha256
    overlay["status_note"] = (
        "Production v3 generation committed; legacy accepted scale sets "
        "retired but preserved for rollback."
        if committed
        else
        "Production v3 generation active under validation; accepted legacy "
        "scale sets are draining."
    )
    return overlay


def write_generation(
    result: dict[str, Any],
    output: pathlib.Path,
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    _atomic_write(
        output / "manifest.json",
        _canonical(result["manifest"]),
        mode=0o644,
    )
    controller_root = output / "controllers"
    controller_root.mkdir(mode=0o755)
    for class_id, policy in result["controller_policies"].items():
        _atomic_write(
            controller_root / f"{class_id}.json",
            _canonical(policy),
            mode=0o644,
        )
    _atomic_write(
        output / "deployment-overlay-active.json",
        _canonical(result["active_overlay"]),
        mode=0o644,
    )
    _atomic_write(
        output / "deployment-overlay-committed.json",
        _canonical(result["committed_overlay"]),
        mode=0o644,
    )
    for route_key, raw in result["rendered_workflows"].items():
        spec = ROUTES[route_key]
        destination = (
            output
            / "repositories"
            / spec["repository"]
            / spec["path"]
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(destination, raw, mode=0o644)


def _validate_private_dir(path: pathlib.Path, label: str) -> None:
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise CutoverError(f"{label} missing") from exc
    if not stat.S_ISDIR(st.st_mode):
        raise CutoverError(f"{label} is not a directory")
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
        raise CutoverError(f"{label} must be root-owned mode 0700")


def _validate_root_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise CutoverError(f"{label} missing") from exc
    if st.st_uid != os.geteuid() or st.st_gid != os.getegid():
        raise CutoverError(f"{label} ownership invalid")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise CutoverError(f"{label} must be mode 0600")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CutoverError(f"{label} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise CutoverError(f"{label} must be an object")
    return value, raw


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CutoverError(f"authority {field} invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CutoverError(f"authority {field} invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CutoverError(f"authority {field} must be timezone-aware")
    return parsed


def validate_authority(
    receipt: dict[str, Any],
    manifest: dict[str, Any],
    *,
    now: datetime | None = None,
) -> None:
    required_keys = {
        "schema_version",
        "authority",
        "operation",
        "authorization_id",
        "source_head",
        "production_generation_sha256",
        "root_policy_sha256",
        "accepted_runner_class_ids",
        "workflow_blob_shas",
        "controller_policy_sha256",
        "issued_at",
        "expires_at",
    }
    if set(receipt) != required_keys:
        raise CutoverError("production authority receipt keys drift")
    if receipt["schema_version"] != 1:
        raise CutoverError("production authority schema invalid")
    if receipt["authority"] != "workspace-control-operator":
        raise CutoverError("production authority identity invalid")
    if receipt["operation"] != "CUTOVER_V3_PRODUCTION_GENERATION":
        raise CutoverError("production authority operation invalid")
    try:
        uuid.UUID(receipt["authorization_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise CutoverError("production authority authorization_id invalid") from exc
    for key in ("source_head", "production_generation_sha256", "root_policy_sha256"):
        if receipt[key] != manifest[key]:
            raise CutoverError(f"production authority {key} mismatch")
    if receipt["accepted_runner_class_ids"] != list(ACCEPTED_CLASSES):
        raise CutoverError("production authority class set mismatch")
    expected_workflows = {
        key: value["new_blob_sha"]
        for key, value in manifest["workflow_bindings"].items()
    }
    if receipt["workflow_blob_shas"] != expected_workflows:
        raise CutoverError("production authority workflow blobs mismatch")
    if receipt["controller_policy_sha256"] != manifest["controller_policy_sha256"]:
        raise CutoverError("production authority controller policy digests mismatch")

    issued = _parse_time(receipt["issued_at"], "issued_at")
    expires = _parse_time(receipt["expires_at"], "expires_at")
    if expires <= issued:
        raise CutoverError("production authority expiry must follow issuance")
    if (expires - issued).total_seconds() > AUTHORITY_MAX_LIFETIME_SECONDS:
        raise CutoverError("production authority lifetime exceeds maximum")
    current = now or datetime.now(timezone.utc)
    if current < issued:
        raise CutoverError("production authority is not yet valid")
    if current > expires:
        raise CutoverError("production authority expired")


def _consume_authority(
    receipt: dict[str, Any],
    raw: bytes,
    *,
    authority_root: pathlib.Path,
) -> pathlib.Path:
    _validate_private_dir(authority_root, "production authority root")
    marker = authority_root / f"{receipt['authorization_id']}.json"
    payload = {
        "schema_version": 1,
        "operation": receipt["operation"],
        "authorization_id": receipt["authorization_id"],
        "production_generation_sha256": receipt[
            "production_generation_sha256"
        ],
        "authorization_receipt_sha256": _sha256(raw),
        "consumed_at": _utcnow(),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(marker, flags, 0o600)
    except FileExistsError as exc:
        raise CutoverError("production authority already consumed") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_canonical(payload))
            handle.flush()
            os.fsync(handle.fileno())
        dir_fd = os.open(authority_root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        # A created marker is never removed: uncertain consumption fails closed.
        raise
    return marker


def _assert_controller_ledgers_terminal(
    controller_state_root: pathlib.Path,
    root_policy: dict[str, Any],
) -> None:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict) or set(classes) != set(ALL_CLASSES):
        raise CutoverError("installed root policy class set invalid")
    if not controller_state_root.exists():
        return
    if controller_state_root.is_symlink() or not controller_state_root.is_dir():
        raise CutoverError("controller state root must be a real directory")
    for class_id in ALL_CLASSES:
        class_root = controller_state_root / class_id
        if not class_root.exists():
            continue
        if class_root.is_symlink() or not class_root.is_dir():
            raise CutoverError(
                f"{class_id}: controller state path must be a real directory"
            )
        for path in sorted(class_root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise CutoverError(
                    f"{class_id}: controller ledger entry must be a regular file"
                )
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CutoverError(
                    f"{class_id}: controller ledger entry unreadable: {path.name}"
                ) from exc
            if not isinstance(record, dict) or record.get("schema_version") != 1:
                raise CutoverError(
                    f"{class_id}: controller ledger entry schema invalid: {path.name}"
                )
            request_id = record.get("runner_request_id")
            if not isinstance(request_id, int) or request_id <= 0:
                raise CutoverError(
                    f"{class_id}: controller ledger identity invalid: {path.name}"
                )
            digest = record.get("controller_policy_sha256")
            if (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise CutoverError(
                    f"{class_id}: controller ledger policy binding invalid: {path.name}"
                )
            state = record.get("state")
            if state not in TERMINAL_CONTROLLER_STATES:
                raise CutoverError(
                    f"{class_id}: nonterminal controller ledger blocks production "
                    f"cutover runner_request_id={request_id} state={state}"
                )


def _assert_no_in_progress_transaction(
    transaction_root: pathlib.Path,
) -> None:
    terminal = {
        "ROLLED_BACK_LEGACY_RESTORED",
        "COMMITTED_V3_PRODUCTION",
    }
    active: list[str] = []
    for path in sorted(transaction_root.glob("*/transaction.json")):
        try:
            value = _load(path)
        except (OSError, json.JSONDecodeError, CutoverError):
            active.append(f"{path}:UNREADABLE")
            continue
        phase = value.get("phase")
        if phase not in terminal:
            active.append(f"{path}:{phase}")
    if active:
        raise CutoverError(
            "nonterminal migration transaction already exists: "
            + ", ".join(active)
        )


def _assert_pre_cutover_boot_state(
    systemd: Systemd,
    root_policy: dict[str, Any],
) -> None:
    for unit in migration.v3_controller_units(root_policy):
        if systemd.enabled(unit):
            raise CutoverError(
                f"v3 class controller is boot-enabled before cutover: {unit}"
            )
    for unit in ROOT_UNITS:
        if systemd.enabled(unit):
            raise CutoverError(
                f"v3 root service is boot-enabled before cutover: {unit}"
            )
    if systemd.enabled(migration.RESEARCH_GPU_V2_UNIT):
        raise CutoverError(
            "legacy Research GPU containment is boot-enabled"
        )


def _assert_root_and_containment(
    systemd: Systemd,
    root_policy: dict[str, Any],
    *,
    accepted_active: bool,
) -> None:
    for unit in ROOT_UNITS:
        if not systemd.active(unit):
            raise CutoverError(f"v3 root service is not active: {unit}")
    migration._assert_research_gpu_containment(systemd)
    v3_units = migration.v3_controller_units(root_policy)
    active = sorted(unit for unit in v3_units if systemd.active(unit))
    expected = sorted(ACCEPTED_V3_UNITS if accepted_active else ())
    if active != expected:
        raise CutoverError(
            f"unexpected v3 controller active set: {active} != {expected}"
        )


def _generation_artifacts(
    generation_dir: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, bytes], bytes, bytes]:
    manifest = _load(generation_dir / "manifest.json")
    if manifest.get("mode") != "V3_PRODUCTION_GENERATION":
        raise CutoverError("production generation manifest mode invalid")
    if manifest.get("accepted_runner_class_ids") != list(ACCEPTED_CLASSES):
        raise CutoverError("production generation accepted class set drift")
    policies: dict[str, bytes] = {}
    for class_id in ACCEPTED_CLASSES:
        path = generation_dir / "controllers" / f"{class_id}.json"
        raw = path.read_bytes()
        policy = json.loads(raw)
        if policy.get("runner_class_id") != class_id:
            raise CutoverError(f"{class_id}: generation policy identity mismatch")
        if (
            policy.get("controller_policy_sha256")
            != manifest["controller_policy_sha256"][class_id]
        ):
            raise CutoverError(f"{class_id}: generation policy digest mismatch")
        policies[class_id] = raw
    active_overlay = (
        generation_dir / "deployment-overlay-active.json"
    ).read_bytes()
    committed_overlay = (
        generation_dir / "deployment-overlay-committed.json"
    ).read_bytes()
    if _sha256(active_overlay) != manifest["active_overlay_sha256"]:
        raise CutoverError("active deployment overlay digest mismatch")
    if _sha256(committed_overlay) != manifest["committed_overlay_sha256"]:
        raise CutoverError("committed deployment overlay digest mismatch")
    return manifest, policies, active_overlay, committed_overlay


def _persist(path: pathlib.Path, receipt: dict[str, Any]) -> None:
    receipt["updated_at"] = _utcnow()
    _atomic_write(path, _canonical(receipt), mode=0o600)


def _backup_file(
    transaction_dir: pathlib.Path,
    source: pathlib.Path,
    name: str,
) -> dict[str, str]:
    raw = source.read_bytes()
    backup = transaction_dir / "backups" / name
    backup.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(backup, raw, mode=0o600)
    return {
        "path": str(source),
        "backup_path": str(backup),
        "sha256": _sha256(raw),
    }


def _restore_backup(entry: dict[str, str], *, mode: int = 0o644) -> None:
    raw = pathlib.Path(entry["backup_path"]).read_bytes()
    if _sha256(raw) != entry["sha256"]:
        raise CutoverError(f"backup digest drift: {entry['backup_path']}")
    _atomic_write(pathlib.Path(entry["path"]), raw, mode=mode)


def _artifact_override(
    manifest: dict[str, Any],
    policies: dict[str, bytes],
    overlay_raw: bytes,
    *,
    base_manifest_raw: bytes,
    base_manifest: dict[str, Any],
) -> dict[str, Any]:
    overrides = {
        str(V3_CONFIG_ROOT / "deployment-overlay.json"): _sha256(overlay_raw),
    }
    for class_id, raw in policies.items():
        overrides[
            str(V3_CONFIG_ROOT / "controllers" / f"{class_id}.json")
        ] = _sha256(raw)
    return {
        "schema_version": 1,
        "mode": "V3_PRODUCTION_CUTOVER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": base_manifest["source_head"],
        "base_install_manifest_sha256": _sha256(base_manifest_raw),
        "root_policy_sha256": base_manifest["root_policy_sha256"],
        "production_generation_sha256": manifest[
            "production_generation_sha256"
        ],
        "accepted_runner_class_ids": list(ACCEPTED_CLASSES),
        "workflow_bindings": manifest["workflow_bindings"],
        "managed_artifact_overrides": overrides,
        "research_gpu_containment_preserved": True,
        "non_selected_classes_inactive": True,
    }


def prepare(
    *,
    systemd: Systemd,
    repo_root: pathlib.Path,
    generation_dir: pathlib.Path,
    authorization_receipt: pathlib.Path,
    transaction_root: pathlib.Path = MIGRATION_ROOT,
    authority_root: pathlib.Path = AUTHORITY_ROOT,
    provisioner_state_root: pathlib.Path = PROVISIONER_STATE,
    controller_state_root: pathlib.Path = CONTROLLER_STATE_ROOT,
) -> pathlib.Path:
    manifest, policies, _, _ = _generation_artifacts(generation_dir)
    authority, authority_raw = _validate_root_json(
        authorization_receipt,
        "production authority receipt",
    )
    validate_authority(authority, manifest)

    installed_root = _load(V3_CONFIG_ROOT / "root-policy.json")
    if installed_root["root_policy_sha256"] != manifest["root_policy_sha256"]:
        raise CutoverError("installed root policy differs from production generation")
    _assert_root_and_containment(
        systemd,
        installed_root,
        accepted_active=False,
    )
    migration._assert_generation_drained(
        systemd,
        registry=compiler.load_inputs(repo_root)["registry"],
        root_policy=installed_root,
        require_legacy_empty=True,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )
    _assert_controller_ledgers_terminal(
        controller_state_root,
        installed_root,
    )
    _validate_private_dir(transaction_root, "production transaction root")
    _assert_no_in_progress_transaction(transaction_root)
    _assert_pre_cutover_boot_state(systemd, installed_root)
    if PRODUCTION_OVERRIDE.exists():
        raise CutoverError("production cutover override already exists")
    marker = _consume_authority(
        authority,
        authority_raw,
        authority_root=authority_root,
    )

    transaction_id = str(uuid.uuid4())
    tx_dir = transaction_root / transaction_id
    tx_dir.mkdir(mode=0o700)
    receipt_path = tx_dir / "transaction.json"

    backups = {
        "deployment_overlay": _backup_file(
            tx_dir,
            V3_CONFIG_ROOT / "deployment-overlay.json",
            "deployment-overlay.json",
        ),
        "controller_policies": {},
    }
    for class_id in ACCEPTED_CLASSES:
        backups["controller_policies"][class_id] = _backup_file(
            tx_dir,
            V3_CONFIG_ROOT / "controllers" / f"{class_id}.json",
            f"{class_id}.json",
        )

    frozen = tx_dir / "generation"
    frozen.mkdir(mode=0o700)
    _atomic_write(
        frozen / "manifest.json",
        _canonical(manifest),
        mode=0o600,
    )
    for class_id, raw in policies.items():
        _atomic_write(
            frozen / f"{class_id}.json",
            raw,
            mode=0o600,
        )
    for name in (
        "deployment-overlay-active.json",
        "deployment-overlay-committed.json",
    ):
        _atomic_write(
            frozen / name,
            (generation_dir / name).read_bytes(),
            mode=0o600,
        )

    registry = compiler.load_inputs(repo_root)["registry"]
    v2_units = migration.v2_controller_units(registry)
    v3_units = migration.v3_controller_units(installed_root)
    prestate = {
        "v2_active": {unit: systemd.active(unit) for unit in v2_units},
        "v2_enabled": {unit: systemd.enabled(unit) for unit in v2_units},
        "v3_enabled": {unit: systemd.enabled(unit) for unit in v3_units},
        "root_enabled": {unit: systemd.enabled(unit) for unit in ROOT_UNITS},
    }
    if prestate["v2_active"].get(migration.RESEARCH_GPU_V2_UNIT):
        raise CutoverError("Research GPU containment drifted during prestate")

    receipt = {
        "schema_version": 1,
        "mode": "V3_PRODUCTION_GENERATION_CUTOVER",
        "transaction_id": transaction_id,
        "authorization_id": authority["authorization_id"],
        "authorization_consumption_marker": str(marker),
        "authorization_receipt_sha256": _sha256(authority_raw),
        "production_generation_sha256": manifest[
            "production_generation_sha256"
        ],
        "source_head": manifest["source_head"],
        "root_policy_sha256": manifest["root_policy_sha256"],
        "accepted_runner_class_ids": list(ACCEPTED_CLASSES),
        "workflow_bindings": manifest["workflow_bindings"],
        "controller_policy_sha256": manifest["controller_policy_sha256"],
        "backups": backups,
        "prestate": prestate,
        "frozen_generation_dir": str(frozen),
        "workflow_mutation_confirmed": False,
        "production_validation_confirmed": False,
        "legacy_scale_sets_deleted": False,
        "research_gpu_containment_preserved": True,
        "phase": "PREPARED",
    }
    _persist(receipt_path, receipt)

    for unit in v2_units:
        if systemd.active(unit):
            systemd.stop(unit)
    if any(systemd.active(unit) for unit in v2_units):
        receipt["phase"] = "ROLLBACK_REQUIRED"
        _persist(receipt_path, receipt)
        raise CutoverError("v2 controller remained active after stop")
    migration._assert_research_gpu_containment(systemd)
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=installed_root,
        require_legacy_empty=True,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )
    receipt["phase"] = "V2_QUIESCED"
    _persist(receipt_path, receipt)
    return receipt_path


def _validate_workflow_confirmation(
    confirmation: dict[str, Any],
    receipt: dict[str, Any],
    *,
    rollback: bool,
) -> None:
    expected_mode = (
        "V3_PRODUCTION_WORKFLOW_ROLLBACK_CONFIRMED"
        if rollback
        else "V3_PRODUCTION_WORKFLOW_CUTOVER_CONFIRMED"
    )
    if confirmation.get("schema_version") != 1 or confirmation.get("mode") != expected_mode:
        raise CutoverError("workflow confirmation mode invalid")
    if (
        confirmation.get("production_generation_sha256")
        != receipt["production_generation_sha256"]
    ):
        raise CutoverError("workflow confirmation generation mismatch")
    bindings = confirmation.get("workflow_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(ROUTES):
        raise CutoverError("workflow confirmation route set invalid")
    for route_key, expected in receipt["workflow_bindings"].items():
        row = bindings[route_key]
        if not isinstance(row, dict):
            raise CutoverError(f"{route_key}: workflow confirmation invalid")
        wanted_blob = (
            expected["old_blob_sha"] if rollback else expected["new_blob_sha"]
        )
        if row.get("blob_sha") != wanted_blob:
            raise CutoverError(f"{route_key}: workflow confirmation blob mismatch")
        if row.get("repository") != expected["repository"]:
            raise CutoverError(f"{route_key}: workflow confirmation repository mismatch")
        if row.get("path") != expected["path"]:
            raise CutoverError(f"{route_key}: workflow confirmation path mismatch")
        commit_sha = row.get("commit_sha")
        if not isinstance(commit_sha, str) or re.fullmatch(r"[0-9a-f]{40}", commit_sha) is None:
            raise CutoverError(f"{route_key}: workflow confirmation commit invalid")


def activate(
    *,
    systemd: Systemd,
    repo_root: pathlib.Path,
    receipt_path: pathlib.Path,
    workflow_confirmation: pathlib.Path,
    provisioner_state_root: pathlib.Path = PROVISIONER_STATE,
) -> None:
    receipt = _load(receipt_path)
    if receipt.get("mode") != "V3_PRODUCTION_GENERATION_CUTOVER":
        raise CutoverError("production transaction mode invalid")
    if receipt.get("phase") != "V2_QUIESCED":
        raise CutoverError("production transaction is not ready for activation")
    confirmation, _ = _validate_root_json(
        workflow_confirmation,
        "production workflow confirmation",
    )
    _validate_workflow_confirmation(confirmation, receipt, rollback=False)

    installed_root = _load(V3_CONFIG_ROOT / "root-policy.json")
    registry = compiler.load_inputs(repo_root)["registry"]
    if any(systemd.active(unit) for unit in migration.v2_controller_units(registry)):
        raise CutoverError("v2 controller became active before v3 activation")
    _assert_root_and_containment(
        systemd,
        installed_root,
        accepted_active=False,
    )
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=installed_root,
        require_legacy_empty=True,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )

    frozen = pathlib.Path(receipt["frozen_generation_dir"])
    manifest = _load(frozen / "manifest.json")
    policies = {
        class_id: (frozen / f"{class_id}.json").read_bytes()
        for class_id in ACCEPTED_CLASSES
    }
    active_overlay = (frozen / "deployment-overlay-active.json").read_bytes()
    base_manifest, base_manifest_raw = (
        _load(BASE_MANIFEST),
        BASE_MANIFEST.read_bytes(),
    )

    try:
        for class_id, raw in policies.items():
            _atomic_write(
                V3_CONFIG_ROOT / "controllers" / f"{class_id}.json",
                raw,
                mode=0o644,
            )
        _atomic_write(
            V3_CONFIG_ROOT / "deployment-overlay.json",
            active_overlay,
            mode=0o644,
        )
        override = _artifact_override(
            manifest,
            policies,
            active_overlay,
            base_manifest_raw=base_manifest_raw,
            base_manifest=base_manifest,
        )
        _ensure_private_dir(PRODUCTION_OVERRIDE.parent)
        _atomic_write(PRODUCTION_OVERRIDE, _canonical(override), mode=0o600)
        reconciler.verify_installed(BASE_MANIFEST)

        for unit in ACCEPTED_V3_UNITS:
            systemd.start(unit)
        _assert_root_and_containment(
            systemd,
            installed_root,
            accepted_active=True,
        )
        if any(systemd.active(unit) for unit in migration.v2_controller_units(registry)):
            raise CutoverError("generation overlap detected after v3 activation")
        receipt["workflow_mutation_confirmed"] = True
        receipt["workflow_confirmation"] = confirmation
        receipt["phase"] = "V3_PRODUCTION_ACTIVE"
        _persist(receipt_path, receipt)
    except BaseException:
        receipt["phase"] = "ROLLBACK_REQUIRED"
        _persist(receipt_path, receipt)
        raise


def _validate_validation_confirmation(
    confirmation: dict[str, Any],
    receipt: dict[str, Any],
) -> None:
    if (
        confirmation.get("schema_version") != 1
        or confirmation.get("mode") != "V3_PRODUCTION_VALIDATION_CONFIRMED"
    ):
        raise CutoverError("production validation confirmation mode invalid")
    if (
        confirmation.get("production_generation_sha256")
        != receipt["production_generation_sha256"]
    ):
        raise CutoverError("production validation generation mismatch")
    routes = confirmation.get("routes")
    if not isinstance(routes, dict) or set(routes) != set(ROUTES):
        raise CutoverError("production validation route set invalid")
    for route_key, row in routes.items():
        if not isinstance(row, dict):
            raise CutoverError(f"{route_key}: validation result invalid")
        if row.get("conclusion") != "success":
            raise CutoverError(f"{route_key}: production validation did not succeed")
        expected_binding = receipt["workflow_bindings"][route_key]
        expected_route = ROUTES[route_key]
        if row.get("workflow_blob_sha") != expected_binding["new_blob_sha"]:
            raise CutoverError(
                f"{route_key}: validation workflow blob mismatch"
            )
        if row.get("runner_class_id") != expected_route["runner_class_id"]:
            raise CutoverError(
                f"{route_key}: validation runner class mismatch"
            )
        if row.get("scale_set_name") != expected_route["target_scale_set_name"]:
            raise CutoverError(
                f"{route_key}: validation scale set mismatch"
            )
        runner_name = row.get("runner_name")
        expected_prefix = expected_route["target_scale_set_name"] + "-"
        if not isinstance(runner_name, str) or not runner_name.startswith(
            expected_prefix
        ):
            raise CutoverError(
                f"{route_key}: validation runner identity mismatch"
            )
        for field in ("run_id", "job_id"):
            value = row.get(field)
            if not isinstance(value, int) or value <= 0:
                raise CutoverError(f"{route_key}: validation {field} invalid")


def commit(
    *,
    systemd: Systemd,
    repo_root: pathlib.Path,
    receipt_path: pathlib.Path,
    validation_confirmation: pathlib.Path,
    provisioner_state_root: pathlib.Path = PROVISIONER_STATE,
) -> None:
    receipt = _load(receipt_path)
    if receipt.get("phase") != "V3_PRODUCTION_ACTIVE":
        raise CutoverError("production transaction is not active")
    confirmation, _ = _validate_root_json(
        validation_confirmation,
        "production validation confirmation",
    )
    _validate_validation_confirmation(confirmation, receipt)

    installed_root = _load(V3_CONFIG_ROOT / "root-policy.json")
    registry = compiler.load_inputs(repo_root)["registry"]
    _assert_root_and_containment(
        systemd,
        installed_root,
        accepted_active=True,
    )
    if any(systemd.active(unit) for unit in migration.v2_controller_units(registry)):
        raise CutoverError("v2 controller active at production commit")
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=installed_root,
        require_legacy_empty=True,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )

    frozen = pathlib.Path(receipt["frozen_generation_dir"])
    manifest = _load(frozen / "manifest.json")
    policies = {
        class_id: (frozen / f"{class_id}.json").read_bytes()
        for class_id in ACCEPTED_CLASSES
    }
    committed_overlay = (
        frozen / "deployment-overlay-committed.json"
    ).read_bytes()
    base_manifest = _load(BASE_MANIFEST)
    base_manifest_raw = BASE_MANIFEST.read_bytes()

    # All v2 controllers remain stopped after generation cutover.  Accepted
    # legacy lanes are logically retired; Research CPU remains merely inactive
    # and separately gated, while Research GPU remains explicitly contained.
    for unit in migration.v2_controller_units(registry):
        systemd.disable(unit)
    if any(systemd.enabled(unit) for unit in migration.v2_controller_units(registry)):
        raise CutoverError("v2 controller remained boot-enabled at commit")
    for unit in ROOT_UNITS:
        systemd.enable(unit)
    for unit in ACCEPTED_V3_UNITS:
        systemd.enable(unit)
    for unit in migration.v3_controller_units(installed_root):
        if unit not in ACCEPTED_V3_UNITS and systemd.enabled(unit):
            raise CutoverError(
                f"non-selected v3 controller is boot-enabled: {unit}"
            )

    _atomic_write(
        V3_CONFIG_ROOT / "deployment-overlay.json",
        committed_overlay,
        mode=0o644,
    )
    override = _artifact_override(
        manifest,
        policies,
        committed_overlay,
        base_manifest_raw=base_manifest_raw,
        base_manifest=base_manifest,
    )
    _ensure_private_dir(PRODUCTION_OVERRIDE.parent)
    _atomic_write(PRODUCTION_OVERRIDE, _canonical(override), mode=0o600)
    reconciler.verify_installed(BASE_MANIFEST)

    _assert_root_and_containment(
        systemd,
        installed_root,
        accepted_active=True,
    )
    receipt["production_validation_confirmed"] = True
    receipt["validation_confirmation"] = confirmation
    receipt["legacy_scale_sets_state"] = "RETIRED_PRESERVED_FOR_ROLLBACK"
    receipt["phase"] = "COMMITTED_V3_PRODUCTION"
    _persist(receipt_path, receipt)


def rollback(
    *,
    systemd: Systemd,
    repo_root: pathlib.Path,
    receipt_path: pathlib.Path,
    workflow_rollback_confirmation: pathlib.Path,
    provisioner_state_root: pathlib.Path = PROVISIONER_STATE,
) -> None:
    receipt = _load(receipt_path)
    if receipt.get("mode") != "V3_PRODUCTION_GENERATION_CUTOVER":
        raise CutoverError("production transaction mode invalid")

    installed_root = _load(V3_CONFIG_ROOT / "root-policy.json")
    registry = compiler.load_inputs(repo_root)["registry"]
    v3_units = migration.v3_controller_units(installed_root)

    # Isolation precedes GitHub rollback confirmation.  If restoring the old
    # default-branch workflows is incomplete or ambiguous, stop v3 and leave
    # every project controller quiesced rather than continuing to execute a
    # partially retargeted routing generation.
    for unit in ACCEPTED_V3_UNITS:
        systemd.stop(unit)
    if any(systemd.active(unit) for unit in v3_units):
        raise CutoverError("v3 controller remained active during rollback")
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=installed_root,
        require_legacy_empty=True,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )
    receipt["phase"] = "ROLLBACK_V3_QUIESCED"
    _persist(receipt_path, receipt)

    confirmation, _ = _validate_root_json(
        workflow_rollback_confirmation,
        "production workflow rollback confirmation",
    )
    _validate_workflow_confirmation(confirmation, receipt, rollback=True)

    backups = receipt["backups"]
    for class_id in ACCEPTED_CLASSES:
        _restore_backup(backups["controller_policies"][class_id])
    _restore_backup(backups["deployment_overlay"])
    try:
        PRODUCTION_OVERRIDE.unlink()
    except FileNotFoundError:
        pass
    reconciler.verify_installed(BASE_MANIFEST)

    prestate = receipt["prestate"]
    for unit, wanted in prestate["v3_enabled"].items():
        if wanted:
            systemd.enable(unit)
        else:
            systemd.disable(unit)
    for unit, wanted in prestate["root_enabled"].items():
        if wanted:
            systemd.enable(unit)
        else:
            systemd.disable(unit)
    for unit, wanted in prestate["v2_enabled"].items():
        if wanted:
            systemd.enable(unit)
        else:
            systemd.disable(unit)
    for unit, wanted in prestate["v2_active"].items():
        if wanted and not systemd.active(unit):
            systemd.start(unit)
        elif not wanted and systemd.active(unit):
            systemd.stop(unit)

    migration._assert_research_gpu_containment(systemd)
    for unit, wanted in prestate["v2_active"].items():
        if systemd.active(unit) != bool(wanted):
            raise CutoverError(f"v2 active-state rollback failed: {unit}")
    receipt["workflow_rollback_confirmation"] = confirmation
    receipt["phase"] = "ROLLED_BACK_LEGACY_RESTORED"
    _persist(receipt_path, receipt)


def _repo_head(repo_root: pathlib.Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _require_clean_head(repo_root: pathlib.Path, expected: str) -> None:
    actual = _repo_head(repo_root)
    if actual != expected:
        raise CutoverError(f"source head mismatch: {actual} != {expected}")
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
    )
    if dirty.strip():
        raise CutoverError("source tree has tracked modifications")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--render-generation", action="store_true")
    parser.add_argument("--source-head")
    parser.add_argument("--workspace-control-workflow", type=pathlib.Path)
    parser.add_argument("--padataset-cpu-workflow", type=pathlib.Path)
    parser.add_argument("--padataset-gpu-workflow", type=pathlib.Path)
    parser.add_argument("--live-overlay", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)

    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--generation-dir", type=pathlib.Path)
    parser.add_argument("--authorization-receipt", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path)
    parser.add_argument("--workflow-confirmation", type=pathlib.Path)
    parser.add_argument("--validation-confirmation", type=pathlib.Path)
    parser.add_argument("--workflow-rollback-confirmation", type=pathlib.Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()

    if args.render_generation:
        required = (
            args.source_head,
            args.workspace_control_workflow,
            args.padataset_cpu_workflow,
            args.padataset_gpu_workflow,
            args.live_overlay,
            args.output,
        )
        if not all(required):
            raise CutoverError("render-generation requires all workflow/overlay/output inputs")
        _require_clean_head(repo_root, args.source_head)
        result = build_generation(
            repo_root,
            {
                "workspace-control:control-validation":
                    args.workspace_control_workflow.read_bytes(),
                "padataset:cpu-ci": args.padataset_cpu_workflow.read_bytes(),
                "padataset:gpu-ci": args.padataset_gpu_workflow.read_bytes(),
            },
            _load(args.live_overlay),
            source_head=args.source_head,
        )
        write_generation(result, args.output)
        print("V3_PRODUCTION_GENERATION_RENDER=PASS")
        print(
            "PRODUCTION_GENERATION_SHA256="
            + result["manifest"]["production_generation_sha256"]
        )
        return 0

    if os.geteuid() != 0:
        raise CutoverError("live production cutover transaction must run as root")
    if not args.source_head:
        raise CutoverError("live production operation requires --source-head")
    _require_clean_head(repo_root, args.source_head)
    systemd = RealSystemd()

    selected = sum(
        bool(value)
        for value in (args.prepare, args.activate, args.commit, args.rollback)
    )
    if selected != 1:
        raise CutoverError("choose exactly one live production operation")

    if args.prepare:
        if not args.generation_dir or not args.authorization_receipt:
            raise CutoverError("prepare requires generation-dir and authorization-receipt")
        receipt = prepare(
            systemd=systemd,
            repo_root=repo_root,
            generation_dir=args.generation_dir,
            authorization_receipt=args.authorization_receipt,
        )
        print("V3_PRODUCTION_V2_QUIESCED=PASS")
        print(f"TRANSACTION_RECEIPT={receipt}")
        return 0

    if not args.receipt:
        raise CutoverError("activate/commit/rollback require --receipt")
    if args.activate:
        if not args.workflow_confirmation:
            raise CutoverError("activate requires workflow-confirmation")
        activate(
            systemd=systemd,
            repo_root=repo_root,
            receipt_path=args.receipt,
            workflow_confirmation=args.workflow_confirmation,
        )
        print("V3_PRODUCTION_ACTIVE=PASS")
        return 0
    if args.commit:
        if not args.validation_confirmation:
            raise CutoverError("commit requires validation-confirmation")
        commit(
            systemd=systemd,
            repo_root=repo_root,
            receipt_path=args.receipt,
            validation_confirmation=args.validation_confirmation,
            provisioner_state_root=PROVISIONER_STATE,
        )
        print("V3_PRODUCTION_COMMIT=PASS")
        return 0
    if not args.workflow_rollback_confirmation:
        raise CutoverError("rollback requires workflow-rollback-confirmation")
    rollback(
        systemd=systemd,
        repo_root=repo_root,
        receipt_path=args.receipt,
        workflow_rollback_confirmation=args.workflow_rollback_confirmation,
    )
    print("V3_PRODUCTION_ROLLBACK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
