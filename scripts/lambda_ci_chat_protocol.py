#!/usr/bin/env python3
"""Deterministic reducer for ChatGPT <-> GitHub Lambda CI orchestration.

This module has no GitHub credentials and performs no network or runtime action.
It reduces normalized GitHub observations into fail-closed correlation and
next-action decisions.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ProtocolError(ValueError):
    pass


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ProtocolError("timestamp must be a non-empty string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ProtocolError(f"invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ProtocolError("timestamp must include timezone")
    return parsed


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "repository",
        "pr_number",
        "pr_title",
        "candidate_sha",
        "workflow_path",
        "workflow_name",
        "actor",
        "trigger_comment_id",
        "trigger_comment_created_at",
        "baseline_run_number",
        "receipt_artifact",
    }
    missing = sorted(required - request.keys())
    if missing:
        raise ProtocolError(f"missing request fields: {', '.join(missing)}")
    if request["schema_version"] != 1:
        raise ProtocolError("unsupported schema_version")
    if not SHA_RE.fullmatch(str(request["candidate_sha"])):
        raise ProtocolError("candidate_sha must be 40 lowercase hex characters")
    if not isinstance(request["pr_number"], int) or request["pr_number"] < 1:
        raise ProtocolError("pr_number must be a positive integer")
    if not isinstance(request["trigger_comment_id"], int) or request["trigger_comment_id"] < 1:
        raise ProtocolError("trigger_comment_id must be a positive integer")
    if not isinstance(request["baseline_run_number"], int) or request["baseline_run_number"] < 0:
        raise ProtocolError("baseline_run_number must be a non-negative integer")
    _time(request["trigger_comment_created_at"])


def _actor_login(run: dict[str, Any]) -> str | None:
    actor = run.get("triggering_actor") or run.get("actor")
    if isinstance(actor, dict):
        value = actor.get("login")
        return value if isinstance(value, str) else None
    return None


def correlate_run(
    request: dict[str, Any], runs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Bind the run caused by one trigger, or fail closed on ambiguity."""
    validate_request(request)
    comment_time = _time(request["trigger_comment_created_at"])
    baseline = request["baseline_run_number"]

    candidates: list[dict[str, Any]] = []
    for run in runs:
        if run.get("path") != request["workflow_path"]:
            continue
        if run.get("event") != "issue_comment":
            continue
        if _actor_login(run) != request["actor"]:
            continue
        run_number = run.get("run_number")
        if not isinstance(run_number, int) or run_number <= baseline:
            continue
        created = run.get("created_at")
        if not isinstance(created, str) or _time(created) < comment_time:
            continue
        candidates.append(run)

    marker = f"comment:{request['trigger_comment_id']}"
    exact = [
        run
        for run in candidates
        if marker in str(run.get("display_title") or "")
    ]
    if len(exact) == 1:
        return {
            "decision": "BOUND_RUN",
            "correlation": "EXACT_COMMENT_ID",
            "run_id": exact[0].get("id"),
            "run_number": exact[0].get("run_number"),
        }
    if len(exact) > 1:
        return {
            "decision": "AMBIGUOUS",
            "correlation": "EXACT_COMMENT_ID_COLLISION",
            "candidate_run_ids": [run.get("id") for run in exact],
        }

    compatible = [
        run
        for run in candidates
        if run.get("display_title") == request["pr_title"]
    ]
    if len(compatible) == 1:
        return {
            "decision": "BOUND_RUN",
            "correlation": "PROVISIONAL_COMPAT",
            "run_id": compatible[0].get("id"),
            "run_number": compatible[0].get("run_number"),
        }
    if not compatible:
        return {
            "decision": "WAIT_FOR_RUN",
            "correlation": "NONE_YET",
        }
    return {
        "decision": "AMBIGUOUS",
        "correlation": "MULTIPLE_COMPAT_CANDIDATES",
        "candidate_run_ids": [run.get("id") for run in compatible],
    }


def verify_receipt(
    request: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    """Require terminal receipt identity to match the requested candidate."""
    validate_request(request)

    if receipt.get("pr_number") != request["pr_number"]:
        return {"verified": False, "reason": "PR_NUMBER_MISMATCH"}
    if receipt.get("expected_sha") != request["candidate_sha"]:
        return {"verified": False, "reason": "EXPECTED_SHA_MISMATCH"}

    actual = receipt.get("actual_sha")
    if actual is not None and actual != request["candidate_sha"]:
        return {"verified": False, "reason": "ACTUAL_SHA_MISMATCH"}

    if receipt.get("decision") != "PASS":
        return {"verified": False, "reason": "RECEIPT_NOT_PASS"}

    return {"verified": True, "reason": "MATCH"}


def next_action(
    request: dict[str, Any],
    run: dict[str, Any] | None,
    receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the cheapest next evidence/action class for one bound run."""
    validate_request(request)

    if run is None:
        return {"action": "DISCOVER_RUN"}

    status = run.get("status")
    conclusion = run.get("conclusion")

    if status == "queued":
        return {
            "action": "WAIT_EXTERNAL",
            "dependency": "RUNNER_ALLOCATION",
            "fetch_logs": False,
        }
    if status == "in_progress":
        return {
            "action": "WAIT_EXTERNAL",
            "dependency": "ACTIVE_COMPUTE",
            "fetch_logs": False,
        }
    if status != "completed":
        return {"action": "INSPECT_RUN_STATE", "status": status}

    if conclusion == "success":
        if receipt is None:
            return {
                "action": "FETCH_ARTIFACTS",
                "expected_artifact": request["receipt_artifact"],
            }
        verdict = verify_receipt(request, receipt)
        if verdict["verified"]:
            return {
                "action": "ACCEPT_AND_CONTINUE",
                "receipt": verdict,
            }
        return {
            "action": "REJECT_EVIDENCE",
            "receipt": verdict,
        }

    if conclusion in {
        "failure",
        "cancelled",
        "timed_out",
        "action_required",
        "stale",
        "startup_failure",
    }:
        return {
            "action": "FETCH_FAILURE_EVIDENCE",
            "conclusion": conclusion,
            "order": ["jobs", "failing-step-summary", "failing-job-log", "receipt"],
        }

    return {
        "action": "INSPECT_TERMINAL_STATE",
        "conclusion": conclusion,
    }


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    correlate = sub.add_parser("correlate")
    correlate.add_argument("--request", required=True)
    correlate.add_argument("--runs", required=True)

    nxt = sub.add_parser("next")
    nxt.add_argument("--request", required=True)
    nxt.add_argument("--run", required=True)
    nxt.add_argument("--receipt")

    args = parser.parse_args()
    request = _load(args.request)

    if args.command == "correlate":
        runs = _load(args.runs)
        if not isinstance(runs, list):
            raise ProtocolError("runs input must be a JSON array")
        _emit(correlate_run(request, runs))
        return 0

    run = _load(args.run)
    receipt = _load(args.receipt) if args.receipt else None
    _emit(next_action(request, run, receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
