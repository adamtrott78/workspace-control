#!/usr/bin/env python3
"""Root-only launch-spec adapter for Lambda CI v3 runner classes.

This module converts one compiled immutable root runner-class projection into
the existing hardened runtime launch-spec shape.  It accepts no GitHub/job
semantics and no caller-selected resource fields.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from typing import Any


class V3SpecError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class RuntimeRequest:
    request_id: str
    jit_config: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise V3SpecError(message)


def _parse_memory_bytes(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        _require(value > 0, "memory value must be positive")
        return value
    _require(isinstance(value, str), "systemd memory value must be string/int")
    match = re.fullmatch(r"([1-9][0-9]*)([KMG])", value)
    _require(match is not None, f"unsupported systemd memory value: {value!r}")
    factor = {"K": 1024, "M": 1024**2, "G": 1024**3}[match.group(2)]
    return int(match.group(1)) * factor


def _parse_runtime_seconds(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        _require(value > 0, "runtime value must be positive")
        return value
    _require(isinstance(value, str), "systemd runtime value must be string/int")
    match = re.fullmatch(r"([1-9][0-9]*)(s|min|h)", value)
    _require(match is not None, f"unsupported systemd runtime value: {value!r}")
    factor = {"s": 1, "min": 60, "h": 3600}[match.group(2)]
    return int(match.group(1)) * factor


def _gpu_uuids(resource: dict[str, Any]) -> list[str]:
    values = list(resource.get("gpu_uuids", []))
    single = resource.get("gpu_uuid")
    if single is not None:
        _require(not values, "resource class mixes gpu_uuid and gpu_uuids")
        values = [single]
    _require(
        all(isinstance(value, str) and value for value in values),
        "GPU UUID set is invalid",
    )
    _require(
        len({value.lower() for value in values}) == len(values),
        "GPU UUID set contains duplicates",
    )
    return values


def build_launch_spec(
    *,
    root_projection: dict[str, Any],
    runner_class_id: str,
    request_id: str,
    runner_name: str,
    jit_config: str,
) -> tuple[RuntimeRequest, dict[str, Any]]:
    classes = root_projection.get("runner_classes")
    _require(isinstance(classes, dict), "root projection runner_classes missing")
    cls = classes.get(runner_class_id)
    _require(isinstance(cls, dict), "unknown runner class")

    prefix = cls["runner_prefix"]
    _require(
        isinstance(runner_name, str) and runner_name.startswith(prefix),
        "runner name does not match immutable class prefix",
    )
    _require(isinstance(jit_config, str) and jit_config, "JIT config required")

    contract = copy.deepcopy(cls["execution_contract"])
    resource = copy.deepcopy(cls["resource_class"])
    profile = contract["execution_profile"]
    _require(
        cls["resource_class_id"] == contract["resource_class"],
        "resource class identity differs from execution contract",
    )
    gpu_uuids = _gpu_uuids(resource)
    _require(
        len(gpu_uuids) == int(contract["gpu_count"]),
        "GPU resource cardinality differs from execution contract",
    )

    systemd_profile = copy.deepcopy(cls["systemd_profile"])
    cpu_quota = systemd_profile.get("CPUQuota")
    _require(
        isinstance(cpu_quota, str) and cpu_quota.endswith("%"),
        "systemd CPUQuota is invalid",
    )
    try:
        cpu_quota_percent = int(cpu_quota[:-1])
    except ValueError as exc:
        raise V3SpecError("systemd CPUQuota is invalid") from exc
    _require(cpu_quota_percent > 0, "systemd CPUQuota must be positive")

    roots = cls["project_roots"]
    required_roots = {"jobs", "staging_cache", "trusted_cache", "home", "logs"}
    _require(required_roots <= set(roots), "project roots are incomplete")

    pins = root_projection.get("upstream_pins")
    _require(isinstance(pins, dict), "root projection upstream pins missing")
    runner_release = pins.get("actions_runner")
    _require(isinstance(runner_release, dict), "actions runner pin missing")
    for key in ("version", "asset_name", "linux_x64_sha256"):
        _require(
            isinstance(runner_release.get(key), str) and runner_release[key],
            f"actions runner pin missing {key}",
        )

    max_runtime = min(
        _parse_runtime_seconds(systemd_profile["RuntimeMaxSec"]),
        int(resource["runtime_seconds"]),
    )
    _require(max_runtime > 0, "runtime bound must be positive")

    bindings = cls.get("bindings")
    _require(isinstance(bindings, dict), "runner-class bindings missing")
    model_binding = copy.deepcopy(bindings.get("model"))
    runtime_binding = copy.deepcopy(bindings.get("runtime"))

    spec = {
        "schema_version": 3,
        "unit_name": (
            f"workspace-ci-v3-{runner_class_id}-{request_id}.service"
        ),
        "project_id": cls["project_id"],
        "runner_class_id": runner_class_id,
        "profile": profile,
        "workload_class": runner_class_id,
        "execution_contract": contract,
        "runner_name": runner_name,
        "admission": None,
        "request_digest_sha256": None,
        "root_policy_sha256": root_projection["root_policy_sha256"],
        "root_envelope_sha256": cls["root_envelope_sha256"],
        "run_as": copy.deepcopy(cls["project_runner_identity"]),
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
            "jit_config_env_value": jit_config,
        },
        "resources": {
            "cpu_quota_percent": cpu_quota_percent,
            "memory_max_bytes": _parse_memory_bytes(systemd_profile["MemoryMax"]),
            "tasks_max": int(systemd_profile["TasksMax"]),
            "runtime_max_seconds": max_runtime,
            "gpu_indices": list(range(len(gpu_uuids))),
            "gpu_uuid": gpu_uuids[0] if len(gpu_uuids) == 1 else None,
            "gpu_uuids": gpu_uuids,
        },
        "systemd_common": copy.deepcopy(cls["systemd_common"]),
        "systemd_profile": systemd_profile,
        "forbidden_paths": copy.deepcopy(cls["forbidden_paths"]),
        "allow_production_services": False,
        "runtime_binding": runtime_binding,
        "model_binding": model_binding,
    }
    return RuntimeRequest(request_id=request_id, jit_config=jit_config), spec
