"""Deterministic JSON codec for durable WorkGraph state.

This codec is infrastructure-neutral and intentionally avoids pickle or
runtime-specific object serialization.
"""
from __future__ import annotations

import json
from typing import Any

from ..domain import (
    DomainKernel,
    EffectReceipt,
    ProcessState,
    ReasoningProcess,
    TransitionRecord,
    ValidationResult,
    WorkGraph,
)


SCHEMA_VERSION = 1


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
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "event_seq": graph.event_seq,
        "graph_history": _encode_value(graph.graph_history),
        "processes": processes,
    }


def decode_work_graph(payload: dict[str, Any]) -> WorkGraph:
    if not isinstance(payload, dict):
        raise GraphCodecError("graph_payload_must_be_object")
    if payload.get("schema_version") != SCHEMA_VERSION:
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
        )
        processes[process_id] = process

    graph = WorkGraph(
        processes=processes,
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
