#!/usr/bin/env python3
"""Pure repository-only compiler for the modeled Lambda CI v3 control plane.

This module does not access GitHub, systemd, sockets, or Lambda.  It compiles
frozen policy/evidence inputs into root/controller/executor projections and a
compatibility matrix.  It is intentionally strict: semantic disagreement is a
compile-time error.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

INPUT_PATHS = {
    "catalog": "architecture/lambda-ci-runner-class-catalog.v1.json",
    "registry": "architecture/lambda-ci-project-registry.v1.json",
    "contracts": "architecture/lambda-ci-execution-contracts.v1.json",
    "workload_policy": "architecture/lambda-ci-workload-policy.v1.json",
    "systemd_profiles": "architecture/lambda-ci-systemd-profiles.v1.json",
    "host_resources": "architecture/lambda-ci-host-resource-policy.v1.json",
    "workflow_evidence": "architecture/lambda-ci-trusted-workflow-evidence.v1.json",
    "parameter_schemas": "architecture/lambda-ci-ingress-parameter-schemas.v1.json",
    "maintenance_actions": "architecture/lambda-ci-maintenance-actions.v2.json",
    "upstream_pins": "architecture/lambda-ci-upstream-pins.v1.json",
    "root_projection_schema": "schemas/workspace-ci-root-policy-projection.v1.schema.json",
    "controller_projection_schema": "schemas/workspace-ci-runner-class-controller-policy.v1.schema.json",
    "executor_projection_schema": "schemas/workspace-ci-executor-policy-projection.v1.schema.json",
}

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{1,20}$")
CONTROLLER_USER = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


class CompileError(ValueError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompileError(f"{path}: expected JSON object")
    return value


def load_inputs(root: pathlib.Path = ROOT) -> dict[str, Any]:
    data = {key: _load(root / rel) for key, rel in INPUT_PATHS.items()}
    registry = data["registry"]
    manifests: dict[str, dict[str, Any]] = {}
    for project_id, entry in registry.get("projects", {}).items():
        source = entry.get("manifest_source_path")
        if not isinstance(source, str):
            raise CompileError(f"registry project {project_id}: manifest_source_path missing")
        manifests[project_id] = _load(root / source)
    data["project_manifests"] = manifests
    return data


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_object(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CompileError(message)


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


def _resolve_model(
    workload_policy: dict[str, Any],
    manifest: dict[str, Any],
    project_id: str,
    model_id: str | None,
) -> dict[str, Any] | None:
    if model_id is None:
        return None

    policy_binding = workload_policy.get("project_bindings", {}).get(project_id, {})
    allowed = policy_binding.get("allowed_models", [])
    matches = [
        item
        for item in allowed
        if isinstance(item, dict) and item.get("model_id") == model_id
    ]
    _require(
        len(matches) == 1,
        f"{project_id}: model authorization {model_id!r} not uniquely resolved",
    )
    authorized = matches[0]

    materialized = manifest.get("bindings", {}).get("models", {}).get(model_id)
    _require(
        isinstance(materialized, dict),
        f"{project_id}: materialized model binding {model_id!r} missing",
    )
    required = {
        "model_id",
        "repository",
        "revision",
        "object_path",
        "object_id",
        "tree_sha256",
        "manifest_sha256",
        "descriptor_sha256",
        "promotion_receipt_sha256",
        "serialization_risk_class",
        "complete_offline",
    }
    _require(
        set(materialized) == required,
        f"{project_id}: materialized model binding keys drift",
    )
    for key in ("model_id", "repository", "revision"):
        _require(
            materialized[key] == authorized[key],
            f"{project_id}: materialized model {key} differs from workload authorization",
        )
    _require(
        authorized.get("serialization_requirement") == "SAFE_ONLY",
        f"{project_id}: model authorization is not SAFE_ONLY",
    )
    _require(
        authorized.get("promotion_required_before_eval") is True,
        f"{project_id}: model authorization must require promotion",
    )
    _require(
        materialized["serialization_risk_class"] == "SAFE",
        f"{project_id}: materialized model is not SAFE",
    )
    _require(
        materialized["complete_offline"] is True,
        f"{project_id}: materialized model is not complete offline",
    )
    _require(
        materialized["object_id"]
        == materialized["tree_sha256"]
        == materialized["manifest_sha256"],
        f"{project_id}: materialized model object/tree/manifest identity drift",
    )
    return copy.deepcopy(materialized)


def _resolve_runtime(
    workload_policy: dict[str, Any],
    manifest: dict[str, Any],
    project_id: str,
    runtime_id: str | None,
) -> dict[str, Any] | None:
    if runtime_id is None:
        return None

    policy_binding = workload_policy.get("project_bindings", {}).get(project_id, {})
    allowed = policy_binding.get("allowed_runtimes", [])
    matches = [
        item
        for item in allowed
        if isinstance(item, dict) and item.get("runtime_id") == runtime_id
    ]
    _require(
        len(matches) == 1,
        f"{project_id}: runtime authorization {runtime_id!r} not uniquely resolved",
    )
    authorized = matches[0]

    materialized = manifest.get("bindings", {}).get("runtimes", {}).get(runtime_id)
    _require(
        isinstance(materialized, dict),
        f"{project_id}: materialized runtime binding {runtime_id!r} missing",
    )
    required = {
        "runtime_id",
        "canonical_path",
        "python_path",
        "receipt_path",
        "tree_digest_sha256",
        "manifest_identity_sha256",
        "source_trusted_runtime_object",
        "required_controls",
    }
    _require(
        set(materialized) == required,
        f"{project_id}: materialized runtime binding keys drift",
    )
    _require(
        authorized.get("promotion_required_before_eval") is True,
        f"{project_id}: runtime authorization must require promotion",
    )
    expanded = authorized.get("expanded_runtime")
    _require(
        isinstance(expanded, dict),
        f"{project_id}: authorized expanded runtime metadata missing",
    )
    _require(
        materialized["runtime_id"] == authorized["runtime_id"],
        f"{project_id}: materialized runtime id differs from authorization",
    )
    for key in (
        "canonical_path",
        "receipt_path",
        "tree_digest_sha256",
        "manifest_identity_sha256",
    ):
        _require(
            materialized[key] == expanded.get(key),
            f"{project_id}: materialized runtime {key} differs from authorization",
        )
    _require(
        materialized["python_path"]
        == str(pathlib.Path(materialized["canonical_path"]) / "bin/python"),
        f"{project_id}: materialized runtime python path drift",
    )
    _require(
        isinstance(materialized["required_controls"], list)
        and len(materialized["required_controls"]) > 0,
        f"{project_id}: materialized runtime controls missing",
    )
    return copy.deepcopy(materialized)


def _check_binding_mode(
    *,
    project_id: str,
    class_id: str,
    contract: dict[str, Any],
    model_id: str | None,
    runtime_id: str | None,
) -> None:
    model_mode = contract.get("model_binding_mode")
    runtime_mode = contract.get("runtime_binding_mode")
    if model_mode == "FORBIDDEN":
        _require(model_id is None, f"{project_id}/{class_id}: model binding forbidden")
    elif model_mode == "REQUIRED_PROMOTED_EXACT":
        _require(model_id is not None, f"{project_id}/{class_id}: model binding required")

    if runtime_mode == "REQUIRED_EXPANDED_RUNTIME_EXACT":
        _require(runtime_id is not None, f"{project_id}/{class_id}: runtime binding required")


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise CompileError(f"unsupported schema type {expected!r}")


def _validate_json_schema_subset(
    value: Any,
    schema: dict[str, Any],
    *,
    path: str = "$",
) -> None:
    """Validate the bounded JSON-Schema subset used by compiler projections."""
    if "oneOf" in schema:
        successes = 0
        errors: list[str] = []
        for candidate in schema["oneOf"]:
            try:
                _validate_json_schema_subset(value, candidate, path=path)
            except CompileError as exc:
                errors.append(str(exc))
            else:
                successes += 1
        _require(successes == 1, f"{path}: oneOf matched {successes} branches; {errors[:3]}")
        return

    if "const" in schema:
        _require(value == schema["const"], f"{path}: value differs from const")
    if "enum" in schema:
        _require(value in schema["enum"], f"{path}: value not in enum")

    expected_type = schema.get("type")
    if expected_type is not None:
        types = expected_type if isinstance(expected_type, list) else [expected_type]
        _require(
            any(_schema_type_matches(value, item) for item in types),
            f"{path}: type mismatch expected {types}",
        )

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        _require(not missing, f"{path}: missing required keys {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            _require(not extra, f"{path}: unexpected keys {extra}")
        additional_schema = schema.get("additionalProperties")
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is None and isinstance(additional_schema, dict):
                child_schema = additional_schema
            if child_schema is not None:
                _validate_json_schema_subset(child, child_schema, path=f"{path}.{key}")
        if "minProperties" in schema:
            _require(len(value) >= int(schema["minProperties"]), f"{path}: too few properties")

    if isinstance(value, list):
        if "minItems" in schema:
            _require(len(value) >= int(schema["minItems"]), f"{path}: too few items")
        if schema.get("uniqueItems") is True:
            encoded = [canonical_bytes(item) for item in value]
            _require(len(encoded) == len(set(encoded)), f"{path}: items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                _validate_json_schema_subset(child, item_schema, path=f"{path}[{index}]")

    if isinstance(value, str):
        if "minLength" in schema:
            _require(len(value) >= int(schema["minLength"]), f"{path}: string too short")
        if "maxLength" in schema:
            _require(len(value) <= int(schema["maxLength"]), f"{path}: string too long")
        if "pattern" in schema:
            _require(re.search(schema["pattern"], value) is not None, f"{path}: pattern mismatch")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema:
            _require(value >= schema["minimum"], f"{path}: below minimum")
        if "maximum" in schema:
            _require(value <= schema["maximum"], f"{path}: above maximum")


def _validate_parameter_schema(
    schema_id: str,
    schema: dict[str, Any],
    *,
    execution_route: bool,
) -> list[dict[str, Any]]:
    _require(isinstance(schema, dict), f"{schema_id}: parameter schema must be object")
    _require(set(schema) == {"arguments"}, f"{schema_id}: parameter schema keys mismatch")
    arguments = schema["arguments"]
    _require(isinstance(arguments, list) and arguments, f"{schema_id}: arguments must be nonempty list")

    allowed_types = {"lower_hex_40", "enum", "catalog_runner_class_id", "uuid"}
    seen_names: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, arg in enumerate(arguments):
        _require(isinstance(arg, dict), f"{schema_id}: argument {index} must be object")
        allowed_keys = {"name", "type", "required", "values"}
        _require(set(arg) <= allowed_keys, f"{schema_id}: argument {index} has unsupported keys")
        _require({"name", "type", "required"} <= set(arg), f"{schema_id}: argument {index} missing required keys")
        name = arg["name"]
        arg_type = arg["type"]
        _require(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name), f"{schema_id}: invalid argument name")
        _require(name not in seen_names, f"{schema_id}: duplicate argument {name}")
        seen_names.add(name)
        _require(arg_type in allowed_types, f"{schema_id}: unsupported argument type {arg_type!r}")
        _require(isinstance(arg["required"], bool), f"{schema_id}/{name}: required must be boolean")
        if execution_route:
            _require(
                arg_type not in {"catalog_runner_class_id", "uuid"},
                f"{schema_id}/{name}: execution ingress cannot select infrastructure identity",
            )
            _require(
                not any(token in name for token in ("runner_class", "gpu", "runtime", "model", "resource", "profile")),
                f"{schema_id}/{name}: execution ingress argument name implies root authority",
            )
        if arg_type == "enum":
            values = arg.get("values")
            _require(isinstance(values, list) and values, f"{schema_id}/{name}: enum values required")
            _require(len(values) == len(set(values)), f"{schema_id}/{name}: enum values must be unique")
            _require(all(isinstance(value, str) and value for value in values), f"{schema_id}/{name}: enum values must be nonempty strings")
        else:
            _require("values" not in arg, f"{schema_id}/{name}: values only allowed for enum")
        normalized.append(copy.deepcopy(arg))
    return normalized


def _input_generation_material(data: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "catalog",
        "registry",
        "contracts",
        "workload_policy",
        "systemd_profiles",
        "host_resources",
        "workflow_evidence",
        "parameter_schemas",
        "maintenance_actions",
        "upstream_pins",
        "project_manifests",
    ]
    return {key: data[key] for key in keys}


def compile_from_inputs(data: dict[str, Any]) -> dict[str, Any]:
    catalog = data["catalog"]
    registry = data["registry"]
    contracts = data["contracts"]["contracts"]
    workload = data["workload_policy"]
    resource_classes = workload["resource_classes"]
    profiles = data["systemd_profiles"]
    host_resources = data["host_resources"]
    upstream_pins = data["upstream_pins"]
    evidence_entries = data["workflow_evidence"]["entries"]
    parameter_schemas = data["parameter_schemas"]["schemas"]
    maintenance = data["maintenance_actions"]
    manifests = data["project_manifests"]

    _require(catalog.get("schema_version") == 1, "catalog schema_version must be 1")
    _require(catalog.get("status") == "MODEL_ONLY_NOT_LIVE", "catalog must remain model-only")
    _require(set(catalog["projects"]) == set(registry["projects"]), "catalog/registry project sets differ")
    _require(set(catalog["projects"]) == set(manifests), "catalog/manifest project sets differ")

    evidence_by_route: dict[tuple[str, str], dict[str, Any]] = {}
    for item in evidence_entries:
        key = (item["project_id"], item["route_id"])
        _require(key not in evidence_by_route, f"duplicate workflow evidence: {key}")
        evidence_by_route[key] = item

    generation_sha = sha256_object(_input_generation_material(data))

    seen_class_ids: set[str] = set()
    seen_scale_sets: set[str] = set()
    seen_prefixes: set[str] = set()
    seen_users: set[str] = set()
    seen_workflows: set[tuple[str, str]] = set()
    seen_commands: set[tuple[str, str]] = set()

    root_classes: dict[str, Any] = {}
    controller_policies: dict[str, Any] = {}
    executor_actions: dict[str, Any] = {}
    compatibility: list[dict[str, Any]] = []

    for project_id in sorted(catalog["projects"]):
        _require(PROJECT_ID.fullmatch(project_id) is not None, f"invalid project_id {project_id}")
        project = catalog["projects"][project_id]
        reg_entry = registry["projects"][project_id]
        manifest = manifests[project_id]
        _require(project["repository"] == reg_entry["repository"], f"{project_id}: repository mismatch")
        _require(project["repository"] == manifest["repository"], f"{project_id}: manifest repository mismatch")
        _require(manifest["project_id"] == project_id, f"{project_id}: manifest project_id mismatch")

        class_ids = set(project["runner_classes"])
        for class_id in sorted(class_ids):
            cls = project["runner_classes"][class_id]
            _require(class_id not in seen_class_ids, f"duplicate runner_class_id {class_id}")
            seen_class_ids.add(class_id)

            scale_set = cls["scale_set_name"]
            prefix = cls["runner_prefix"]
            controller_user = cls["controller_peer"]["unix_user"]
            _require(scale_set not in seen_scale_sets, f"duplicate scale_set_name {scale_set}")
            _require(prefix not in seen_prefixes, f"duplicate runner_prefix {prefix}")
            _require(controller_user not in seen_users, f"duplicate controller unix user {controller_user}")
            _require(CONTROLLER_USER.fullmatch(controller_user) is not None, f"{class_id}: invalid controller unix user")
            seen_scale_sets.add(scale_set)
            seen_prefixes.add(prefix)
            seen_users.add(controller_user)

            contract_id = cls["execution_contract_id"]
            _require(contract_id in contracts, f"{class_id}: unknown execution contract {contract_id}")
            contract = copy.deepcopy(contracts[contract_id])
            resource_id = contract["resource_class"]
            _require(resource_id in resource_classes, f"{class_id}: unknown resource class {resource_id}")
            resource = copy.deepcopy(resource_classes[resource_id])
            profile_id = contract["execution_profile"]
            _require(profile_id in profiles["profiles"], f"{class_id}: unknown systemd profile {profile_id}")
            systemd_profile = copy.deepcopy(profiles["profiles"][profile_id])

            model_id = cls["bindings"]["model_id"]
            runtime_id = cls["bindings"]["runtime_id"]
            _check_binding_mode(
                project_id=project_id,
                class_id=class_id,
                contract=contract,
                model_id=model_id,
                runtime_id=runtime_id,
            )
            model_binding = _resolve_model(
                workload,
                manifest,
                project_id,
                model_id,
            )
            runtime_binding = _resolve_runtime(
                workload,
                manifest,
                project_id,
                runtime_id,
            )

            payload_broker_identity = None
            if (
                contract.get("payload_network_class")
                == "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE"
            ):
                broker_user = f"ci-payload-{project_id}"
                _require(
                    CONTROLLER_USER.fullmatch(broker_user) is not None,
                    f"{class_id}: invalid payload broker unix user",
                )
                _require(
                    broker_user != manifest["derived_identity"]["runner_user"],
                    f"{class_id}: payload broker user must differ from runner user",
                )
                _require(
                    broker_user != controller_user,
                    f"{class_id}: payload broker user must differ from controller user",
                )
                payload_broker_identity = {
                    "user": broker_user,
                    "group": manifest["derived_identity"]["runner_group"],
                }

            gpu_uuids = list(resource.get("gpu_uuids", []))
            if resource.get("gpu_uuid") is not None:
                _require(not gpu_uuids, f"{class_id}: both gpu_uuid and gpu_uuids present")
                gpu_uuids = [resource["gpu_uuid"]]
            _require(
                len(gpu_uuids) == int(contract["gpu_count"]),
                f"{class_id}: resource GPU UUID count differs from contract",
            )

            root_class = {
                "runner_class_id": class_id,
                "project_id": project_id,
                "repository": project["repository"],
                "control_plane_generation_sha256": generation_sha,
                "controller_peer": copy.deepcopy(cls["controller_peer"]),
                "scale_set_name": scale_set,
                "runner_prefix": prefix,
                "max_runners": int(cls["max_runners"]),
                "project_runner_identity": {
                    "user": manifest["derived_identity"]["runner_user"],
                    "group": manifest["derived_identity"]["runner_group"],
                },
                "payload_broker_identity": payload_broker_identity,
                "project_roots": copy.deepcopy(manifest["roots"]),
                "forbidden_paths": copy.deepcopy(manifest["forbidden_paths"]),
                "execution_contract_id": contract_id,
                "execution_contract": contract,
                "resource_class_id": resource_id,
                "resource_class": resource,
                "systemd_common": _generic_systemd_common(profiles, manifest),
                "systemd_profile": systemd_profile,
                "exclusive_resource_claims": [f"gpu:{uuid}" for uuid in gpu_uuids],
                "bindings": {
                    "model": model_binding,
                    "runtime": runtime_binding,
                },
                "project_max_active_runners": int(
                    host_resources["project_limits"][project_id]["max_active_runners"]
                ),
            }
            root_class["root_envelope_sha256"] = sha256_object(
                {k: v for k, v in root_class.items() if k not in {"control_plane_generation_sha256", "root_envelope_sha256"}}
            )
            root_classes[class_id] = root_class

            controller_policies[class_id] = {
                "schema_version": 1,
                "runner_class_id": class_id,
                "repository": project["repository"],
                "scale_set_name": scale_set,
                "runner_prefix": prefix,
                "max_runners": int(cls["max_runners"]),
                "trusted_workflows": [],
            }

        for route_id in sorted(project["routes"]):
            route = project["routes"][route_id]
            class_id = route["runner_class_id"]
            _require(class_id in class_ids, f"{project_id}/{route_id}: unknown class {class_id}")
            workflow = route["trusted_workflow"]
            wf_key = (project["repository"], workflow["path"])
            _require(wf_key not in seen_workflows, f"workflow registered more than once: {wf_key}")
            seen_workflows.add(wf_key)
            command_key = (project["repository"], route["ingress"]["command"])
            _require(command_key not in seen_commands, f"command registered more than once: {command_key}")
            seen_commands.add(command_key)

            parameter_schema_id = route["ingress"]["parameter_schema_id"]
            _require(
                parameter_schema_id in parameter_schemas,
                f"{project_id}/{route_id}: missing parameter schema {parameter_schema_id}",
            )
            route_arguments = _validate_parameter_schema(
                parameter_schema_id,
                parameter_schemas[parameter_schema_id],
                execution_route=True,
            )

            ev_key = (project_id, route_id)
            _require(ev_key in evidence_by_route, f"{project_id}/{route_id}: workflow evidence missing")
            ev = evidence_by_route[ev_key]
            _require(ev["repository"] == project["repository"], f"{project_id}/{route_id}: evidence repository mismatch")
            _require(ev["workflow_path"] == workflow["path"], f"{project_id}/{route_id}: evidence workflow path mismatch")
            _require(ev["workflow_blob_sha"] == workflow["blob_sha"], f"{project_id}/{route_id}: workflow blob mismatch")
            _require(HEX40.fullmatch(workflow["blob_sha"]) is not None, f"{project_id}/{route_id}: invalid workflow blob")
            _require(ev["top_level_job_count"] == 1, f"{project_id}/{route_id}: trusted workflow must have one top-level job")
            _require(ev["top_level_job_key"] == workflow["job_key"], f"{project_id}/{route_id}: compile-time job key mismatch")
            _require(
                ev["target_scale_set_name"] == root_classes[class_id]["scale_set_name"],
                f"{project_id}/{route_id}: target scale set differs from runner class",
            )

            controller_policies[class_id]["trusted_workflows"].append({
                "route_id": route_id,
                "path": workflow["path"],
                "default_branch": workflow["default_branch"],
                "blob_sha": workflow["blob_sha"],
                "compile_time_job_key": workflow["job_key"],
                "compile_time_top_level_job_count": ev["top_level_job_count"],
                "allowed_events": copy.deepcopy(workflow["allowed_events"]),
                "allowed_actor_logins": copy.deepcopy(workflow["allowed_actor_logins"]),
            })

            action_id = f"{project_id.replace('-', '_')}.{route_id.replace('-', '_')}"
            args = route_arguments
            executor_actions[action_id] = {
                "kind": "EXECUTION_TRIGGER",
                "repository": project["repository"],
                "route_id": route_id,
                "command": route["ingress"]["command"],
                "parameter_schema_id": parameter_schema_id,
                "arguments": args,
            }

            compatibility.append({
                "project_id": project_id,
                "route_id": route_id,
                "source_checkpoint": ev["source_checkpoint"],
                "workflow_path": workflow["path"],
                "workflow_blob_sha": workflow["blob_sha"],
                "legacy_scale_set_name": ev["current_scale_set_name"],
                "target_runner_class_id": class_id,
                "target_scale_set_name": root_classes[class_id]["scale_set_name"],
                "root_envelope_sha256": root_classes[class_id]["root_envelope_sha256"],
                "parameter_schema_id": parameter_schema_id,
            })

    _require(len(compatibility) == len(evidence_entries), "unused or missing workflow evidence entries")

    # Every exclusive GPU claim must exist in the host resource policy.
    known_resources = set(host_resources["exclusive_resources"])
    for class_id, root_class in root_classes.items():
        unknown = set(root_class["exclusive_resource_claims"]) - known_resources
        _require(not unknown, f"{class_id}: unknown exclusive resources {sorted(unknown)}")

    maintenance_actions: dict[str, Any] = {}
    for action_id, action in sorted(maintenance["actions"].items()):
        schema_id = action["parameter_schema_id"]
        _require(schema_id in parameter_schemas, f"{action_id}: missing maintenance parameter schema")
        maintenance_arguments = _validate_parameter_schema(
            schema_id,
            parameter_schemas[schema_id],
            execution_route=False,
        )
        maintenance_actions[action_id] = {
            **copy.deepcopy(action),
            "arguments": maintenance_arguments,
        }

    root_projection = {
        "schema_version": 1,
        "control_plane_generation_sha256": generation_sha,
        "host_resource_policy": copy.deepcopy(host_resources),
        "upstream_pins": copy.deepcopy(upstream_pins),
        "runner_classes": root_classes,
    }
    root_projection["root_policy_sha256"] = sha256_object({
        "schema_version": root_projection["schema_version"],
        "host_resource_policy": root_projection["host_resource_policy"],
        "upstream_pins": root_projection["upstream_pins"],
        "runner_classes": {
            class_id: {
                key: value
                for key, value in class_policy.items()
                if key != "control_plane_generation_sha256"
            }
            for class_id, class_policy in root_projection["runner_classes"].items()
        },
    })

    controller_policy_digests = {}
    for class_id, policy in controller_policies.items():
        policy["control_plane_generation_sha256"] = generation_sha
        policy["controller_policy_sha256"] = sha256_object({
            key: value
            for key, value in policy.items()
            if key not in {"control_plane_generation_sha256", "controller_policy_sha256"}
        })
        controller_policy_digests[class_id] = policy["controller_policy_sha256"]

    executor_projection = {
        "schema_version": 1,
        "control_plane_generation_sha256": generation_sha,
        "execution_actions": executor_actions,
        "maintenance_actions": maintenance_actions,
    }
    executor_projection["executor_policy_sha256"] = sha256_object({
        key: value
        for key, value in executor_projection.items()
        if key not in {"control_plane_generation_sha256", "executor_policy_sha256"}
    })
    _validate_json_schema_subset(
        root_projection,
        data["root_projection_schema"],
        path="$root_projection",
    )
    for class_id, policy in controller_policies.items():
        _validate_json_schema_subset(
            policy,
            data["controller_projection_schema"],
            path=f"$controller_projections.{class_id}",
        )
    _validate_json_schema_subset(
        executor_projection,
        data["executor_projection_schema"],
        path="$executor_projection",
    )

    compatibility.sort(key=lambda x: (x["project_id"], x["route_id"]))

    return {
        "catalog_generation_sha256": generation_sha,
        "root_projection": root_projection,
        "controller_projections": controller_policies,
        "controller_policy_digests": controller_policy_digests,
        "executor_projection": executor_projection,
        "compatibility_matrix": compatibility,
    }


def compile_policy(root: pathlib.Path = ROOT) -> dict[str, Any]:
    return compile_from_inputs(load_inputs(root))


def _write_outputs(compiled: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "root-policy.json").write_text(
        json.dumps(compiled["root_projection"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    controllers = out / "controllers"
    controllers.mkdir(exist_ok=True)
    for class_id, policy in sorted(compiled["controller_projections"].items()):
        (controllers / f"{class_id}.json").write_text(
            json.dumps(policy, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out / "executor-actions.json").write_text(
        json.dumps(compiled["executor_projection"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "compatibility-matrix.json").write_text(
        json.dumps(compiled["compatibility_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": 1,
        "decision": "PASS",
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "executor_policy_sha256": compiled["executor_projection"]["executor_policy_sha256"],
        "runner_class_count": len(compiled["root_projection"]["runner_classes"]),
        "route_count": len(compiled["compatibility_matrix"]),
        "controller_projection_count": len(compiled["controller_projections"]),
        "execution_action_count": len(compiled["executor_projection"]["execution_actions"]),
        "maintenance_action_count": len(compiled["executor_projection"]["maintenance_actions"]),
    }
    (out / "compilation-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--output-dir", type=pathlib.Path)
    args = parser.parse_args()
    compiled = compile_policy(args.root)
    if args.output_dir:
        _write_outputs(compiled, args.output_dir)
    print("CONTROL_PLANE_POLICY_COMPILE=PASS")
    print(f"CATALOG_GENERATION_SHA256={compiled['catalog_generation_sha256']}")
    print(f"RUNNER_CLASSES={len(compiled['root_projection']['runner_classes'])}")
    print(f"ROUTES={len(compiled['compatibility_matrix'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
