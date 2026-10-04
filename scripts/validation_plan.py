#!/usr/bin/env python3

import argparse
import fnmatch
import json
import sys
from pathlib import Path


TIER_ORDER = {
    "FAST_STATIC": 0,
    "TARGETED_PR": 1,
    "FULL_INTEGRATION": 2,
    "CANONICAL_REGRESSION": 3,
}


class ValidationPlanError(ValueError):
    pass


def load_profile(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text())
    except OSError as exc:
        raise ValidationPlanError(f"could not read profile {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationPlanError(f"invalid profile JSON in {path}: {exc}") from exc
    validate_profile(data)
    return data


def _require_nonempty_string(value, field):
    if not isinstance(value, str) or not value:
        raise ValidationPlanError(f"{field}: expected non-empty string")


def _require_string_list(value, field, *, allow_empty=False):
    if not isinstance(value, list):
        raise ValidationPlanError(f"{field}: expected array")
    if not allow_empty and not value:
        raise ValidationPlanError(f"{field}: expected non-empty array")
    for index, item in enumerate(value):
        _require_nonempty_string(item, f"{field}[{index}]")


def validate_profile(data):
    if not isinstance(data, dict):
        raise ValidationPlanError("profile: expected object")
    if data.get("schema_version") != 1:
        raise ValidationPlanError("schema_version: expected 1")
    _require_nonempty_string(data.get("repository"), "repository")
    default_tier = data.get("default_tier")
    force_full_tier = data.get("force_full_tier")
    if default_tier not in TIER_ORDER:
        raise ValidationPlanError("default_tier: unknown tier")
    if force_full_tier not in TIER_ORDER:
        raise ValidationPlanError("force_full_tier: unknown tier")
    if TIER_ORDER[force_full_tier] < TIER_ORDER["FULL_INTEGRATION"]:
        raise ValidationPlanError(
            "force_full_tier: must be FULL_INTEGRATION or stronger"
        )

    tier_checks = data.get("tier_checks", {})
    if not isinstance(tier_checks, dict):
        raise ValidationPlanError("tier_checks: expected object")
    for tier, checks in tier_checks.items():
        if tier not in TIER_ORDER:
            raise ValidationPlanError(f"tier_checks.{tier}: unknown tier")
        _require_string_list(
            checks,
            f"tier_checks.{tier}",
            allow_empty=True,
        )

    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValidationPlanError("rules: expected non-empty array")

    seen_ids = set()
    for index, rule in enumerate(rules):
        field = f"rules[{index}]"
        if not isinstance(rule, dict):
            raise ValidationPlanError(f"{field}: expected object")
        rule_id = rule.get("id")
        _require_nonempty_string(rule_id, f"{field}.id")
        if rule_id in seen_ids:
            raise ValidationPlanError(f"{field}.id: duplicate {rule_id!r}")
        seen_ids.add(rule_id)
        tier = rule.get("tier")
        if tier not in TIER_ORDER:
            raise ValidationPlanError(f"{field}.tier: unknown tier")
        _require_string_list(rule.get("patterns"), f"{field}.patterns")
        _require_string_list(rule.get("checks", []), f"{field}.checks", allow_empty=True)
    return True


def _matches(path, patterns):
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def build_plan(profile, changed_paths, *, force_full=False):
    validate_profile(profile)
    if not isinstance(changed_paths, list) or not changed_paths:
        raise ValidationPlanError("changed_paths: expected non-empty array")

    normalized = []
    for index, path in enumerate(changed_paths):
        _require_nonempty_string(path, f"changed_paths[{index}]")
        clean = path.strip()
        if clean.startswith("./"):
            clean = clean[2:]
        if not clean:
            raise ValidationPlanError(
                f"changed_paths[{index}]: path became empty after normalization"
            )
        if (
            clean.startswith("/")
            or clean == ".."
            or clean.startswith("../")
            or "/../" in clean
            or clean.endswith("/..")
        ):
            raise ValidationPlanError(
                f"changed_paths[{index}]: expected repository-relative path"
            )
        normalized.append(clean)
    normalized = sorted(set(normalized))

    path_results = []
    selected_tier = "FAST_STATIC"
    required_checks = set()
    escalation_reasons = []

    for path in normalized:
        matches = []
        for rule in profile["rules"]:
            if _matches(path, rule["patterns"]):
                matches.append({
                    "id": rule["id"],
                    "tier": rule["tier"],
                    "checks": list(rule.get("checks", [])),
                })

        if not matches:
            tier = profile["default_tier"]
            path_checks = []
            escalation_reasons.append(
                f"{path}: no lower-risk rule matched; defaulted to {tier}"
            )
        else:
            tier = max(matches, key=lambda item: TIER_ORDER[item["tier"]])["tier"]
            path_checks = sorted({
                check
                for match in matches
                for check in match["checks"]
            })

        required_checks.update(path_checks)
        if TIER_ORDER[tier] > TIER_ORDER[selected_tier]:
            selected_tier = tier

        path_results.append({
            "path": path,
            "tier": tier,
            "matches": matches,
            "required_checks": path_checks,
        })

    if force_full:
        floor = profile["force_full_tier"]
        if TIER_ORDER[selected_tier] < TIER_ORDER[floor]:
            selected_tier = floor
        escalation_reasons.append(
            f"force_full requested; selected at least {floor}"
        )

    for result in path_results:
        if TIER_ORDER[result["tier"]] < TIER_ORDER[selected_tier]:
            escalation_reasons.append(
                f"{result['path']}: raised by mixed-change maximum {selected_tier}"
            )

    tier_checks = profile.get("tier_checks", {})
    if isinstance(tier_checks, dict):
        required_checks.update(tier_checks.get(selected_tier, []))

    return {
        "schema_version": 1,
        "repository": profile["repository"],
        "changed_paths": normalized,
        "force_full": bool(force_full),
        "selected_tier": selected_tier,
        "required_checks": sorted(required_checks),
        "escalation_reasons": sorted(set(escalation_reasons)),
        "paths": path_results,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Compute a fail-closed validation plan from changed paths."
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument(
        "--changed-path",
        action="append",
        dest="changed_paths",
        required=True,
        help="changed repository-relative path; repeat for multiple paths",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="force at least the profile's full-integration tier",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        profile = load_profile(args.profile)
        plan = build_plan(profile, args.changed_paths, force_full=args.force_full)
    except ValidationPlanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"REPOSITORY: {plan['repository']}")
        print(f"TIER:       {plan['selected_tier']}")
        print("PATHS:")
        for item in plan["paths"]:
            print(f"  - {item['path']}: {item['tier']}")
        print("REQUIRED CHECKS:")
        for check in plan["required_checks"]:
            print(f"  - {check}")
        if plan["escalation_reasons"]:
            print("ESCALATIONS:")
            for reason in plan["escalation_reasons"]:
                print(f"  - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
