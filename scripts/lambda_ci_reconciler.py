#!/usr/bin/env python3
"""Disabled/non-live multi-project reconciliation planner for Run 2."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import lambda_ci_multirepo as multi


class ReconcileError(RuntimeError):
    pass


def plan_reconciliation(
    registry: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if registry.get("status") not in {"CONTRACT_ONLY_NOT_INSTALLED", "ACTIVE"}:
        raise ReconcileError("registry status is invalid")
    actions: list[dict[str, Any]] = []
    for project_id in sorted(registry.get("projects", {})):
        manifest = multi.resolve_project_manifest(registry, manifests, project_id)
        ident = manifest["derived_identity"]
        root = ident["project_root"]
        actions.extend(
            [
                {"kind": "ensure_group", "name": ident["runner_group"]},
                {"kind": "ensure_user", "name": ident["runner_user"], "group": ident["runner_group"]},
                {"kind": "ensure_project_root", "path": root, "owner": ident["runner_user"]},
                {
                    "kind": "install_project_manifest",
                    "project_id": project_id,
                    "destination": f"/etc/workspace-ci/projects/{project_id}.json",
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
                }
            )
    return {
        "schema_version": 1,
        "mode": "DRY_RUN_ONLY_RUN2",
        "project_count": len(registry.get("projects", {})),
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        raise ReconcileError(
            "Run-2 reconciler is deliberately non-live; root apply is authorized only in Run 3"
        )
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    manifests = {}
    for path in args.manifest:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifests[manifest["project_id"]] = manifest
    print(json.dumps(plan_reconciliation(registry, manifests), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
