"""Deterministic classification of bounded worker actions."""

from __future__ import annotations


def classify_action(action: dict) -> str:
    """Validate an action and classify it using fixed precedence.

    Intrinsic reasoning/authority issues outrank task-size decomposition.
    """
    if not isinstance(action, dict):
        raise ValueError("action must be a dictionary")

    required = (
        "reasoning_class",
        "unresolved_architecture",
        "authority_expansion",
        "objective_validator",
        "context_items",
        "files_touched",
    )
    if any(field not in action for field in required):
        raise ValueError("action is missing a required field")

    if (
        not isinstance(action["reasoning_class"], str)
        or action["reasoning_class"] not in {"LOW", "MEDIUM", "HIGH"}
    ):
        raise ValueError("invalid reasoning_class")

    for field in ("unresolved_architecture", "authority_expansion", "objective_validator"):
        if type(action[field]) is not bool:
            raise ValueError(f"{field} must be a boolean")

    for field in ("context_items", "files_touched"):
        if type(action[field]) is not int or action[field] < 0:
            raise ValueError(f"{field} must be a non-negative integer")

    if (
        action["reasoning_class"] == "HIGH"
        or action["unresolved_architecture"]
        or action["authority_expansion"]
    ):
        return "ESCALATE_REASONING"

    if (
        action["context_items"] > 8
        or action["files_touched"] > 3
        or not action["objective_validator"]
    ):
        return "DECOMPOSE_AGAIN"

    return "LEAF_EXECUTABLE"
