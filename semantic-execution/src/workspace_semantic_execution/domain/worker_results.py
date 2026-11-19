"""Durable worker-authored result publication contracts."""
from __future__ import annotations

from copy import deepcopy

from .models import (
    WorkerResultKind,
    WorkerResultPublication,
    WorkGraph,
)


class WorkerResultError(RuntimeError):
    """Fail-closed worker-result publication error."""


class WorkerResultKernel:
    @staticmethod
    def _valid_sha256(value: str | None) -> bool:
        return (
            value is not None
            and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value)
        )

    @classmethod
    def validate_publication(
        cls,
        publication: WorkerResultPublication,
    ) -> None:
        required = (
            publication.publication_id,
            publication.source_ref,
            publication.action_id,
            publication.process_id,
            publication.executor_id,
            publication.worker_slot_id,
            publication.observed_at,
        )
        if not all(
            isinstance(value, str) and value
            for value in required
        ):
            raise WorkerResultError(
                "worker_result_required_identity"
            )
        if (
            publication.action_generation < 0
            or publication.process_generation < 0
            or publication.session_generation < 0
        ):
            raise WorkerResultError(
                "worker_result_generation_invalid"
            )
        if not cls._valid_sha256(publication.source_sha256):
            raise WorkerResultError(
                "worker_result_source_sha256_invalid"
            )
        if not cls._valid_sha256(publication.packet_sha256):
            raise WorkerResultError(
                "worker_result_packet_sha256_invalid"
            )
        if any(not ref for ref in publication.evidence_refs):
            raise WorkerResultError(
                "worker_result_evidence_ref_invalid"
            )

        if publication.kind == WorkerResultKind.RESULT:
            if (
                not publication.result_payload_ref
                or not cls._valid_sha256(
                    publication.result_payload_sha256
                )
            ):
                raise WorkerResultError(
                    "worker_result_payload_required"
                )
            if (
                publication.children
                or publication.wait_key is not None
            ):
                raise WorkerResultError(
                    "worker_result_result_shape_invalid"
                )
        elif publication.kind == WorkerResultKind.TOO_LARGE:
            if not publication.reason or not publication.children:
                raise WorkerResultError(
                    "worker_result_decomposition_required"
                )
            if (
                publication.result_payload_ref is not None
                or publication.result_payload_sha256 is not None
                or publication.wait_key is not None
            ):
                raise WorkerResultError(
                    "worker_result_too_large_shape_invalid"
                )
            ids = [child.process_id for child in publication.children]
            if len(ids) != len(set(ids)):
                raise WorkerResultError(
                    "worker_result_duplicate_child"
                )
            for child in publication.children:
                if not child.process_id or not child.objective:
                    raise WorkerResultError(
                        "worker_result_child_identity_required"
                    )
                for values in (
                    child.dependencies,
                    child.mandatory_constraints,
                    child.provenance_refs,
                    child.authority_refs,
                    child.validator_contracts,
                    child.output_schema_refs,
                ):
                    if any(not value for value in values):
                        raise WorkerResultError(
                            "worker_result_child_value_invalid"
                        )
        elif (
            publication.kind
            == WorkerResultKind.INTRINSICALLY_DIFFICULT
        ):
            if not publication.reason:
                raise WorkerResultError(
                    "worker_result_escalation_reason_required"
                )
            if (
                publication.children
                or publication.wait_key is not None
                or publication.result_payload_ref is not None
                or publication.result_payload_sha256 is not None
            ):
                raise WorkerResultError(
                    "worker_result_escalation_shape_invalid"
                )
        elif publication.kind == WorkerResultKind.WAIT_EXTERNAL:
            if not publication.wait_key:
                raise WorkerResultError(
                    "worker_result_wait_key_required"
                )
            if (
                publication.children
                or publication.result_payload_ref is not None
                or publication.result_payload_sha256 is not None
            ):
                raise WorkerResultError(
                    "worker_result_wait_shape_invalid"
                )
        else:
            raise WorkerResultError("worker_result_kind_unknown")

    @classmethod
    def register(
        cls,
        graph: WorkGraph,
        publication: WorkerResultPublication,
    ) -> WorkGraph:
        cls.validate_publication(publication)
        next_graph = deepcopy(graph)
        existing = next_graph.worker_results.get(
            publication.publication_id
        )
        if existing is not None:
            if existing == publication:
                return next_graph
            raise WorkerResultError(
                "worker_result_publication_conflict"
            )

        next_graph.worker_results[
            publication.publication_id
        ] = deepcopy(publication)
        next_graph.event_seq += 1
        next_graph.graph_history.append(
            {
                "seq": next_graph.event_seq,
                "event": "WORKER_RESULT_REGISTER",
                "details": {
                    "publication_id": publication.publication_id,
                    "source_ref": publication.source_ref,
                    "source_sha256": publication.source_sha256,
                    "action_id": publication.action_id,
                    "process_id": publication.process_id,
                    "process_generation": (
                        publication.process_generation
                    ),
                    "executor_id": publication.executor_id,
                    "worker_slot_id": publication.worker_slot_id,
                    "session_generation": (
                        publication.session_generation
                    ),
                    "packet_sha256": publication.packet_sha256,
                    "kind": publication.kind.value,
                },
            }
        )
        return next_graph

    @classmethod
    def validate_graph(cls, graph: WorkGraph) -> None:
        for publication_id, publication in graph.worker_results.items():
            if publication.publication_id != publication_id:
                raise WorkerResultError(
                    "worker_result_key_mismatch"
                )
            cls.validate_publication(publication)
