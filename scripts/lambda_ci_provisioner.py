#!/usr/bin/env python3
"""Static policy engine for the Lambda CI root provisioner.

P5 v1 remains the accepted cpu-test/gpu-small request path.
Admission v2 is additive and root-owned: controller facts are attestations,
while this module derives the actual profile/capability grant from local policy.
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
import pathlib
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import lambda_ci_admission as admission_policy  # noqa: E402
import lambda_ci_multirepo as multirepo_policy  # noqa: E402

DEFAULT_MANIFEST = ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json"
DEFAULT_PROFILES = ROOT / "architecture" / "lambda-ci-systemd-profiles.v1.json"
DEFAULT_PINS = ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json"
DEFAULT_WORKLOAD_POLICY = ROOT / "architecture" / "lambda-ci-workload-policy.v1.json"
DEFAULT_PROJECT_REGISTRY = ROOT / "architecture" / "lambda-ci-project-registry.v1.json"
DEFAULT_EXECUTION_CONTRACTS = ROOT / "architecture" / "lambda-ci-execution-contracts.v1.json"

_ALLOWED_REQUEST_KEYS = {
    "schema_version",
    "request_id",
    "project_id",
    "profile",
    "runner_name",
    "jit_config",
}
_ALLOWED_REQUEST_KEYS_V2 = {
    "schema_version",
    "request_id",
    "project_id",
    "workload_class",
    "runner_name",
    "jit_config",
    "attestation",
}
_RUNNER_NAME = re.compile(r"^lambda-research-engine-[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_JIT_BYTES = 128 * 1024


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedRequest:
    request_id: str
    project_id: str
    profile: str
    runner_name: str
    jit_config: str
    workload_class: str | None = None
    admission: dict[str, Any] | None = None
    request_digest_sha256: str | None = None


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_request_id(value: Any) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise PolicyError("request_id must be UUID") from exc


def _validate_runner_name(value: Any) -> str:
    if not isinstance(value, str) or not _RUNNER_NAME.fullmatch(value):
        raise PolicyError("runner_name rejected")
    return value


def _validate_jit(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise PolicyError("jit_config must be non-empty string")
    if len(value.encode("utf-8")) > _MAX_JIT_BYTES:
        raise PolicyError("jit_config exceeds size limit")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise PolicyError("jit_config must be strict base64") from exc
    if not decoded:
        raise PolicyError("jit_config decodes empty")
    return value


def validate_request(data: dict[str, Any], manifest: dict[str, Any]) -> ValidatedRequest:
    """Validate the exact accepted P5 v1 request contract."""

    if set(data) != _ALLOWED_REQUEST_KEYS:
        extra = sorted(set(data) - _ALLOWED_REQUEST_KEYS)
        missing = sorted(_ALLOWED_REQUEST_KEYS - set(data))
        raise PolicyError(f"request keys mismatch extra={extra} missing={missing}")

    if data["schema_version"] != 1:
        raise PolicyError("unsupported schema_version")

    request_id = _validate_request_id(data["request_id"])

    project_id = data["project_id"]
    if project_id != manifest["project_id"]:
        raise PolicyError("project_id not authorized by manifest")

    profile = data["profile"]
    if profile not in manifest["profiles"]:
        raise PolicyError("profile not authorized by manifest")

    return ValidatedRequest(
        request_id=request_id,
        project_id=project_id,
        profile=profile,
        runner_name=_validate_runner_name(data["runner_name"]),
        jit_config=_validate_jit(data["jit_config"]),
        workload_class=profile,
    )


def validate_request_v2(
    data: dict[str, Any],
    manifest: dict[str, Any],
    workload_policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> ValidatedRequest:
    """Validate a controller-attested claim and mint a root-owned admission."""

    if set(data) != _ALLOWED_REQUEST_KEYS_V2:
        extra = sorted(set(data) - _ALLOWED_REQUEST_KEYS_V2)
        missing = sorted(_ALLOWED_REQUEST_KEYS_V2 - set(data))
        raise PolicyError(f"v2 request keys mismatch extra={extra} missing={missing}")
    if data["schema_version"] != 2:
        raise PolicyError("v2 request requires schema_version=2")

    request_id = _validate_request_id(data["request_id"])
    if data["project_id"] != manifest["project_id"]:
        raise PolicyError("project_id not authorized by manifest")
    runner_name = _validate_runner_name(data["runner_name"])
    jit_config = _validate_jit(data["jit_config"])

    normalized = dict(data)
    normalized["request_id"] = request_id
    normalized["runner_name"] = runner_name
    normalized["jit_config"] = jit_config

    try:
        admission = admission_policy.mint_admission(
            normalized,
            manifest,
            workload_policy,
            now=now,
            policy_sha256=policy_sha256,
        )
    except admission_policy.AdmissionError as exc:
        raise PolicyError(f"admission rejected: {exc}") from exc

    return ValidatedRequest(
        request_id=request_id,
        project_id=manifest["project_id"],
        profile=admission["execution_profile"],
        runner_name=runner_name,
        jit_config=jit_config,
        workload_class=admission["workload_class"],
        admission=admission,
        request_digest_sha256=admission["request_digest_sha256"],
    )



def validate_request_v2_generic(
    data: dict[str, Any],
    manifest: dict[str, Any],
    execution_contracts: dict[str, Any],
    workload_policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> ValidatedRequest:
    """Validate a project-manifest-v2 request without route-name privilege."""

    if set(data) != _ALLOWED_REQUEST_KEYS_V2:
        extra = sorted(set(data) - _ALLOWED_REQUEST_KEYS_V2)
        missing = sorted(_ALLOWED_REQUEST_KEYS_V2 - set(data))
        raise PolicyError(f"v2 request keys mismatch extra={extra} missing={missing}")
    if data["schema_version"] != 2:
        raise PolicyError("generic v2 request requires schema_version=2")

    request_id = _validate_request_id(data["request_id"])
    jit_config = _validate_jit(data["jit_config"])
    normalized = dict(data)
    normalized["request_id"] = request_id
    normalized["jit_config"] = jit_config

    try:
        admission = multirepo_policy.mint_admission(
            normalized,
            manifest,
            execution_contracts,
            workload_policy,
            now=now,
            policy_sha256=policy_sha256,
        )
    except multirepo_policy.MultiRepoPolicyError as exc:
        raise PolicyError(f"generic admission rejected: {exc}") from exc

    return ValidatedRequest(
        request_id=request_id,
        project_id=manifest["project_id"],
        profile=admission["execution_profile"],
        runner_name=data["runner_name"],
        jit_config=jit_config,
        workload_class=admission["workload_class"],
        admission=admission,
        request_digest_sha256=admission["request_digest_sha256"],
    )

def build_legacy_launch_spec(
    request: ValidatedRequest,
    manifest: dict[str, Any],
    profiles: dict[str, Any],
    pins: dict[str, Any],
) -> dict[str, Any]:
    project_profile = manifest["profiles"][request.profile]
    systemd_profile = profiles["profiles"][request.profile]

    job_root = pathlib.PurePosixPath(manifest["roots"]["jobs"])
    staging = pathlib.PurePosixPath(manifest["roots"]["staging_cache"])
    trusted = pathlib.PurePosixPath(manifest["roots"]["trusted_cache"])
    home = pathlib.PurePosixPath(manifest["roots"]["home"])
    logs = pathlib.PurePosixPath(manifest["roots"]["logs"])

    unit_name = f"workspace-ci-{request.project_id}-{request.request_id}.service"
    runner_release = pins["actions_runner"]
    runtime_binding = manifest.get("expanded_runtime_bindings", {}).get(request.profile)
    model_binding = None
    if request.admission is not None and request.workload_class:
        route = manifest.get("admission_v2", {}).get("routes", {}).get(
            request.workload_class,
            {},
        )
        binding_id = route.get("model_binding_id") if isinstance(route, dict) else None
        if binding_id is not None:
            model_binding = manifest.get("promoted_model_bindings", {}).get(binding_id)
            if not isinstance(model_binding, dict):
                raise PolicyError("admitted workload promoted model binding is missing")

    profile_gpu_uuids = project_profile.get("gpu_uuids")
    if profile_gpu_uuids is None:
        single_gpu_uuid = project_profile.get("gpu_uuid")
        profile_gpu_uuids = [single_gpu_uuid] if single_gpu_uuid is not None else []

    # This is a declarative spec consumed only by the privileged launcher.
    # The only secret is jit_config_env_value; callers must not log/serialize it.
    return {
        "schema_version": 2 if request.admission is not None else 1,
        "unit_name": unit_name,
        "project_id": request.project_id,
        "profile": request.profile,
        "workload_class": request.workload_class or request.profile,
        "runner_name": request.runner_name,
        "admission": request.admission,
        "request_digest_sha256": request.request_digest_sha256,
        "run_as": {
            "user": manifest["runner_user"],
            "group": manifest["runner_group"],
        },
        "paths": {
            "job_root": str(job_root),
            "staging_cache": str(staging),
            "trusted_cache": str(trusted),
            "home": str(home),
            "logs": str(logs),
        },
        "runner": {
            "version": runner_release["version"],
            "asset_name": runner_release["asset_name"],
            "sha256": runner_release["linux_x64_sha256"],
            "fixed_command": ["./run.sh"],
            "jit_config_env_name": "ACTIONS_RUNNER_INPUT_JITCONFIG",
            "jit_config_env_value": request.jit_config,
        },
        "resources": {
            "cpu_quota_percent": project_profile["cpu_quota_percent"],
            "memory_max_bytes": project_profile["memory_max_bytes"],
            "tasks_max": project_profile["tasks_max"],
            "runtime_max_seconds": project_profile["runtime_max_seconds"],
            "gpu_indices": project_profile["gpu_indices"],
            "gpu_uuid": project_profile.get("gpu_uuid"),
            "gpu_uuids": list(profile_gpu_uuids),
        },
        "systemd_common": profiles["common"],
        "systemd_profile": systemd_profile,
        "forbidden_paths": manifest["forbidden_paths"],
        "allow_production_services": project_profile["allow_production_services"],
        "runtime_binding": runtime_binding,
        "model_binding": model_binding,
    }



def _parse_memory_bytes(value: Any) -> int:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise PolicyError("systemd memory value is invalid")
    match = re.fullmatch(r"([1-9][0-9]*)([KMG])", value)
    if match is None:
        raise PolicyError(f"unsupported systemd memory value: {value}")
    factor = {"K": 1024, "M": 1024**2, "G": 1024**3}[match.group(2)]
    return int(match.group(1)) * factor


def _parse_runtime_seconds(value: Any) -> int:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise PolicyError("systemd runtime value is invalid")
    match = re.fullmatch(r"([1-9][0-9]*)(s|min|h)", value)
    if match is None:
        raise PolicyError(f"unsupported systemd runtime value: {value}")
    factor = {"s": 1, "min": 60, "h": 3600}[match.group(2)]
    return int(match.group(1)) * factor


def _generic_systemd_common(
    profiles: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    common = copy.deepcopy(profiles["common"])
    ident = manifest["derived_identity"]
    roots = manifest["roots"]
    common["User"] = ident["runner_user"]
    common["Group"] = ident["runner_group"]
    common["Environment"] = [
        f"HOME={roots['home']}",
        f"XDG_CACHE_HOME={roots['staging_cache']}",
        f"HF_HOME={roots['staging_cache']}/huggingface",
        f"TRANSFORMERS_CACHE={roots['staging_cache']}/huggingface/transformers",
    ]
    common["ReadWritePaths"] = [
        roots["jobs"],
        roots["staging_cache"],
        roots["home"],
    ]
    common["ReadOnlyPaths"] = [roots["trusted_cache"]]
    return common


def build_generic_launch_spec(
    request: ValidatedRequest,
    manifest: dict[str, Any],
    profiles: dict[str, Any],
    pins: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(request.admission, dict):
        raise PolicyError("generic launch requires root-issued admission")
    try:
        semantics = multirepo_policy.execution_semantics_from_admission(
            request.admission
        )
    except multirepo_policy.MultiRepoPolicyError as exc:
        raise PolicyError(f"generic execution semantics invalid: {exc}") from exc

    profile = request.profile
    systemd_profile = copy.deepcopy(profiles["profiles"].get(profile))
    if not isinstance(systemd_profile, dict):
        raise PolicyError("generic execution profile is unknown")
    if semantics.get("execution_profile") != profile:
        raise PolicyError("execution semantics/profile mismatch")

    roots = manifest["roots"]
    ident = manifest["derived_identity"]
    runner_release = pins["actions_runner"]
    gpu_uuids = list(request.admission["resource_ceiling"].get("gpu_uuids", []))
    gpu_count = int(semantics.get("gpu_count", -1))
    if len(gpu_uuids) != gpu_count:
        raise PolicyError("generic GPU UUID count differs from semantic contract")
    gpu_indices = list(range(gpu_count))

    cpu_quota = systemd_profile.get("CPUQuota")
    if not isinstance(cpu_quota, str) or not cpu_quota.endswith("%"):
        raise PolicyError("systemd CPUQuota is invalid")
    try:
        cpu_quota_percent = int(cpu_quota[:-1])
    except ValueError as exc:
        raise PolicyError("systemd CPUQuota is invalid") from exc

    models = request.admission.get("models") or []
    if len(models) > 1:
        raise PolicyError("generic v1 launcher supports at most one model binding")
    model_binding = copy.deepcopy(models[0]) if models else None
    runtime_binding = copy.deepcopy(request.admission.get("runtime"))

    return {
        "schema_version": 2,
        "unit_name": f"workspace-ci-{request.project_id}-{request.request_id}.service",
        "project_id": request.project_id,
        "profile": profile,
        "workload_class": request.workload_class,
        "execution_contract": semantics,
        "runner_name": request.runner_name,
        "admission": request.admission,
        "request_digest_sha256": request.request_digest_sha256,
        "run_as": {
            "user": ident["runner_user"],
            "group": ident["runner_group"],
        },
        "paths": {
            "job_root": roots["jobs"],
            "staging_cache": roots["staging_cache"],
            "trusted_cache": roots["trusted_cache"],
            "home": roots["home"],
            "logs": roots["logs"],
        },
        "runner": {
            "version": runner_release["version"],
            "asset_name": runner_release["asset_name"],
            "sha256": runner_release["linux_x64_sha256"],
            "fixed_command": ["./run.sh"],
            "jit_config_env_name": "ACTIONS_RUNNER_INPUT_JITCONFIG",
            "jit_config_env_value": request.jit_config,
        },
        "resources": {
            "cpu_quota_percent": cpu_quota_percent,
            "memory_max_bytes": _parse_memory_bytes(systemd_profile["MemoryMax"]),
            "tasks_max": int(systemd_profile["TasksMax"]),
            "runtime_max_seconds": min(
                _parse_runtime_seconds(systemd_profile["RuntimeMaxSec"]),
                int(request.admission["resource_ceiling"]["runtime_seconds"]),
            ),
            "gpu_indices": gpu_indices,
            "gpu_uuid": gpu_uuids[0] if gpu_count == 1 else None,
            "gpu_uuids": gpu_uuids,
        },
        "systemd_common": _generic_systemd_common(profiles, manifest),
        "systemd_profile": systemd_profile,
        "forbidden_paths": list(manifest["forbidden_paths"]),
        "allow_production_services": False,
        "runtime_binding": runtime_binding,
        "model_binding": model_binding,
    }


def build_launch_spec(
    request: ValidatedRequest,
    manifest: dict[str, Any],
    profiles: dict[str, Any],
    pins: dict[str, Any],
) -> dict[str, Any]:
    if manifest.get("schema_version") == 2:
        return build_generic_launch_spec(request, manifest, profiles, pins)
    spec = build_legacy_launch_spec(request, manifest, profiles, pins)
    if isinstance(request.admission, dict):
        try:
            spec["execution_contract"] = (
                multirepo_policy.execution_semantics_from_admission(
                    request.admission
                )
            )
        except multirepo_policy.MultiRepoPolicyError as exc:
            raise PolicyError(f"legacy execution semantics invalid: {exc}") from exc
    return spec

def redacted_spec(spec: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(spec))
    clone["runner"]["jit_config_env_value"] = "<REDACTED>"
    return clone


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("request", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    p.add_argument("--profiles", type=pathlib.Path, default=DEFAULT_PROFILES)
    p.add_argument("--pins", type=pathlib.Path, default=DEFAULT_PINS)
    p.add_argument(
        "--workload-policy",
        type=pathlib.Path,
        default=DEFAULT_WORKLOAD_POLICY,
    )
    p.add_argument("--registry", type=pathlib.Path)
    p.add_argument("--project-manifest", type=pathlib.Path, action="append", default=[])
    p.add_argument("--execution-contracts", type=pathlib.Path, default=DEFAULT_EXECUTION_CONTRACTS)
    p.add_argument("--emit-redacted-spec", action="store_true")
    args = p.parse_args()

    profiles = _load(args.profiles)
    pins = _load(args.pins)
    workload_policy = _load(args.workload_policy)
    request_data = _load(args.request)

    if args.registry is not None:
        registry = _load(args.registry)
        manifests = {}
        for path in args.project_manifest:
            candidate = _load(path)
            manifests[candidate["project_id"]] = candidate
        try:
            manifest = multirepo_policy.resolve_project_manifest(
                registry,
                manifests,
                str(request_data.get("project_id", "")),
            )
        except multirepo_policy.MultiRepoPolicyError as exc:
            raise PolicyError(f"project registry resolution failed: {exc}") from exc
        if request_data.get("schema_version") != 2:
            raise PolicyError("multi-project registry mode requires schema_version=2")
        req = validate_request_v2_generic(
            request_data,
            manifest,
            _load(args.execution_contracts),
            workload_policy,
        )
    else:
        manifest = _load(args.manifest)
        if request_data.get("schema_version") == 2:
            req = validate_request_v2(
                request_data,
                manifest,
                workload_policy,
            )
        else:
            req = validate_request(request_data, manifest)
    spec = build_launch_spec(req, manifest, profiles, pins)

    if args.emit_redacted_spec:
        print(json.dumps(redacted_spec(spec), indent=2, sort_keys=True))
    else:
        print("REQUEST_POLICY=PASS")
        print(f"PROJECT={req.project_id}")
        print(f"PROFILE={req.profile}")
        print(f"WORKLOAD={req.workload_class or req.profile}")
        print(f"RUNNER={req.runner_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
