#!/usr/bin/env python3
"""Fail-closed root reconciliation for the Lambda CI multi-project substrate.

V1 accepts only the frozen registry/manifest request document. It cannot accept
commands, paths, unit text, UIDs, device lists, network policy, environment, or
secrets from GitHub.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pathlib
import pwd
import shutil
import socket
import stat
import struct
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

import lambda_ci_multirepo as multi

MAX_REQUEST_BYTES = 2 * 1024 * 1024
ACTIVE_PROJECT_STATE = "ACTIVE"
ACTIVE_ROUTE_STATES = {"ACTIVE", "MIGRATION_LIVE_EQUIVALENT"}


class ReconcileError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise ReconcileError(
            f"command failed rc={proc.returncode}: {argv[0]}: {proc.stderr.strip()}"
        )
    return proc


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return multi.sha256_json(value)


def render_controller_env(
    manifest: dict[str, Any],
    lane: str,
) -> str:
    multi.validate_project_manifest_derivations(manifest)
    lane_cfg = manifest["derived_identity"]["lanes"].get(lane)
    if lane_cfg is None:
        raise ReconcileError(f"unsupported project lane: {lane}")
    values = {
        "WORKSPACE_CI_ADMISSION_V2_ENABLED": "YES",
        "WORKSPACE_CI_GITHUB_URL": f"https://github.com/{manifest['repository']}",
        "WORKSPACE_CI_LANE": lane,
        "WORKSPACE_CI_PAT_FILE": "/var/lib/workspace-ci/controller/github-token",
        "WORKSPACE_CI_PROJECT_ID": manifest["project_id"],
        "WORKSPACE_CI_PROVISIONER_SOCKET": "/run/workspace-ci/provisioner.sock",
        "WORKSPACE_CI_RUNNER_PREFIX": lane_cfg["runner_prefix"],
        "WORKSPACE_CI_SCALESET_NAME": lane_cfg["scale_set_name"],
    }
    return "".join(f"{key}={values[key]}\n" for key in sorted(values))


def controller_env_sha256(manifest: dict[str, Any], lane: str) -> str:
    return _sha256_bytes(render_controller_env(manifest, lane).encode("utf-8"))


def _active_project_ids(registry: dict[str, Any]) -> list[str]:
    return sorted(
        project_id
        for project_id, entry in registry.get("projects", {}).items()
        if isinstance(entry, dict) and entry.get("activation_state") == ACTIVE_PROJECT_STATE
    )


def _planned_project_ids(registry: dict[str, Any]) -> list[str]:
    active = set(_active_project_ids(registry))
    return sorted(set(registry.get("projects", {})) - active)


def plan_reconciliation(
    registry: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if registry.get("status") not in {"CONTRACT_ONLY_NOT_INSTALLED", "ACTIVE"}:
        raise ReconcileError("registry status is invalid")
    actions: list[dict[str, Any]] = []
    active_projects = _active_project_ids(registry)
    for project_id in active_projects:
        manifest = multi.resolve_project_manifest(registry, manifests, project_id)
        if manifest.get("status") != ACTIVE_PROJECT_STATE:
            raise ReconcileError(
                f"active registry project {project_id} must have ACTIVE manifest"
            )
        ident = manifest["derived_identity"]
        root = ident["project_root"]
        actions.extend(
            [
                {"kind": "ensure_group", "name": ident["runner_group"]},
                {
                    "kind": "ensure_user",
                    "name": ident["runner_user"],
                    "group": ident["runner_group"],
                },
                {
                    "kind": "ensure_project_root",
                    "path": root,
                    "owner": ident["runner_user"],
                },
                {
                    "kind": "install_project_manifest",
                    "project_id": project_id,
                    "destination": f"/etc/workspace-ci/projects/{project_id}.json",
                    "sha256": _canonical_sha256(manifest),
                },
            ]
        )
        for lane in registry["projects"][project_id]["lanes"]:
            lane_cfg = ident["lanes"][lane]
            actions.append(
                {
                    "kind": "install_controller_instance_config",
                    "project_id": project_id,
                    "lane": lane,
                    "repository": manifest["repository"],
                    "scale_set_name": lane_cfg["scale_set_name"],
                    "runner_prefix": lane_cfg["runner_prefix"],
                    "destination": f"/etc/workspace-ci/controllers/{project_id}-{lane}.env",
                    "content_sha256": controller_env_sha256(manifest, lane),
                    "service_instance": f"workspace-ci-controller@{project_id}-{lane}.service",
                }
            )
    return {
        "schema_version": 1,
        "mode": "APPLY_READY_V1",
        "registry_sha256": _canonical_sha256(registry),
        "active_projects": active_projects,
        "planned_projects_skipped": _planned_project_ids(registry),
        "actions": actions,
    }


def _validate_source_attestation(
    value: Any,
    ceiling: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReconcileError("source_attestation must be an object")
    required = {
        "repository",
        "default_branch",
        "commit_sha",
        "workflow_path",
        "workflow_blob_sha",
        "actor_login",
        "verified_at",
    }
    if set(value) != required:
        raise ReconcileError("source_attestation keys mismatch")
    if value["repository"] != ceiling["source_repository"]:
        raise ReconcileError("reconciliation repository is not trusted")
    if value["default_branch"] != ceiling["source_default_branch"]:
        raise ReconcileError("reconciliation branch is not trusted")
    if value["workflow_path"] != ceiling["trusted_workflow_path"]:
        raise ReconcileError("reconciliation workflow path is not trusted")
    if value["workflow_blob_sha"] != ceiling["trusted_workflow_blob_sha"]:
        raise ReconcileError("reconciliation workflow blob is not trusted")
    if value["actor_login"] not in ceiling["allowed_actor_logins"]:
        raise ReconcileError("reconciliation actor is not trusted")
    for key in ("commit_sha", "workflow_blob_sha"):
        raw = value[key]
        if not isinstance(raw, str) or len(raw) != 40 or any(
            ch not in "0123456789abcdef" for ch in raw
        ):
            raise ReconcileError(f"{key} must be 40 lowercase hex")
    if not isinstance(value["verified_at"], str) or not value["verified_at"]:
        raise ReconcileError("source verified_at is missing")
    return value


def _validate_registry_semantics(
    registry: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
    execution_contracts: dict[str, Any],
) -> None:
    if registry.get("schema_version") != 1:
        raise ReconcileError("registry schema_version must be 1")
    if registry.get("registry_id") != "lambda-ci-project-registry-v1":
        raise ReconcileError("registry id drift")
    if registry.get("status") != "ACTIVE":
        raise ReconcileError("live reconciliation requires ACTIVE registry")
    authority = registry.get("authority")
    reconciliation = registry.get("reconciliation")
    if not isinstance(authority, dict) or not isinstance(reconciliation, dict):
        raise ReconcileError("registry authority/reconciliation missing")
    if authority.get("owner") != "workspace-control":
        raise ReconcileError("registry authority owner drift")
    if authority.get("target_repository_policy_authority") is not False:
        raise ReconcileError("target repository policy authority must remain false")
    if authority.get("candidate_invocable_reconciliation") is not False:
        raise ReconcileError("candidate reconciliation must remain disabled")
    if reconciliation.get("arbitrary_commands_allowed") is not False:
        raise ReconcileError("arbitrary reconciliation commands must remain disabled")
    if reconciliation.get("arbitrary_paths_allowed") is not False:
        raise ReconcileError("arbitrary reconciliation paths must remain disabled")
    if reconciliation.get("arbitrary_systemd_properties_allowed") is not False:
        raise ReconcileError("arbitrary systemd properties must remain disabled")

    projects = registry.get("projects")
    if not isinstance(projects, dict) or not projects:
        raise ReconcileError("registry projects missing")
    if len(projects) > int(authority.get("max_projects", 0)):
        raise ReconcileError("registry exceeds max_projects")

    allowed_owners = set(authority.get("allowed_repository_owners") or [])
    if not allowed_owners:
        raise ReconcileError("allowed repository owner set is empty")

    if set(manifests) != set(projects):
        raise ReconcileError("request must carry every registry manifest exactly once")

    contracts = execution_contracts.get("contracts")
    if not isinstance(contracts, dict):
        raise ReconcileError("execution contract catalog missing")

    for project_id, entry in projects.items():
        if not isinstance(entry, dict):
            raise ReconcileError(f"registry project {project_id} is invalid")
        manifest = multi.resolve_project_manifest(registry, manifests, project_id)
        repository = manifest["repository"]
        owner, sep, _ = repository.partition("/")
        if not sep or owner not in allowed_owners:
            raise ReconcileError(f"repository owner is not allowed: {repository}")
        active_project = entry.get("activation_state") == ACTIVE_PROJECT_STATE
        if active_project and manifest.get("status") != ACTIVE_PROJECT_STATE:
            raise ReconcileError(
                f"active project {project_id} requires ACTIVE manifest"
            )
        if not active_project and manifest.get("status") == ACTIVE_PROJECT_STATE:
            raise ReconcileError(
                f"planned project {project_id} cannot have ACTIVE manifest"
            )

        for route_id, route in manifest.get("routes", {}).items():
            if not isinstance(route, dict):
                raise ReconcileError(f"route {project_id}/{route_id} is invalid")
            contract_id = route.get("execution_contract_id")
            if contract_id not in contracts:
                raise ReconcileError(
                    f"route {project_id}/{route_id} uses unknown execution contract"
                )
            active_route = route.get("activation_state") in ACTIVE_ROUTE_STATES
            workflow = route.get("trusted_workflow")
            trigger = route.get("trigger")
            if not isinstance(workflow, dict) or not isinstance(trigger, dict):
                raise ReconcileError(f"route {project_id}/{route_id} contract missing")
            if active_route:
                blob = workflow.get("blob_sha")
                if not isinstance(blob, str) or len(blob) != 40:
                    raise ReconcileError(
                        f"active route {project_id}/{route_id} lacks trusted workflow blob"
                    )
            if manifest.get("repository_visibility") == "public":
                if trigger.get("require_open_same_repository_pr_head") is not True:
                    raise ReconcileError("public project route must require same-repo PR head")
                if trigger.get("fork_pr_execution_allowed") is not False:
                    raise ReconcileError("public project route must deny fork execution")
                actors = trigger.get("allowed_actor_logins")
                if not isinstance(actors, list) or not actors:
                    raise ReconcileError("public project route requires explicit actors")


def _validate_no_removal(
    new_registry: dict[str, Any],
    installed_registry_path: pathlib.Path,
) -> None:
    if not installed_registry_path.is_file():
        return
    installed = json.loads(installed_registry_path.read_text(encoding="utf-8"))
    old_projects = installed.get("projects", {})
    new_projects = new_registry.get("projects", {})
    removed = sorted(set(old_projects) - set(new_projects))
    if removed:
        raise ReconcileError(f"project removal is forbidden in v1: {removed}")
    for project_id in sorted(set(old_projects) & set(new_projects)):
        old_entry = old_projects[project_id]
        new_entry = new_projects[project_id]
        old_lanes = set(old_entry.get("lanes", []))
        new_lanes = set(new_entry.get("lanes", []))
        if not old_lanes.issubset(new_lanes):
            raise ReconcileError(
                f"lane removal is forbidden in v1 for {project_id}"
            )


def validate_reconciliation_request(
    request: Any,
    *,
    ceiling: dict[str, Any],
    execution_contracts: dict[str, Any],
    installed_registry_path: pathlib.Path,
) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ReconcileError("reconciliation request must be an object")
    expected = {
        "schema_version",
        "request_id",
        "operation",
        "source_attestation",
        "registry",
        "project_manifests",
        "dry_run",
    }
    if set(request) != expected:
        raise ReconcileError("reconciliation request keys mismatch")
    if request["schema_version"] != 1:
        raise ReconcileError("reconciliation request schema_version must be 1")
    try:
        uuid.UUID(str(request["request_id"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReconcileError("reconciliation request_id must be UUID") from exc
    if request["operation"] != "APPLY_PROJECT_REGISTRY":
        raise ReconcileError("reconciliation operation is unsupported")
    if not isinstance(request["dry_run"], bool):
        raise ReconcileError("dry_run must be boolean")
    source = _validate_source_attestation(request["source_attestation"], ceiling)

    registry_wrapper = request["registry"]
    if not isinstance(registry_wrapper, dict) or set(registry_wrapper) != {
        "sha256",
        "document",
    }:
        raise ReconcileError("registry wrapper keys mismatch")
    registry = registry_wrapper["document"]
    if registry_wrapper["sha256"] != _canonical_sha256(registry):
        raise ReconcileError("registry digest mismatch")
    if source["repository"] != registry.get("reconciliation", {}).get(
        "source_repository"
    ):
        raise ReconcileError("registry reconciliation source differs from attestation")
    if source["default_branch"] != registry.get("reconciliation", {}).get(
        "source_default_branch"
    ):
        raise ReconcileError("registry reconciliation branch differs from attestation")
    if source["workflow_path"] != registry.get("reconciliation", {}).get(
        "trusted_workflow_path"
    ):
        raise ReconcileError("registry reconciliation workflow differs from attestation")
    if source["actor_login"] not in registry.get("reconciliation", {}).get(
        "allowed_actor_logins", []
    ):
        raise ReconcileError("source actor is outside registry allowlist")

    manifest_wrappers = request["project_manifests"]
    if not isinstance(manifest_wrappers, list) or not manifest_wrappers:
        raise ReconcileError("project_manifests must be non-empty array")
    manifests: dict[str, dict[str, Any]] = {}
    for wrapper in manifest_wrappers:
        if not isinstance(wrapper, dict) or set(wrapper) != {
            "project_id",
            "sha256",
            "document",
        }:
            raise ReconcileError("project manifest wrapper keys mismatch")
        project_id = wrapper["project_id"]
        if project_id in manifests:
            raise ReconcileError(f"duplicate project manifest: {project_id}")
        document = wrapper["document"]
        if wrapper["sha256"] != _canonical_sha256(document):
            raise ReconcileError(f"project manifest digest mismatch: {project_id}")
        if not isinstance(document, dict) or document.get("project_id") != project_id:
            raise ReconcileError(f"project manifest id mismatch: {project_id}")
        manifests[project_id] = document

    _validate_registry_semantics(registry, manifests, execution_contracts)
    _validate_no_removal(registry, installed_registry_path)
    plan = plan_reconciliation(registry, manifests)
    return {
        "request": request,
        "source": source,
        "registry": registry,
        "manifests": manifests,
        "plan": plan,
    }


def _atomic_write(path: pathlib.Path, data: bytes, *, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = pathlib.Path(tmp_raw)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _atomic_write_json(path: pathlib.Path, value: Any, *, mode: int = 0o644) -> None:
    _atomic_write(
        path,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode=mode,
    )


def _ensure_project_identity(manifest: dict[str, Any]) -> None:
    ident = manifest["derived_identity"]
    user = ident["runner_user"]
    group = ident["runner_group"]
    try:
        group_row = grp.getgrnam(group)
    except KeyError:
        _run(["groupadd", "--system", group])
        group_row = grp.getgrnam(group)
    try:
        user_row = pwd.getpwnam(user)
    except KeyError:
        _run(
            [
                "useradd",
                "--system",
                "--gid",
                group,
                "--home-dir",
                manifest["roots"]["home"],
                "--shell",
                "/usr/sbin/nologin",
                "--no-create-home",
                user,
            ]
        )
        user_row = pwd.getpwnam(user)
    if user_row.pw_gid != group_row.gr_gid:
        raise ReconcileError(f"project identity group drift: {user}")
    if user_row.pw_name != user or group_row.gr_name != group:
        raise ReconcileError(f"project identity drift: {user}")


def _ensure_dir(
    path: pathlib.Path,
    *,
    uid: int,
    gid: int,
    mode: int,
    preserve_existing: bool = True,
) -> None:
    if not path.exists():
        path.mkdir(parents=True, mode=mode)
        os.chown(path, uid, gid)
        os.chmod(path, mode)
        return
    if not path.is_dir():
        raise ReconcileError(f"required directory is not a directory: {path}")
    if not preserve_existing:
        os.chown(path, uid, gid)
        os.chmod(path, mode)


def _ensure_project_roots(manifest: dict[str, Any]) -> None:
    ident = manifest["derived_identity"]
    user_row = pwd.getpwnam(ident["runner_user"])
    root = pathlib.Path(ident["project_root"])
    _ensure_dir(root, uid=0, gid=0, mode=0o755)
    for key in ("jobs", "staging_cache", "logs", "home"):
        _ensure_dir(
            pathlib.Path(manifest["roots"][key]),
            uid=user_row.pw_uid,
            gid=user_row.pw_gid,
            mode=0o700,
        )
    _ensure_dir(
        pathlib.Path(manifest["roots"]["trusted_cache"]),
        uid=0,
        gid=0,
        mode=0o755,
    )


def primary_local_subnet() -> str:
    route = _run(["ip", "-4", "route", "get", "1.1.1.1"])
    fields = route.stdout.split()
    try:
        dev = fields[fields.index("dev") + 1]
    except (ValueError, IndexError) as exc:
        raise ReconcileError("unable to resolve primary network device") from exc
    routes = _run(["ip", "-4", "route", "show", "dev", dev, "proto", "kernel", "scope", "link"])
    for line in routes.stdout.splitlines():
        parts = line.split()
        first = parts[0] if parts else ""
        if "/" in first and first[:1].isdigit():
            return first
    raise ReconcileError("unable to resolve primary local subnet")


def controller_network_dropin(project_id: str, lane: str, subnet: str) -> tuple[pathlib.Path, bytes]:
    multi.derive_project_identity(project_id)
    if lane not in {"cpu", "gpu"}:
        raise ReconcileError("controller lane is invalid")
    if not subnet or "/" not in subnet:
        raise ReconcileError("local subnet is invalid")
    path = pathlib.Path(
        f"/etc/systemd/system/workspace-ci-controller@{project_id}-{lane}.service.d/network.conf"
    )
    body = f"[Service]\nIPAddressDeny={subnet}\n".encode("utf-8")
    return path, body


def _service_active(name: str) -> bool:
    proc = _run(["systemctl", "is-active", "--quiet", name], check=False)
    return proc.returncode == 0


def apply_reconciliation(
    validated: dict[str, Any],
    *,
    registry_path: pathlib.Path,
    projects_dir: pathlib.Path,
    controllers_dir: pathlib.Path,
    state_dir: pathlib.Path,
) -> dict[str, Any]:
    request = validated["request"]
    request_id = str(request["request_id"])
    receipts = state_dir / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    os.chown(state_dir, 0, 0)
    os.chmod(state_dir, 0o700)
    os.chown(receipts, 0, 0)
    os.chmod(receipts, 0o700)
    receipt_path = receipts / f"{request_id}.json"

    identity = {
        "request_id": request_id,
        "commit_sha": validated["source"]["commit_sha"],
        "registry_sha256": request["registry"]["sha256"],
        "manifest_sha256": {
            item["project_id"]: item["sha256"]
            for item in request["project_manifests"]
        },
    }
    if receipt_path.is_file():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        if existing.get("identity") != identity:
            raise ReconcileError("request_id replay digest mismatch")
        if existing.get("status") in {"COMPLETED", "DRY_RUN"}:
            return existing
        if existing.get("status") != "IN_PROGRESS":
            raise ReconcileError("stored reconciliation receipt status is invalid")
        # Interrupted APPLY resumes idempotently from root-owned desired state.
        # V1 operations are add/update only; removal remains forbidden.

    plan = validated["plan"]
    if request["dry_run"]:
        receipt = {
            "schema_version": 1,
            "status": "DRY_RUN",
            "identity": identity,
            "timestamp_utc": _utc_now(),
            "plan": plan,
            "mutation_performed": False,
        }
        _atomic_write_json(receipt_path, receipt, mode=0o600)
        return receipt

    in_progress = {
        "schema_version": 1,
        "status": "IN_PROGRESS",
        "identity": identity,
        "timestamp_utc": _utc_now(),
        "plan": plan,
        "mutation_performed": True,
    }
    _atomic_write_json(receipt_path, in_progress, mode=0o600)

    registry = validated["registry"]
    manifests = validated["manifests"]
    active_projects = plan["active_projects"]

    for project_id in active_projects:
        manifest = manifests[project_id]
        _ensure_project_identity(manifest)
        _ensure_project_roots(manifest)

    # Install complete reviewed policy state before starting/restarting controllers.
    _atomic_write_json(registry_path, registry)
    projects_dir.mkdir(parents=True, exist_ok=True)
    os.chown(projects_dir, 0, 0)
    os.chmod(projects_dir, 0o755)
    for project_id, manifest in manifests.items():
        _atomic_write_json(projects_dir / f"{project_id}.json", manifest)

    controllers_dir.mkdir(parents=True, exist_ok=True)
    os.chown(controllers_dir, 0, 0)
    os.chmod(controllers_dir, 0o755)
    controller_services: list[str] = []
    local_subnet = primary_local_subnet()
    for project_id in active_projects:
        manifest = manifests[project_id]
        for lane in registry["projects"][project_id]["lanes"]:
            env_path = controllers_dir / f"{project_id}-{lane}.env"
            _atomic_write(
                env_path,
                render_controller_env(manifest, lane).encode("utf-8"),
                mode=0o644,
            )
            dropin_path, dropin_body = controller_network_dropin(
                project_id,
                lane,
                local_subnet,
            )
            _atomic_write(dropin_path, dropin_body, mode=0o644)
            controller_services.append(
                f"workspace-ci-controller@{project_id}-{lane}.service"
            )

    _run(["systemctl", "daemon-reload"])
    for service in controller_services:
        _run(["systemctl", "enable", service])
        _run(["systemctl", "restart", service])
        if not _service_active(service):
            raise ReconcileError(f"controller service is not active: {service}")

    receipt = {
        "schema_version": 1,
        "status": "COMPLETED",
        "identity": identity,
        "timestamp_utc": _utc_now(),
        "plan": plan,
        "mutation_performed": True,
        "active_controller_services": controller_services,
        "planned_projects_skipped": plan["planned_projects_skipped"],
        "controller_local_subnet_denied": local_subnet,
        "installed_registry_sha256": _canonical_sha256(registry),
        "installed_manifest_sha256": {
            project_id: _canonical_sha256(manifests[project_id])
            for project_id in sorted(manifests)
        },
    }
    _atomic_write_json(receipt_path, receipt, mode=0o600)
    return receipt


def peer_uid(conn: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise ReconcileError("SO_PEERCRED is required")
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def read_request(conn: socket.socket) -> dict[str, Any]:
    handle = conn.makefile("rb")
    line = handle.readline(MAX_REQUEST_BYTES + 1)
    if not line:
        raise ReconcileError("empty reconciliation request")
    if len(line) > MAX_REQUEST_BYTES:
        raise ReconcileError("reconciliation request exceeds transport limit")
    if handle.readline(2):
        raise ReconcileError("exactly one reconciliation JSON object is allowed")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ReconcileError("reconciliation request is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ReconcileError("reconciliation request must be object")
    return value


def serve(
    *,
    socket_path: pathlib.Path,
    socket_group: str,
    controller_uid: int,
    ceiling_path: pathlib.Path,
    contracts_path: pathlib.Path,
    registry_path: pathlib.Path,
    projects_dir: pathlib.Path,
    controllers_dir: pathlib.Path,
    state_dir: pathlib.Path,
) -> None:
    ceiling = json.loads(ceiling_path.read_text(encoding="utf-8"))
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    group = grp.getgrnam(socket_group)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    os.chown(socket_path, 0, group.gr_gid)
    os.chmod(socket_path, 0o660)
    server.listen(8)
    try:
        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    uid = peer_uid(conn)
                    if uid != controller_uid:
                        raise ReconcileError("peer UID is not ci-reconciler")
                    request = read_request(conn)
                    validated = validate_reconciliation_request(
                        request,
                        ceiling=ceiling,
                        execution_contracts=contracts,
                        installed_registry_path=registry_path,
                    )
                    receipt = apply_reconciliation(
                        validated,
                        registry_path=registry_path,
                        projects_dir=projects_dir,
                        controllers_dir=controllers_dir,
                        state_dir=state_dir,
                    )
                    response = {
                        "schema_version": 1,
                        "status": "PASS",
                        "request_id": request["request_id"],
                        "receipt": receipt,
                    }
                except Exception as exc:
                    response = {
                        "schema_version": 1,
                        "status": "REJECTED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                conn.sendall(
                    (json.dumps(response, sort_keys=True) + "\n").encode("utf-8")
                )
    finally:
        server.close()
        if socket_path.exists():
            socket_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--socket", type=pathlib.Path, default=pathlib.Path("/run/workspace-ci/reconciler.sock"))
    parser.add_argument("--socket-group", default="workspace-ci-reconciler")
    parser.add_argument("--controller-user", default="ci-reconciler")
    parser.add_argument("--ceiling", type=pathlib.Path, default=pathlib.Path("/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json"))
    parser.add_argument("--contracts", type=pathlib.Path, default=pathlib.Path("/etc/workspace-ci/lambda-ci-execution-contracts.v1.json"))
    parser.add_argument("--installed-registry", type=pathlib.Path, default=pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json"))
    parser.add_argument("--projects-dir", type=pathlib.Path, default=pathlib.Path("/etc/workspace-ci/projects"))
    parser.add_argument("--controllers-dir", type=pathlib.Path, default=pathlib.Path("/etc/workspace-ci/controllers"))
    parser.add_argument("--state-dir", type=pathlib.Path, default=pathlib.Path("/var/lib/workspace-ci/reconciler"))
    args = parser.parse_args()

    if args.serve:
        controller = pwd.getpwnam(args.controller_user)
        serve(
            socket_path=args.socket,
            socket_group=args.socket_group,
            controller_uid=controller.pw_uid,
            ceiling_path=args.ceiling,
            contracts_path=args.contracts,
            registry_path=args.installed_registry,
            projects_dir=args.projects_dir,
            controllers_dir=args.controllers_dir,
            state_dir=args.state_dir,
        )
        return 0

    if args.registry is None:
        raise ReconcileError("--registry is required outside --serve mode")
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    manifests: dict[str, dict[str, Any]] = {}
    for path in args.manifest:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifests[manifest["project_id"]] = manifest
    plan = plan_reconciliation(registry, manifests)
    if args.apply:
        raise ReconcileError(
            "direct CLI apply is forbidden; live mutation is accepted only through the root reconciliation socket"
        )
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
