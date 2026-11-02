#!/usr/bin/env python3
"""Pure verifier for Lambda CI v3 deployment-state overlays.

Desired policy compilation and live deployment authority are intentionally
separate.  This module proves that binding a catalog generation to a deployment
overlay cannot implicitly install, activate, enable, or unquarantine anything.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

COMPILER_PATH = ROOT / "scripts" / "lambda_ci_policy_compiler.py"
_spec = importlib.util.spec_from_file_location("lambda_ci_policy_compiler", COMPILER_PATH)
compiler = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
import sys
sys.modules["lambda_ci_policy_compiler"] = compiler
_spec.loader.exec_module(compiler)


class OverlayError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OverlayError(message)


def load_overlay(root: pathlib.Path = ROOT) -> dict[str, Any]:
    return json.loads(
        (root / "architecture/lambda-ci-deployment-overlay.v1.json").read_text(
            encoding="utf-8"
        )
    )


def load_schema(root: pathlib.Path = ROOT) -> dict[str, Any]:
    return json.loads(
        (root / "schemas/workspace-ci-deployment-overlay.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def bind_generation(
    overlay: dict[str, Any],
    *,
    generation_sha256: str,
) -> dict[str, Any]:
    bound = copy.deepcopy(overlay)
    before_classes = copy.deepcopy(bound["classes"])
    before_routes = copy.deepcopy(bound["routes"])
    before_legacy = copy.deepcopy(bound["legacy"])
    bound["catalog_generation_sha256"] = generation_sha256
    _require(bound["classes"] == before_classes, "generation binding changed class state")
    _require(bound["routes"] == before_routes, "generation binding changed route state")
    _require(bound["legacy"] == before_legacy, "generation binding changed legacy state")
    return bound


def verify_overlay(
    overlay: dict[str, Any],
    compiled: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
    allow_template_zero_digest: bool = True,
) -> dict[str, Any]:
    schema = schema or load_schema(ROOT)
    try:
        compiler._validate_json_schema_subset(
            overlay,
            schema,
            path="$deployment_overlay",
        )
    except compiler.CompileError as exc:
        raise OverlayError(str(exc)) from exc

    generation = compiled["catalog_generation_sha256"]
    overlay_generation = overlay["catalog_generation_sha256"]
    zero = "0" * 64
    if overlay_generation == zero:
        _require(
            allow_template_zero_digest,
            "template zero catalog generation is not allowed",
        )
    else:
        _require(
            overlay_generation == generation,
            "deployment overlay catalog generation mismatch",
        )

    class_ids = set(compiled["root_projection"]["runner_classes"])
    _require(
        set(overlay["classes"]) == class_ids,
        "deployment overlay class set differs from compiled runner classes",
    )

    route_to_class: dict[str, str] = {}
    expected_routes: set[str] = set()
    for row in compiled["compatibility_matrix"]:
        route_key = f"{row['project_id']}:{row['route_id']}"
        expected_routes.add(route_key)
        route_to_class[route_key] = row["target_runner_class_id"]
    _require(
        set(overlay["routes"]) == expected_routes,
        "deployment overlay route set differs from compiled routes",
    )

    enabled_routes = []
    active_classes = []
    installed_classes = []
    contained_classes = []

    for class_id, state in overlay["classes"].items():
        install = state["install_state"]
        controller = state["controller_state"]
        containment = state["containment"]["state"]

        if install == "INSTALLED":
            installed_classes.append(class_id)
        if controller == "ACTIVE":
            active_classes.append(class_id)
            _require(install == "INSTALLED", f"{class_id}: ACTIVE but not INSTALLED")
            _require(
                containment == "CLEAR",
                f"{class_id}: contained/quarantined class cannot be ACTIVE",
            )
        if controller == "DRAINING":
            _require(install == "INSTALLED", f"{class_id}: DRAINING but not INSTALLED")
        if containment != "CLEAR":
            contained_classes.append(class_id)
            _require(
                controller != "ACTIVE",
                f"{class_id}: containment must prevent ACTIVE controller",
            )

    for route_key, state in overlay["routes"].items():
        if state["admission_state"] != "ENABLED":
            continue
        enabled_routes.append(route_key)
        class_id = route_to_class[route_key]
        class_state = overlay["classes"][class_id]
        _require(
            class_state["install_state"] == "INSTALLED",
            f"{route_key}: enabled route class is not installed",
        )
        _require(
            class_state["controller_state"] == "ACTIVE",
            f"{route_key}: enabled route class controller is not active",
        )
        _require(
            class_state["containment"]["state"] == "CLEAR",
            f"{route_key}: enabled route class is contained",
        )

    legacy = overlay["legacy"]
    research_quarantine = [
        item
        for item in legacy["quarantine_receipts"]
        if item.startswith("research-engine-gpu:")
    ]
    research_retry = [
        item
        for item in legacy["retry_receipts"]
        if item.startswith("research-engine-gpu:")
    ]
    _require(
        len(research_quarantine) == 1,
        "legacy research-engine GPU quarantine receipt is not preserved exactly once",
    )
    _require(
        len(research_retry) == 1
        and research_retry[0].endswith(":RECOVERY_RETRY_INVALIDATED"),
        "legacy research-engine GPU retry-invalidated receipt is not preserved",
    )

    exact_provenance = overlay["routes"][
        "research-engine:cpu-validation-exact-provenance"
    ]
    if overlay["legacy"]["controllers"].get("research-engine-gpu") != "RETIRED":
        _require(
            exact_provenance["admission_state"] == "DISABLED",
            "exact-provenance route moved to CPU class but bypassed legacy GPU containment",
        )

    return {
        "decision": "PASS",
        "catalog_generation_sha256": overlay_generation,
        "installed_classes": sorted(installed_classes),
        "active_classes": sorted(active_classes),
        "contained_classes": sorted(contained_classes),
        "enabled_routes": sorted(enabled_routes),
        "legacy_research_gpu_quarantine_preserved": True,
        "legacy_research_gpu_retry_invalidated_preserved": True,
    }


def verify_template(root: pathlib.Path = ROOT) -> dict[str, Any]:
    compiled = compiler.compile_policy(root)
    overlay = load_overlay(root)
    return verify_overlay(overlay, compiled, schema=load_schema(root))


def main() -> int:
    compiled = compiler.compile_policy(ROOT)
    overlay = load_overlay(ROOT)
    template = verify_overlay(overlay, compiled, schema=load_schema(ROOT))
    bound = bind_generation(
        overlay,
        generation_sha256=compiled["catalog_generation_sha256"],
    )
    frozen = verify_overlay(
        bound,
        compiled,
        schema=load_schema(ROOT),
        allow_template_zero_digest=False,
    )
    print("DEPLOYMENT_OVERLAY_TEMPLATE=PASS")
    print("DEPLOYMENT_OVERLAY_BOUND=PASS")
    print(json.dumps({"template": template, "bound": frozen}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
