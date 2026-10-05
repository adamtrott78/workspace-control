#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


MILESTONE_STATUSES = {"DONE", "CURRENT", "PENDING", "BLOCKED"}
STATES = {
    "PLANNING",
    "IMPLEMENTING",
    "VALIDATING",
    "WAITING_EXTERNAL",
    "RECOVERING",
    "CLOSING",
}
MAX_TOOL_CALLS_PER_HEARTBEAT_LEASE = 3

TRIGGER_EVENTS = {
    "OBJECTIVE_CHANGED",
    "DIAGNOSIS_CHANGED",
    "SCOPE_CHANGED",
    "FAILURE_DISCOVERED",
    "MILESTONE_STARTED",
    "MILESTONE_COMPLETED",
    "EXTERNAL_WAIT_STARTED",
    "EXTERNAL_WAIT_ENDED",
    "CLOSURE_EVALUATED",
}


class ProgressHeartbeatError(ValueError):
    pass


def _nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ProgressHeartbeatError(f"{field}: expected non-empty string")
    return value.strip()


def _nonnegative_int(value, field):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProgressHeartbeatError(f"{field}: expected non-negative integer")
    return value


def _bool(value, field):
    if not isinstance(value, bool):
        raise ProgressHeartbeatError(f"{field}: expected boolean")
    return value


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise ProgressHeartbeatError("snapshot: expected object")
    if snapshot.get("schema_version") != 1:
        raise ProgressHeartbeatError("schema_version: expected 1")

    _nonempty(snapshot.get("task_id"), "task_id")
    _nonempty(snapshot.get("objective"), "objective")
    _nonempty(snapshot.get("current_operation"), "current_operation")
    _nonempty(snapshot.get("next_milestone"), "next_milestone")

    state = snapshot.get("state")
    if state not in STATES:
        raise ProgressHeartbeatError(
            f"state: expected one of {sorted(STATES)}"
        )

    milestones = snapshot.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        raise ProgressHeartbeatError("milestones: expected non-empty array")

    ids = set()
    current_count = 0
    for index, item in enumerate(milestones):
        field = f"milestones[{index}]"
        if not isinstance(item, dict):
            raise ProgressHeartbeatError(f"{field}: expected object")
        mid = _nonempty(item.get("id"), f"{field}.id")
        if mid in ids:
            raise ProgressHeartbeatError(f"{field}.id: duplicate milestone id")
        ids.add(mid)
        _nonempty(item.get("label"), f"{field}.label")
        status = item.get("status")
        if status not in MILESTONE_STATUSES:
            raise ProgressHeartbeatError(
                f"{field}.status: expected one of {sorted(MILESTONE_STATUSES)}"
            )
        if status == "CURRENT":
            current_count += 1

    if current_count > 1:
        raise ProgressHeartbeatError(
            "milestones: at most one CURRENT milestone is allowed"
        )

    progress = snapshot.get("scope_progress")
    if not isinstance(progress, dict):
        raise ProgressHeartbeatError("scope_progress: expected object")
    completed = _nonnegative_int(
        progress.get("completed_execute_now"),
        "scope_progress.completed_execute_now",
    )
    total = _nonnegative_int(
        progress.get("total_execute_now"),
        "scope_progress.total_execute_now",
    )
    if completed > total:
        raise ProgressHeartbeatError(
            "scope_progress.completed_execute_now: cannot exceed total_execute_now"
        )

    for field in (
        "required_corrections_remaining",
        "bounded_enabling_remaining",
        "authorized_expansion_remaining",
        "deferred_followups",
    ):
        _nonnegative_int(progress.get(field), f"scope_progress.{field}")

    wait = snapshot.get("wait_state")
    if not isinstance(wait, dict):
        raise ProgressHeartbeatError("wait_state: expected object")
    active = _bool(wait.get("active"), "wait_state.active")
    reason = wait.get("reason")
    dependency = wait.get("dependency")
    if active:
        _nonempty(reason, "wait_state.reason")
        _nonempty(dependency, "wait_state.dependency")
    else:
        if reason is not None:
            _nonempty(reason, "wait_state.reason")
        if dependency is not None:
            _nonempty(dependency, "wait_state.dependency")

    _bool(snapshot.get("meaningful_change"), "meaningful_change")
    return True


def should_emit(*, event, tool_calls_since_update, elapsed_seconds,
                meaningful_change):
    if event is not None and event not in TRIGGER_EVENTS | {"POLL_UNCHANGED"}:
        raise ProgressHeartbeatError("event: unknown heartbeat event")
    calls = _nonnegative_int(tool_calls_since_update, "tool_calls_since_update")
    elapsed = _nonnegative_int(elapsed_seconds, "elapsed_seconds")
    changed = _bool(meaningful_change, "meaningful_change")

    if changed:
        return True
    if event in TRIGGER_EVENTS:
        return True
    if calls >= 3:
        return True
    if elapsed >= 15:
        return True
    return False


def tool_gate(*, event, tool_calls_since_heartbeat, elapsed_seconds,
              meaningful_change):
    """Return whether another tool operation is allowed before a heartbeat.

    A heartbeat resets tool_calls_since_heartbeat to zero. Once three tool
    operations have occurred, the lease is exhausted and the next tool call is
    blocked until a human-readable heartbeat is emitted.
    """
    if event is not None and event not in TRIGGER_EVENTS | {"POLL_UNCHANGED"}:
        raise ProgressHeartbeatError("event: unknown heartbeat event")
    calls = _nonnegative_int(
        tool_calls_since_heartbeat,
        "tool_calls_since_heartbeat",
    )
    elapsed = _nonnegative_int(elapsed_seconds, "elapsed_seconds")
    changed = _bool(meaningful_change, "meaningful_change")

    if changed or event in TRIGGER_EVENTS:
        return "HEARTBEAT_REQUIRED"
    if calls >= MAX_TOOL_CALLS_PER_HEARTBEAT_LEASE:
        return "HEARTBEAT_REQUIRED"
    if elapsed >= 15:
        return "HEARTBEAT_REQUIRED"
    return "ALLOW_TOOL"


def render_snapshot(snapshot):
    validate_snapshot(snapshot)

    progress = snapshot["scope_progress"]
    done = [
        item["label"]
        for item in snapshot["milestones"]
        if item["status"] == "DONE"
    ]
    current = [
        item["label"]
        for item in snapshot["milestones"]
        if item["status"] == "CURRENT"
    ]

    lines = [
        f"Objective: {snapshot['objective']}",
        (
            "Progress: "
            f"{progress['completed_execute_now']}/"
            f"{progress['total_execute_now']} execute-now items complete."
        ),
    ]

    if done:
        lines.append("Completed: " + "; ".join(done[-4:]) + ".")
    if current:
        lines.append("Current milestone: " + current[0] + ".")

    lines.append("Now: " + snapshot["current_operation"])
    lines.append(
        "Scope remaining: "
        f"required={progress['required_corrections_remaining']}, "
        f"enabling={progress['bounded_enabling_remaining']}, "
        f"authorized-expansion={progress['authorized_expansion_remaining']}; "
        f"deferred={progress['deferred_followups']}."
    )
    lines.append("Next durable milestone: " + snapshot["next_milestone"])

    wait = snapshot["wait_state"]
    if wait["active"]:
        lines.append(
            f"External dependency: {wait['dependency']} — {wait['reason']}"
        )
        if not snapshot["meaningful_change"]:
            lines.append(
                "No meaningful state change since the previous heartbeat; "
                "no additional implementation is justified by polling alone."
            )

    return "\n".join(lines)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProgressHeartbeatError(
            f"could not read JSON {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ProgressHeartbeatError(
            f"invalid JSON in {path}: {exc}"
        ) from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate and render operator progress heartbeats."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--file", required=True)

    render = sub.add_parser("render")
    render.add_argument("--file", required=True)

    due = sub.add_parser("due")
    due.add_argument("--event")
    due.add_argument("--tool-calls", type=int, default=0)
    due.add_argument("--elapsed-seconds", type=int, default=0)
    due.add_argument("--meaningful-change", action="store_true")

    gate = sub.add_parser("gate")
    gate.add_argument("--event")
    gate.add_argument("--tool-calls", type=int, default=0)
    gate.add_argument("--elapsed-seconds", type=int, default=0)
    gate.add_argument("--meaningful-change", action="store_true")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "validate":
            validate_snapshot(load_json(args.file))
            print("PASS")
        elif args.command == "render":
            print(render_snapshot(load_json(args.file)))
        elif args.command == "due":
            print(
                "EMIT"
                if should_emit(
                    event=args.event,
                    tool_calls_since_update=args.tool_calls,
                    elapsed_seconds=args.elapsed_seconds,
                    meaningful_change=args.meaningful_change,
                )
                else "SUPPRESS"
            )
        elif args.command == "gate":
            print(
                tool_gate(
                    event=args.event,
                    tool_calls_since_heartbeat=args.tool_calls,
                    elapsed_seconds=args.elapsed_seconds,
                    meaningful_change=args.meaningful_change,
                )
            )
        else:
            raise ProgressHeartbeatError("unknown command")
        return 0
    except ProgressHeartbeatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
