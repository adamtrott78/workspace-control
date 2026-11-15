"""Deterministic JSON codec for durable WorkGraph state.

This codec is infrastructure-neutral and intentionally avoids pickle or
runtime-specific object serialization. Schema v8 adds durable production-scheduler dispatch specifications while retaining v1-v7 decode compatibility.
"""
from __future__ import annotations

import json
from typing import Any

from ..domain import (
    CandidateAction,
    DomainKernel,
    EffectReceipt,
    ExecutionRequirement,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorSession,
    ExecutorSessionState,
    InvocationMode,
    MemoryResetPolicy,
    OperatorAckMode,
    OperatorAction,
    OperatorActionClaim,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    PrivacyClass,
    ProcessState,
    ReasoningProcess,
    SemanticPacketDecision,
    SemanticPacketFinding,
    SemanticPacketQuestion,
    SemanticPacketSource,
    SchedulerDeterministicSpec,
    SchedulerDispatchSpec,
    SchedulerOperatorSpec,
    SchedulerPacketSpec,
    SessionMode,
    TransitionRecord,
    ValidationResult,
    WorkerChildProposal,
    WorkerResultKind,
    WorkerResultPublication,
    WorkerResultPublicationContract,
    WorkContract,
    WorkDisposition,
    WorkGraph,
)


SCHEMA_VERSION = 8
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3, 4, 5, 6, 7, 8}


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


def _encode_packet_source(
    source: SemanticPacketSource,
) -> dict[str, Any]:
    return {
        "payload_ref": source.payload_ref,
        "process_id": source.process_id,
        "process_generation": source.process_generation,
        "executor_id": source.executor_id,
        "packet_sha256": source.packet_sha256,
        "source_checkpoint": source.source_checkpoint,
        "objective": source.objective,
        "findings": [
            {
                "finding_id": item.finding_id,
                "text": item.text,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in source.findings
        ],
        "decisions": [
            {
                "decision_id": item.decision_id,
                "decision": item.decision,
                "rationale": item.rationale,
                "evidence_refs": list(item.evidence_refs),
                "alternatives": list(item.alternatives),
            }
            for item in source.decisions
        ],
        "unresolved_questions": [
            {
                "question_id": item.question_id,
                "text": item.text,
            }
            for item in source.unresolved_questions
        ],
        "constraints": list(source.constraints),
        "evidence_refs": list(source.evidence_refs),
        "authority_refs": list(source.authority_refs),
        "allowed_actions": list(source.allowed_actions),
        "validator_contract": source.validator_contract,
        "output_schema": source.output_schema,
        "next_safe_boundary": source.next_safe_boundary,
        "result_publication": (
            None
            if source.result_publication is None
            else {
                "publication_id": (
                    source.result_publication.publication_id
                ),
                "action_id": source.result_publication.action_id,
                "action_generation": (
                    source.result_publication.action_generation
                ),
                "process_generation": (
                    source.result_publication.process_generation
                ),
                "worker_slot_id": (
                    source.result_publication.worker_slot_id
                ),
                "session_generation": (
                    source.result_publication.session_generation
                ),
                "schema_ref": source.result_publication.schema_ref,
                "target_ref": source.result_publication.target_ref,
                "candidate_only": (
                    source.result_publication.candidate_only
                ),
            }
        ),
    }


def _encode_worker_result(
    publication: WorkerResultPublication,
) -> dict[str, Any]:
    return {
        "publication_id": publication.publication_id,
        "source_ref": publication.source_ref,
        "source_sha256": publication.source_sha256,
        "action_id": publication.action_id,
        "action_generation": publication.action_generation,
        "process_id": publication.process_id,
        "process_generation": publication.process_generation,
        "executor_id": publication.executor_id,
        "worker_slot_id": publication.worker_slot_id,
        "session_generation": publication.session_generation,
        "packet_sha256": publication.packet_sha256,
        "kind": publication.kind.value,
        "observed_at": publication.observed_at,
        "result_payload_ref": publication.result_payload_ref,
        "result_payload_sha256": publication.result_payload_sha256,
        "evidence_refs": list(publication.evidence_refs),
        "reason": publication.reason,
        "wait_key": publication.wait_key,
        "children": [
            {
                "process_id": child.process_id,
                "objective": child.objective,
                "dependencies": list(child.dependencies),
                "mandatory_constraints": list(
                    child.mandatory_constraints
                ),
                "provenance_refs": list(child.provenance_refs),
                "authority_refs": list(child.authority_refs),
                "validator_contracts": list(
                    child.validator_contracts
                ),
                "output_schema_refs": list(
                    child.output_schema_refs
                ),
            }
            for child in publication.children
        ],
    }


def _encode_execution_requirement(
    requirement: ExecutionRequirement,
) -> dict[str, Any]:
    return {
        "required_capabilities": sorted(
            requirement.required_capabilities
        ),
        "allowed_invocation_modes": sorted(
            item.value
            for item in requirement.allowed_invocation_modes
        ),
        "allowed_session_modes": sorted(
            item.value
            for item in requirement.allowed_session_modes
        ),
        "allowed_lifecycles": sorted(
            item.value
            for item in requirement.allowed_lifecycles
        ),
        "allowed_memory_reset_policies": sorted(
            item.value
            for item in requirement.allowed_memory_reset_policies
        ),
        "allowed_localities": sorted(
            item.value
            for item in requirement.allowed_localities
        ),
        "privacy_class": requirement.privacy_class.value,
        "minimum_context_capacity": (
            requirement.minimum_context_capacity
        ),
        "required_resource_classes": sorted(
            requirement.required_resource_classes
        ),
        "require_human_launch": requirement.require_human_launch,
    }


def _decode_execution_requirement(
    raw: object,
) -> ExecutionRequirement:
    if not isinstance(raw, dict):
        raise GraphCodecError(
            "scheduler_execution_requirement_must_be_object"
        )
    try:
        return ExecutionRequirement(
            required_capabilities=frozenset(
                _decode_string_tuple(
                    raw.get("required_capabilities"),
                    "scheduler_required_capabilities",
                )
            ),
            allowed_invocation_modes=frozenset(
                InvocationMode(value)
                for value in _decode_string_tuple(
                    raw.get("allowed_invocation_modes"),
                    "scheduler_allowed_invocation_modes",
                )
            ),
            allowed_session_modes=frozenset(
                SessionMode(value)
                for value in _decode_string_tuple(
                    raw.get("allowed_session_modes"),
                    "scheduler_allowed_session_modes",
                )
            ),
            allowed_lifecycles=frozenset(
                ExecutorLifecycle(value)
                for value in _decode_string_tuple(
                    raw.get("allowed_lifecycles"),
                    "scheduler_allowed_lifecycles",
                )
            ),
            allowed_memory_reset_policies=frozenset(
                MemoryResetPolicy(value)
                for value in _decode_string_tuple(
                    raw.get("allowed_memory_reset_policies"),
                    "scheduler_allowed_memory_reset_policies",
                )
            ),
            allowed_localities=frozenset(
                ExecutorLocality(value)
                for value in _decode_string_tuple(
                    raw.get("allowed_localities"),
                    "scheduler_allowed_localities",
                )
            ),
            privacy_class=PrivacyClass(
                str(
                    raw.get(
                        "privacy_class",
                        PrivacyClass.PUBLIC.value,
                    )
                )
            ),
            minimum_context_capacity=(
                None
                if raw.get("minimum_context_capacity") is None
                else int(raw["minimum_context_capacity"])
            ),
            required_resource_classes=frozenset(
                _decode_string_tuple(
                    raw.get("required_resource_classes"),
                    "scheduler_required_resource_classes",
                )
            ),
            require_human_launch=raw.get("require_human_launch"),
        )
    except (TypeError, ValueError) as exc:
        raise GraphCodecError(
            "invalid_scheduler_execution_requirement"
        ) from exc


def _encode_candidate_action(
    action: CandidateAction,
) -> dict[str, Any]:
    return {
        "action_id": action.action_id,
        "process_id": action.process_id,
        "process_generation": action.process_generation,
        "target_ref": action.target_ref,
        "executor_type": action.executor_type,
        "idempotency_key": action.idempotency_key,
        "preconditions": list(action.preconditions),
        "expected_effect": action.expected_effect,
        "postcondition_validator": action.postcondition_validator,
        "authorization_state": action.authorization_state,
    }


def _decode_candidate_action(
    raw: object,
) -> CandidateAction:
    if not isinstance(raw, dict):
        raise GraphCodecError(
            "scheduler_candidate_action_must_be_object"
        )
    try:
        return CandidateAction(
            action_id=str(raw["action_id"]),
            process_id=str(raw["process_id"]),
            process_generation=int(raw["process_generation"]),
            target_ref=str(raw["target_ref"]),
            executor_type=str(raw["executor_type"]),
            idempotency_key=str(raw["idempotency_key"]),
            preconditions=_decode_string_tuple(
                raw.get("preconditions"),
                "scheduler_candidate_preconditions",
            ),
            expected_effect=str(raw["expected_effect"]),
            postcondition_validator=str(
                raw["postcondition_validator"]
            ),
            authorization_state=str(
                raw.get("authorization_state", "UNDECIDED")
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GraphCodecError(
            "invalid_scheduler_candidate_action"
        ) from exc


def _encode_scheduler_packet(
    packet: SchedulerPacketSpec,
) -> dict[str, Any]:
    return {
        "source_checkpoint": packet.source_checkpoint,
        "objective": packet.objective,
        "findings": [
            {
                "finding_id": item.finding_id,
                "text": item.text,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in packet.findings
        ],
        "decisions": [
            {
                "decision_id": item.decision_id,
                "decision": item.decision,
                "rationale": item.rationale,
                "evidence_refs": list(item.evidence_refs),
                "alternatives": list(item.alternatives),
            }
            for item in packet.decisions
        ],
        "unresolved_questions": [
            {
                "question_id": item.question_id,
                "text": item.text,
            }
            for item in packet.unresolved_questions
        ],
        "constraints": list(packet.constraints),
        "evidence_refs": list(packet.evidence_refs),
        "authority_refs": list(packet.authority_refs),
        "allowed_actions": list(packet.allowed_actions),
        "validator_contract": packet.validator_contract,
        "output_schema": packet.output_schema,
        "next_safe_boundary": packet.next_safe_boundary,
    }


def _decode_scheduler_packet(
    raw: object,
) -> SchedulerPacketSpec:
    if not isinstance(raw, dict):
        raise GraphCodecError("scheduler_packet_must_be_object")
    findings = tuple(
        SemanticPacketFinding(
            finding_id=str(item.get("finding_id", "")),
            text=str(item.get("text", "")),
            evidence_refs=_decode_string_tuple(
                item.get("evidence_refs"),
                "scheduler_finding_evidence_refs",
            ),
        )
        for item in raw.get("findings", [])
    )
    decisions = tuple(
        SemanticPacketDecision(
            decision_id=str(item.get("decision_id", "")),
            decision=str(item.get("decision", "")),
            rationale=str(item.get("rationale", "")),
            evidence_refs=_decode_string_tuple(
                item.get("evidence_refs"),
                "scheduler_decision_evidence_refs",
            ),
            alternatives=_decode_string_tuple(
                item.get("alternatives"),
                "scheduler_decision_alternatives",
            ),
        )
        for item in raw.get("decisions", [])
    )
    questions = tuple(
        SemanticPacketQuestion(
            question_id=str(item.get("question_id", "")),
            text=str(item.get("text", "")),
        )
        for item in raw.get("unresolved_questions", [])
    )
    return SchedulerPacketSpec(
        source_checkpoint=str(raw.get("source_checkpoint", "")),
        objective=str(raw.get("objective", "")),
        findings=findings,
        decisions=decisions,
        unresolved_questions=questions,
        constraints=_decode_string_tuple(
            raw.get("constraints"),
            "scheduler_constraints",
        ),
        evidence_refs=_decode_string_tuple(
            raw.get("evidence_refs"),
            "scheduler_evidence_refs",
        ),
        authority_refs=_decode_string_tuple(
            raw.get("authority_refs"),
            "scheduler_authority_refs",
        ),
        allowed_actions=_decode_string_tuple(
            raw.get("allowed_actions"),
            "scheduler_allowed_actions",
        ),
        validator_contract=str(
            raw.get("validator_contract", "")
        ),
        output_schema=str(raw.get("output_schema", "")),
        next_safe_boundary=str(
            raw.get("next_safe_boundary", "")
        ),
    )


def _encode_scheduler_dispatch(
    spec: SchedulerDispatchSpec,
) -> dict[str, Any]:
    operator = None
    if spec.operator is not None:
        operator = {
            "task_id": spec.operator.task_id,
            "action_id": spec.operator.action_id,
            "action_generation": spec.operator.action_generation,
            "worker_slot_id": spec.operator.worker_slot_id,
            "session_generation": spec.operator.session_generation,
            "priority_rank": spec.operator.priority_rank,
            "queue_sequence": spec.operator.queue_sequence,
            "created_at": spec.operator.created_at,
            "candidate_repository": (
                spec.operator.candidate_repository
            ),
            "candidate_ref": spec.operator.candidate_ref,
            "candidate_path": spec.operator.candidate_path,
            "candidate_schema_ref": (
                spec.operator.candidate_schema_ref
            ),
        }
    deterministic = None
    if spec.deterministic is not None:
        deterministic = {
            "worker_id": spec.deterministic.worker_id,
            "lease_id": spec.deterministic.lease_id,
            "candidate_action": _encode_candidate_action(
                spec.deterministic.candidate_action
            ),
        }
    return {
        "dispatch_id": spec.dispatch_id,
        "process_id": spec.process_id,
        "process_generation": spec.process_generation,
        "requirement_id": spec.requirement_id,
        "requirement": _encode_execution_requirement(
            spec.requirement
        ),
        "packet": _encode_scheduler_packet(spec.packet),
        "operator": operator,
        "deterministic": deterministic,
    }


def _decode_scheduler_dispatch(
    raw: object,
) -> SchedulerDispatchSpec:
    if not isinstance(raw, dict):
        raise GraphCodecError(
            "scheduler_dispatch_must_be_object"
        )
    raw_operator = raw.get("operator")
    operator = None
    if raw_operator is not None:
        if not isinstance(raw_operator, dict):
            raise GraphCodecError(
                "scheduler_operator_must_be_object"
            )
        try:
            operator = SchedulerOperatorSpec(
                task_id=str(raw_operator["task_id"]),
                action_id=str(raw_operator["action_id"]),
                action_generation=int(
                    raw_operator["action_generation"]
                ),
                worker_slot_id=str(
                    raw_operator["worker_slot_id"]
                ),
                session_generation=int(
                    raw_operator["session_generation"]
                ),
                priority_rank=int(
                    raw_operator["priority_rank"]
                ),
                queue_sequence=int(
                    raw_operator["queue_sequence"]
                ),
                created_at=str(raw_operator["created_at"]),
                candidate_repository=str(
                    raw_operator["candidate_repository"]
                ),
                candidate_ref=str(
                    raw_operator["candidate_ref"]
                ),
                candidate_path=str(
                    raw_operator["candidate_path"]
                ),
                candidate_schema_ref=str(
                    raw_operator["candidate_schema_ref"]
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GraphCodecError(
                "invalid_scheduler_operator"
            ) from exc
    raw_deterministic = raw.get("deterministic")
    deterministic = None
    if raw_deterministic is not None:
        if not isinstance(raw_deterministic, dict):
            raise GraphCodecError(
                "scheduler_deterministic_must_be_object"
            )
        try:
            deterministic = SchedulerDeterministicSpec(
                worker_id=str(raw_deterministic["worker_id"]),
                lease_id=str(raw_deterministic["lease_id"]),
                candidate_action=_decode_candidate_action(
                    raw_deterministic["candidate_action"]
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GraphCodecError(
                "invalid_scheduler_deterministic"
            ) from exc
    try:
        return SchedulerDispatchSpec(
            dispatch_id=str(raw["dispatch_id"]),
            process_id=str(raw["process_id"]),
            process_generation=int(
                raw["process_generation"]
            ),
            requirement_id=str(raw["requirement_id"]),
            requirement=_decode_execution_requirement(
                raw["requirement"]
            ),
            packet=_decode_scheduler_packet(raw["packet"]),
            operator=operator,
            deterministic=deterministic,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GraphCodecError(
            "invalid_scheduler_dispatch"
        ) from exc


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
        "packet_sources": [
            _encode_packet_source(source)
            for source in sorted(
                graph.packet_sources.values(),
                key=lambda item: item.payload_ref,
            )
        ],
        "worker_results": [
            _encode_worker_result(publication)
            for publication in sorted(
                graph.worker_results.values(),
                key=lambda item: item.publication_id,
            )
        ],
        "scheduler_dispatches": [
            _encode_scheduler_dispatch(spec)
            for spec in sorted(
                graph.scheduler_dispatches.values(),
                key=lambda item: item.dispatch_id,
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

    packet_sources: dict[str, SemanticPacketSource] = {}
    if schema_version >= 5:
        raw_sources = payload.get("packet_sources", [])
        if not isinstance(raw_sources, list):
            raise GraphCodecError("packet_sources_must_be_list")
        for raw in raw_sources:
            if not isinstance(raw, dict):
                raise GraphCodecError("packet_source_must_be_object")
            payload_ref = raw.get("payload_ref")
            if not isinstance(payload_ref, str) or not payload_ref:
                raise GraphCodecError("packet_source_payload_ref_required")
            if payload_ref in packet_sources:
                raise GraphCodecError(
                    f"duplicate_packet_source:{payload_ref}"
                )
            findings = tuple(
                SemanticPacketFinding(
                    finding_id=str(item.get("finding_id", "")),
                    text=str(item.get("text", "")),
                    evidence_refs=_decode_string_tuple(
                        item.get("evidence_refs"),
                        "packet_finding_evidence_refs",
                    ),
                )
                for item in raw.get("findings", [])
            )
            decisions = tuple(
                SemanticPacketDecision(
                    decision_id=str(item.get("decision_id", "")),
                    decision=str(item.get("decision", "")),
                    rationale=str(item.get("rationale", "")),
                    evidence_refs=_decode_string_tuple(
                        item.get("evidence_refs"),
                        "packet_decision_evidence_refs",
                    ),
                    alternatives=_decode_string_tuple(
                        item.get("alternatives"),
                        "packet_decision_alternatives",
                    ),
                )
                for item in raw.get("decisions", [])
            )
            questions = tuple(
                SemanticPacketQuestion(
                    question_id=str(item.get("question_id", "")),
                    text=str(item.get("text", "")),
                )
                for item in raw.get("unresolved_questions", [])
            )
            raw_publication = raw.get("result_publication")
            result_publication = None
            if schema_version >= 7 and raw_publication is not None:
                if not isinstance(raw_publication, dict):
                    raise GraphCodecError(
                        "packet_result_publication_must_be_object"
                    )
                try:
                    result_publication = (
                        WorkerResultPublicationContract(
                            publication_id=str(
                                raw_publication["publication_id"]
                            ),
                            action_id=str(
                                raw_publication["action_id"]
                            ),
                            action_generation=int(
                                raw_publication[
                                    "action_generation"
                                ]
                            ),
                            process_generation=int(
                                raw_publication[
                                    "process_generation"
                                ]
                            ),
                            worker_slot_id=str(
                                raw_publication[
                                    "worker_slot_id"
                                ]
                            ),
                            session_generation=int(
                                raw_publication[
                                    "session_generation"
                                ]
                            ),
                            schema_ref=str(
                                raw_publication["schema_ref"]
                            ),
                            target_ref=str(
                                raw_publication["target_ref"]
                            ),
                            candidate_only=bool(
                                raw_publication.get(
                                    "candidate_only",
                                    True,
                                )
                            ),
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise GraphCodecError(
                        "invalid_packet_result_publication"
                    ) from exc

            packet_sources[payload_ref] = SemanticPacketSource(
                payload_ref=payload_ref,
                process_id=str(raw.get("process_id", "")),
                process_generation=int(
                    raw.get("process_generation", 0)
                ),
                executor_id=str(raw.get("executor_id", "")),
                packet_sha256=str(raw.get("packet_sha256", "")),
                source_checkpoint=str(
                    raw.get("source_checkpoint", "")
                ),
                objective=str(raw.get("objective", "")),
                findings=findings,
                decisions=decisions,
                unresolved_questions=questions,
                constraints=_decode_string_tuple(
                    raw.get("constraints"),
                    "packet_constraints",
                ),
                evidence_refs=_decode_string_tuple(
                    raw.get("evidence_refs"),
                    "packet_evidence_refs",
                ),
                authority_refs=_decode_string_tuple(
                    raw.get("authority_refs"),
                    "packet_authority_refs",
                ),
                allowed_actions=_decode_string_tuple(
                    raw.get("allowed_actions"),
                    "packet_allowed_actions",
                ),
                validator_contract=str(
                    raw.get("validator_contract", "")
                ),
                output_schema=str(raw.get("output_schema", "")),
                next_safe_boundary=str(
                    raw.get("next_safe_boundary", "")
                ),
                result_publication=result_publication,
            )

    worker_results: dict[str, WorkerResultPublication] = {}
    if schema_version >= 6:
        raw_results = payload.get("worker_results", [])
        if not isinstance(raw_results, list):
            raise GraphCodecError("worker_results_must_be_list")
        for raw in raw_results:
            if not isinstance(raw, dict):
                raise GraphCodecError("worker_result_must_be_object")
            publication_id = raw.get("publication_id")
            if (
                not isinstance(publication_id, str)
                or not publication_id
            ):
                raise GraphCodecError(
                    "worker_result_publication_id_required"
                )
            if publication_id in worker_results:
                raise GraphCodecError(
                    f"duplicate_worker_result:{publication_id}"
                )
            children = tuple(
                WorkerChildProposal(
                    process_id=str(child.get("process_id", "")),
                    objective=str(child.get("objective", "")),
                    dependencies=_decode_string_tuple(
                        child.get("dependencies"),
                        "worker_child_dependencies",
                    ),
                    mandatory_constraints=_decode_string_tuple(
                        child.get("mandatory_constraints"),
                        "worker_child_mandatory_constraints",
                    ),
                    provenance_refs=_decode_string_tuple(
                        child.get("provenance_refs"),
                        "worker_child_provenance_refs",
                    ),
                    authority_refs=_decode_string_tuple(
                        child.get("authority_refs"),
                        "worker_child_authority_refs",
                    ),
                    validator_contracts=_decode_string_tuple(
                        child.get("validator_contracts"),
                        "worker_child_validator_contracts",
                    ),
                    output_schema_refs=_decode_string_tuple(
                        child.get("output_schema_refs"),
                        "worker_child_output_schema_refs",
                    ),
                )
                for child in raw.get("children", [])
            )
            try:
                worker_results[publication_id] = (
                    WorkerResultPublication(
                        publication_id=publication_id,
                        source_ref=str(raw.get("source_ref", "")),
                        source_sha256=str(
                            raw.get("source_sha256", "")
                        ),
                        action_id=str(raw.get("action_id", "")),
                        action_generation=int(
                            raw.get("action_generation", 0)
                        ),
                        process_id=str(raw.get("process_id", "")),
                        process_generation=int(
                            raw.get("process_generation", 0)
                        ),
                        executor_id=str(
                            raw.get("executor_id", "")
                        ),
                        worker_slot_id=str(
                            raw.get("worker_slot_id", "")
                        ),
                        session_generation=int(
                            raw.get("session_generation", 0)
                        ),
                        packet_sha256=str(
                            raw.get("packet_sha256", "")
                        ),
                        kind=WorkerResultKind(str(raw["kind"])),
                        observed_at=str(raw.get("observed_at", "")),
                        result_payload_ref=raw.get(
                            "result_payload_ref"
                        ),
                        result_payload_sha256=raw.get(
                            "result_payload_sha256"
                        ),
                        evidence_refs=_decode_string_tuple(
                            raw.get("evidence_refs"),
                            "worker_result_evidence_refs",
                        ),
                        reason=raw.get("reason"),
                        wait_key=raw.get("wait_key"),
                        children=children,
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise GraphCodecError(
                    "invalid_worker_result"
                ) from exc

    scheduler_dispatches: dict[str, SchedulerDispatchSpec] = {}
    if schema_version >= 8:
        raw_dispatches = payload.get("scheduler_dispatches", [])
        if not isinstance(raw_dispatches, list):
            raise GraphCodecError(
                "scheduler_dispatches_must_be_list"
            )
        for raw in raw_dispatches:
            spec = _decode_scheduler_dispatch(raw)
            if spec.dispatch_id in scheduler_dispatches:
                raise GraphCodecError(
                    f"duplicate_scheduler_dispatch:{spec.dispatch_id}"
                )
            scheduler_dispatches[spec.dispatch_id] = spec

    graph = WorkGraph(
        processes=processes,
        executor_sessions=executor_sessions,
        operator_actions=operator_actions,
        packet_sources=packet_sources,
        worker_results=worker_results,
        scheduler_dispatches=scheduler_dispatches,
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
