"""Executable reference model for the Workspace Semantic Execution kernel.

NON-PRODUCTION. This module is an executable specification used to freeze
state-machine semantics before the production backend is authorized.

It intentionally uses only the Python standard library.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable


class KernelContractError(RuntimeError):
    """Raised when a transition or invariant fails closed."""


TERMINAL_STATES = {"COMPLETED", "FAILED", "AUTHORITY_BLOCKED"}
WAIT_STATES = {"WAITING_EXTERNAL", "WAITING_DEPENDENCIES"}
CLAIMABLE_STATES = {"READY", "READY_TO_RESUME"}


def new_process(process_id: str, *, dependencies: Iterable[str] = ()) -> dict[str, Any]:
    if not process_id:
        raise KernelContractError("process_id_required")
    deps = list(dict.fromkeys(dependencies))
    if process_id in deps:
        raise KernelContractError("self_dependency")
    return {
        "process_id": process_id,
        "state": "READY",
        "generation": 0,
        "worker_id": None,
        "lease_id": None,
        "dependencies": deps,
        "children": [],
        "wait_key": None,
        "effect_receipts": {},
        "validations": [],
        "reasoning_quanta": 0,
        "history": [],
        "repair_required": False,
    }


def new_graph(processes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    graph = {"event_seq": 0, "processes": {}}
    for raw in processes:
        process = deepcopy(raw)
        pid = process["process_id"]
        if pid in graph["processes"]:
            raise KernelContractError(f"duplicate_process:{pid}")
        graph["processes"][pid] = process
    validate_graph(graph)
    return graph


def _copy_graph(graph: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(graph)


def _process(graph: dict[str, Any], process_id: str) -> dict[str, Any]:
    try:
        return graph["processes"][process_id]
    except KeyError as exc:
        raise KernelContractError(f"unknown_process:{process_id}") from exc


def _append_event(
    graph: dict[str, Any],
    process: dict[str, Any],
    event: str,
    **details: Any,
) -> None:
    graph["event_seq"] += 1
    process["history"].append(
        {
            "seq": graph["event_seq"],
            "event": event,
            "state": process["state"],
            "generation": process["generation"],
            "details": deepcopy(details),
        }
    )


def _guard_generation(process: dict[str, Any], expected_generation: int) -> None:
    if expected_generation != process["generation"]:
        raise KernelContractError(
            f"stale_generation:expected={expected_generation}:current={process['generation']}"
        )


def _guard_lease(process: dict[str, Any], lease_id: str) -> None:
    if not lease_id or process["lease_id"] != lease_id:
        raise KernelContractError("lease_mismatch")


def _dependencies_satisfied(graph: dict[str, Any], process: dict[str, Any]) -> bool:
    for dependency_id in process["dependencies"]:
        dependency = _process(graph, dependency_id)
        if dependency["state"] != "COMPLETED":
            return False
    return True


def claim(
    graph: dict[str, Any],
    process_id: str,
    *,
    worker_id: str,
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    if process["state"] not in CLAIMABLE_STATES:
        raise KernelContractError(f"claim_invalid_state:{process['state']}")
    if process["lease_id"] is not None or process["worker_id"] is not None:
        raise KernelContractError("existing_lease")
    if not worker_id or not lease_id:
        raise KernelContractError("worker_and_lease_required")
    if not _dependencies_satisfied(next_graph, process):
        raise KernelContractError("dependencies_unsatisfied")
    process["worker_id"] = worker_id
    process["lease_id"] = lease_id
    process["state"] = "CLAIMED"
    _append_event(next_graph, process, "CLAIM", worker_id=worker_id, lease_id=lease_id)
    validate_graph(next_graph)
    return next_graph


def start(
    graph: dict[str, Any],
    process_id: str,
    *,
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    _guard_lease(process, lease_id)
    if process["state"] != "CLAIMED":
        raise KernelContractError(f"start_invalid_state:{process['state']}")
    process["state"] = "RUNNING"
    _append_event(next_graph, process, "START")
    validate_graph(next_graph)
    return next_graph


def record_reasoning_quantum(
    graph: dict[str, Any],
    process_id: str,
    *,
    expected_generation: int,
    lease_id: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    _guard_lease(process, lease_id)
    if process["state"] != "RUNNING":
        raise KernelContractError(f"reasoning_invalid_state:{process['state']}")
    process["reasoning_quanta"] += 1
    _append_event(next_graph, process, "REASONING_QUANTUM")
    validate_graph(next_graph)
    return next_graph


def wait_external(
    graph: dict[str, Any],
    process_id: str,
    *,
    wait_key: str,
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    _guard_lease(process, lease_id)
    if process["state"] != "RUNNING":
        raise KernelContractError(f"wait_invalid_state:{process['state']}")
    if not wait_key:
        raise KernelContractError("wait_key_required")
    process["state"] = "WAITING_EXTERNAL"
    process["wait_key"] = wait_key
    process["worker_id"] = None
    process["lease_id"] = None
    _append_event(next_graph, process, "WAIT_EXTERNAL", wait_key=wait_key)
    validate_graph(next_graph)
    return next_graph


def wake_external(
    graph: dict[str, Any],
    process_id: str,
    *,
    wait_key: str,
    event_id: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    if process["state"] != "WAITING_EXTERNAL":
        raise KernelContractError(f"wake_invalid_state:{process['state']}")
    if not event_id:
        raise KernelContractError("event_id_required")
    if process["wait_key"] != wait_key:
        raise KernelContractError("wait_key_mismatch")
    process["state"] = "READY_TO_RESUME"
    process["wait_key"] = None
    _append_event(next_graph, process, "WAKE_EXTERNAL", event_id=event_id)
    validate_graph(next_graph)
    return next_graph


def decompose(
    graph: dict[str, Any],
    process_id: str,
    *,
    children: Iterable[dict[str, Any]],
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    parent = _process(next_graph, process_id)
    _guard_generation(parent, expected_generation)
    _guard_lease(parent, lease_id)
    if parent["state"] != "RUNNING":
        raise KernelContractError(f"decompose_invalid_state:{parent['state']}")

    child_specs = list(children)
    if not child_specs:
        raise KernelContractError("children_required")

    child_ids: list[str] = []
    for spec in child_specs:
        child_id = str(spec.get("process_id", ""))
        if not child_id:
            raise KernelContractError("child_process_id_required")
        if child_id == process_id:
            raise KernelContractError("self_child")
        if child_id in next_graph["processes"]:
            raise KernelContractError(f"duplicate_child:{child_id}")
        child = new_process(
            child_id,
            dependencies=spec.get("dependencies", ()),
        )
        child["parent_process_id"] = process_id
        next_graph["processes"][child_id] = child
        child_ids.append(child_id)

    parent["children"] = child_ids
    parent["state"] = "WAITING_DEPENDENCIES"
    parent["worker_id"] = None
    parent["lease_id"] = None
    _append_event(next_graph, parent, "DECOMPOSE", children=child_ids)
    validate_graph(next_graph)
    return next_graph


def refresh_dependency_waits(
    graph: dict[str, Any],
    *,
    event_id: str,
) -> dict[str, Any]:
    if not event_id:
        raise KernelContractError("event_id_required")
    next_graph = _copy_graph(graph)
    changed = False
    for process in next_graph["processes"].values():
        if process["state"] != "WAITING_DEPENDENCIES":
            continue
        if not process["children"]:
            raise KernelContractError("dependency_wait_without_children")
        if all(
            _process(next_graph, child_id)["state"] == "COMPLETED"
            for child_id in process["children"]
        ):
            process["state"] = "READY_TO_RESUME"
            _append_event(
                next_graph,
                process,
                "DEPENDENCIES_SATISFIED",
                event_id=event_id,
                children=list(process["children"]),
            )
            changed = True
    if not changed:
        _append_graph_event(next_graph, "DEPENDENCY_REFRESH_NOOP", event_id=event_id)
    validate_graph(next_graph)
    return next_graph


def _append_graph_event(graph: dict[str, Any], event: str, **details: Any) -> None:
    graph["event_seq"] += 1
    graph.setdefault("graph_history", []).append(
        {"seq": graph["event_seq"], "event": event, "details": deepcopy(details)}
    )


def record_effect(
    graph: dict[str, Any],
    process_id: str,
    *,
    action_id: str,
    idempotency_key: str,
    target_ref: str,
    effect_hash: str,
    executor_id: str,
    observed_at: str,
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    _guard_lease(process, lease_id)
    if process["state"] != "RUNNING":
        raise KernelContractError(f"effect_invalid_state:{process['state']}")
    required = {
        "action_id": action_id,
        "idempotency_key": idempotency_key,
        "target_ref": target_ref,
        "effect_hash": effect_hash,
        "executor_id": executor_id,
        "observed_at": observed_at,
    }
    if not all(required.values()):
        raise KernelContractError("effect_receipt_fields_required")
    receipt = {
        **required,
        "generation": process["generation"],
    }
    existing = process["effect_receipts"].get(idempotency_key)
    if existing is not None:
        if existing != receipt:
            raise KernelContractError("conflicting_duplicate_effect")
        _append_event(
            next_graph,
            process,
            "RECORD_EFFECT_DUPLICATE_NOOP",
            idempotency_key=idempotency_key,
        )
        validate_graph(next_graph)
        return next_graph
    process["effect_receipts"][idempotency_key] = receipt
    _append_event(next_graph, process, "RECORD_EFFECT", idempotency_key=idempotency_key)
    validate_graph(next_graph)
    return next_graph


def propose_terminal(
    graph: dict[str, Any],
    process_id: str,
    *,
    lease_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    _guard_lease(process, lease_id)
    if process["state"] != "RUNNING":
        raise KernelContractError(f"terminal_invalid_state:{process['state']}")
    if not process["effect_receipts"]:
        raise KernelContractError("terminal_requires_effect_receipt")
    process["state"] = "TERMINAL_CANDIDATE"
    process["worker_id"] = None
    process["lease_id"] = None
    _append_event(next_graph, process, "PROPOSE_TERMINAL")
    validate_graph(next_graph)
    return next_graph


def begin_validation(
    graph: dict[str, Any],
    process_id: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    if process["state"] != "TERMINAL_CANDIDATE":
        raise KernelContractError(f"validation_invalid_state:{process['state']}")
    if not process["effect_receipts"]:
        raise KernelContractError("validation_requires_receipt")
    process["state"] = "VALIDATING"
    _append_event(next_graph, process, "BEGIN_VALIDATION")
    validate_graph(next_graph)
    return next_graph


def record_validation(
    graph: dict[str, Any],
    process_id: str,
    *,
    validator_id: str,
    passed: bool,
    evidence_ref: str,
    observed_at: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    if process["state"] != "VALIDATING":
        raise KernelContractError(f"validation_result_invalid_state:{process['state']}")
    if not validator_id or not evidence_ref or not observed_at:
        raise KernelContractError("validation_fields_required")
    result = {
        "validator_id": validator_id,
        "passed": bool(passed),
        "evidence_ref": evidence_ref,
        "observed_at": observed_at,
    }
    process["validations"].append(result)
    if passed:
        if not process["effect_receipts"]:
            raise KernelContractError("complete_requires_receipt")
        process["state"] = "COMPLETED"
        process["repair_required"] = False
        _append_event(next_graph, process, "VALIDATION_PASS", evidence_ref=evidence_ref)
    else:
        process["state"] = "READY_TO_RESUME"
        process["repair_required"] = True
        _append_event(next_graph, process, "VALIDATION_FAIL", evidence_ref=evidence_ref)
    validate_graph(next_graph)
    return next_graph


def recover(
    graph: dict[str, Any],
    process_id: str,
    *,
    expected_generation: int,
    reason: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    _guard_generation(process, expected_generation)
    if process["state"] in TERMINAL_STATES:
        raise KernelContractError(f"recover_terminal_state:{process['state']}")
    if not reason:
        raise KernelContractError("recovery_reason_required")
    process["generation"] += 1
    process["state"] = "READY_TO_RESUME"
    process["worker_id"] = None
    process["lease_id"] = None
    process["wait_key"] = None
    _append_event(next_graph, process, "RECOVER", reason=reason)
    validate_graph(next_graph)
    return next_graph


def authority_block(
    graph: dict[str, Any],
    process_id: str,
    *,
    reason: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    if process["state"] not in {"READY", "CLAIMED", "RUNNING", "READY_TO_RESUME"}:
        raise KernelContractError(f"authority_block_invalid_state:{process['state']}")
    if not reason:
        raise KernelContractError("authority_reason_required")
    process["state"] = "AUTHORITY_BLOCKED"
    process["worker_id"] = None
    process["lease_id"] = None
    _append_event(next_graph, process, "AUTHORITY_BLOCK", reason=reason)
    validate_graph(next_graph)
    return next_graph


def fail(
    graph: dict[str, Any],
    process_id: str,
    *,
    reason: str,
) -> dict[str, Any]:
    next_graph = _copy_graph(graph)
    process = _process(next_graph, process_id)
    if process["state"] in TERMINAL_STATES:
        raise KernelContractError(f"fail_terminal_state:{process['state']}")
    if not reason:
        raise KernelContractError("failure_reason_required")
    process["state"] = "FAILED"
    process["worker_id"] = None
    process["lease_id"] = None
    process["wait_key"] = None
    _append_event(next_graph, process, "FAIL", reason=reason)
    validate_graph(next_graph)
    return next_graph


def candidate_action(
    *,
    action_id: str,
    process_id: str,
    target_ref: str,
    executor_type: str,
    idempotency_key: str,
    preconditions: Iterable[str],
    expected_effect: str,
    postcondition_validator: str,
) -> dict[str, Any]:
    required = [
        action_id,
        process_id,
        target_ref,
        executor_type,
        idempotency_key,
        expected_effect,
        postcondition_validator,
    ]
    if not all(required):
        raise KernelContractError("candidate_action_fields_required")
    return {
        "action_id": action_id,
        "process_id": process_id,
        "target_ref": target_ref,
        "executor_type": executor_type,
        "idempotency_key": idempotency_key,
        "preconditions": list(preconditions),
        "expected_effect": expected_effect,
        "postcondition_validator": postcondition_validator,
        "authorization_state": "UNDECIDED",
    }


def compile_action_spec(
    candidate: dict[str, Any],
    *,
    authority_decision: dict[str, Any],
) -> dict[str, Any]:
    if candidate.get("authorization_state") != "UNDECIDED":
        raise KernelContractError("candidate_claimed_authority")
    if authority_decision.get("outcome") != "ALLOW":
        raise KernelContractError("authority_not_allow")
    decision_id = authority_decision.get("decision_id")
    scope_ref = authority_decision.get("authority_scope_ref")
    if not decision_id or not scope_ref:
        raise KernelContractError("authority_binding_required")
    if authority_decision.get("action_id") != candidate.get("action_id"):
        raise KernelContractError("authority_action_mismatch")
    if authority_decision.get("target_ref") != candidate.get("target_ref"):
        raise KernelContractError("authority_target_mismatch")
    return {
        "action_id": candidate["action_id"],
        "process_id": candidate["process_id"],
        "target_ref": candidate["target_ref"],
        "executor_type": candidate["executor_type"],
        "authority_decision_id": decision_id,
        "authority_scope_ref": scope_ref,
        "idempotency_key": candidate["idempotency_key"],
        "preconditions": list(candidate["preconditions"]),
        "expected_effect": candidate["expected_effect"],
        "postcondition_validator": candidate["postcondition_validator"],
    }


def apply_event(
    graph: dict[str, Any],
    process_id: str,
    event: str,
    **kwargs: Any,
) -> dict[str, Any]:
    handlers = {
        "CLAIM": claim,
        "START": start,
        "REASONING_QUANTUM": record_reasoning_quantum,
        "WAIT_EXTERNAL": wait_external,
        "WAKE_EXTERNAL": wake_external,
        "DECOMPOSE": decompose,
        "RECORD_EFFECT": record_effect,
        "PROPOSE_TERMINAL": propose_terminal,
        "BEGIN_VALIDATION": begin_validation,
        "VALIDATION_RESULT": record_validation,
        "RECOVER": recover,
        "AUTHORITY_BLOCK": authority_block,
        "FAIL": fail,
    }
    handler = handlers.get(event)
    if handler is None:
        raise KernelContractError(f"unknown_event:{event}")
    return handler(graph, process_id, **kwargs)


def validate_graph(graph: dict[str, Any]) -> None:
    if set(graph) - {"event_seq", "processes", "graph_history"}:
        raise KernelContractError("unknown_graph_fields")
    if not isinstance(graph.get("event_seq"), int) or graph["event_seq"] < 0:
        raise KernelContractError("invalid_event_seq")
    processes = graph.get("processes")
    if not isinstance(processes, dict):
        raise KernelContractError("processes_required")

    for process_id, process in processes.items():
        if process.get("process_id") != process_id:
            raise KernelContractError("process_identity_mismatch")
        state = process.get("state")
        if state not in {
            "READY",
            "CLAIMED",
            "RUNNING",
            "WAITING_EXTERNAL",
            "WAITING_DEPENDENCIES",
            "READY_TO_RESUME",
            "TERMINAL_CANDIDATE",
            "VALIDATING",
            "COMPLETED",
            "FAILED",
            "AUTHORITY_BLOCKED",
        }:
            raise KernelContractError(f"unknown_state:{state}")

        worker = process.get("worker_id")
        lease = process.get("lease_id")
        if (worker is None) != (lease is None):
            raise KernelContractError("partial_lease_binding")

        if state in WAIT_STATES | {"TERMINAL_CANDIDATE", "VALIDATING"}:
            if worker is not None or lease is not None:
                raise KernelContractError("lease_present_in_nonleased_state")

        if state in {"CLAIMED", "RUNNING"}:
            if worker is None or lease is None:
                raise KernelContractError("lease_missing_in_active_state")

        if state == "WAITING_EXTERNAL" and not process.get("wait_key"):
            raise KernelContractError("external_wait_missing_key")
        if state != "WAITING_EXTERNAL" and process.get("wait_key") is not None:
            raise KernelContractError("wait_key_outside_external_wait")

        if state == "WAITING_DEPENDENCIES" and not process.get("children"):
            raise KernelContractError("dependency_wait_missing_children")

        if state == "COMPLETED":
            if not process.get("effect_receipts"):
                raise KernelContractError("completed_without_effect_receipt")
            validations = process.get("validations", [])
            if not validations or not validations[-1].get("passed"):
                raise KernelContractError("completed_without_passing_validation")
            if not validations[-1].get("evidence_ref"):
                raise KernelContractError("completed_without_validation_evidence")

        for dependency_id in process.get("dependencies", []):
            if dependency_id not in processes:
                raise KernelContractError(f"unknown_dependency:{dependency_id}")
            if dependency_id == process_id:
                raise KernelContractError("self_dependency")

        for child_id in process.get("children", []):
            if child_id not in processes:
                raise KernelContractError(f"unknown_child:{child_id}")
            if child_id == process_id:
                raise KernelContractError("self_child")

        receipts = process.get("effect_receipts", {})
        if len(receipts) != len(set(receipts)):
            raise KernelContractError("duplicate_idempotency_key")

        if process.get("generation", -1) < 0:
            raise KernelContractError("invalid_generation")

        if state in TERMINAL_STATES and (worker is not None or lease is not None):
            raise KernelContractError("terminal_state_has_lease")


def snapshot(graph: dict[str, Any]) -> dict[str, Any]:
    """Return a detached deterministic copy for assertions/serialization."""
    validate_graph(graph)
    return deepcopy(graph)
