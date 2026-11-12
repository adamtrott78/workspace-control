#!/usr/bin/env python3
"""Typed executor ingress builder for the modeled Lambda CI v3 control plane.

This is an ingress renderer only.  It cannot select runner classes, root
resources, GPU devices, model/runtime mounts, or systemd profiles.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import uuid
from typing import Any

import lambda_ci_policy_compiler as compiler

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class BuilderError(ValueError):
    pass


def _fail(message: str) -> None:
    raise BuilderError(message)


def _validate_argument(
    spec: dict[str, Any],
    value: Any,
    *,
    runner_class_ids: set[str],
) -> str:
    arg_type = spec["type"]
    name = spec["name"]
    if not isinstance(value, str):
        _fail(f"{name}: value must be string")

    if arg_type == "lower_hex_40":
        if HEX40.fullmatch(value) is None:
            _fail(f"{name}: expected lowercase 40-hex SHA")
    elif arg_type == "enum":
        if value not in spec["values"]:
            _fail(f"{name}: value is not an allowed enum member")
    elif arg_type == "catalog_runner_class_id":
        if value not in runner_class_ids:
            _fail(f"{name}: unknown runner class")
    elif arg_type == "uuid":
        try:
            parsed = uuid.UUID(value)
        except (ValueError, AttributeError) as exc:
            raise BuilderError(f"{name}: invalid UUID") from exc
        if str(parsed) != value.lower():
            _fail(f"{name}: UUID must use canonical form")
    else:
        _fail(f"{name}: unsupported argument type {arg_type!r}")

    if any(ch.isspace() for ch in value):
        _fail(f"{name}: whitespace is not allowed")
    if "\n" in value or "\r" in value:
        _fail(f"{name}: line breaks are not allowed")
    return value


def _runner_class_ids(compiled: dict[str, Any]) -> set[str]:
    return set(compiled["root_projection"]["runner_classes"])


def build_action(
    action_id: str,
    arguments: dict[str, Any],
    *,
    compiled: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if compiled is None:
        compiled = compiler.compile_policy(ROOT)
    executor = compiled["executor_projection"]
    execution = executor["execution_actions"]
    maintenance = executor["maintenance_actions"]

    if action_id in execution:
        action = execution[action_id]
        kind = "EXECUTION_TRIGGER"
    elif action_id in maintenance:
        action = maintenance[action_id]
        kind = "MAINTENANCE"
    else:
        _fail(f"unknown action_id: {action_id}")

    specs = action["arguments"]
    expected = {item["name"] for item in specs}
    supplied = set(arguments)
    extra = sorted(supplied - expected)
    missing = sorted(
        item["name"]
        for item in specs
        if item.get("required") is True and item["name"] not in supplied
    )
    if extra:
        _fail(f"{action_id}: unexpected arguments: {extra}")
    if missing:
        _fail(f"{action_id}: missing required arguments: {missing}")

    class_ids = _runner_class_ids(compiled)
    rendered_args = []
    normalized = {}
    for spec in specs:
        name = spec["name"]
        if name not in arguments:
            continue
        normalized[name] = _validate_argument(
            spec,
            arguments[name],
            runner_class_ids=class_ids,
        )
        rendered_args.append(normalized[name])

    command = action["command"]
    rendered = " ".join([command, *rendered_args])
    if "\n" in rendered or "\r" in rendered:
        _fail("rendered command contains line break")

    result = {
        "schema_version": 1,
        "control_plane_generation_sha256": executor["control_plane_generation_sha256"],
        "executor_policy_sha256": executor["executor_policy_sha256"],
        "action_id": action_id,
        "kind": kind,
        "repository": action.get("repository", "adamtrott78/workspace-control"),
        "arguments": normalized,
        "rendered_comment": rendered,
    }
    if kind == "EXECUTION_TRIGGER":
        result["route_id"] = action["route_id"]
    else:
        result["root_operation"] = action["root_operation"]
        result["authority"] = action["authority"]
    return result


def list_actions(*, compiled: dict[str, Any] | None = None) -> list[str]:
    if compiled is None:
        compiled = compiler.compile_policy(ROOT)
    executor = compiled["executor_projection"]
    return sorted([
        *executor["execution_actions"].keys(),
        *executor["maintenance_actions"].keys(),
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action_id", nargs="?")
    parser.add_argument("--arg", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    compiled = compiler.compile_policy(ROOT)
    if args.list:
        for action_id in list_actions(compiled=compiled):
            print(action_id)
        return 0
    if not args.action_id:
        parser.error("action_id is required unless --list is used")

    values: dict[str, str] = {}
    for item in args.arg:
        if "=" not in item:
            parser.error("--arg requires NAME=VALUE")
        name, value = item.split("=", 1)
        if not name or name in values:
            parser.error(f"duplicate/invalid argument name: {name!r}")
        values[name] = value

    result = build_action(args.action_id, values, compiled=compiled)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
