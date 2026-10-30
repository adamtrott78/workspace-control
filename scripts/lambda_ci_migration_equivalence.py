#!/usr/bin/env python3
"""Repository-only equivalence proof from legacy Lambda CI routes to v3 classes."""

from __future__ import annotations

import copy
import importlib.util
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
compiler = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
import sys
sys.modules["lambda_ci_policy_compiler"] = compiler
_spec.loader.exec_module(compiler)


class EquivalenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EquivalenceError(message)


def _current_route_envelope(
    data: dict[str, Any],
    *,
    project_id: str,
    route_id: str,
) -> dict[str, Any]:
    manifest = data["project_manifests"][project_id]
    route = manifest["routes"][route_id]
    contracts = data["contracts"]["contracts"]
    workload = data["workload_policy"]
    profiles = data["systemd_profiles"]

    contract_id = route["execution_contract_id"]
    contract = copy.deepcopy(contracts[contract_id])
    resource_id = contract["resource_class"]
    resource = copy.deepcopy(workload["resource_classes"][resource_id])
    profile_id = contract["execution_profile"]

    model_id = route["bindings"]["model_id"]
    runtime_id = route["bindings"]["runtime_id"]
    model_binding = compiler._resolve_model(workload, project_id, model_id)
    runtime_binding = compiler._resolve_runtime(workload, project_id, runtime_id)
    compiler._check_binding_mode(
        project_id=project_id,
        class_id=f"legacy-route:{route_id}",
        contract=contract,
        model_id=model_id,
        runtime_id=runtime_id,
    )

    gpu_uuids = list(resource.get("gpu_uuids", []))
    if resource.get("gpu_uuid") is not None:
        _require(not gpu_uuids, f"{project_id}/{route_id}: duplicate GPU representation")
        gpu_uuids = [resource["gpu_uuid"]]

    return {
        "project_id": project_id,
        "repository": manifest["repository"],
        "project_runner_identity": {
            "user": manifest["derived_identity"]["runner_user"],
            "group": manifest["derived_identity"]["runner_group"],
        },
        "project_roots": copy.deepcopy(manifest["roots"]),
        "forbidden_paths": copy.deepcopy(manifest["forbidden_paths"]),
        "execution_contract_id": contract_id,
        "execution_contract": contract,
        "resource_class_id": resource_id,
        "resource_class": resource,
        "systemd_common": compiler._generic_systemd_common(profiles, manifest),
        "systemd_profile": copy.deepcopy(profiles["profiles"][profile_id]),
        "exclusive_resource_claims": [f"gpu:{uuid}" for uuid in gpu_uuids],
        "bindings": {
            "model": model_binding,
            "runtime": runtime_binding,
        },
    }


def _target_route_envelope(
    compiled: dict[str, Any],
    *,
    class_id: str,
) -> dict[str, Any]:
    cls = compiled["root_projection"]["runner_classes"][class_id]
    keys = [
        "project_id",
        "repository",
        "project_runner_identity",
        "project_roots",
        "forbidden_paths",
        "execution_contract_id",
        "execution_contract",
        "resource_class_id",
        "resource_class",
        "systemd_common",
        "systemd_profile",
        "exclusive_resource_claims",
        "bindings",
    ]
    return {key: copy.deepcopy(cls[key]) for key in keys}


def verify_migration(root: pathlib.Path = ROOT) -> dict[str, Any]:
    data = compiler.load_inputs(root)
    compiled = compiler.compile_from_inputs(copy.deepcopy(data))

    rows = []
    for item in compiled["compatibility_matrix"]:
        project_id = item["project_id"]
        route_id = item["route_id"]
        target_class = item["target_runner_class_id"]

        current = _current_route_envelope(
            data,
            project_id=project_id,
            route_id=route_id,
        )
        target = _target_route_envelope(
            compiled,
            class_id=target_class,
        )
        _require(
            current == target,
            f"{project_id}/{route_id}: target runner class changes root launch semantics",
        )

        current_contract = current["execution_contract"]
        target_contract = target["execution_contract"]
        _require(
            int(target_contract["gpu_count"]) <= int(current_contract["gpu_count"]),
            f"{project_id}/{route_id}: target gains GPU authority",
        )
        _require(
            target_contract["payload_network_class"]
            == current_contract["payload_network_class"],
            f"{project_id}/{route_id}: payload network class changed",
        )
        _require(
            target_contract["filesystem_class"]
            == current_contract["filesystem_class"],
            f"{project_id}/{route_id}: filesystem class changed",
        )
        _require(
            target_contract["state_effect_class"]
            == current_contract["state_effect_class"],
            f"{project_id}/{route_id}: state-effect class changed",
        )

        manifest = data["project_manifests"][project_id]
        legacy_route = manifest["routes"][route_id]
        rows.append({
            "project_id": project_id,
            "route_id": route_id,
            "legacy_lane": legacy_route["lane"],
            "legacy_scale_set_name": item["legacy_scale_set_name"],
            "target_runner_class_id": target_class,
            "target_scale_set_name": item["target_scale_set_name"],
            "execution_contract_id": current["execution_contract_id"],
            "gpu_count": current_contract["gpu_count"],
            "payload_network_class": current_contract["payload_network_class"],
            "root_launch_semantics": "EXACT_EQUIVALENT",
        })

    _require(len(rows) == 23, "expected 23 route equivalence proofs")
    return {
        "decision": "PASS",
        "route_count": len(rows),
        "exact_equivalence_count": sum(
            row["root_launch_semantics"] == "EXACT_EQUIVALENT"
            for row in rows
        ),
        "rows": sorted(rows, key=lambda x: (x["project_id"], x["route_id"])),
    }


def main() -> int:
    result = verify_migration(ROOT)
    print("MIGRATION_EQUIVALENCE=PASS")
    print(f"ROUTES={result['route_count']}")
    print(f"EXACT_EQUIVALENCE={result['exact_equivalence_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
