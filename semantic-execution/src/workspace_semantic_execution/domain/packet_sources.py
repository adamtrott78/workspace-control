"""Durable semantic packet-source records.

Packet text is never authoritative durable state. These records preserve the
typed inputs required to deterministically reconstruct a packet and verify its
hash at the transport boundary.
"""
from __future__ import annotations

from copy import deepcopy

from .models import SemanticPacketSource, WorkGraph


class PacketSourceError(RuntimeError):
    """Fail-closed packet-source contract error."""


class PacketSourceKernel:
    @staticmethod
    def _valid_sha256(value: str) -> bool:
        return (
            len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value)
        )

    @classmethod
    def validate_source(cls, source: SemanticPacketSource) -> None:
        required = (
            source.payload_ref,
            source.process_id,
            source.executor_id,
            source.source_checkpoint,
            source.objective,
            source.validator_contract,
            source.output_schema,
            source.next_safe_boundary,
        )
        if not all(isinstance(value, str) and value for value in required):
            raise PacketSourceError("packet_source_required_fields")
        if source.process_generation < 0:
            raise PacketSourceError("packet_source_generation_invalid")
        if not cls._valid_sha256(source.packet_sha256):
            raise PacketSourceError("packet_source_sha256_invalid")

        for finding in source.findings:
            if (
                not finding.finding_id
                or not finding.text
                or any(not ref for ref in finding.evidence_refs)
            ):
                raise PacketSourceError("packet_source_finding_invalid")
        if len({item.finding_id for item in source.findings}) != len(
            source.findings
        ):
            raise PacketSourceError("packet_source_duplicate_finding")

        for decision in source.decisions:
            if (
                not decision.decision_id
                or not decision.decision
                or not decision.rationale
                or any(not ref for ref in decision.evidence_refs)
                or any(not alt for alt in decision.alternatives)
            ):
                raise PacketSourceError("packet_source_decision_invalid")
        if len({item.decision_id for item in source.decisions}) != len(
            source.decisions
        ):
            raise PacketSourceError("packet_source_duplicate_decision")

        for question in source.unresolved_questions:
            if not question.question_id or not question.text:
                raise PacketSourceError("packet_source_question_invalid")
        if len(
            {item.question_id for item in source.unresolved_questions}
        ) != len(source.unresolved_questions):
            raise PacketSourceError("packet_source_duplicate_question")

        for name in (
            "constraints",
            "evidence_refs",
            "authority_refs",
            "allowed_actions",
        ):
            values = getattr(source, name)
            if any(not isinstance(value, str) or not value for value in values):
                raise PacketSourceError(f"packet_source_{name}_invalid")

    @classmethod
    def validate_graph(cls, graph: WorkGraph) -> None:
        for payload_ref, source in graph.packet_sources.items():
            if source.payload_ref != payload_ref:
                raise PacketSourceError("packet_source_key_mismatch")
            cls.validate_source(source)
            if source.process_id not in graph.processes:
                raise PacketSourceError("packet_source_unknown_process")

    @classmethod
    def register(
        cls,
        graph: WorkGraph,
        source: SemanticPacketSource,
    ) -> WorkGraph:
        cls.validate_source(source)
        next_graph = deepcopy(graph)
        process = next_graph.processes.get(source.process_id)
        if process is None:
            raise PacketSourceError("packet_source_unknown_process")
        if process.generation != source.process_generation:
            raise PacketSourceError("packet_source_stale_process_generation")

        existing = next_graph.packet_sources.get(source.payload_ref)
        if existing is not None:
            if existing == source:
                return next_graph
            raise PacketSourceError(
                f"packet_source_conflict:{source.payload_ref}"
            )

        next_graph.packet_sources[source.payload_ref] = deepcopy(source)
        next_graph.event_seq += 1
        next_graph.graph_history.append(
            {
                "seq": next_graph.event_seq,
                "event": "PACKET_SOURCE_REGISTER",
                "details": {
                    "payload_ref": source.payload_ref,
                    "process_id": source.process_id,
                    "process_generation": source.process_generation,
                    "executor_id": source.executor_id,
                    "packet_sha256": source.packet_sha256,
                },
            }
        )
        cls.validate_graph(next_graph)
        return next_graph
