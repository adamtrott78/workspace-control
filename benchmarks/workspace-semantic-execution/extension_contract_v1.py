"""Validation helpers for open-world semantic execution extensions."""
from __future__ import annotations

from typing import Any, Mapping


class ExtensionContractError(ValueError):
    pass


FORBIDDEN_AUTHORITY_EFFECTS = {
    "creates_permission",
    "removes_prohibition",
    "satisfies_review_requirement",
    "widens_authority",
    "guesses_unknown_extension_as_executable",
}


def validate_extension(core: Mapping[str, Any], extension: Mapping[str, Any]) -> dict[str, Any]:
    contract = core["extension_contract"]
    missing = [
        field for field in contract["required_metadata"]
        if field not in extension
    ]
    if missing:
        raise ExtensionContractError("missing required metadata: " + ",".join(sorted(missing)))

    extension_id = extension["extension_id"]
    if not isinstance(extension_id, str) or not extension_id or ":" in extension_id:
        raise ExtensionContractError("extension_id must be a non-empty namespace token")

    if extension["compatible_core_version"] != core["design_id"]:
        raise ExtensionContractError("extension targets a different core version")

    authority_effects = extension.get("authority_effects", {})
    for field in FORBIDDEN_AUTHORITY_EFFECTS:
        if authority_effects.get(field) is True:
            raise ExtensionContractError(f"forbidden authority effect: {field}")

    for item in extension["type_definitions"]:
        name = item.get("name")
        if not isinstance(name, str) or not name.startswith(extension_id + ":"):
            raise ExtensionContractError("all extension types must be namespaced")

    for item in extension["relation_definitions"]:
        name = item.get("name")
        if not isinstance(name, str) or not name.startswith(extension_id + ":"):
            raise ExtensionContractError("all extension relations must be namespaced")

    workflow = extension.get("workflow_projection")
    if not isinstance(workflow, Mapping):
        raise ExtensionContractError("workflow_projection is required for this proof fixture")
    missing_workflow = [
        field
        for field in core["workflow_projection_contract"]["required_generic_fields"]
        if field not in workflow
    ]
    if missing_workflow:
        raise ExtensionContractError(
            "workflow projection missing generic fields: "
            + ",".join(sorted(missing_workflow))
        )

    if workflow.get("domain_extension") != extension_id:
        raise ExtensionContractError("workflow projection must reference its own extension")

    if workflow.get("authority_refs"):
        # This synthetic proof requires no execution authority. A future extension
        # may reference existing authority, but it may never manufacture it.
        raise ExtensionContractError("unseen-extension proof must remain authority-free")

    if extension_id in core.get("example_extensions", {}):
        raise ExtensionContractError(
            "proof extension is already encoded as a core example and is not unseen"
        )

    return {
        "valid": True,
        "extension_id": extension_id,
        "core_kernel_change_required": False,
        "closed_domain_enum_change_required": False,
        "authority_widened": False,
        "unknown_extension_behavior": contract["unknown_extension_behavior"],
    }
