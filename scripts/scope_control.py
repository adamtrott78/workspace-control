#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


REQUIRED_CORRECTION = "REQUIRED_CORRECTION"
BOUNDED_ENABLING_CHANGE = "BOUNDED_ENABLING_CHANGE"
AUTHORIZED_SCOPE_EXPANSION = "AUTHORIZED_SCOPE_EXPANSION"
DEFERRED_FOLLOWUP = "DEFERRED_FOLLOWUP"

EXECUTE_NOW_CLASSES = {
    REQUIRED_CORRECTION,
    BOUNDED_ENABLING_CHANGE,
    AUTHORIZED_SCOPE_EXPANSION,
}

CHECKPOINT_REQUIRED = "CHECKPOINT_REQUIRED"
CONTINUE_BOUNDED_WORK = "CONTINUE_BOUNDED_WORK"
CONTINUE_OWNING_TASK = "CONTINUE_OWNING_TASK"
CHECKPOINT_AND_STOP = "CHECKPOINT_AND_STOP"


class ScopeControlError(ValueError):
    pass


def _require_nonempty_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ScopeControlError(f"{field}: expected non-empty string")
    return value.strip()


def _require_bool(value, field):
    if not isinstance(value, bool):
        raise ScopeControlError(f"{field}: expected boolean")
    return value


def _require_string_list(value, field, *, allow_empty=True):
    if not isinstance(value, list):
        raise ScopeControlError(f"{field}: expected array")
    if not allow_empty and not value:
        raise ScopeControlError(f"{field}: expected non-empty array")
    for index, item in enumerate(value):
        _require_nonempty_string(item, f"{field}[{index}]")
    return value


def validate_scope_envelope(envelope):
    if not isinstance(envelope, dict):
        raise ScopeControlError("scope_envelope: expected object")
    if envelope.get("schema_version") != 1:
        raise ScopeControlError("scope_envelope.schema_version: expected 1")

    _require_nonempty_string(
        envelope.get("task_id"),
        "scope_envelope.task_id",
    )
    _require_nonempty_string(
        envelope.get("objective"),
        "scope_envelope.objective",
    )
    _require_nonempty_string(
        envelope.get("next_safe_action"),
        "scope_envelope.next_safe_action",
    )
    _require_string_list(
        envelope.get("allowed_now", []),
        "scope_envelope.allowed_now",
    )
    _require_string_list(
        envelope.get("defer_by_default", []),
        "scope_envelope.defer_by_default",
    )
    _require_string_list(
        envelope.get("explicit_authorizations", []),
        "scope_envelope.explicit_authorizations",
    )

    policy = envelope.get("closure_policy")
    if not isinstance(policy, dict):
        raise ScopeControlError(
            "scope_envelope.closure_policy: expected object"
        )
    for name in (
        "stop_when_objective_satisfied",
        "defer_nonblocking_findings",
        "require_validation_pass",
        "require_durable_checkpoint",
    ):
        _require_bool(
            policy.get(name),
            f"scope_envelope.closure_policy.{name}",
        )
    return True


def validate_finding(finding):
    if not isinstance(finding, dict):
        raise ScopeControlError("finding: expected object")
    for field in ("id", "summary"):
        _require_nonempty_string(
            finding.get(field),
            f"finding.{field}",
        )
    _require_string_list(
        finding.get("evidence", []),
        "finding.evidence",
        allow_empty=False,
    )
    for field in (
        "affects_correctness",
        "affects_safety",
        "affects_durability",
        "blocks_next_safe_action",
        "required_for_validation",
        "new_workstream",
    ):
        _require_bool(
            finding.get(field),
            f"finding.{field}",
        )
    owner = finding.get("suggested_owner")
    if owner is not None:
        _require_nonempty_string(owner, "finding.suggested_owner")
    urgency = finding.get("urgency")
    if urgency is not None and urgency not in {
        "LOW",
        "NORMAL",
        "HIGH",
        "CRITICAL",
    }:
        raise ScopeControlError(
            "finding.urgency: expected LOW, NORMAL, HIGH, or CRITICAL"
        )
    return True


def classify_finding(envelope, finding):
    validate_scope_envelope(envelope)
    validate_finding(finding)

    finding_id = finding["id"]
    authorized = finding_id in set(
        envelope.get("explicit_authorizations", [])
    )

    if (
        finding["affects_correctness"]
        or finding["affects_safety"]
        or finding["affects_durability"]
    ):
        classification = REQUIRED_CORRECTION
        reason = (
            "finding affects correctness, safety, or durability of the "
            "owning objective"
        )
    elif (
        finding["blocks_next_safe_action"]
        or finding["required_for_validation"]
    ):
        classification = BOUNDED_ENABLING_CHANGE
        reason = (
            "finding directly blocks the recorded next_safe_action or "
            "required validation"
        )
    elif authorized:
        classification = AUTHORIZED_SCOPE_EXPANSION
        reason = "owning scope explicitly authorizes this finding"
    else:
        classification = DEFERRED_FOLLOWUP
        reason = (
            "finding is non-blocking adjacent work and lacks explicit "
            "scope-expansion authorization"
        )

    return {
        "finding_id": finding_id,
        "classification": classification,
        "execute_now": classification in EXECUTE_NOW_CLASSES,
        "scope_expansion": classification == AUTHORIZED_SCOPE_EXPANSION,
        "reason": reason,
    }


def build_followup(finding, decision):
    validate_finding(finding)
    if not isinstance(decision, dict):
        raise ScopeControlError("decision: expected object")
    if decision.get("finding_id") != finding["id"]:
        raise ScopeControlError(
            "decision.finding_id: must match finding.id"
        )
    if decision.get("classification") != DEFERRED_FOLLOWUP:
        raise ScopeControlError(
            "decision.classification: follow-up requires DEFERRED_FOLLOWUP"
        )

    return {
        "schema_version": 1,
        "finding_id": finding["id"],
        "summary": finding["summary"],
        "evidence": list(finding["evidence"]),
        "suggested_owner": finding.get("suggested_owner"),
        "urgency": finding.get("urgency", "NORMAL"),
        "reason": decision["reason"],
    }


def validate_scope_state(state):
    if not isinstance(state, dict):
        raise ScopeControlError("scope_state: expected object")
    for field in (
        "objective_satisfied",
        "required_validation_passed",
        "mutation_durable",
    ):
        _require_bool(state.get(field), f"scope_state.{field}")
    _require_string_list(
        state.get("blockers", []),
        "scope_state.blockers",
    )

    decisions = state.get("finding_decisions", [])
    if not isinstance(decisions, list):
        raise ScopeControlError(
            "scope_state.finding_decisions: expected array"
        )
    for index, decision in enumerate(decisions):
        field = f"scope_state.finding_decisions[{index}]"
        if not isinstance(decision, dict):
            raise ScopeControlError(f"{field}: expected object")
        _require_nonempty_string(
            decision.get("finding_id"),
            f"{field}.finding_id",
        )
        classification = decision.get("classification")
        if classification not in {
            REQUIRED_CORRECTION,
            BOUNDED_ENABLING_CHANGE,
            AUTHORIZED_SCOPE_EXPANSION,
            DEFERRED_FOLLOWUP,
        }:
            raise ScopeControlError(
                f"{field}.classification: unknown classification"
            )
        _require_bool(
            decision.get("execute_now"),
            f"{field}.execute_now",
        )
        if decision["execute_now"] != (
            classification in EXECUTE_NOW_CLASSES
        ):
            raise ScopeControlError(
                f"{field}.execute_now: inconsistent with classification"
            )
    return True


def scope_closure_decision(envelope, state):
    validate_scope_envelope(envelope)
    validate_scope_state(state)

    policy = envelope["closure_policy"]

    if policy["require_durable_checkpoint"] and not state["mutation_durable"]:
        return {
            "decision": CHECKPOINT_REQUIRED,
            "stop": False,
            "reason": "current mutation/evidence is not yet durably checkpointed",
        }

    execute_now = [
        decision
        for decision in state["finding_decisions"]
        if decision["execute_now"]
    ]
    if execute_now:
        return {
            "decision": CONTINUE_BOUNDED_WORK,
            "stop": False,
            "reason": (
                "one or more findings are required, blocking, or explicitly "
                "authorized for the current scope"
            ),
            "finding_ids": [
                decision["finding_id"] for decision in execute_now
            ],
        }

    if state["blockers"]:
        return {
            "decision": CONTINUE_OWNING_TASK,
            "stop": False,
            "reason": "owning task still has unresolved blockers",
            "blockers": list(state["blockers"]),
        }

    if not state["objective_satisfied"]:
        return {
            "decision": CONTINUE_OWNING_TASK,
            "stop": False,
            "reason": "owning objective is not yet satisfied",
        }

    if (
        policy["require_validation_pass"]
        and not state["required_validation_passed"]
    ):
        return {
            "decision": CONTINUE_OWNING_TASK,
            "stop": False,
            "reason": "required validation has not passed",
        }

    if policy["stop_when_objective_satisfied"]:
        return {
            "decision": CHECKPOINT_AND_STOP,
            "stop": True,
            "reason": (
                "owning objective is satisfied, required validation passed, "
                "durable state exists, and remaining findings are non-blocking"
            ),
            "deferred_followup_ids": [
                decision["finding_id"]
                for decision in state["finding_decisions"]
                if decision["classification"] == DEFERRED_FOLLOWUP
            ],
        }

    return {
        "decision": CONTINUE_OWNING_TASK,
        "stop": False,
        "reason": "closure policy does not require stop",
    }


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScopeControlError(
            f"could not read JSON {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ScopeControlError(
            f"invalid JSON in {path}: {exc}"
        ) from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Workspace-control scope adherence and scope-closure primitives."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    classify = sub.add_parser("classify")
    classify.add_argument("--envelope", required=True)
    classify.add_argument("--finding", required=True)

    closure = sub.add_parser("closure")
    closure.add_argument("--envelope", required=True)
    closure.add_argument("--state", required=True)

    followup = sub.add_parser("followup")
    followup.add_argument("--finding", required=True)
    followup.add_argument("--decision", required=True)

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "classify":
            result = classify_finding(
                load_json(args.envelope),
                load_json(args.finding),
            )
        elif args.command == "closure":
            result = scope_closure_decision(
                load_json(args.envelope),
                load_json(args.state),
            )
        elif args.command == "followup":
            result = build_followup(
                load_json(args.finding),
                load_json(args.decision),
            )
        else:
            raise ScopeControlError("unknown command")

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except ScopeControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
