"""Deterministic compilation of durable semantic state into worker packets."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from ..domain import (
    ContextMode,
    ExecutorProfile,
    SessionMode,
    WorkerResultPublicationContract,
)
from .token_economy import TokenEconomyDecision


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
    result_publication: WorkerResultPublicationContract | None = None


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
        contract = source.result_publication
        if contract is not None:
            if (
                not contract.publication_id
                or not contract.action_id
                or not contract.worker_slot_id
                or not contract.schema_ref
                or not contract.target_ref
                or contract.action_generation < 0
                or contract.process_generation < 0
                or contract.session_generation < 0
                or not contract.candidate_only
            ):
                raise ValueError("invalid_result_publication_contract")

    @staticmethod
    def _surface_prefix(objective: str) -> str:
        """Lift leading @-mention directives into raw clipboard lines.

        The prefix is derived only from the hashed objective stored in durable
        packet state, so materialization remains deterministic and no
        unauthenticated text is introduced outside the canonical payload.
        """
        mentions: list[str] = []
        for line in objective.splitlines():
            if not line:
                break
            if not line.startswith("@") or line != line.strip():
                break
            mentions.append(line)
        if not mentions:
            return ""
        return "\n".join(mentions) + "\n\n"

    @staticmethod
    def _compact_list(label: str, values: tuple[str, ...]) -> str:
        if not values:
            return f"{label}=NONE\n"
        return f"{label}=" + "|".join(values) + "\n"

    def _render_compact(
        self,
        *,
        source: PacketCompilationInput,
        executor: ExecutorProfile,
        digest: str,
        decision: TokenEconomyDecision,
    ) -> str:
        """Render a token-economical worker projection.

        The full canonical payload remains hashed and durable. Compact rendering
        removes repeated presentation/contract boilerplate only; mandatory
        constraints, authority refs, validator/output contracts, findings,
        decisions, questions and result-publication bindings remain explicit.
        """
        budget = decision.budget
        context = decision.context
        lines = [
            self.VERSION,
            f"packet_sha256={digest}",
            f"executor_id={executor.executor_id}",
            f"context_mode={context.context_mode.value}",
            f"reasoning_profile={budget.reasoning_profile.value}",
            f"communication_mode={budget.communication_mode.value}",
            f"max_output_tokens={budget.max_output_tokens}",
            f"source_checkpoint={source.source_checkpoint}",
            "AUTHORITY=PROPOSAL_ONLY",
            "COMPLETION=VALIDATOR_REQUIRED",
            "RETRY=NEW_EVIDENCE_REQUIRED",
            "DURABLE_STATE=AUTHORITATIVE",
            "OBJECTIVE",
            source.objective,
            "END_OBJECTIVE",
        ]
        text = "\n".join(lines) + "\n"
        text += self._compact_list("CONSTRAINTS", source.constraints)
        text += self._compact_list("EVIDENCE_REFS", source.evidence_refs)
        text += self._compact_list("AUTHORITY_REFS", source.authority_refs)
        text += self._compact_list("ALLOWED_ACTIONS", source.allowed_actions)
        text += f"VALIDATOR={source.validator_contract}\n"
        text += f"OUTPUT_SCHEMA={source.output_schema}\n"
        text += f"NEXT_SAFE_BOUNDARY={source.next_safe_boundary}\n"

        if source.findings:
            text += "FINDINGS_BEGIN\n"
            for item in source.findings:
                refs = "|".join(item.evidence_refs) or "NONE"
                text += f"{item.finding_id}\t{refs}\t{item.text}\n"
            text += "FINDINGS_END\n"
        if source.decisions:
            text += "DECISIONS_BEGIN\n"
            for item in source.decisions:
                refs = "|".join(item.evidence_refs) or "NONE"
                alternatives = "|".join(item.alternatives) or "NONE"
                text += (
                    f"{item.decision_id}\t{refs}\t{alternatives}\t"
                    f"{item.decision}\t{item.rationale}\n"
                )
            text += "DECISIONS_END\n"
        if source.unresolved_questions:
            text += "QUESTIONS_BEGIN\n"
            for item in source.unresolved_questions:
                text += f"{item.question_id}\t{item.text}\n"
            text += "QUESTIONS_END\n"

        if context.context_mode == ContextMode.DELTA:
            text += (
                f"BASE_CHECKPOINT={context.base_checkpoint or source.source_checkpoint}\n"
            )
            text += self._compact_list("DELTA_REFS", context.delta_refs)

        if source.result_publication is not None:
            publication = json.dumps(
                asdict(source.result_publication),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            text += f"RESULT_PUBLICATION={publication}\n"
        return text

    def compile(
        self,
        source: PacketCompilationInput,
        *,
        executor: ExecutorProfile,
        token_economy: TokenEconomyDecision | None = None,
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
            "result_publication": (
                None
                if source.result_publication is None
                else asdict(source.result_publication)
            ),
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
                "result_publication_rule": (
                    "If result_publication is non-null, publish exactly one JSON "
                    "candidate matching its schema at its target_ref. Copy the "
                    "packet_sha256 header value into the candidate packet_sha256 "
                    "field. Do not include source_ref/source_sha256 in worker JSON; "
                    "the intake adapter binds those from immutable bytes. Do not "
                    "modify task capsules, authority/policy state, runtime control "
                    "state, or any path other than the exact candidate target."
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
        surface_prefix = self._surface_prefix(source.objective)
        if (
            token_economy is None
            or token_economy.context.context_mode == ContextMode.FULL_RECOVERY
        ):
            text = (
                surface_prefix
                + f"{self.VERSION}\n"
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
        else:
            text = surface_prefix + self._render_compact(
                source=source,
                executor=executor,
                digest=digest,
                decision=token_economy,
            )
        return CompiledPacket(
            packet_version=self.VERSION,
            executor_id=executor.executor_id,
            packet_sha256=digest,
            canonical_payload_json=canonical,
            text=text,
        )
