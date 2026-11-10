#!/usr/bin/env python3
"""Generic multi-repository Lambda CI admission helpers.

This module is root-policy logic only. Route/workload names are audit labels;
authority is resolved from the root-owned project registry, project manifest,
execution-contract catalog, and host resource policy.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


class MultiRepoPolicyError(ValueError):
    pass


PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,20}$")
ROUTE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
CLAIM_VERSION = "wc-admission-v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def request_digest(request: dict[str, Any]) -> str:
    """Hash replay-stable authority, excluding ephemeral GitHub lifecycle data."""
    nonsecret = copy.deepcopy(
        {
            key: value
            for key, value in request.items()
            if key != "jit_config"
        }
    )
    attestation = nonsecret.get("attestation")
    if isinstance(attestation, dict):
        attestation.pop("verified_at", None)
        attestation.pop("job_message_type", None)
        attestation.pop("runner_request_id", None)
    return sha256_json(nonsecret)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def derive_project_identity(project_id: str) -> dict[str, Any]:
    if not isinstance(project_id, str) or PROJECT_ID_RE.fullmatch(project_id) is None:
        raise MultiRepoPolicyError("project_id is invalid")
    return {
        "runner_user": f"ci-{project_id}",
        "runner_group": f"ci-{project_id}",
        "project_root": f"/srv/workspace-ci/{project_id}",
        "lanes": {
            "cpu": {
                "scale_set_name": f"lambda-{project_id}",
                "runner_prefix": f"lambda-{project_id}-",
            },
            "gpu": {
                "scale_set_name": f"lambda-{project_id}-gpu",
                "runner_prefix": f"lambda-{project_id}-gpu-",
            },
        },
    }


def validate_project_manifest_derivations(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 2:
        raise MultiRepoPolicyError("generic project manifest requires schema_version=2")
    expected = derive_project_identity(manifest.get("project_id"))
    if manifest.get("derived_identity") != expected:
        raise MultiRepoPolicyError("project manifest derived identity drift")
    roots = manifest.get("roots")
    if not isinstance(roots, dict):
        raise MultiRepoPolicyError("project roots missing")
    root = expected["project_root"]
    expected_roots = {
        "jobs": f"{root}/jobs",
        "staging_cache": f"{root}/staging-cache",
        "trusted_cache": f"{root}/trusted-cache",
        "logs": f"{root}/logs",
        "home": f"{root}/home",
    }
    if roots != expected_roots:
        raise MultiRepoPolicyError("project manifest roots drift from derived identity")


def resolve_project_manifest(
    registry: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
    project_id: str,
) -> dict[str, Any]:
    if registry.get("schema_version") != 1:
        raise MultiRepoPolicyError("project registry schema is unsupported")
    entry = registry.get("projects", {}).get(project_id)
    if not isinstance(entry, dict):
        raise MultiRepoPolicyError("project_id is not registered")
    manifest = manifests.get(project_id)
    if not isinstance(manifest, dict):
        raise MultiRepoPolicyError("registered project manifest is unavailable")
    validate_project_manifest_derivations(manifest)
    if manifest.get("project_id") != project_id:
        raise MultiRepoPolicyError("project manifest id mismatch")
    if manifest.get("repository") != entry.get("repository"):
        raise MultiRepoPolicyError("project repository differs from registry")
    if manifest.get("repository_visibility") != entry.get("repository_visibility"):
        raise MultiRepoPolicyError("project repository visibility differs from registry")
    return manifest


def parse_display_claim(display_name: Any, route_id: str, command: str) -> tuple[int, str]:
    if not isinstance(display_name, str):
        raise MultiRepoPolicyError("job display name is missing")
    if ROUTE_ID_RE.fullmatch(route_id or "") is None:
        raise MultiRepoPolicyError("route id is invalid")
    if not isinstance(command, str) or re.fullmatch(r"/[a-z0-9][a-z0-9-]{2,63}", command) is None:
        raise MultiRepoPolicyError("route command is invalid")
    pattern = re.compile(
        rf"^{CLAIM_VERSION}\|workload={re.escape(route_id)}"
        rf"\|pr=([1-9][0-9]*)\|request={re.escape(command)} ([0-9a-f]{{40}})"
        rf"(?: ([a-z0-9][a-z0-9._:+/@=-]{{0,127}}))?$"
    )
    match = pattern.fullmatch(display_name)
    if match is None:
        raise MultiRepoPolicyError("job display claim does not match route")
    return int(match.group(1)), match.group(2)


def _require_hex40(value: Any, field: str) -> str:
    if not isinstance(value, str) or HEX40_RE.fullmatch(value) is None:
        raise MultiRepoPolicyError(f"{field} must be 40 lowercase hex")
    return value


def _route_and_contract(
    manifest: dict[str, Any],
    execution_contracts: dict[str, Any],
    route_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if ROUTE_ID_RE.fullmatch(route_id or "") is None:
        raise MultiRepoPolicyError("route id is invalid")
    route = manifest.get("routes", {}).get(route_id)
    if not isinstance(route, dict):
        raise MultiRepoPolicyError("project route is unknown")
    if route.get("activation_state") not in {"MIGRATION_LIVE_EQUIVALENT", "ACTIVE"}:
        raise MultiRepoPolicyError("project route is not active")
    contract_id = route.get("execution_contract_id")
    contract = execution_contracts.get("contracts", {}).get(contract_id)
    if not isinstance(contract, dict):
        raise MultiRepoPolicyError("route execution contract is unknown")
    if contract.get("admission_enabled_after_generic_activation") is not True:
        raise MultiRepoPolicyError("execution contract is not admission-enabled")
    if contract.get("lifecycle") == "PLANNED_NOT_ACCEPTED":
        raise MultiRepoPolicyError("execution contract is not accepted")
    return route, contract


def _validate_attestation(
    request: dict[str, Any],
    manifest: dict[str, Any],
    route_id: str,
    route: dict[str, Any],
) -> dict[str, Any]:
    att = request.get("attestation")
    if not isinstance(att, dict):
        raise MultiRepoPolicyError("controller attestation is missing")
    if att.get("repository") != manifest.get("repository"):
        raise MultiRepoPolicyError("controller repository attestation mismatch")

    lane = route.get("lane")
    lane_identity = manifest["derived_identity"]["lanes"].get(lane)
    if not isinstance(lane_identity, dict):
        raise MultiRepoPolicyError("route lane is invalid")
    if att.get("scale_set_name") != lane_identity.get("scale_set_name"):
        raise MultiRepoPolicyError("controller scale-set attestation mismatch")

    trusted = route.get("trusted_workflow")
    trigger = route.get("trigger")
    if not isinstance(trusted, dict) or not isinstance(trigger, dict):
        raise MultiRepoPolicyError("route workflow/trigger contract is missing")
    blob = trusted.get("blob_sha")
    _require_hex40(blob, "trusted workflow blob")
    expected_ref = (
        f"{manifest['repository']}/{trusted['path']}@refs/heads/{trusted['default_branch']}"
    )
    if att.get("job_workflow_ref") != expected_ref:
        raise MultiRepoPolicyError("job workflow ref is not trusted")
    if att.get("workflow_path") != trusted.get("path"):
        raise MultiRepoPolicyError("workflow path is not trusted")
    if att.get("workflow_blob_sha") != blob:
        raise MultiRepoPolicyError("workflow blob identity is not trusted")
    _require_hex40(att.get("workflow_default_branch_commit_sha"), "workflow default-branch commit")
    if att.get("event_name") != trigger.get("event_name"):
        raise MultiRepoPolicyError("workflow event is not trusted")

    allowed_actors = trigger.get("allowed_actor_logins")
    if not isinstance(allowed_actors, list) or not allowed_actors:
        raise MultiRepoPolicyError("route actor allowlist is empty")
    if (
        att.get("actor_login") not in allowed_actors
        or att.get("triggering_actor_login") not in allowed_actors
    ):
        raise MultiRepoPolicyError("workflow actor is not trusted")

    if att.get("pr_state") != "open":
        raise MultiRepoPolicyError("pull request is not open")
    if trigger.get("require_open_same_repository_pr_head") is not True:
        raise MultiRepoPolicyError("route must require same-repository PR heads")
    if trigger.get("fork_pr_execution_allowed") is not False:
        raise MultiRepoPolicyError("fork PR execution must remain disabled")
    if att.get("pr_head_repository") != manifest.get("repository"):
        raise MultiRepoPolicyError("fork or foreign PR head is not admitted")
    candidate_sha = _require_hex40(att.get("candidate_sha"), "candidate_sha")
    if att.get("candidate_verification") != "PR_HEAD_MATCH":
        raise MultiRepoPolicyError("candidate SHA is not exact PR head")

    claim_pr, claim_sha = parse_display_claim(
        att.get("job_display_name"),
        route_id,
        trigger.get("command"),
    )
    if claim_pr != att.get("pr_number"):
        raise MultiRepoPolicyError("display-claim PR number mismatches attestation")
    if claim_sha != candidate_sha:
        raise MultiRepoPolicyError("display-claim candidate SHA mismatches attestation")
    return att


def _resource_class(
    contract: dict[str, Any],
    workload_policy: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    resource_id = contract.get("resource_class")
    resource = workload_policy.get("resource_classes", {}).get(resource_id)
    if not isinstance(resource, dict):
        raise MultiRepoPolicyError("execution contract resource class is unavailable")
    if resource.get("execution_profile") != contract.get("execution_profile"):
        raise MultiRepoPolicyError("execution contract/profile resource mismatch")
    gpu_count = int(resource.get("gpu_count", -1))
    if gpu_count != int(contract.get("gpu_count", -2)):
        raise MultiRepoPolicyError("execution contract GPU count differs from resource class")
    uuids = resource.get("gpu_uuids", [])
    if not isinstance(uuids, list) or len(uuids) != gpu_count:
        raise MultiRepoPolicyError("resource GPU UUID set is invalid")
    return str(resource_id), resource


def _resolve_bindings(
    manifest: dict[str, Any],
    route: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    bindings = route.get("bindings")
    if not isinstance(bindings, dict):
        raise MultiRepoPolicyError("route bindings missing")
    model_id = bindings.get("model_id")
    runtime_id = bindings.get("runtime_id")
    model_mode = contract.get("model_binding_mode")
    runtime_mode = contract.get("runtime_binding_mode")

    models: list[dict[str, Any]] = []
    model_catalog = manifest.get("bindings", {}).get("models", {})
    if model_mode == "FORBIDDEN":
        if model_id is not None:
            raise MultiRepoPolicyError("execution contract forbids model binding")
    elif model_mode == "REQUIRED_PROMOTED_EXACT":
        binding = model_catalog.get(model_id)
        if not isinstance(binding, dict):
            raise MultiRepoPolicyError("required promoted model binding is unavailable")
        models = [copy.deepcopy(binding)]
    elif model_mode == "OPTIONAL_EXACT_IF_ROUTE_BINDS":
        if model_id is not None:
            binding = model_catalog.get(model_id)
            if not isinstance(binding, dict):
                raise MultiRepoPolicyError("optional model binding id is unavailable")
            models = [copy.deepcopy(binding)]
    else:
        raise MultiRepoPolicyError("unknown model binding mode")

    runtime = None
    runtime_catalog = manifest.get("bindings", {}).get("runtimes", {})
    if runtime_mode == "REQUIRED_EXPANDED_RUNTIME_EXACT":
        binding = runtime_catalog.get(runtime_id)
        if not isinstance(binding, dict):
            raise MultiRepoPolicyError("required runtime binding is unavailable")
        runtime = copy.deepcopy(binding)
    elif runtime_mode == "OPTIONAL_EXACT_IF_ROUTE_BINDS":
        if runtime_id is not None:
            binding = runtime_catalog.get(runtime_id)
            if not isinstance(binding, dict):
                raise MultiRepoPolicyError("optional runtime binding id is unavailable")
            runtime = copy.deepcopy(binding)
    else:
        raise MultiRepoPolicyError("unknown runtime binding mode")

    return models, runtime


def mint_admission(
    request: dict[str, Any],
    manifest: dict[str, Any],
    execution_contracts: dict[str, Any],
    workload_policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> dict[str, Any]:
    validate_project_manifest_derivations(manifest)
    if request.get("schema_version") != 2:
        raise MultiRepoPolicyError("generic admission requires schema_version=2")
    if request.get("project_id") != manifest.get("project_id"):
        raise MultiRepoPolicyError("request project_id differs from root manifest")
    try:
        uuid.UUID(str(request.get("request_id")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MultiRepoPolicyError("request_id must be UUID") from exc
    if not isinstance(request.get("runner_name"), str) or not request["runner_name"]:
        raise MultiRepoPolicyError("runner_name is required")
    if not isinstance(request.get("jit_config"), str) or not request["jit_config"]:
        raise MultiRepoPolicyError("jit_config is required")

    route_id = request.get("workload_class")
    if not isinstance(route_id, str):
        raise MultiRepoPolicyError("workload_class/route id is required")
    route, contract = _route_and_contract(manifest, execution_contracts, route_id)
    att = _validate_attestation(request, manifest, route_id, route)

    lane_identity = manifest["derived_identity"]["lanes"][route["lane"]]
    if not request["runner_name"].startswith(lane_identity["runner_prefix"]):
        raise MultiRepoPolicyError("runner_name does not match project/lane prefix")
    suffix = request["runner_name"][len(lane_identity["runner_prefix"]):]
    if re.fullmatch(r"[a-f0-9]{12}", suffix) is None:
        raise MultiRepoPolicyError("runner_name suffix is not deterministic hex")

    resource_id, resource = _resource_class(contract, workload_policy)
    models, runtime = _resolve_bindings(manifest, route, contract)

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    max_ttl = int(workload_policy.get("admission_semantics", {}).get("admission_ttl_seconds_max", 900))
    ttl = min(900, max_ttl)
    if ttl <= 0:
        raise MultiRepoPolicyError("admission TTL is invalid")

    effective_policy_sha = policy_sha256 or sha256_json(
        {"workload_policy": workload_policy, "execution_contracts": execution_contracts}
    )
    if HEX64_RE.fullmatch(effective_policy_sha) is None:
        raise MultiRepoPolicyError("policy digest is invalid")
    profile_digest = sha256_json(
        {
            "project_id": manifest["project_id"],
            "repository": manifest["repository"],
            "derived_identity": manifest["derived_identity"],
            "roots": manifest["roots"],
            "route_id": route_id,
            "route": route,
            "execution_contract_id": route["execution_contract_id"],
            "execution_contract": contract,
        }
    )

    capability_classes = {
        "payload_network": contract["payload_network_class"],
        "payload_secrets": contract["payload_secret_class"],
        "filesystem": contract["filesystem_class"],
        "cache_access": contract["cache_access_class"],
        "state_effect": contract["state_effect_class"],
    }
    return {
        "schema_version": 1,
        "admission_id": str(uuid.uuid4()),
        "request_id": request["request_id"],
        "request_digest_sha256": request_digest(request),
        "policy": {
            "policy_id": workload_policy.get("policy_id", "lambda-ci-workload-policy-v1"),
            "policy_epoch": int(workload_policy.get("policy_epoch", 1)),
            "policy_sha256": effective_policy_sha,
            "project_profile_sha256": profile_digest,
            "kill_switch_epoch": 0,
        },
        "lifecycle": {
            "issued_at": _iso(now),
            "not_before": _iso(now),
            "expires_at": _iso(now + timedelta(seconds=ttl)),
            "single_use": True,
            "consumed_at": None,
        },
        "project": {
            "project_id": manifest["project_id"],
            "repository": manifest["repository"],
        },
        "trusted_workflow": {
            "path": att["workflow_path"],
            "default_branch_commit_sha": att["workflow_default_branch_commit_sha"],
            "workflow_blob_sha": att["workflow_blob_sha"],
        },
        "candidate_sha": att["candidate_sha"],
        "workload_class": route_id,
        "execution_profile": contract["execution_profile"],
        "resource_class": resource_id,
        "capability_classes": capability_classes,
        "resource_ceiling": {
            "runtime_seconds": int(resource["max_runtime_seconds"]),
            "scratch_max_bytes": int(resource["scratch_max_bytes"]),
            "staging_max_bytes": int(resource["staging_max_bytes"]),
            "gpu_uuids": list(resource.get("gpu_uuids", [])),
        },
        "models": models,
        "runtime": runtime,
        "exception_ids": [],
        "required_receipt_schema": "lambda-ci-execution-receipt-v1",
        "_generic": {
            "execution_contract_id": route["execution_contract_id"],
            "execution_contract": copy.deepcopy(contract),
            "route_lane": route["lane"],
            "registry_model": "lambda-ci-project-registry-v1",
        },
    }


def consume_admission(
    admission: dict[str, Any],
    request: dict[str, Any],
    manifest: dict[str, Any],
    execution_contracts: dict[str, Any],
    workload_policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> dict[str, Any]:
    if admission.get("lifecycle", {}).get("consumed_at") is not None:
        raise MultiRepoPolicyError("admission is already consumed")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires_raw = admission.get("lifecycle", {}).get("expires_at")
    if not isinstance(expires_raw, str):
        raise MultiRepoPolicyError("admission expiry missing")
    expires = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
    if now >= expires:
        raise MultiRepoPolicyError("admission is expired")

    current = mint_admission(
        request,
        manifest,
        execution_contracts,
        workload_policy,
        now=now,
        policy_sha256=policy_sha256,
    )
    stable_keys = (
        "request_digest_sha256",
        "policy",
        "project",
        "trusted_workflow",
        "candidate_sha",
        "workload_class",
        "execution_profile",
        "resource_class",
        "capability_classes",
        "resource_ceiling",
        "models",
        "runtime",
        "required_receipt_schema",
        "_generic",
    )
    for key in stable_keys:
        if current.get(key) != admission.get(key):
            raise MultiRepoPolicyError(f"admission binding is stale: {key}")
    consumed = copy.deepcopy(admission)
    consumed["lifecycle"]["consumed_at"] = _iso(now)
    return consumed


def execution_semantics_from_admission(admission: dict[str, Any]) -> dict[str, Any]:
    generic = admission.get("_generic")
    if isinstance(generic, dict):
        contract = copy.deepcopy(generic.get("execution_contract"))
        if not isinstance(contract, dict):
            raise MultiRepoPolicyError("generic admission execution contract missing")
        contract["execution_contract_id"] = generic["execution_contract_id"]
        return contract

    # Legacy v1 migration fallback derives semantics from the root-issued grant,
    # not the route name. This keeps existing research-engine receipts usable
    # while privileged runtime code stops branching on experiment names.
    models = admission.get("models") or []
    runtime = admission.get("runtime")
    resource = admission.get("resource_ceiling") or {}
    gpu_count = len(resource.get("gpu_uuids") or [])
    return {
        "execution_contract_id": "legacy-admission-derived-v1",
        "lifecycle": "ACCEPTED_MIGRATION_EQUIVALENT",
        "execution_plane": "jit_runner",
        "execution_profile": admission.get("execution_profile"),
        "resource_class": admission.get("resource_class"),
        "payload_network_class": admission.get("capability_classes", {}).get("payload_network"),
        "payload_secret_class": admission.get("capability_classes", {}).get("payload_secrets"),
        "filesystem_class": admission.get("capability_classes", {}).get("filesystem"),
        "cache_access_class": admission.get("capability_classes", {}).get("cache_access"),
        "state_effect_class": admission.get("capability_classes", {}).get("state_effect"),
        "candidate_payload_allowed": True,
        "model_binding_mode": "REQUIRED_PROMOTED_EXACT" if models else "FORBIDDEN",
        "runtime_binding_mode": "REQUIRED_EXPANDED_RUNTIME_EXACT" if runtime else "OPTIONAL_EXACT_IF_ROUTE_BINDS",
        "gpu_count": gpu_count,
        "admission_enabled_after_generic_activation": True,
    }
