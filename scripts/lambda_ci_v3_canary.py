#!/usr/bin/env python3
"""Generate inert migration-only v3 canary workflows and controller policies.

Outputs are staging artifacts for review/copy into each owning repository.
This tool never writes .github/workflows in the source repository, never calls
GitHub, never activates a controller, and never modifies the executor catalog.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
from typing import Any

import lambda_ci_policy_compiler as compiler


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC_PATH = pathlib.Path("architecture/lambda-ci-v3-migration-canaries.v1.json")
MIGRATION_PATH = pathlib.Path("architecture/lambda-ci-v3-migration-plan.v1.json")


class CanaryGenerationError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CanaryGenerationError(f"{path}: expected object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _workflow_path(template: str, class_id: str) -> str:
    value = template.format(runner_class_id=class_id)
    if not value.startswith(".github/workflows/") or not value.endswith(".yml"):
        raise CanaryGenerationError(f"{class_id}: canary workflow path invalid")
    return value


def render_workflow(
    *,
    class_id: str,
    scale_set_name: str,
    owner_actor: str,
    probe_path: str,
    timeout_minutes: int,
) -> bytes:
    actor_expression = "$" + "{{ github.actor == '" + owner_actor + "' }}"
    shell_actor = "$" + "{GITHUB_ACTOR}"
    raw = """name: Workspace CI v3 migration canary - {class_id}
on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  v3-class-canary:
    if: {actor_expression}
    runs-on: {scale_set_name}
    timeout-minutes: {timeout_minutes}
    steps:
      - name: Verify immutable v3 class envelope
        shell: bash
        run: |
          set -euo pipefail
          test "{shell_actor}" = "{owner_actor}"
          exec /usr/bin/python3 "{probe_path}" --expected-class "{class_id}"
""".format(
        class_id=class_id,
        actor_expression=actor_expression,
        scale_set_name=scale_set_name,
        timeout_minutes=timeout_minutes,
        shell_actor=shell_actor,
        owner_actor=owner_actor,
        probe_path=probe_path,
    )
    return raw.encode("utf-8")


def _project_default_branch(controller_policy: dict[str, Any]) -> str:
    branches = {
        item["default_branch"]
        for item in controller_policy["trusted_workflows"]
    }
    if len(branches) != 1:
        raise CanaryGenerationError(
            f"production workflow evidence does not resolve one default branch: {branches}"
        )
    return next(iter(branches))


def generate(repo_root: pathlib.Path, output_root: pathlib.Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    compiled = compiler.compile_policy(repo_root)
    spec = _load(repo_root / SPEC_PATH)
    migration = _load(repo_root / MIGRATION_PATH)

    if spec.get("status") != "GENERATED_NOT_INSTALLED_NOT_AUTHORIZED_FOR_LIVE_EXECUTION":
        raise CanaryGenerationError("canary spec status drifted")
    if spec.get("ordinary_executor_action_catalog_excluded") is not True:
        raise CanaryGenerationError("canaries must remain outside executor action catalog")

    classes = compiled["root_projection"]["runner_classes"]
    order = migration["canary_order"]
    if order != sorted(order, key=lambda item: item["order"]):
        raise CanaryGenerationError("canary order is not stable")
    if set(item["runner_class_id"] for item in order) != set(classes):
        raise CanaryGenerationError("canary order does not cover exactly nine classes")

    owner_actor = spec["owner_actor_login"]
    workflow_records: dict[str, dict[str, Any]] = {}
    for item in order:
        class_id = item["runner_class_id"]
        root_class = classes[class_id]
        controller = compiled["controller_projections"][class_id]
        workflow_path = _workflow_path(spec["workflow_path_template"], class_id)
        workflow_raw = render_workflow(
            class_id=class_id,
            scale_set_name=root_class["scale_set_name"],
            owner_actor=owner_actor,
            probe_path=spec["probe_path"],
            timeout_minutes=int(spec["timeout_minutes"]),
        )
        workflow_records[class_id] = {
            "path": workflow_path,
            "raw": workflow_raw,
            "blob_sha": git_blob_sha(workflow_raw),
            "repository": root_class["repository"],
            "default_branch": _project_default_branch(controller),
            "order": int(item["order"]),
            "migration_allowed": item.get("allowed") != "NO_BY_DEFAULT",
            "rationale": item["rationale"],
            "network_class": root_class["execution_contract"]["payload_network_class"],
        }

    canary_generation = compiler.sha256_object({
        "base_catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "workflows": {
            class_id: {
                key: value
                for key, value in record.items()
                if key != "raw"
            }
            for class_id, record in sorted(workflow_records.items())
        },
        "canary_spec": spec,
    })

    manifest_classes: dict[str, Any] = {}
    output_root.mkdir(parents=True, exist_ok=True)
    for class_id, record in sorted(workflow_records.items()):
        repository = record["repository"]
        owner, repo = repository.split("/", 1)
        workflow_target = output_root / "repositories" / owner / repo / record["path"]
        workflow_target.parent.mkdir(parents=True, exist_ok=True)
        workflow_target.write_bytes(record["raw"])

        policy = copy.deepcopy(compiled["controller_projections"][class_id])
        policy["control_plane_generation_sha256"] = canary_generation
        policy["trusted_workflows"] = [{
            "route_id": f"migration-canary:{class_id}",
            "path": record["path"],
            "default_branch": record["default_branch"],
            "blob_sha": record["blob_sha"],
            "compile_time_job_key": spec["job_key"],
            "compile_time_top_level_job_count": 1,
            "allowed_events": [spec["trigger"]],
            "allowed_actor_logins": [owner_actor],
        }]
        policy["controller_policy_sha256"] = compiler.sha256_object({
            key: value
            for key, value in policy.items()
            if key not in {
                "control_plane_generation_sha256",
                "controller_policy_sha256",
            }
        })
        policy_target = output_root / "controllers" / f"{class_id}.canary.json"
        policy_target.parent.mkdir(parents=True, exist_ok=True)
        policy_target.write_bytes(_canonical(policy))

        blockers = []
        if not record["migration_allowed"]:
            blockers.append("INHERITED_CONTAINMENT_REQUIRES_SEPARATE_AUTHORITY")
        if record["network_class"] in spec["network_verification"]["unresolved_payload_network_classes"]:
            blockers.append("PAYLOAD_NETWORK_ISOLATION_UNIMPLEMENTED")
        manifest_classes[class_id] = {
            "order": record["order"],
            "repository": repository,
            "workflow_path": record["path"],
            "workflow_blob_sha": record["blob_sha"],
            "controller_policy_path": str(policy_target.relative_to(output_root)),
            "controller_policy_sha256": policy["controller_policy_sha256"],
            "scale_set_name": classes[class_id]["scale_set_name"],
            "payload_network_class": record["network_class"],
            "authorization_state": (
                "BLOCKED"
                if blockers
                else "REQUIRES_SEPARATE_LIVE_CANARY_AUTHORITY"
            ),
            "blockers": blockers,
            "rationale": record["rationale"],
        }

    manifest = {
        "schema_version": 1,
        "status": "STAGED_NOT_INSTALLED_NOT_AUTHORIZED",
        "canary_generation_sha256": canary_generation,
        "base_catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "ordinary_executor_action_catalog_sha256": compiler.sha256_object(
            compiled["executor_projection"]
        ),
        "ordinary_executor_action_catalog_modified": False,
        "owner_actor_login": owner_actor,
        "trigger": spec["trigger"],
        "classes": manifest_classes,
    }
    (output_root / "canary-manifest.json").write_bytes(_canonical(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    manifest = generate(args.repo_root, args.output)
    print("V3_MIGRATION_CANARIES_GENERATED=PASS")
    print(f"CANARY_GENERATION_SHA256={manifest['canary_generation_sha256']}")
    print(f"RUNNER_CLASS_COUNT={len(manifest['classes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
