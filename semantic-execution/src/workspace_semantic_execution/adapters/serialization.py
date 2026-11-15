"""Deterministic JSON codec for durable WorkGraph state.

This codec is infrastructure-neutral and intentionally avoids pickle or
runtime-specific object serialization. Schema v4 adds durable OperatorAction lifecycle state while retaining v1-v3 decode compatibility.
"""
from __future__ import annotations

import json
from typing import Any

from ..domain import (
    DomainKernel,
    EffectReceipt,
    ExecutorSession,
    ExecutorSessionState,
    OperatorAckMode,
    OperatorAction,
    OperatorActionClaim,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    ProcessState,
    ReasoningProcess,
    TransitionRecord,
    ValidationResult,
    WorkContract,
    WorkDisposition,
    WorkGraph,
)


SCHEMA_VERSION = 4
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3, 4}


class GraphCodecError(ValueError):
    """Raised when durable graph data is malformed or unsupported."""


def _encode_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return {"$tuple": [_encode_value(item) for item in value]}
    if isinstance(value, list):
        return [_encode_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise GraphCodecError("durable_dict_keys_must_be_strings")
        return {
            key: _encode_value(value[key])
            for key in sorted(value)
        }
    raise GraphCodecError(f"unsupported_durable_value:{type(value).__name__}")


def _decode_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_decode_value(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {"$tuple"}:
            raw = value["$tuple"]
            if not isinstance(raw, list):
                raise GraphCodecError("invalid_tuple_encoding")
            return tuple(_decode_value(item) for item in raw)
        return {
            str(key): _decode_value(item)
            for key, item in value.items()
        }
    raise GraphCodecError("invalid_durable_value")


def _encode_work_contract(
    contract: WorkContract | None,
) -> dict[str, Any] | None:
    if contract is None:
        return None
    return {
        "objective": contract.objective,
        "mandatory_constraints": list(contract.mandatory_constraints),
        "provenance_refs": list(contract.provenance_refs),
        "authority_refs": list(contract.authority_refs),
        "validator_contracts": list(contract.validator_contracts),
        "output_schema_refs": list(contract.output_schema_refs),
    }


def _decode_string_tuple(raw: object, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise GraphCodecError(f"{field_name}_must_be_list")
    if any(not isinstance(value, str) for value in raw):
        raise GraphCodecError(f"{field_name}_must_contain_strings")
    return tuple(raw)


def _decode_work_contract(raw: object) -> WorkContract | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise GraphCodecError("work_contract_must_be_object")
    objective = raw.get("objective")
    if not isinstance(objective, str):
        raise GraphCodecError("work_contract_objective_must_be_string")
    return WorkContract(
        objective=objective,
        mandatory_constraints=_decode_string_tuple(
            raw.get("mandatory_constraints"),
            "mandatory_constraints",
        ),
        provenance_refs=_decode_string_tuple(
            raw.get("provenance_refs"),
            "provenance_refs",
        ),
        authority_refs=_decode_string_tuple(
            raw.get("authority_refs"),
            "authority_refs",
        ),
        validator_contracts=_decode_string_tuple(
            raw.get("validator_contracts"),
            "validator_contracts",
        ),
        output_schema_refs=_decode_string_tuple(
            raw.get("output_schema_refs"),
            "output_schema_refs",
        ),
    )


def _encode_executor_session(session: ExecutorSession) -> dict[str, Any]:
    return {
        "slot_id": session.slot_id,
        "executor_id": session.executor_id,
        "session_generation": session.session_generation,
        "session_id": session.session_id,
        "state": session.state.value,
        "bound_process_id": session.bound_process_id,
        "bound_process_generation": session.bound_process_generation,
        "bound_packet_sha256": session.bound_packet_sha256,
        "last_ack_id": session.last_ack_id,
        "last_ack_process_id": session.last_ack_process_id,
        "last_ack_process_generation": session.last_ack_process_generation,
        "retirement_reason": session.retirement_reason,
    }


def _encode_operator_action(action: OperatorAction) -> dict[str, Any]:
    claim = None
    if action.claim is not None:
        claim = {
            "claim_id": action.claim.claim_id,
            "helper_instance_id": action.claim.helper_instance_id,
            "claimed_at": action.claim.claimed_at,
            "expires_at": action.claim.expires_at,
        }
    return {
        "action_id": action.action_id,
        "generation": action.generation,
        "action_type": action.action_type.value,
        "status": action.status.value,
        "priority_rank": action.priority_rank,
        "queue_sequence": action.queue_sequence,
        "created_at": action.created_at,
        "task_id": action.task_id,
        "reasoning_process_id": action.reasoning_process_id,
        "process_generation": action.process_generation,
        "worker_slot_id": action.worker_slot_id,
        "session_generation": action.session_generation,
        "executor_id": action.executor_id,
        "payload_ref": action.payload_ref,
        "payload_sha256": action.payload_sha256,
        "human_requirement": action.human_requirement.value,
        "ack_mode": action.ack_mode.value,
        "post_local_success": action.post_local_success.value,
        "not_before": action.not_before,
        "stale_after": action.stale_after,
        "supersedes_action_id": action.supersedes_action_id,
        "superseded_by_action_id": action.superseded_by_action_id,
        "claim": claim,
        "local_prepared_at": action.local_prepared_at,
        "durable_ack_id": action.durable_ack_id,
        "failure_code": action.failure_code,
        "failure_message": action.failure_message,
        "completed_at": action.completed_at,
    }


def encode_work_graph(graph: WorkGraph) -> dict[str, Any]:
    DomainKernel.validate(graph)
    processes: list[dict[str, Any]] = []
    for process in sorted(
        graph.processes.values(),
        key=lambda item: item.process_id,
    ):
        processes.append(
            {
                "process_id": process.process_id,
                "state": process.state.value,
                "generation": process.generation,
                "worker_id": process.worker_id,
                "lease_id": process.lease_id,
                "dependencies": list(process.dependencies),
                "children": list(process.children),
                "wait_key": process.wait_key,
                "effect_receipts": [
                    {
                        "idempotency_key": key,
                        "receipt": {
                            "action_id": receipt.action_id,
                            "idempotency_key": receipt.idempotency_key,
                            "target_ref": receipt.target_ref,
                            "effect_hash": receipt.effect_hash,
                            "executor_id": receipt.executor_id,
                            "generation": receipt.generation,
                            "observed_at": receipt.observed_at,
                        },
                    }
                    for key, receipt in sorted(
                        process.effect_receipts.items()
                    )
                ],
                "validations": [
                    {
                        "validator_id": result.validator_id,
                        "passed": result.passed,
                        "evidence_ref": result.evidence_ref,
                        "observed_at": result.observed_at,
                    }
                    for result in process.validations
                ],
                "reasoning_quanta": process.reasoning_quanta,
                "repair_required": process.repair_required,
                "history": [
                    {
                        "seq": record.seq,
                        "event": record.event,
                        "state": record.state.value,
                        "generation": record.generation,
                        "details": _encode_value(record.details),
                    }
                    for record in process.history
                ],
                "parent_process_id": process.parent_process_id,
                "work_contract": _encode_work_contract(
                    process.work_contract
                ),
                "disposition": process.disposition.value,
                "disposition_reason": process.disposition_reason,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "event_seq": graph.event_seq,
        "graph_history": _encode_value(graph.graph_history),
        "processes": processes,
        "executor_sessions": [
            _encode_executor_session(session)
            for session in sorted(
                graph.executor_sessions.values(),
                key=lambda item: item.slot_id,
            )
        ],
        "operator_actions": [
            _encode_operator_action(action)
            for action in sorted(
                graph.operator_actions.values(),
                key=lambda item: item.action_id,
            )
        ],
    }


def decode_work_graph(payload: dict[str, Any]) -> WorkGraph:
    if not isinstance(payload, dict):
        raise GraphCodecError("graph_payload_must_be_object")
    schema_version = payload.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise GraphCodecError("unsupported_graph_schema_version")
    raw_processes = payload.get("processes")
    if not isinstance(raw_processes, list):
        raise GraphCodecError("processes_must_be_list")

    processes: dict[str, ReasoningProcess] = {}
    for raw in raw_processes:
        if not isinstance(raw, dict):
            raise GraphCodecError("process_must_be_object")
        process_id = raw.get("process_id")
        if not isinstance(process_id, str) or not process_id:
            raise GraphCodecError("process_id_required")
        if process_id in processes:
            raise GraphCodecError(f"duplicate_process:{process_id}")

        receipts: dict[str, EffectReceipt] = {}
        raw_receipts = raw.get("effect_receipts", [])
        if not isinstance(raw_receipts, list):
            raise GraphCodecError("effect_receipts_must_be_list")
        for item in raw_receipts:
            if not isinstance(item, dict) or not isinstance(
                item.get("receipt"),
                dict,
            ):
                raise GraphCodecError("invalid_effect_receipt_entry")
            key = item.get("idempotency_key")
            receipt = item["receipt"]
            if not isinstance(key, str) or not key:
                raise GraphCodecError("receipt_key_required")
            parsed = EffectReceipt(
                action_id=str(receipt["action_id"]),
                idempotency_key=str(receipt["idempotency_key"]),
                target_ref=str(receipt["target_ref"]),
                effect_hash=str(receipt["effect_hash"]),
                executor_id=str(receipt["executor_id"]),
                generation=int(receipt["generation"]),
                observed_at=str(receipt["observed_at"]),
            )
            if parsed.idempotency_key != key:
                raise GraphCodecError("receipt_key_mismatch")
            receipts[key] = parsed

        validations = [
            ValidationResult(
                validator_id=str(item["validator_id"]),
                passed=bool(item["passed"]),
                evidence_ref=str(item["evidence_ref"]),
                observed_at=str(item["observed_at"]),
            )
            for item in raw.get("validations", [])
        ]
        history = [
            TransitionRecord(
                seq=int(item["seq"]),
                event=str(item["event"]),
                state=ProcessState(str(item["state"])),
                generation=int(item["generation"]),
                details=_decode_value(item.get("details", {})),
            )
            for item in raw.get("history", [])
        ]
        try:
            state = ProcessState(str(raw["state"]))
        except (KeyError, ValueError) as exc:
            raise GraphCodecError("invalid_process_state") from exc

        if schema_version == 1:
            work_contract = None
            disposition = WorkDisposition.UNCLASSIFIED
            disposition_reason = None
        else:
            work_contract = _decode_work_contract(raw.get("work_contract"))
            try:
                disposition = WorkDisposition(
                    str(
                        raw.get(
                            "disposition",
                            WorkDisposition.UNCLASSIFIED.value,
                        )
                    )
                )
            except ValueError as exc:
                raise GraphCodecError(
                    "invalid_work_disposition"
                ) from exc
            disposition_reason = raw.get("disposition_reason")
            if disposition_reason is not None and not isinstance(
                disposition_reason,
                str,
            ):
                raise GraphCodecError(
                    "disposition_reason_must_be_string_or_null"
                )

        process = ReasoningProcess(
            process_id=process_id,
            state=state,
            generation=int(raw.get("generation", 0)),
            worker_id=raw.get("worker_id"),
            lease_id=raw.get("lease_id"),
            dependencies=tuple(str(x) for x in raw.get("dependencies", [])),
            children=tuple(str(x) for x in raw.get("children", [])),
            wait_key=raw.get("wait_key"),
            effect_receipts=receipts,
            validations=validations,
            reasoning_quanta=int(raw.get("reasoning_quanta", 0)),
            repair_required=bool(raw.get("repair_required", False)),
            history=history,
            parent_process_id=raw.get("parent_process_id"),
            work_contract=work_contract,
            disposition=disposition,
            disposition_reason=disposition_reason,
        )
        processes[process_id] = process

    executor_sessions: dict[str, ExecutorSession] = {}
    if schema_version >= 3:
        raw_sessions = payload.get("executor_sessions", [])
        if not isinstance(raw_sessions, list):
            raise GraphCodecError("executor_sessions_must_be_list")
        for raw in raw_sessions:
            if not isinstance(raw, dict):
                raise GraphCodecError("executor_session_must_be_object")
            slot_id = raw.get("slot_id")
            if not isinstance(slot_id, str) or not slot_id:
                raise GraphCodecError("session_slot_id_required")
            if slot_id in executor_sessions:
                raise GraphCodecError(f"duplicate_session_slot:{slot_id}")
            try:
                session_state = ExecutorSessionState(str(raw["state"]))
            except (KeyError, ValueError) as exc:
                raise GraphCodecError("invalid_executor_session_state") from exc
            executor_sessions[slot_id] = ExecutorSession(
                slot_id=slot_id,
                executor_id=str(raw.get("executor_id", "")),
                session_generation=int(raw.get("session_generation", 0)),
                session_id=raw.get("session_id"),
                state=session_state,
                bound_process_id=raw.get("bound_process_id"),
                bound_process_generation=(None if raw.get("bound_process_generation") is None else int(raw["bound_process_generation"])),
                bound_packet_sha256=raw.get("bound_packet_sha256"),
                last_ack_id=raw.get("last_ack_id"),
                last_ack_process_id=raw.get("last_ack_process_id"),
                last_ack_process_generation=(None if raw.get("last_ack_process_generation") is None else int(raw["last_ack_process_generation"])),
                retirement_reason=raw.get("retirement_reason"),
            )

    operator_actions: dict[str, OperatorAction] = {}
    if schema_version >= 4:
        raw_actions = payload.get("operator_actions", [])
        if not isinstance(raw_actions, list):
            raise GraphCodecError("operator_actions_must_be_list")
        for raw in raw_actions:
            if not isinstance(raw, dict):
                raise GraphCodecError("operator_action_must_be_object")
            action_id = raw.get("action_id")
            if not isinstance(action_id, str) or not action_id:
                raise GraphCodecError("operator_action_id_required")
            if action_id in operator_actions:
                raise GraphCodecError(f"duplicate_operator_action:{action_id}")
            raw_claim = raw.get("claim")
            claim = None
            if raw_claim is not None:
                if not isinstance(raw_claim, dict):
                    raise GraphCodecError("operator_action_claim_must_be_object")
                claim = OperatorActionClaim(
                    claim_id=str(raw_claim.get("claim_id", "")),
                    helper_instance_id=str(raw_claim.get("helper_instance_id", "")),
                    claimed_at=str(raw_claim.get("claimed_at", "")),
                    expires_at=str(raw_claim.get("expires_at", "")),
                )
            try:
                operator_actions[action_id] = OperatorAction(
                    action_id=action_id,
                    generation=int(raw.get("generation", 0)),
                    action_type=OperatorActionType(str(raw["action_type"])),
                    status=OperatorActionState(str(raw["status"])),
                    priority_rank=int(raw.get("priority_rank", 0)),
                    queue_sequence=int(raw.get("queue_sequence", 0)),
                    created_at=str(raw.get("created_at", "")),
                    task_id=str(raw.get("task_id", "")),
                    reasoning_process_id=raw.get("reasoning_process_id"),
                    process_generation=(
                        None if raw.get("process_generation") is None
                        else int(raw["process_generation"])
                    ),
                    worker_slot_id=raw.get("worker_slot_id"),
                    session_generation=(
                        None if raw.get("session_generation") is None
                        else int(raw["session_generation"])
                    ),
                    executor_id=raw.get("executor_id"),
                    payload_ref=raw.get("payload_ref"),
                    payload_sha256=raw.get("payload_sha256"),
                    human_requirement=OperatorHumanRequirement(
                        str(raw["human_requirement"])
                    ),
                    ack_mode=OperatorAckMode(str(raw["ack_mode"])),
                    post_local_success=OperatorPostLocalSuccess(
                        str(raw["post_local_success"])
                    ),
                    not_before=raw.get("not_before"),
                    stale_after=raw.get("stale_after"),
                    supersedes_action_id=raw.get("supersedes_action_id"),
                    superseded_by_action_id=raw.get("superseded_by_action_id"),
                    claim=claim,
                    local_prepared_at=raw.get("local_prepared_at"),
                    durable_ack_id=raw.get("durable_ack_id"),
                    failure_code=raw.get("failure_code"),
                    failure_message=raw.get("failure_message"),
                    completed_at=raw.get("completed_at"),
                )
            except (KeyError, ValueError) as exc:
                raise GraphCodecError("invalid_operator_action") from exc

    graph = WorkGraph(
        processes=processes,
        executor_sessions=executor_sessions,
        operator_actions=operator_actions,
        event_seq=int(payload.get("event_seq", 0)),
        graph_history=_decode_value(payload.get("graph_history", [])),
    )
    DomainKernel.validate(graph)
    return graph


def dumps_work_graph(graph: WorkGraph) -> str:
    return json.dumps(
        encode_work_graph(graph),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def loads_work_graph(text: str) -> WorkGraph:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraphCodecError("invalid_graph_json") from exc
    return decode_work_graph(payload)
