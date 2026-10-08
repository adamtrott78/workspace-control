#!/usr/bin/env python3
"""Root-owned Lambda CI admission policy evaluation.

This module contains no GitHub client and handles no GitHub credential. It accepts
only a controller attestation plus root-owned project/workload policy objects,
then derives the bounded admission that may be consumed by the provisioner.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


class AdmissionError(ValueError):
    """Raised when a requested capability cannot be admitted."""


_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_KEYS_V2 = {
    "schema_version",
    "request_id",
    "project_id",
    "workload_class",
    "runner_name",
    "jit_config",
    "attestation",
}
_ATTESTATION_KEYS = {
    "schema_version",
    "source",
    "repository",
    "scale_set_name",
    "job_message_type",
    "runner_request_id",
    "workflow_run_id",
    "job_id",
    "job_workflow_ref",
    "workflow_path",
    "workflow_default_branch_commit_sha",
    "workflow_blob_sha",
    "event_name",
    "job_display_name",
    "actor_login",
    "triggering_actor_login",
    "pr_number",
    "pr_state",
    "pr_head_repository",
    "candidate_sha",
    "candidate_verification",
    "verified_at",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AdmissionError(f"{label} keys mismatch missing={missing} extra={extra}")


def _require_hex40(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX40.fullmatch(value) is None:
        raise AdmissionError(f"{label} must be a lowercase 40-hex Git object id")
    return value


def _parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AdmissionError(f"{label} must be an RFC3339 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AdmissionError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise AdmissionError(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_job_display_claim(
    display_name: Any,
    workload_class: str,
    command: str,
    version: str,
) -> tuple[int, str]:
    if not isinstance(display_name, str) or len(display_name) > 512:
        raise AdmissionError("job display claim is invalid")
    pattern = re.compile(
        rf"^{re.escape(version)}\|workload={re.escape(workload_class)}"
        rf"\|pr=([1-9][0-9]*)\|request={re.escape(command)} ([0-9a-f]{{40}})$"
    )
    match = pattern.fullmatch(display_name)
    if match is None:
        raise AdmissionError("job display claim does not match the trusted route grammar")
    return int(match.group(1)), match.group(2)


def _validated_route(
    manifest: dict[str, Any],
    policy: dict[str, Any],
    workload_class: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    admission_cfg = manifest.get("admission_v2")
    if not isinstance(admission_cfg, dict):
        raise AdmissionError("project manifest has no admission_v2 contract")
    if admission_cfg.get("enabled") is not True:
        raise AdmissionError("admission_v2 is not enabled for this project")
    if admission_cfg.get("policy_id") != policy.get("policy_id"):
        raise AdmissionError("project admission policy id does not match root workload policy")
    if workload_class not in admission_cfg.get("live_enabled_workload_classes", []):
        raise AdmissionError(f"workload class is not live-enabled: {workload_class}")

    route = admission_cfg.get("routes", {}).get(workload_class)
    if not isinstance(route, dict):
        raise AdmissionError(f"project has no admission route for workload: {workload_class}")

    workload = policy.get("workload_classes", {}).get(workload_class)
    if not isinstance(workload, dict):
        raise AdmissionError(f"root policy has no workload class: {workload_class}")
    if workload.get("policy_decision") != "EXISTING_P5_CAPABILITY":
        raise AdmissionError(
            f"workload class is not an accepted live capability: {workload_class}"
        )
    if workload.get("admission_enabled_after_enforcement") is not True:
        raise AdmissionError(f"workload class admission is disabled: {workload_class}")

    resource_class_id = workload.get("resource_class")
    resource_class = policy.get("resource_classes", {}).get(resource_class_id)
    if not isinstance(resource_class, dict):
        raise AdmissionError("workload resource class is missing")
    if route.get("execution_profile") != resource_class.get("execution_profile"):
        raise AdmissionError("project route/profile does not match workload resource class")

    profile = manifest.get("profiles", {}).get(route.get("execution_profile"))
    if not isinstance(profile, dict):
        raise AdmissionError("project route references an unknown execution profile")
    if int(resource_class.get("max_runtime_seconds", 0)) > int(
        profile.get("runtime_max_seconds", 0)
    ):
        raise AdmissionError("workload runtime ceiling exceeds the project profile")

    gpu_count = int(resource_class.get("gpu_count", 0))
    profile_gpu_indices = profile.get("gpu_indices", [])
    if gpu_count != len(profile_gpu_indices):
        raise AdmissionError("workload GPU count does not match the project profile")
    if gpu_count:
        resource_uuids = resource_class.get("gpu_uuids", [])
        if resource_uuids != [profile.get("gpu_uuid")]:
            raise AdmissionError("workload GPU UUID does not match the project profile")

    return admission_cfg, route, workload


def validate_controller_attestation(
    attestation: dict[str, Any],
    *,
    manifest: dict[str, Any],
    route: dict[str, Any],
    workload_class: str,
    now: datetime,
    ttl_seconds: int,
) -> dict[str, Any]:
    if not isinstance(attestation, dict):
        raise AdmissionError("controller attestation must be an object")
    _require_exact_keys(attestation, _ATTESTATION_KEYS, "controller attestation")

    if attestation.get("schema_version") != 2:
        raise AdmissionError("unsupported controller attestation schema")
    if attestation.get("source") != "github_scale_set_controller":
        raise AdmissionError("controller attestation source is not trusted")
    if attestation.get("repository") != manifest.get("repository"):
        raise AdmissionError("controller repository attestation does not match project")
    if attestation.get("scale_set_name") != route.get("scale_set_name"):
        raise AdmissionError("controller scale-set attestation does not match route")
    message_type = attestation.get("job_message_type")
    if message_type not in {"JobAvailable", "JobAssigned"}:
        raise AdmissionError("job_message_type is not an admitted lifecycle source")
    runner_request_id = attestation.get("runner_request_id")
    if not isinstance(runner_request_id, int) or runner_request_id < 0:
        raise AdmissionError("runner_request_id must be a non-negative integer")
    if message_type == "JobAvailable" and runner_request_id <= 0:
        raise AdmissionError("JobAvailable runner_request_id must be positive")
    if not isinstance(attestation.get("workflow_run_id"), int) or attestation["workflow_run_id"] <= 0:
        raise AdmissionError("workflow_run_id must be positive")
    if (
        not isinstance(attestation.get("job_id"), str)
        or not attestation["job_id"].isdigit()
        or int(attestation["job_id"]) <= 0
    ):
        raise AdmissionError("job_id must be a positive GitHub Actions REST job id")

    trusted = route.get("trusted_workflow")
    if not isinstance(trusted, dict):
        raise AdmissionError("route has no trusted workflow")
    if attestation.get("job_workflow_ref") != trusted.get("job_workflow_ref"):
        raise AdmissionError("job workflow ref is not trusted")
    if attestation.get("workflow_path") != trusted.get("path"):
        raise AdmissionError("workflow path is not trusted")
    if attestation.get("workflow_blob_sha") != trusted.get("blob_sha"):
        raise AdmissionError("workflow blob identity is not trusted")
    _require_hex40(
        attestation.get("workflow_default_branch_commit_sha"),
        "workflow_default_branch_commit_sha",
    )
    _require_hex40(attestation.get("workflow_blob_sha"), "workflow_blob_sha")
    if attestation.get("event_name") != trusted.get("event_name"):
        raise AdmissionError("workflow event is not trusted")

    allowed_actors = trusted.get("allowed_actors", [])
    if (
        attestation.get("actor_login") not in allowed_actors
        or attestation.get("triggering_actor_login") not in allowed_actors
    ):
        raise AdmissionError("workflow actor is not trusted")

    if not isinstance(attestation.get("pr_number"), int) or attestation["pr_number"] <= 0:
        raise AdmissionError("pr_number must be positive")
    if attestation.get("pr_state") != "open":
        raise AdmissionError("pull request is not open")
    if attestation.get("pr_head_repository") != manifest.get("repository"):
        raise AdmissionError("fork or foreign PR head repository is not admitted")
    candidate_sha = _require_hex40(attestation.get("candidate_sha"), "candidate_sha")
    if attestation.get("candidate_verification") != "PR_HEAD_MATCH":
        raise AdmissionError("candidate SHA was not attested as the exact PR head")

    claim = trusted.get("job_display_claim", {})
    claim_pr, claim_sha = _parse_job_display_claim(
        attestation.get("job_display_name"),
        workload_class,
        str(claim.get("command", "")),
        str(claim.get("version", "")),
    )
    if claim_pr != attestation["pr_number"] or claim_sha != candidate_sha:
        raise AdmissionError("job display claim disagrees with controller PR attestation")

    verified_at = _parse_datetime(attestation.get("verified_at"), "verified_at")
    if verified_at > now + timedelta(seconds=60):
        raise AdmissionError("controller attestation timestamp is in the future")
    if now - verified_at > timedelta(seconds=ttl_seconds):
        raise AdmissionError("controller attestation is stale")

    return dict(attestation)


def request_digest(request: dict[str, Any]) -> str:
    """Hash only authoritative, replay-stable request identity.

    JIT configuration is an ephemeral GitHub transport credential under the
    unprivileged controller's authority. GitHub may regenerate it for the same
    assigned job after controller recovery, so it must not create a new root
    admission identity.
    """

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



def project_profile_digest(
    manifest: dict[str, Any],
    route: dict[str, Any],
    admission_cfg: dict[str, Any],
) -> str:
    return sha256_json(
        {
            "project_id": manifest["project_id"],
            "repository": manifest["repository"],
            "profile": route["execution_profile"],
            "profile_contract": manifest["profiles"][route["execution_profile"]],
            "expanded_runtime_binding": manifest.get(
                "expanded_runtime_bindings", {}
            ).get(route["execution_profile"]),
            "admission_route": route,
            "kill_switch_epoch": admission_cfg["kill_switch_epoch"],
        }
    )

def expanded_runtime_admission_binding(
    manifest: dict[str, Any],
    route: dict[str, Any],
    workload: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any] | None:
    requirement = workload.get("runtime_binding")
    if requirement in (None, "OPTIONAL_PROJECT_TEST_RUNTIME"):
        return None
    if requirement != "REQUIRED_EXPANDED_RUNTIME_EXACT":
        raise AdmissionError(f"unsupported runtime binding requirement: {requirement}")

    binding = manifest.get("expanded_runtime_bindings", {}).get(
        route["execution_profile"]
    )
    if not isinstance(binding, dict):
        raise AdmissionError("required expanded runtime binding is missing")

    required = (
        "runtime_id",
        "tree_digest_sha256",
        "manifest_identity_sha256",
    )
    if any(not isinstance(binding.get(key), str) or not binding[key] for key in required):
        raise AdmissionError("required expanded runtime binding is incomplete")

    project_binding = policy.get("project_bindings", {}).get(manifest["project_id"], {})
    runtime_contract = None
    for candidate in project_binding.get("allowed_runtimes", []):
        if candidate.get("runtime_id") == binding["runtime_id"]:
            runtime_contract = candidate
            break
    if not isinstance(runtime_contract, dict):
        raise AdmissionError("expanded runtime is not allowed by project policy")

    owning_paths = runtime_contract.get("owning_contracts", [])
    research_engine_sha = policy.get("baselines", {}).get("research_engine_sha")
    if (
        not isinstance(research_engine_sha, str)
        or len(research_engine_sha) != 40
        or not owning_paths
    ):
        raise AdmissionError("expanded runtime owning-contract binding is incomplete")

    owning_contracts = [
        {
            "repository": manifest["repository"],
            "path": path,
            "commit_sha": research_engine_sha,
        }
        for path in owning_paths
    ]

    return {
        "runtime_id": binding["runtime_id"],
        "cache_object": {
            "object_state": "PROMOTED",
            "object_id": binding["tree_digest_sha256"],
            "tree_sha256": binding["tree_digest_sha256"],
            "dependency_manifest_sha256": binding["manifest_identity_sha256"],
            "promotion_receipt_sha256": None,
        },
        "owning_contracts": owning_contracts,
    }


def mint_admission(
    request: dict[str, Any],
    manifest: dict[str, Any],
    policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate a v2 controller claim and mint a bounded root-owned admission."""

    if not isinstance(request, dict):
        raise AdmissionError("provision request must be an object")
    _require_exact_keys(request, _REQUEST_KEYS_V2, "v2 provision request")
    if request.get("schema_version") != 2:
        raise AdmissionError("v2 admission requires schema_version=2")
    if request.get("project_id") != manifest.get("project_id"):
        raise AdmissionError("project id does not match the root-owned project manifest")
    try:
        uuid.UUID(str(request.get("request_id")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise AdmissionError("request_id must be a UUID") from exc
    if not isinstance(request.get("runner_name"), str) or not request["runner_name"]:
        raise AdmissionError("runner_name must be non-empty")
    if not isinstance(request.get("jit_config"), str) or not request["jit_config"]:
        raise AdmissionError("jit_config must be non-empty")

    workload_class = request.get("workload_class")
    if not isinstance(workload_class, str) or not workload_class:
        raise AdmissionError("workload_class must be non-empty")

    admission_cfg, route, workload = _validated_route(
        manifest,
        policy,
        workload_class,
    )

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ttl_seconds = min(
        int(admission_cfg.get("admission_ttl_seconds", 0)),
        int(policy.get("admission_semantics", {}).get("admission_ttl_seconds_max", 0)),
    )
    if ttl_seconds <= 0:
        raise AdmissionError("admission TTL must be positive")

    attestation = validate_controller_attestation(
        request["attestation"],
        manifest=manifest,
        route=route,
        workload_class=workload_class,
        now=now,
        ttl_seconds=ttl_seconds,
    )

    resource_class_id = workload["resource_class"]
    resource_class = policy["resource_classes"][resource_class_id]
    network_class = workload["payload_network_class"]
    secret_class = workload["payload_secret_class"]
    filesystem_class = workload["filesystem_class"]
    cache_class = workload["cache_access_class"]
    state_effect_class = workload["state_effect_class"]

    for collection, key in (
        ("payload_network_classes", network_class),
        ("payload_secret_classes", secret_class),
        ("filesystem_classes", filesystem_class),
        ("cache_access_classes", cache_class),
        ("state_effect_classes", state_effect_class),
    ):
        if key not in policy.get(collection, {}):
            raise AdmissionError(f"workload references unknown {collection}: {key}")

    request_digest_sha256 = request_digest(request)
    effective_policy_sha256 = policy_sha256 or sha256_json(policy)
    if _HEX64.fullmatch(effective_policy_sha256) is None:
        raise AdmissionError("policy_sha256 must be 64 lowercase hex characters")

    project_profile_sha256 = project_profile_digest(
        manifest,
        route,
        admission_cfg,
    )
    issued_at = now
    expires_at = now + timedelta(seconds=ttl_seconds)
    runtime_binding = expanded_runtime_admission_binding(
        manifest,
        route,
        workload,
        policy,
    )

    return {
        "schema_version": 1,
        "admission_id": str(uuid.uuid4()),
        "request_id": request["request_id"],
        "request_digest_sha256": request_digest_sha256,
        "policy": {
            "policy_id": policy["policy_id"],
            "policy_epoch": int(policy["policy_epoch"]),
            "policy_sha256": effective_policy_sha256,
            "project_profile_sha256": project_profile_sha256,
            "kill_switch_epoch": int(admission_cfg["kill_switch_epoch"]),
        },
        "lifecycle": {
            "issued_at": _iso(issued_at),
            "not_before": _iso(issued_at),
            "expires_at": _iso(expires_at),
            "single_use": True,
            "consumed_at": None,
        },
        "project": {
            "project_id": manifest["project_id"],
            "repository": manifest["repository"],
        },
        "trusted_workflow": {
            "path": attestation["workflow_path"],
            "default_branch_commit_sha": attestation[
                "workflow_default_branch_commit_sha"
            ],
            "workflow_blob_sha": attestation["workflow_blob_sha"],
        },
        "candidate_sha": attestation["candidate_sha"],
        "workload_class": workload_class,
        "execution_profile": route["execution_profile"],
        "resource_class": resource_class_id,
        "capability_classes": {
            "payload_network": network_class,
            "payload_secrets": secret_class,
            "filesystem": filesystem_class,
            "cache_access": cache_class,
            "state_effect": state_effect_class,
        },
        "resource_ceiling": {
            "runtime_seconds": int(resource_class["max_runtime_seconds"]),
            "scratch_max_bytes": int(resource_class["scratch_max_bytes"]),
            "staging_max_bytes": int(resource_class["staging_max_bytes"]),
            "gpu_uuids": list(resource_class.get("gpu_uuids", [])),
        },
        "models": [],
        "runtime": runtime_binding,
        "exception_ids": [],
        "required_receipt_schema": "lambda-ci-execution-receipt-v1",
    }



def validate_admission_freshness(
    admission: dict[str, Any],
    manifest: dict[str, Any],
    policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> None:
    """Revalidate a minted admission immediately before single-use consumption."""

    if not isinstance(admission, dict):
        raise AdmissionError("admission must be an object")
    if admission.get("schema_version") != 1:
        raise AdmissionError("unsupported admission schema")

    lifecycle = admission.get("lifecycle")
    if not isinstance(lifecycle, dict) or lifecycle.get("single_use") is not True:
        raise AdmissionError("admission must be single-use")
    if lifecycle.get("consumed_at") is not None:
        raise AdmissionError("admission is already consumed")

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    not_before = _parse_datetime(lifecycle.get("not_before"), "not_before")
    expires_at = _parse_datetime(lifecycle.get("expires_at"), "expires_at")
    if now < not_before:
        raise AdmissionError("admission is not active yet")
    if now >= expires_at:
        raise AdmissionError("admission is expired")

    workload_class = admission.get("workload_class")
    if not isinstance(workload_class, str) or not workload_class:
        raise AdmissionError("admission workload class is missing")
    admission_cfg, route, workload = _validated_route(
        manifest,
        policy,
        workload_class,
    )

    current_policy_sha256 = policy_sha256 or sha256_json(policy)
    if _HEX64.fullmatch(current_policy_sha256) is None:
        raise AdmissionError("policy_sha256 must be 64 lowercase hex characters")

    bound_policy = admission.get("policy")
    if not isinstance(bound_policy, dict):
        raise AdmissionError("admission policy binding is missing")
    if bound_policy.get("policy_id") != policy.get("policy_id"):
        raise AdmissionError("admission policy id is stale")
    if int(bound_policy.get("policy_epoch", -1)) != int(policy.get("policy_epoch", -2)):
        raise AdmissionError("admission policy epoch is stale")
    if bound_policy.get("policy_sha256") != current_policy_sha256:
        raise AdmissionError("admission policy digest is stale")
    if int(bound_policy.get("kill_switch_epoch", -1)) != int(
        admission_cfg.get("kill_switch_epoch", -2)
    ):
        raise AdmissionError("admission kill-switch epoch is stale")

    current_project_profile = project_profile_digest(
        manifest,
        route,
        admission_cfg,
    )
    if bound_policy.get("project_profile_sha256") != current_project_profile:
        raise AdmissionError("admission project/profile binding is stale")

    project = admission.get("project")
    if not isinstance(project, dict):
        raise AdmissionError("admission project binding is missing")
    if (
        project.get("project_id") != manifest.get("project_id")
        or project.get("repository") != manifest.get("repository")
    ):
        raise AdmissionError("admission project binding is stale")

    if admission.get("execution_profile") != route.get("execution_profile"):
        raise AdmissionError("admission execution profile is stale")
    if admission.get("resource_class") != workload.get("resource_class"):
        raise AdmissionError("admission resource class is stale")

    current_runtime_binding = expanded_runtime_admission_binding(
        manifest,
        route,
        workload,
        policy,
    )
    if admission.get("runtime") != current_runtime_binding:
        raise AdmissionError("admission expanded runtime binding is stale")


def consume_admission(
    admission: dict[str, Any],
    manifest: dict[str, Any],
    policy: dict[str, Any],
    *,
    now: datetime | None = None,
    policy_sha256: str | None = None,
) -> dict[str, Any]:
    """Atomically represent the root decision to consume one admission.

    Persistence/serialization of the returned object is owned by the root
    provisioner state store; this function is intentionally side-effect free.
    """

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    validate_admission_freshness(
        admission,
        manifest,
        policy,
        now=now,
        policy_sha256=policy_sha256,
    )
    consumed = copy.deepcopy(admission)
    consumed["lifecycle"]["consumed_at"] = _iso(now)
    return consumed
