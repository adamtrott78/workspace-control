"""Durable worker-result publication and intake acceptance tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    dumps_work_graph,
    loads_work_graph,
)
from workspace_semantic_execution.adapters.worker_result_json import (  # noqa: E402
    WorkerResultJsonError,
    parse_worker_result_json,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorRegistry,
    OperatorDispatchPlanner,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutorSessionState,
    OperatorActionState,
    ProcessState,
    ValidationResult,
    WorkerChildProposal,
    WorkerResultKind,
    WorkerResultPublication,
    WorkContract,
    WorkDisposition,
)


PROCESS_ID = "research-iterate.instant-leaf"
PROCESS_ID_2 = "research-iterate.instant-leaf-2"
SLOT_ID = "instant-result-slot"
PROFILE = openai_chat_instant_current_profile()
REGISTRY = ExecutorRegistry((PROFILE,))
VALIDATOR_ID = "validator:worker-result-v1"


def runtime(*, contracted: bool = False) -> RuntimeCoordinator:
    contract = None
    if contracted:
        contract = WorkContract(
            objective="Resolve the research objective.",
            mandatory_constraints=("no write effects",),
            provenance_refs=("root:provenance",),
            authority_refs=("scope:proposal-only",),
            validator_contracts=(VALIDATOR_ID,),
            output_schema_refs=("schema:root-result",),
        )
    coordinator = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    coordinator.initialize(
        DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    PROCESS_ID,
                    work_contract=contract,
                ),
                DomainKernel.create_process(
                    PROCESS_ID_2,
                    work_contract=contract,
                ),
            ]
        )
    )
    PersistentExecutorSessionBroker(coordinator).ensure_session(
        profile=PROFILE,
        slot_id=SLOT_ID,
        session_id="chat-result-session",
    )
    return coordinator


def packet_input(
    *,
    process_id: str = PROCESS_ID,
    source_checkpoint: str = "task@result-sha",
    evidence_refs: tuple[str, ...] = ("evidence:input",),
) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=process_id,
        source_checkpoint=source_checkpoint,
        objective="Return one typed durable transition proposal.",
        constraints=("publish durable result only",),
        evidence_refs=evidence_refs,
        authority_refs=("scope:proposal-only",),
        allowed_actions=("publish-worker-result",),
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable result state",
    )


def plan_and_prepare(
    coordinator: RuntimeCoordinator,
    *,
    action_id: str = "action:worker-result",
):
    planned = OperatorDispatchPlanner(
        runtime=coordinator,
        registry=REGISTRY,
    ).plan_service_existing(
        task_id="task:research-iterate",
        action_id=action_id,
        action_generation=0,
        process_id=PROCESS_ID,
        process_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        executor_id=PROFILE.executor_id,
        packet_input=packet_input(),
        priority_rank=10,
        queue_sequence=1,
        created_at="T0",
    )
    coordinator.claim_next_operator_action(
        helper_instance_id="windows-helper",
        claim_id="claim-result",
        claimed_at="T1",
        expires_at="T2",
    )
    coordinator.record_operator_action_local_prepared(
        action_id=action_id,
        generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        observed_at="T1.5",
    )
    return planned


def publication(
    planned,
    *,
    kind: WorkerResultKind = WorkerResultKind.RESULT,
    publication_id: str = "result:1",
    reason: str | None = None,
    wait_key: str | None = None,
    children=(),
) -> WorkerResultPublication:
    is_result = kind == WorkerResultKind.RESULT
    return WorkerResultPublication(
        publication_id=publication_id,
        source_ref=(
            "github://worker-results/"
            f"{publication_id}.json@immutable-blob"
        ),
        source_sha256="a" * 64,
        action_id=planned.action.action_id,
        action_generation=planned.action.generation,
        process_id=PROCESS_ID,
        process_generation=0,
        executor_id=PROFILE.executor_id,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        packet_sha256=planned.packet.packet_sha256,
        kind=kind,
        observed_at="T3",
        result_payload_ref=(
            "github://worker-results/result-payload@blob"
            if is_result
            else None
        ),
        result_payload_sha256=("b" * 64 if is_result else None),
        evidence_refs=("evidence:worker-output",),
        reason=reason,
        wait_key=wait_key,
        children=tuple(children),
    )


class FixedValidator:
    def __init__(self, *, passed: bool) -> None:
        self.passed = passed
        self.calls = 0

    def validate(self, publication, packet_source):
        self.calls += 1
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=self.passed,
            evidence_ref=(
                "validator-evidence:"
                f"{publication.publication_id}"
            ),
            observed_at="T4",
        )


class WorkerResultIntakeTests(unittest.TestCase):
    def test_result_completes_only_after_independent_validation(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        validator = FixedValidator(passed=True)
        service = WorkerResultIntakeService(
            runtime=coordinator,
            validators={VALIDATOR_ID: validator},
        )

        outcome = service.ingest(publication(planned))

        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)
        self.assertTrue(outcome.validation.passed)
        self.assertEqual(validator.calls, 1)
        graph = coordinator.snapshot().graph
        process = graph.processes[PROCESS_ID]
        action = graph.operator_actions[planned.action.action_id]
        session = graph.executor_sessions[SLOT_ID]
        self.assertEqual(action.status, OperatorActionState.COMPLETED)
        self.assertEqual(
            action.durable_ack_id,
            "result:1",
        )
        self.assertEqual(session.state, ExecutorSessionState.READY)
        self.assertEqual(session.last_ack_id, "result:1")
        self.assertEqual(
            session.last_ack_packet_sha256,
            planned.packet.packet_sha256,
        )
        self.assertEqual(session.last_ack_session_generation, 0)
        self.assertEqual(len(process.effect_receipts), 1)
        self.assertEqual(
            next(iter(process.effect_receipts.values())).effect_hash,
            "b" * 64,
        )
        self.assertEqual(
            graph.worker_results["result:1"],
            publication(planned),
        )

    def test_next_packet_uses_delta_only_after_exact_durable_session_ack(self):
        coordinator = runtime(contracted=True)
        first = plan_and_prepare(coordinator)
        WorkerResultIntakeService(
            runtime=coordinator,
            validators={VALIDATOR_ID: FixedValidator(passed=True)},
        ).ingest(publication(first))

        second = OperatorDispatchPlanner(
            runtime=coordinator,
            registry=REGISTRY,
        ).plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:worker-result-2",
            action_generation=0,
            process_id=PROCESS_ID_2,
            process_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            executor_id=PROFILE.executor_id,
            packet_input=packet_input(
                process_id=PROCESS_ID_2,
                source_checkpoint="task@result-sha-2",
                evidence_refs=("evidence:input", "evidence:new"),
            ),
            priority_rank=11,
            queue_sequence=2,
            created_at="T5",
        )

        self.assertIn("context_mode=DELTA", second.packet.text)
        self.assertIn(
            f"BASE_PACKET_SHA256={first.packet.packet_sha256}",
            second.packet.text,
        )
        self.assertIn("BASE_CHECKPOINT=task@result-sha", second.packet.text)
        self.assertIn("EVIDENCE_REFS=evidence:new", second.packet.text)
        self.assertNotIn(
            "EVIDENCE_REFS=evidence:input|evidence:new",
            second.packet.text,
        )

    def test_validator_failure_returns_repair_ready(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        validator = FixedValidator(passed=False)
        outcome = WorkerResultIntakeService(
            runtime=coordinator,
            validators={VALIDATOR_ID: validator},
        ).ingest(publication(planned))

        self.assertEqual(
            outcome.process_state,
            ProcessState.READY_TO_RESUME,
        )
        process = coordinator.snapshot().graph.processes[PROCESS_ID]
        self.assertTrue(process.repair_required)
        self.assertFalse(process.validations[-1].passed)

    def test_exact_publication_replay_is_idempotent(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        validator = FixedValidator(passed=True)
        service = WorkerResultIntakeService(
            runtime=coordinator,
            validators={VALIDATOR_ID: validator},
        )
        item = publication(planned)

        first = service.ingest(item)
        version = coordinator.snapshot().version
        second = service.ingest(item)

        self.assertEqual(first.process_state, ProcessState.COMPLETED)
        self.assertEqual(second.process_state, ProcessState.COMPLETED)
        self.assertEqual(validator.calls, 1)
        self.assertEqual(coordinator.snapshot().version, version)

    def test_too_large_decomposes_and_preserves_inherited_obligations(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        item = publication(
            planned,
            kind=WorkerResultKind.TOO_LARGE,
            reason="two independent evidence streams",
            children=(
                WorkerChildProposal(
                    process_id=f"{PROCESS_ID}.A",
                    objective="Investigate stream A.",
                    mandatory_constraints=("screen first",),
                    provenance_refs=("stream:A",),
                ),
                WorkerChildProposal(
                    process_id=f"{PROCESS_ID}.B",
                    objective="Investigate stream B.",
                    provenance_refs=("stream:B",),
                ),
            ),
        )

        outcome = WorkerResultIntakeService(
            runtime=coordinator,
        ).ingest(item)

        self.assertEqual(
            outcome.process_state,
            ProcessState.WAITING_DEPENDENCIES,
        )
        graph = coordinator.snapshot().graph
        parent = graph.processes[PROCESS_ID]
        self.assertEqual(
            parent.disposition,
            WorkDisposition.TOO_LARGE,
        )
        self.assertEqual(
            set(parent.children),
            {f"{PROCESS_ID}.A", f"{PROCESS_ID}.B"},
        )
        for child_id in parent.children:
            contract = graph.processes[child_id].work_contract
            self.assertIsNotNone(contract)
            assert contract is not None
            self.assertIn(
                "no write effects",
                contract.mandatory_constraints,
            )
            self.assertIn(
                "root:provenance",
                contract.provenance_refs,
            )
            self.assertIn(
                "scope:proposal-only",
                contract.authority_refs,
            )
            self.assertIn(
                VALIDATOR_ID,
                contract.validator_contracts,
            )

    def test_intrinsically_difficult_releases_for_stronger_executor(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)

        outcome = WorkerResultIntakeService(
            runtime=coordinator,
        ).ingest(
            publication(
                planned,
                kind=WorkerResultKind.INTRINSICALLY_DIFFICULT,
                reason="coupled residual decision exceeds current tier",
            )
        )

        self.assertEqual(
            outcome.process_state,
            ProcessState.READY_TO_RESUME,
        )
        process = coordinator.snapshot().graph.processes[PROCESS_ID]
        self.assertEqual(
            process.disposition,
            WorkDisposition.INTRINSICALLY_DIFFICULT,
        )
        self.assertIsNone(process.worker_id)
        self.assertIsNone(process.lease_id)
        self.assertEqual(process.children, ())

    def test_wait_external_enters_event_wait_without_reasoning_poll(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)

        outcome = WorkerResultIntakeService(
            runtime=coordinator,
        ).ingest(
            publication(
                planned,
                kind=WorkerResultKind.WAIT_EXTERNAL,
                wait_key="ci:run:123",
            )
        )

        self.assertEqual(
            outcome.process_state,
            ProcessState.WAITING_EXTERNAL,
        )
        process = coordinator.snapshot().graph.processes[PROCESS_ID]
        self.assertEqual(process.wait_key, "ci:run:123")
        self.assertIsNone(process.worker_id)
        self.assertIsNone(process.lease_id)

    def test_process_recovery_rejects_late_worker_publication(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        coordinator.recover(
            PROCESS_ID,
            expected_generation=0,
            reason="worker_session_lost",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "worker_result_action_not_awaiting_ack|"
            "worker_result_action_binding_mismatch|"
            "worker_result_process_binding_mismatch",
        ):
            WorkerResultIntakeService(
                runtime=coordinator,
                validators={
                    VALIDATOR_ID: FixedValidator(passed=True)
                },
            ).ingest(publication(planned))

        self.assertNotIn(
            "result:1",
            coordinator.snapshot().graph.worker_results,
        )

    def test_result_state_round_trip_does_not_store_chat_transcript(self):
        coordinator = runtime(contracted=True)
        planned = plan_and_prepare(coordinator)
        WorkerResultIntakeService(
            runtime=coordinator,
            validators={VALIDATOR_ID: FixedValidator(passed=True)},
        ).ingest(publication(planned))

        raw = dumps_work_graph(coordinator.snapshot().graph)
        restored = loads_work_graph(raw)

        self.assertEqual(
            restored,
            coordinator.snapshot().graph,
        )
        self.assertNotIn("BEGIN_PAYLOAD", raw)
        self.assertNotIn(planned.packet.text, raw)


class WorkerResultJsonTests(unittest.TestCase):
    def _raw(self):
        return json.dumps(
            {
                "publication_id": "json-result-1",
                "action_id": "action:json",
                "action_generation": 2,
                "process_id": "process:json",
                "process_generation": 3,
                "executor_id": "OPENAI_CHAT_INSTANT_CURRENT",
                "worker_slot_id": "instant-general-1",
                "session_generation": 4,
                "packet_sha256": "c" * 64,
                "kind": "RESULT",
                "observed_at": "2026-11-15T17:00:00Z",
                "result_payload_ref": "github://result@blob",
                "result_payload_sha256": "d" * 64,
                "evidence_refs": ["github://evidence@blob"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def test_parser_binds_exact_source_bytes_hash(self):
        raw = self._raw()
        parsed = parse_worker_result_json(
            raw,
            source_ref="github://worker-result@blob",
        )

        self.assertEqual(parsed.publication_id, "json-result-1")
        self.assertEqual(parsed.kind, WorkerResultKind.RESULT)
        import hashlib
        self.assertEqual(
            parsed.source_sha256,
            hashlib.sha256(raw).hexdigest(),
        )

    def test_unknown_authority_field_is_rejected(self):
        payload = json.loads(self._raw().decode("utf-8"))
        payload["authority_decision"] = "ALLOW"
        raw = json.dumps(payload).encode("utf-8")

        with self.assertRaisesRegex(
            WorkerResultJsonError,
            "worker_result_unknown_fields:authority_decision",
        ):
            parse_worker_result_json(
                raw,
                source_ref="github://worker-result@blob",
            )


if __name__ == "__main__":
    unittest.main()
