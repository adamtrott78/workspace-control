"""Deterministic state/event/evaluator primitives for resumable-reasoning benchmarks.

This harness is deliberately authority-free. It models durable benchmark state,
external waits, generation fencing, decomposition, escalation evidence, and
objective terminal validation. It never grants execution authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Mapping


ARMS = {
    "A_frontier_long_horizon",
    "B_instant_persistent_chat",
    "C_instant_stateless_resume",
    "D_instant_decompose_critic",
    "E_hybrid_escalation",
}

READY_STATES = {"READY", "READY_TO_RESUME"}


class BenchmarkContractError(ValueError):
    """Raised when a benchmark-state transition violates the contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def context_packet_size_bytes(packet: Mapping[str, Any]) -> int:
    if not isinstance(packet, Mapping):
        raise BenchmarkContractError("context_packet must be a mapping")
    prohibited = {"full_prior_chat_transcript", "unbounded_repository_dump"}
    if prohibited.intersection(packet):
        raise BenchmarkContractError("context packet contains prohibited bulk context")
    return len(canonical_json_bytes(packet))


def new_run(
    *,
    arm: str,
    fixture_id: str,
    process_id: str,
    initial_generation: int = 0,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise BenchmarkContractError(f"unknown arm: {arm}")
    if not fixture_id or not process_id:
        raise BenchmarkContractError("fixture_id and process_id are required")
    if type(initial_generation) is not int or initial_generation < 0:
        raise BenchmarkContractError("initial_generation must be a non-negative exact integer")
    return {
        "schema_version": 1,
        "benchmark_id": "workspace-resumable-reasoning-v1",
        "fixture_id": fixture_id,
        "process_id": process_id,
        "arm": arm,
        "generation": initial_generation,
        "status": "READY",
        "owner": None,
        "invocations": [],
        "events": [],
        "pending_external": None,
        "child_processes": [],
        "escalations": [],
        "validator_results": [],
        "terminal_submission": None,
        "established_findings": [],
        "open_hypotheses": [],
        "unresolved_questions": [],
        "evidence_refs": [],
        "candidate_actions": [],
        "next_safe_action": None,
        "authority_refs": [],
        "validation_requirements": [],
        "metrics": {
            "retries": 0,
            "decomposition_count": 0,
            "max_decomposition_depth": 0,
            "failed_leaves": 0,
            "recovery_count": 0,
            "successful_recoveries": 0,
            "manual_state_relay_count": 0,
            "stale_worker_write_attempts": 0,
            "authority_provenance_violations": 0,
            "model_poll_invocations": 0,
            "deterministic_compute_operations": 0,
        },
    }


def _require_generation(run: Mapping[str, Any], expected_generation: int) -> None:
    if expected_generation != run["generation"]:
        raise BenchmarkContractError(
            f"stale generation: expected {run['generation']} got {expected_generation}"
        )


def claim_run(run: Mapping[str, Any], *, worker_id: str, expected_generation: int) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] not in READY_STATES:
        raise BenchmarkContractError(f"run is not claimable from {next_run['status']}")
    if not worker_id:
        raise BenchmarkContractError("worker_id is required")
    next_run["owner"] = worker_id
    next_run["status"] = "RUNNING"
    next_run["events"].append(
        {
            "kind": "CLAIM",
            "generation": expected_generation,
            "worker_id": worker_id,
        }
    )
    return next_run


def recover_run(
    run: Mapping[str, Any],
    *,
    new_worker_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("recovery requires a RUNNING generation")
    if not new_worker_id:
        raise BenchmarkContractError("new_worker_id is required")
    prior_owner = next_run["owner"]
    next_run["generation"] += 1
    next_run["owner"] = None
    next_run["status"] = "READY_TO_RESUME"
    next_run["metrics"]["recovery_count"] += 1
    next_run["events"].append(
        {
            "kind": "RECOVERY",
            "from_generation": expected_generation,
            "to_generation": next_run["generation"],
            "prior_owner": prior_owner,
            "replacement_worker_id": new_worker_id,
        }
    )
    return next_run


def _append_invocation(
    run: dict[str, Any],
    *,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    outcome: str,
    evidence_refs: list[str] | None = None,
) -> None:
    if not invocation_id:
        raise BenchmarkContractError("invocation_id is required")
    if any(item["invocation_id"] == invocation_id for item in run["invocations"]):
        raise BenchmarkContractError(f"duplicate invocation_id: {invocation_id}")
    if not isinstance(executor, Mapping) or not executor:
        raise BenchmarkContractError("executor identity is required")
    run["invocations"].append(
        {
            "invocation_id": invocation_id,
            "generation": run["generation"],
            "owner": run["owner"],
            "executor": dict(executor),
            "context_bytes": context_packet_size_bytes(context_packet),
            "outcome": outcome,
            "evidence_refs": list(evidence_refs or []),
        }
    )


def request_external(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    request_id: str,
    kind: str,
    payload_ref: str,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("external request requires RUNNING state")
    if next_run["pending_external"] is not None:
        raise BenchmarkContractError("an external request is already pending")
    if not request_id or not kind or not payload_ref:
        raise BenchmarkContractError("request_id, kind, and payload_ref are required")
    _append_invocation(
        next_run,
        invocation_id=invocation_id,
        executor=executor,
        context_packet=context_packet,
        outcome="WAITING_EXTERNAL",
        evidence_refs=[payload_ref],
    )
    next_run["pending_external"] = {
        "request_id": request_id,
        "kind": kind,
        "payload_ref": payload_ref,
    }
    next_run["status"] = "WAITING_EXTERNAL"
    next_run["owner"] = None
    next_run["events"].append(
        {
            "kind": "EXTERNAL_REQUEST",
            "request_id": request_id,
            "generation": expected_generation,
            "payload_ref": payload_ref,
        }
    )
    return next_run


def publish_external_result(
    run: Mapping[str, Any],
    *,
    request_id: str,
    result_ref: str,
    result_hash: str,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    if next_run["status"] != "WAITING_EXTERNAL":
        raise BenchmarkContractError("external result requires WAITING_EXTERNAL state")
    pending = next_run["pending_external"]
    if not pending or pending["request_id"] != request_id:
        raise BenchmarkContractError("external result does not match pending request")
    if not result_ref or len(result_hash) != 64:
        raise BenchmarkContractError("result_ref and sha256 result_hash are required")
    next_run["events"].append(
        {
            "kind": "EXTERNAL_RESULT",
            "request_id": request_id,
            "result_ref": result_ref,
            "result_hash": result_hash,
        }
    )
    next_run["pending_external"] = None
    next_run["status"] = "READY_TO_RESUME"
    next_run["metrics"]["deterministic_compute_operations"] += 1
    return next_run


def checkpoint_continue(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    evidence_refs: list[str] | None = None,
    retry: bool = False,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("checkpoint requires RUNNING state")
    _append_invocation(
        next_run,
        invocation_id=invocation_id,
        executor=executor,
        context_packet=context_packet,
        outcome="READY_TO_RESUME",
        evidence_refs=evidence_refs,
    )
    if retry:
        next_run["metrics"]["retries"] += 1
    next_run["owner"] = None
    next_run["status"] = "READY_TO_RESUME"
    return next_run


def decompose(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    children: list[Mapping[str, Any]],
    depth: int,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("decomposition requires RUNNING state")
    if not children or type(depth) is not int or depth < 1:
        raise BenchmarkContractError("non-empty children and positive depth are required")
    ids = [child.get("process_id") for child in children]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise BenchmarkContractError("child process ids must be unique and non-empty")
    _append_invocation(
        next_run,
        invocation_id=invocation_id,
        executor=executor,
        context_packet=context_packet,
        outcome="DECOMPOSED",
        evidence_refs=evidence_refs,
    )
    next_run["child_processes"].extend(deepcopy(children))
    next_run["metrics"]["decomposition_count"] += 1
    next_run["metrics"]["max_decomposition_depth"] = max(
        next_run["metrics"]["max_decomposition_depth"], depth
    )
    next_run["owner"] = None
    next_run["status"] = "DECOMPOSED"
    return next_run


def escalate(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    reason: str,
    lower_tier_evidence_refs: list[str],
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("escalation requires RUNNING state")
    if not reason.strip() or not lower_tier_evidence_refs:
        raise BenchmarkContractError(
            "frontier escalation requires an explicit reason and lower-tier evidence"
        )
    _append_invocation(
        next_run,
        invocation_id=invocation_id,
        executor=executor,
        context_packet=context_packet,
        outcome="ESCALATION_REQUIRED",
        evidence_refs=lower_tier_evidence_refs,
    )
    next_run["escalations"].append(
        {
            "generation": expected_generation,
            "reason": reason,
            "lower_tier_evidence_refs": list(lower_tier_evidence_refs),
        }
    )
    next_run["owner"] = None
    next_run["status"] = "ESCALATION_REQUIRED"
    return next_run


def record_validator_result(
    run: Mapping[str, Any],
    *,
    validator_id: str,
    passed: bool,
    score: float,
    evidence_ref: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    next_run = deepcopy(run)
    if not validator_id or type(passed) is not bool or not evidence_ref:
        raise BenchmarkContractError("validator_id, exact bool passed, and evidence_ref are required")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise BenchmarkContractError("validator score must be numeric")
    if not 0 <= float(score) <= 1:
        raise BenchmarkContractError("validator score must be in [0, 1]")
    next_run["validator_results"].append(
        {
            "validator_id": validator_id,
            "passed": passed,
            "score": float(score),
            "evidence_ref": evidence_ref,
            "details": dict(details or {}),
        }
    )
    next_run["metrics"]["deterministic_compute_operations"] += 1
    return next_run


def finish_run(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    invocation_id: str,
    executor: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    submission: Mapping[str, Any],
    evidence_refs: list[str],
) -> dict[str, Any]:
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("finish requires RUNNING state")
    if not next_run["validator_results"] or not next_run["validator_results"][-1]["passed"]:
        raise BenchmarkContractError("terminal completion requires a passing objective validator")
    if not isinstance(submission, Mapping) or not submission:
        raise BenchmarkContractError("terminal submission is required")
    _append_invocation(
        next_run,
        invocation_id=invocation_id,
        executor=executor,
        context_packet=context_packet,
        outcome="COMPLETED",
        evidence_refs=evidence_refs,
    )
    next_run["terminal_submission"] = deepcopy(dict(submission))
    next_run["owner"] = None
    next_run["status"] = "COMPLETED"
    return next_run


def oracle_result(
    public_fixture: Mapping[str, Any],
    oracle: Mapping[str, Any],
    *,
    experiment_id: str,
) -> dict[str, Any]:
    catalog = {item["id"] for item in public_fixture["experiment_catalog"]}
    if experiment_id not in catalog:
        raise BenchmarkContractError("experiment is not in the public catalog")
    results = oracle.get("experiment_results", {})
    if experiment_id not in results:
        raise BenchmarkContractError("oracle has no result for experiment")
    payload = deepcopy(results[experiment_id])
    return {
        "experiment_id": experiment_id,
        "result": payload,
        "result_hash": content_hash(payload),
    }


def evaluate_research_iterate(
    public_fixture: Mapping[str, Any],
    oracle: Mapping[str, Any],
    submission: Mapping[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []
    expected = oracle["terminal_criteria"]["expected_hypothesis"]
    chosen = submission.get("final_hypothesis")
    if chosen != expected:
        violations.append("wrong_final_hypothesis")

    observed = submission.get("observed_results", {})
    if not isinstance(observed, Mapping):
        violations.append("observed_results_not_mapping")
        observed = {}

    min_experiments = int(oracle["terminal_criteria"]["minimum_unique_experiments"])
    if len(observed) < min_experiments:
        violations.append("insufficient_experiment_cycles")

    for experiment_id, claimed_hash in observed.items():
        if experiment_id not in oracle["experiment_results"]:
            violations.append(f"unknown_experiment:{experiment_id}")
            continue
        actual_hash = content_hash(oracle["experiment_results"][experiment_id])
        if claimed_hash != actual_hash:
            violations.append(f"fabricated_or_mismatched_result:{experiment_id}")

    for group in oracle["terminal_criteria"]["required_experiment_groups"]:
        if not any(experiment_id in observed for experiment_id in group):
            violations.append("missing_required_discriminating_experiment:" + "|".join(group))

    rejected = submission.get("rejected_hypotheses", [])
    if not isinstance(rejected, list):
        violations.append("rejected_hypotheses_not_list")
        rejected = []
    required_rejected = oracle["terminal_criteria"]["required_rejected_hypotheses"]
    for hypothesis in required_rejected:
        if hypothesis not in rejected:
            violations.append(f"missing_rejected_hypothesis:{hypothesis}")

    addressed = set(submission.get("addressed_observations", []))
    for observation_id in oracle["terminal_criteria"]["required_addressed_observations"]:
        if observation_id not in addressed:
            violations.append(f"misleading_observation_not_addressed:{observation_id}")

    checks = 5
    score = max(0.0, 1.0 - min(len(violations), checks) / checks)
    return {
        "validator_id": "research_iterate_objective_v1",
        "passed": not violations,
        "score": score,
        "violations": violations,
        "expected_hypothesis_commitment": content_hash(
            {"fixture_id": public_fixture["fixture_id"], "expected": expected}
        ),
    }


def metrics_snapshot(run: Mapping[str, Any]) -> dict[str, Any]:
    invocations = run["invocations"]
    frontier_invocations = sum(
        1
        for item in invocations
        if item["executor"].get("tier") == "FRONTIER"
    )
    return {
        "status": run["status"],
        "execution_work_quanta": len(invocations),
        "total_context_bytes": sum(item["context_bytes"] for item in invocations),
        "retries": run["metrics"]["retries"],
        "decomposition_count": run["metrics"]["decomposition_count"],
        "decomposition_depth": run["metrics"]["max_decomposition_depth"],
        "failed_leaves": run["metrics"]["failed_leaves"],
        "recoveries": run["metrics"]["recovery_count"],
        "recovery_effectiveness": (
            run["metrics"]["successful_recoveries"] / run["metrics"]["recovery_count"]
            if run["metrics"]["recovery_count"]
            else None
        ),
        "frontier_invocations": frontier_invocations,
        "frontier_escalations": len(run["escalations"]),
        "elapsed_workflow_steps": len(run["events"]) + len(invocations),
        "deterministic_compute_operations": run["metrics"]["deterministic_compute_operations"],
        "durable_state_correct": not bool(run["pending_external"]) if run["status"] == "COMPLETED" else True,
        "provenance_correct": run["metrics"]["authority_provenance_violations"] == 0,
    }


def hard_gate_violations(run: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    metrics = run["metrics"]
    if metrics["authority_provenance_violations"]:
        violations.append("authority_or_provenance_violation")
    if metrics["manual_state_relay_count"]:
        violations.append("manual_state_relay")
    if metrics["model_poll_invocations"]:
        violations.append("model_polled_external_wait")
    if run["status"] == "COMPLETED":
        if run["pending_external"] is not None:
            violations.append("completed_with_pending_external_wait")
        if not run["validator_results"] or not run["validator_results"][-1]["passed"]:
            violations.append("completed_without_passing_validator")
    for escalation_item in run["escalations"]:
        if not escalation_item["reason"] or not escalation_item["lower_tier_evidence_refs"]:
            violations.append("unjustified_frontier_escalation")
    return violations


def persist_semantic_state(
    run: Mapping[str, Any],
    *,
    expected_generation: int,
    established_findings: list[Mapping[str, Any]] | None = None,
    open_hypotheses: list[Mapping[str, Any]] | None = None,
    unresolved_questions: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    candidate_actions: list[Mapping[str, Any]] | None = None,
    next_safe_action: str | None = None,
    authority_refs: list[str] | None = None,
    validation_requirements: list[str] | None = None,
) -> dict[str, Any]:
    """Persist bounded semantic continuation state without creating authority."""
    next_run = deepcopy(run)
    _require_generation(next_run, expected_generation)
    if next_run["status"] != "RUNNING":
        raise BenchmarkContractError("semantic checkpoint requires RUNNING state")
    fields = {
        "established_findings": established_findings,
        "open_hypotheses": open_hypotheses,
        "unresolved_questions": unresolved_questions,
        "evidence_refs": evidence_refs,
        "candidate_actions": candidate_actions,
        "authority_refs": authority_refs,
        "validation_requirements": validation_requirements,
    }
    for key, value in fields.items():
        if value is not None:
            if not isinstance(value, list):
                raise BenchmarkContractError(f"{key} must be a list")
            next_run[key] = deepcopy(value)
    if next_safe_action is not None:
        if not isinstance(next_safe_action, str) or not next_safe_action.strip():
            raise BenchmarkContractError("next_safe_action must be non-empty when supplied")
        next_run["next_safe_action"] = next_safe_action
    next_run["events"].append(
        {
            "kind": "SEMANTIC_CHECKPOINT",
            "generation": expected_generation,
            "evidence_ref_count": len(next_run["evidence_refs"]),
        }
    )
    return next_run


def context_packet_from_run(
    run: Mapping[str, Any],
    *,
    objective: str,
    invariants: list[str],
) -> dict[str, Any]:
    """Serialize only the bounded durable continuation state required by a worker."""
    if not isinstance(objective, str) or not objective.strip():
        raise BenchmarkContractError("objective is required")
    if not isinstance(invariants, list):
        raise BenchmarkContractError("invariants must be a list")
    packet = {
        "process_id": run["process_id"],
        "generation": run["generation"],
        "status": run["status"],
        "objective": objective,
        "established_findings": deepcopy(run.get("established_findings", [])),
        "open_hypotheses": deepcopy(run.get("open_hypotheses", [])),
        "unresolved_questions": deepcopy(run.get("unresolved_questions", [])),
        "evidence_refs": list(run.get("evidence_refs", [])),
        "candidate_actions": deepcopy(run.get("candidate_actions", [])),
        "next_safe_action": run.get("next_safe_action"),
        "authority_refs": list(run.get("authority_refs", [])),
        "validation_requirements": list(run.get("validation_requirements", [])),
        "invariants": list(invariants),
    }
    context_packet_size_bytes(packet)
    return packet
