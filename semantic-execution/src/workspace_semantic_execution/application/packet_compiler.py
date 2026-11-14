"""Deterministic compilation of durable semantic state into worker packets."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from ..domain import ExecutorProfile, SessionMode


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    text: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuestionRecord:
    question_id: str
    text: str


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    decision: str
    rationale: str
    evidence_refs: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class PacketCompilationInput:
    process_id: str
    source_checkpoint: str
    objective: str
    findings: tuple[FindingRecord, ...] = ()
    decisions: tuple[DecisionRecord, ...] = ()
    unresolved_questions: tuple[QuestionRecord, ...] = ()
    constraints: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    validator_contract: str = ""
    output_schema: str = "WORKSPACE_REASONING_RESULT_V1"
    next_safe_boundary: str = ""


@dataclass(frozen=True)
class CompiledPacket:
    packet_version: str
    executor_id: str
    packet_sha256: str
    canonical_payload_json: str
    text: str


class SemanticPacketCompiler:
    VERSION = "WORKSPACE_REASONING_PACKET_V1"

    @staticmethod
    def _continuity_contract(session_mode: SessionMode) -> str:
        if session_mode == SessionMode.PERSISTENT_CHAT:
            return (
                "Conversation context may be used as a cache, but durable packet "
                "state and cited evidence remain authoritative."
            )
        if session_mode == SessionMode.SESSION_SCOPED:
            return (
                "Session-local context is optional optimization state; resume "
                "must remain possible from durable packet state."
            )
        if session_mode == SessionMode.STATELESS:
            return (
                "Assume no prior conversational memory. Use only this packet "
                "and explicitly retrieved evidence."
            )
        if session_mode == SessionMode.NONE:
            return (
                "No conversational continuity is available or required; durable "
                "packet state remains authoritative."
            )
        raise ValueError(f"unknown_session_mode:{session_mode}")

    @staticmethod
    def _validate(source: PacketCompilationInput) -> None:
        required = (
            source.process_id,
            source.source_checkpoint,
            source.objective,
            source.validator_contract,
            source.output_schema,
            source.next_safe_boundary,
        )
        if not all(required):
            raise ValueError("packet_required_fields_missing")
        if any(not item.finding_id or not item.text for item in source.findings):
            raise ValueError("invalid_finding")
        if any(
            not item.question_id or not item.text
            for item in source.unresolved_questions
        ):
            raise ValueError("invalid_question")
        if any(
            not item.decision_id
            or not item.decision
            or not item.rationale
            for item in source.decisions
        ):
            raise ValueError("invalid_decision")

    def compile(
        self,
        source: PacketCompilationInput,
        *,
        executor: ExecutorProfile,
    ) -> CompiledPacket:
        self._validate(source)

        payload = {
            "packet_version": self.VERSION,
            "process": {
                "process_id": source.process_id,
                "source_checkpoint": source.source_checkpoint,
                "objective": source.objective,
                "findings": [asdict(item) for item in source.findings],
                "decisions": [asdict(item) for item in source.decisions],
                "unresolved_questions": [
                    asdict(item) for item in source.unresolved_questions
                ],
                "constraints": list(source.constraints),
                "evidence_refs": list(source.evidence_refs),
                "authority_refs": list(source.authority_refs),
                "allowed_actions": list(source.allowed_actions),
                "validator_contract": source.validator_contract,
                "output_schema": source.output_schema,
                "next_safe_boundary": source.next_safe_boundary,
            },
            "executor": {
                "executor_id": executor.executor_id,
                "provider_id": executor.provider_id,
                "model_id": executor.model_id,
                "surface_id": executor.surface_id,
                "harness_id": executor.harness_id,
                "toolset_id": executor.toolset_id,
                "invocation_mode": executor.invocation_mode.value,
                "session_mode": executor.session_mode.value,
                "lifecycle": executor.lifecycle.value,
                "memory_reset_policy": executor.memory_reset_policy.value,
            },
            "execution_contract": {
                "authority_rule": (
                    "Reasoning output is proposal/evidence only and cannot grant "
                    "or widen execution authority."
                ),
                "validation_rule": (
                    "Do not claim completion from tool success alone; report "
                    "durable evidence for the declared validator."
                ),
                "continuity_rule": self._continuity_contract(
                    executor.session_mode
                ),
                "memory_rule": (
                    "Executor memory is an optimization governed by the declared "
                    "memory_reset_policy; durable packet state is the recovery "
                    "source regardless of service lifetime."
                ),
                "retry_rule": (
                    "Do not repeat an unchanged reasoning attempt. A retry must "
                    "be justified by new evidence, changed context, validator "
                    "feedback, a new branch, or changed resource/authority state."
                ),
            },
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        pretty = json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        text = (
            f"{self.VERSION}\n"
            f"packet_sha256={digest}\n"
            f"executor_id={executor.executor_id}\n"
            f"invocation_mode={executor.invocation_mode.value}\n"
            f"session_mode={executor.session_mode.value}\n"
            f"lifecycle={executor.lifecycle.value}\n"
            f"memory_reset_policy={executor.memory_reset_policy.value}\n"
            "BEGIN_PAYLOAD\n"
            f"{pretty}\n"
            "END_PAYLOAD\n"
        )
        return CompiledPacket(
            packet_version=self.VERSION,
            executor_id=executor.executor_id,
            packet_sha256=digest,
            canonical_payload_json=canonical,
            text=text,
        )
