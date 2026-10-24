#!/usr/bin/env python3
"""Validate finite scientific verdict partitions for methodology meta-experiments."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any


def enumerate_states(dimensions: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(dimensions)
    values = [dimensions[key] for key in keys]
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def rule_matches(state: dict[str, Any], rule: dict[str, Any]) -> bool:
    return all(state.get(key) == value for key, value in rule["when"].items())


def audit_partition(partition: dict[str, Any]) -> dict[str, Any]:
    states = enumerate_states(partition["dimensions"])
    uncovered: list[dict[str, Any]] = []
    overlaps: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []

    for state in states:
        matched = [
            rule["verdict"]
            for rule in partition["rules"]
            if rule_matches(state, rule)
        ]
        assignments.append({"state": state, "verdicts": matched})
        if not matched:
            uncovered.append(state)
        elif len(matched) > 1:
            overlaps.append({"state": state, "verdicts": matched})

    return {
        "state_count": len(states),
        "uncovered_count": len(uncovered),
        "uncovered_states": uncovered,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "assignments": assignments,
    }


def classify(audit: dict[str, Any]) -> dict[str, Any]:
    original = audit_partition(audit["positive_control"]["original_design"])
    corrected = audit_partition(audit["positive_control"]["corrected_design"])

    generic_rule = (
        original["uncovered_count"] > 0
        and corrected["uncovered_count"] == 0
        and original["overlap_count"] == 0
        and corrected["overlap_count"] == 0
        and audit["positive_control"]["original_design"]["operational_invalidity_separate"]
        and audit["positive_control"]["corrected_design"]["operational_invalidity_separate"]
    )

    verdict = "CANDIDATE_SUPPORTED" if generic_rule else "CANDIDATE_REJECTED"
    return {
        "verdict": verdict,
        "original": original,
        "corrected": corrected,
        "generic_rule_uses_literal_missing_verdict_name": False,
        "operational_invalidity_separate": (
            audit["positive_control"]["original_design"]["operational_invalidity_separate"]
            and audit["positive_control"]["corrected_design"]["operational_invalidity_separate"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_file", type=Path)
    parser.add_argument("--write-result", type=Path)
    args = parser.parse_args()

    audit = json.loads(args.audit_file.read_text())
    result = classify(audit)

    if args.write_result:
        output = dict(audit)
        output["result"] = result
        args.write_result.write_text(json.dumps(output, indent=2) + "\n")
    else:
        print(json.dumps(result, indent=2))

    return 0 if result["verdict"] == "CANDIDATE_SUPPORTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
