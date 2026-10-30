#!/usr/bin/env python3
"""Local root provisioner service for Lambda CI P5.

The service has no GitHub credential. P5 request schema v1 remains supported for
the already accepted cpu-test/gpu-small path. Admission v2 is additive: the
controller supplies an attestation, but root revalidates current local policy,
mints/consumes the single-use admission, and persists non-secret replay state.
"""

from __future__ import annotations

import argparse
import dataclasses
import grp
import json
import os
import pathlib
import pwd
import socket
import struct
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import lambda_ci_provisioner as policy
import lambda_ci_multirepo as multirepo_policy
import lambda_ci_runtime as runtime

DEFAULT_SOCKET = pathlib.Path("/run/workspace-ci/provisioner.sock")
DEFAULT_STATE = pathlib.Path("/var/lib/workspace-ci/provisioner")
MAX_REQUEST_BYTES = 192 * 1024
SUPPORTED_EXECUTION_PROFILES = {"cpu-test", "gpu-small", "gpu-heavy", "control-small"}


class ServiceError(RuntimeError):
    pass


class StateStore:
    def __init__(self, root: pathlib.Path):
        self.root = root

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

    def path(self, request_id: str) -> pathlib.Path:
        return self.root / f"{request_id}.json"

    def lane_quarantine_path(
        self,
        profile: str,
        *,
        project_id: str | None = None,
    ) -> pathlib.Path:
        if profile not in SUPPORTED_EXECUTION_PROFILES:
            raise ServiceError(f"unsupported lane quarantine profile: {profile}")
        if project_id is None:
            suffix = profile
        else:
            try:
                multirepo_policy.derive_project_identity(project_id)
            except multirepo_policy.MultiRepoPolicyError as exc:
                raise ServiceError(f"invalid quarantine project id: {exc}") from exc
            suffix = f"{project_id}-{profile}"
        return self.root / f"_lane-quarantine-{suffix}.json"

    def read_lane_quarantine(
        self,
        profile: str,
        *,
        project_id: str | None = None,
    ) -> dict[str, Any] | None:
        path = self.lane_quarantine_path(profile, project_id=project_id)
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ServiceError("stored lane quarantine is not a JSON object")
        return value

    def quarantine_lane(
        self,
        profile: str,
        *,
        request_id: str,
        error_type: str,
        error: str,
        quarantined_at: datetime,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        self.ensure()
        path = self.lane_quarantine_path(profile, project_id=project_id)
        record = {
            "schema_version": 1,
            "profile": profile,
            "project_id": project_id,
            "status": "QUARANTINED",
            "request_id": request_id,
            "error_type": error_type,
            "error": error,
            "quarantined_at": quarantined_at.astimezone(timezone.utc).isoformat(),
        }
        tmp = self.root / f".{path.name}.{os.getpid()}.tmp"
        tmp.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        return record

    def read(self, request_id: str) -> dict[str, Any] | None:
        path = self.path(request_id)
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ServiceError("stored request state is not a JSON object")
        return value

    def claim(self, request_id: str, metadata: dict[str, Any]) -> bool:
        self.ensure()
        path = self.path(request_id)
        payload = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return True

    def update(self, request_id: str, metadata: dict[str, Any]) -> None:
        self.ensure()
        path = self.path(request_id)
        tmp = self.root / f".{request_id}.{os.getpid()}.tmp"
        tmp.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)


class ProvisionerService:
    def __init__(
        self,
        *,
        manifest: dict[str, Any] | None,
        profiles: dict[str, Any],
        pins: dict[str, Any],
        workload_policy: dict[str, Any],
        state_store: StateStore,
        controller_uid: int,
        launcher: Callable[[Any, dict[str, Any]], dict[str, Any]] = runtime.launch_runner,
        clock: Callable[[], datetime] | None = None,
        registry: dict[str, Any] | None = None,
        project_manifests: dict[str, dict[str, Any]] | None = None,
        execution_contracts: dict[str, Any] | None = None,
        registry_path: pathlib.Path | None = None,
        manifest_dir: pathlib.Path | None = None,
    ):
        self.manifest = manifest
        self.profiles = profiles
        self.pins = pins
        self.workload_policy = workload_policy
        self.policy_sha256 = policy.admission_policy.sha256_json(workload_policy)
        self.registry = registry
        self.project_manifests = project_manifests or {}
        self.execution_contracts = execution_contracts
        self.registry_path = registry_path
        self.manifest_dir = manifest_dir
        self.generic_policy_sha256 = (
            multirepo_policy.sha256_json(
                {
                    "workload_policy": workload_policy,
                    "execution_contracts": execution_contracts,
                }
            )
            if registry is not None and execution_contracts is not None
            else None
        )
        if registry is not None:
            if manifest is not None:
                raise ServiceError("generic registry mode cannot also use a fixed manifest")
            if execution_contracts is None:
                raise ServiceError("generic registry mode requires execution contracts")
            if not self.project_manifests:
                raise ServiceError("generic registry mode requires project manifests")
        elif manifest is None:
            raise ServiceError("legacy provisioner mode requires a manifest")
        self.state_store = state_store
        self.controller_uid = controller_uid
        self.launcher = launcher
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = threading.Lock()
        self._active: set[str] = set()

    def _reload_generic_project_state(self) -> None:
        if self.registry_path is None or self.manifest_dir is None:
            return
        registry = policy._load(self.registry_path)
        manifests: dict[str, dict[str, Any]] = {}
        for project_id in registry.get("projects", {}):
            path = self.manifest_dir / f"{project_id}.json"
            if not path.is_file():
                raise ServiceError(f"registered project manifest missing: {path}")
            manifests[project_id] = policy._load(path)
        self.registry = registry
        self.project_manifests = manifests

    def _manifest_for_request(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.registry is None:
            if self.manifest is None:
                raise ServiceError("fixed project manifest is unavailable")
            return self.manifest
        self._reload_generic_project_state()
        try:
            return multirepo_policy.resolve_project_manifest(
                self.registry,
                self.project_manifests,
                str(data.get("project_id", "")),
            )
        except multirepo_policy.MultiRepoPolicyError as exc:
            raise policy.PolicyError(f"project registry resolution failed: {exc}") from exc

    def _admission_identity(self, req) -> dict[str, Any] | None:
        admission = getattr(req, "admission", None)
        if not isinstance(admission, dict):
            return None
        identity = {
            "admission_id": admission["admission_id"],
            "request_digest_sha256": admission["request_digest_sha256"],
            "candidate_sha": admission["candidate_sha"],
            "workload_class": admission["workload_class"],
            "execution_profile": admission["execution_profile"],
            "resource_class": admission["resource_class"],
            "policy": admission["policy"],
            "trusted_workflow": admission["trusted_workflow"],
            "consumed_at": admission["lifecycle"]["consumed_at"],
        }
        generic = admission.get("_generic")
        if isinstance(generic, dict):
            identity["execution_contract_id"] = generic.get("execution_contract_id")
        return identity

    def _nonsecret_record(self, req, status: str, **extra: Any) -> dict[str, Any]:
        record = {
            "schema_version": 2 if req.admission is not None else 1,
            "request_id": req.request_id,
            "project_id": req.project_id,
            "profile": req.profile,
            "workload_class": req.workload_class or req.profile,
            "runner_name": req.runner_name,
            "status": status,
        }
        identity = self._admission_identity(req)
        if identity is not None:
            record["request_digest_sha256"] = identity["request_digest_sha256"]
            record["admission_identity"] = identity
        record.update(extra)
        return record

    def _worker(self, req, spec: dict[str, Any]) -> None:
        try:
            result = self.launcher(req, spec)
            record = self._nonsecret_record(req, "COMPLETED", result=result)
        except runtime.RuntimeCleanupError as exc:
            generic = (
                isinstance(getattr(req, "admission", None), dict)
                and isinstance(req.admission.get("_generic"), dict)
            )
            quarantine = self.state_store.quarantine_lane(
                req.profile,
                request_id=req.request_id,
                error_type=type(exc).__name__,
                error=str(exc),
                quarantined_at=self.clock(),
                project_id=req.project_id if generic else None,
            )
            record = self._nonsecret_record(
                req,
                "FAILED",
                error_type=type(exc).__name__,
                error=str(exc),
                lane_quarantined=True,
                lane_quarantine=quarantine,
            )
        except Exception as exc:
            record = self._nonsecret_record(
                req,
                "FAILED",
                error_type=type(exc).__name__,
                error=str(exc),
                lane_quarantined=False,
            )
        finally:
            with self._lock:
                self._active.discard(req.request_id)
        self.state_store.update(req.request_id, record)

    def _lane_quarantine_response(
        self,
        profile: str,
        request_id: str,
        *,
        project_id: str | None = None,
    ) -> dict[str, Any] | None:
        quarantine = self.state_store.read_lane_quarantine(
            profile,
            project_id=project_id,
        )
        if quarantine is None:
            return None
        return {
            "schema_version": 2,
            "status": "REJECTED",
            "request_id": request_id,
            "error_type": "LaneQuarantined",
            "error": (
                f"{profile} is quarantined after cleanup failure; "
                "root operator clearance is required"
            ),
            "lane_quarantine": quarantine,
        }

    def _duplicate_v2_response(
        self,
        req,
        existing: dict[str, Any],
    ) -> dict[str, Any]:
        existing_digest = existing.get("request_digest_sha256")
        if existing_digest != req.request_digest_sha256:
            return {
                "schema_version": 2,
                "status": "REJECTED",
                "request_id": req.request_id,
                "error_type": "ReplayConflict",
                "error": "request_id was previously bound to a different request digest",
            }
        identity = existing.get("admission_identity")
        response = {
            "schema_version": 2,
            "status": "DUPLICATE",
            "request_id": req.request_id,
            "receipt_status": existing.get("status"),
        }
        if isinstance(identity, dict) and isinstance(identity.get("admission_id"), str):
            response["admission_id"] = identity["admission_id"]
        return response

    def handle_request(self, data: dict[str, Any], *, peer_uid: int) -> dict[str, Any]:
        if peer_uid != self.controller_uid:
            raise ServiceError("peer UID is not ci-controller")

        schema_version = data.get("schema_version")
        if schema_version == 2 and data.get("operation") == "STATUS":
            expected = {"schema_version", "operation", "request_id"}
            if set(data) != expected:
                raise ServiceError("status query keys mismatch")
            try:
                request_id = str(uuid.UUID(str(data.get("request_id"))))
            except (ValueError, AttributeError, TypeError) as exc:
                raise ServiceError("status query request_id must be UUID") from exc

            with self._lock:
                existing = self.state_store.read(request_id)
            if existing is None:
                return {
                    "schema_version": 2,
                    "status": "MISSING",
                    "request_id": request_id,
                }

            status = existing.get("status")
            if status not in {"ACCEPTED", "COMPLETED", "FAILED"}:
                raise ServiceError(
                    f"stored request has unsupported status for recovery: {status!r}"
                )
            response = {
                "schema_version": 2,
                "status": status,
                "request_id": request_id,
                "runner_name": existing.get("runner_name", ""),
            }
            identity = existing.get("admission_identity")
            if isinstance(identity, dict) and isinstance(identity.get("admission_id"), str):
                response["admission_id"] = identity["admission_id"]
            return response

        if schema_version == 2:
            try:
                request_id = str(uuid.UUID(str(data.get("request_id"))))
            except (ValueError, AttributeError, TypeError) as exc:
                raise policy.PolicyError("request_id must be UUID") from exc
            request_digest_sha256 = policy.admission_policy.request_digest(data)

            with self._lock:
                existing = self.state_store.read(request_id)
                if existing is not None:
                    existing_digest = existing.get("request_digest_sha256")
                    if existing_digest != request_digest_sha256:
                        return {
                            "schema_version": 2,
                            "status": "REJECTED",
                            "request_id": request_id,
                            "error_type": "ReplayConflict",
                            "error": (
                                "request_id was previously bound to a different "
                                "request digest"
                            ),
                        }
                    identity = existing.get("admission_identity")
                    response = {
                        "schema_version": 2,
                        "status": "DUPLICATE",
                        "request_id": request_id,
                        "receipt_status": existing.get("status"),
                    }
                    if isinstance(identity, dict) and isinstance(
                        identity.get("admission_id"), str
                    ):
                        response["admission_id"] = identity["admission_id"]
                    return response

                manifest = self._manifest_for_request(data)
                generic_mode = manifest.get("schema_version") == 2
                if generic_mode:
                    if self.execution_contracts is None or self.generic_policy_sha256 is None:
                        raise ServiceError("generic policy inputs are unavailable")
                    req = policy.validate_request_v2_generic(
                        data,
                        manifest,
                        self.execution_contracts,
                        self.workload_policy,
                        now=self.clock(),
                        policy_sha256=self.generic_policy_sha256,
                    )
                else:
                    req = policy.validate_request_v2(
                        data,
                        manifest,
                        self.workload_policy,
                        now=self.clock(),
                        policy_sha256=self.policy_sha256,
                    )

                if req.profile not in SUPPORTED_EXECUTION_PROFILES:
                    raise ServiceError(
                        "admission v2 execution profile is not supported"
                    )
                semantics = multirepo_policy.execution_semantics_from_admission(
                    req.admission
                )
                if semantics.get("execution_profile") != req.profile:
                    raise ServiceError("admission execution semantics/profile mismatch")
                if req.profile == "gpu-heavy":
                    if int(semantics.get("gpu_count", -1)) != 2:
                        raise ServiceError(
                            "gpu-heavy admission requires an accepted two-GPU semantic contract"
                        )
                    if semantics.get("admission_enabled_after_generic_activation") is not True:
                        raise ServiceError(
                            "gpu-heavy semantic contract is not admission-enabled"
                        )

                quarantined = self._lane_quarantine_response(
                    req.profile,
                    req.request_id,
                    project_id=req.project_id if generic_mode else None,
                )
                if quarantined is not None:
                    return quarantined

                concurrency = int(manifest["concurrency"])
                if len(self._active) >= concurrency:
                    return {
                        "schema_version": 2,
                        "status": "BUSY",
                        "request_id": req.request_id,
                    }

                if generic_mode:
                    consumed = multirepo_policy.consume_admission(
                        req.admission,
                        data,
                        manifest,
                        self.execution_contracts,
                        self.workload_policy,
                        now=self.clock(),
                        policy_sha256=self.generic_policy_sha256,
                    )
                else:
                    consumed = policy.admission_policy.consume_admission(
                        req.admission,
                        manifest,
                        self.workload_policy,
                        now=self.clock(),
                        policy_sha256=self.policy_sha256,
                    )
                req = dataclasses.replace(req, admission=consumed)
                spec = policy.build_launch_spec(
                    req,
                    manifest,
                    self.profiles,
                    self.pins,
                )
                accepted = self._nonsecret_record(req, "ACCEPTED")
                if not self.state_store.claim(req.request_id, accepted):
                    existing = self.state_store.read(req.request_id)
                    if existing is None:
                        raise ServiceError("request state claim failed without durable state")
                    return self._duplicate_v2_response(req, existing)

                self._active.add(req.request_id)
                thread = threading.Thread(
                    target=self._worker,
                    args=(req, spec),
                    name=f"workspace-ci-{req.request_id}",
                    daemon=True,
                )
                thread.start()

            return accepted

        # Accepted P5 v1 compatibility path. Keep its behavior unchanged.
        if self.registry is not None or self.manifest is None:
            raise ServiceError("schema v1 is unavailable in generic multi-project mode")
        req = policy.validate_request(data, self.manifest)
        if req.profile not in {"cpu-test", "gpu-small"}:
            raise ServiceError("P5 provisioner enables only cpu-test and gpu-small")

        quarantine = self.state_store.read_lane_quarantine(req.profile)
        if quarantine is not None:
            return {
                "schema_version": 1,
                "status": "REJECTED",
                "request_id": req.request_id,
                "error_type": "LaneQuarantined",
                "error": (
                    f"{req.profile} is quarantined after cleanup failure; "
                    "root operator clearance is required"
                ),
            }

        spec = policy.build_launch_spec(req, self.manifest, self.profiles, self.pins)
        concurrency = int(self.manifest["concurrency"])

        with self._lock:
            if len(self._active) >= concurrency:
                return {
                    "schema_version": 1,
                    "status": "BUSY",
                    "request_id": req.request_id,
                }

            accepted = self._nonsecret_record(req, "ACCEPTED")
            if not self.state_store.claim(req.request_id, accepted):
                return {
                    "schema_version": 1,
                    "status": "DUPLICATE",
                    "request_id": req.request_id,
                }

            self._active.add(req.request_id)
            thread = threading.Thread(
                target=self._worker,
                args=(req, spec),
                name=f"workspace-ci-{req.request_id}",
                daemon=True,
            )
            thread.start()

        return accepted


def peer_uid(conn: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise ServiceError("SO_PEERCRED is required")
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def read_request(conn: socket.socket) -> dict[str, Any]:
    handle = conn.makefile("rb")
    line = handle.readline(MAX_REQUEST_BYTES + 1)
    if not line:
        raise ServiceError("empty request")
    if len(line) > MAX_REQUEST_BYTES:
        raise ServiceError("request exceeds transport size limit")
    if handle.readline(2):
        raise ServiceError("exactly one JSON object is allowed")
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ServiceError("request is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ServiceError("request must be a JSON object")
    return data


def serve(
    service: ProvisionerService,
    *,
    socket_path: pathlib.Path = DEFAULT_SOCKET,
    socket_group: str = "workspace-ci-controller",
) -> None:
    # The provisioner and reconciler use distinct socket groups under one
    # shared runtime directory. Keep the parent searchable but not listable;
    # each socket's 0660 owner/group remains the authorization boundary.
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        os.chown(socket_path.parent, 0, 0)
    os.chmod(socket_path.parent, 0o711)
    if socket_path.exists():
        socket_path.unlink()

    group = grp.getgrnam(socket_group)
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
                    response = service.handle_request(
                        read_request(conn),
                        peer_uid=peer_uid(conn),
                    )
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
    parser.add_argument("--socket", type=pathlib.Path, default=DEFAULT_SOCKET)
    parser.add_argument("--state-dir", type=pathlib.Path, default=DEFAULT_STATE)
    parser.add_argument("--manifest", type=pathlib.Path, default=policy.DEFAULT_MANIFEST)
    parser.add_argument("--profiles", type=pathlib.Path, default=policy.DEFAULT_PROFILES)
    parser.add_argument("--pins", type=pathlib.Path, default=policy.DEFAULT_PINS)
    parser.add_argument(
        "--workload-policy",
        type=pathlib.Path,
        default=policy.DEFAULT_WORKLOAD_POLICY,
    )
    parser.add_argument("--registry", type=pathlib.Path)
    parser.add_argument("--manifest-dir", type=pathlib.Path)
    parser.add_argument(
        "--execution-contracts",
        type=pathlib.Path,
        default=policy.DEFAULT_EXECUTION_CONTRACTS,
    )
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise ServiceError("provisioner service must run as root")

    controller = pwd.getpwnam("ci-controller")
    store = StateStore(args.state_dir)
    registry = None
    project_manifests = None
    execution_contracts = None
    manifest = None
    if args.registry is not None:
        if args.manifest_dir is None:
            raise ServiceError("--registry requires --manifest-dir")
        registry = policy._load(args.registry)
        project_manifests = {}
        for project_id in registry.get("projects", {}):
            path = args.manifest_dir / f"{project_id}.json"
            if not path.is_file():
                raise ServiceError(f"registered project manifest missing: {path}")
            project_manifests[project_id] = policy._load(path)
        execution_contracts = policy._load(args.execution_contracts)
    else:
        manifest = policy._load(args.manifest)

    service = ProvisionerService(
        manifest=manifest,
        profiles=policy._load(args.profiles),
        pins=policy._load(args.pins),
        workload_policy=policy._load(args.workload_policy),
        state_store=store,
        controller_uid=controller.pw_uid,
        registry=registry,
        project_manifests=project_manifests,
        execution_contracts=execution_contracts,
        registry_path=args.registry,
        manifest_dir=args.manifest_dir,
    )
    serve(service, socket_path=args.socket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
