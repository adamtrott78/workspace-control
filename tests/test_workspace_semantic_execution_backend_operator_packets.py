"""Durable packet-source planning/materialization acceptance tests."""
from __future__ import annotations

from pathlib import Path
import json
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
from workspace_semantic_execution.application import (  # noqa: E402
    DecisionRecord,
    DurableOperatorPacketMaterializer,
    ExecutorRegistry,
    FindingRecord,
    OperatorDispatchPlanner,
    PacketCompilationInput,
    QuestionRecord,
    RuntimeCoordinator,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutorSessionState,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
)


PROCESS_ID = "research-iterate.leaf.instant"
SLOT_ID = "instant-slot-packet"
PROFILE = openai_chat_instant_current_profile()
REGISTRY = ExecutorRegistry((PROFILE,))


def runtime() -> RuntimeCoordinator:
    coordinator = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    coordinator.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    coordinator.register_executor_session(
        slot_id=SLOT_ID,
        executor_id=PROFILE.executor_id,
        session_id="chat-session-packet",
    )
    return coordinator


def packet_input(*, objective: str = "Analyze the bounded research leaf."):
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint="research-engine@exact-sha",
        objective=objective,
        findings=(
            FindingRecord(
                finding_id="F1",
                text="Known durable finding.",
                evidence_refs=("evidence:F1",),
            ),
        ),
        decisions=(
            DecisionRecord(
                decision_id="D1",
                decision="Keep the leaf read-only.",
                rationale="Current authority is proposal-only.",
                evidence_refs=("evidence:D1",),
                alternatives=("write-capable path rejected",),
            ),
        ),
        unresolved_questions=(
            QuestionRecord(
                question_id="Q1",
                text="Does the new evidence change the hypothesis?",
            ),
        ),
        constraints=(
            "no write-capable external effect",
            "return typed evidence",
        ),
        evidence_refs=("evidence:root",),
        authority_refs=("scope:proposal-only",),
        allowed_actions=("report-result",),
        validator_contract="validator:research-leaf-v1",
        output_schema="RESEARCH_LEAF_RESULT_V1",
        next_safe_boundary="return result for independent validation",
    )


def planner(coordinator: RuntimeCoordinator) -> OperatorDispatchPlanner:
    return OperatorDispatchPlanner(
        runtime=coordinator,
        registry=REGISTRY,
    )


class DurableOperatorPacketTests(unittest.TestCase):
    def test_plan_is_atomic_and_materializes_exact_packet_from_durable_state(self):
        coordinator = runtime()
        planned = planner(coordinator).plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:instant-leaf",
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

        graph = coordinator.snapshot().graph
        action = graph.operator_actions["action:instant-leaf"]
        source = graph.packet_sources[action.payload_ref]
        session = graph.executor_sessions[SLOT_ID]

        self.assertEqual(action.status, OperatorActionState.QUEUED)
        self.assertEqual(source.packet_sha256, planned.packet.packet_sha256)
        self.assertEqual(source.process_id, PROCESS_ID)
        self.assertEqual(source.executor_id, PROFILE.executor_id)
        self.assertEqual(session.state, ExecutorSessionState.BOUND)
        self.assertEqual(
            session.bound_packet_sha256,
            planned.packet.packet_sha256,
        )

        materialized = DurableOperatorPacketMaterializer(
            runtime=coordinator,
            registry=REGISTRY,
        ).materialize(action)
        self.assertEqual(materialized, planned.packet)

        durable_json = dumps_work_graph(graph)
        self.assertNotIn("BEGIN_PAYLOAD", durable_json)
        self.assertNotIn(planned.packet.text, durable_json)
        self.assertIn(planned.packet.packet_sha256, durable_json)

    def test_exact_retry_is_idempotent(self):
        coordinator = runtime()
        kwargs = dict(
            task_id="task:research-iterate",
            action_id="action:instant-leaf",
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
        first = planner(coordinator).plan_service_existing(**kwargs)
        version_after_first = coordinator.snapshot().version
        second = planner(coordinator).plan_service_existing(**kwargs)

        self.assertEqual(first.packet, second.packet)
        graph = coordinator.snapshot().graph
        self.assertEqual(len(graph.packet_sources), 1)
        self.assertEqual(len(graph.operator_actions), 1)
        self.assertEqual(
            graph.executor_sessions[SLOT_ID].bound_packet_sha256,
            first.packet.packet_sha256,
        )
        self.assertGreaterEqual(
            coordinator.snapshot().version,
            version_after_first,
        )

    def test_recovery_stales_action_fences_session_and_blocks_materialization(self):
        coordinator = runtime()
        planned = planner(coordinator).plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:instant-leaf",
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
        coordinator.recover(
            PROCESS_ID,
            expected_generation=0,
            reason="worker_lost_before_manual_service",
        )

        graph = coordinator.snapshot().graph
        action = graph.operator_actions["action:instant-leaf"]
        session = graph.executor_sessions[SLOT_ID]
        self.assertEqual(action.status, OperatorActionState.STALE)
        self.assertEqual(
            session.state,
            ExecutorSessionState.NEEDS_REPLACEMENT,
        )
        self.assertEqual(session.session_generation, 1)

        with self.assertRaisesRegex(
            RuntimeError,
            "packet_source_stale_process_generation",
        ):
            DurableOperatorPacketMaterializer(
                runtime=coordinator,
                registry=REGISTRY,
            ).materialize(action)

        self.assertEqual(
            graph.packet_sources[planned.packet_source.payload_ref],
            planned.packet_source,
        )

    def test_packet_source_round_trip_preserves_typed_inputs(self):
        coordinator = runtime()
        planned = planner(coordinator).plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:instant-leaf",
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

        restored = loads_work_graph(
            dumps_work_graph(coordinator.snapshot().graph)
        )
        source = restored.packet_sources[
            planned.packet_source.payload_ref
        ]
        self.assertEqual(source, planned.packet_source)
        self.assertEqual(
            source.findings[0].evidence_refs,
            ("evidence:F1",),
        )
        self.assertEqual(
            source.decisions[0].alternatives,
            ("write-capable path rejected",),
        )
        self.assertEqual(
            source.unresolved_questions[0].question_id,
            "Q1",
        )

    def test_github_candidate_packet_prepends_explicit_plugin_call(self):
        coordinator = runtime()
        planned = planner(coordinator).plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:github-publication",
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
            result_publication_target_ref=(
                "github-candidate://adamtrott78/workspace-control/"
                "ref/refs%2Fheads%2Fworker-result-candidates-v1/"
                "path/worker-results%2Fcandidates%2Fresult.json"
            ),
        )

        payload = json.loads(planned.packet.canonical_payload_json)
        self.assertEqual(payload["plugin_calls"], ["@github"])
        self.assertTrue(planned.packet.text.startswith("@github\n"))

        materialized = DurableOperatorPacketMaterializer(
            runtime=coordinator,
            registry=REGISTRY,
        ).materialize(planned.action)
        self.assertEqual(materialized.text, planned.packet.text)

    def test_retire_session_is_durable_and_completes_as_local_action(self):
        coordinator = runtime()
        retire = planner(coordinator).plan_retire_session(
            task_id="task:research-iterate",
            action_id="action:retire-session",
            action_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            executor_id=PROFILE.executor_id,
            priority_rank=1,
            queue_sequence=99,
            created_at="T-retire",
            reason="task_complete",
        )

        graph = coordinator.snapshot().graph
        self.assertEqual(
            graph.executor_sessions[SLOT_ID].state,
            ExecutorSessionState.RETIRED,
        )
        self.assertEqual(retire.action_type, OperatorActionType.RETIRE_SESSION)
        self.assertEqual(
            retire.human_requirement,
            OperatorHumanRequirement.NONE,
        )
        self.assertEqual(
            retire.post_local_success,
            OperatorPostLocalSuccess.COMPLETE_AND_REQUERY,
        )
        self.assertEqual(retire.status, OperatorActionState.QUEUED)

        claimed = coordinator.claim_next_operator_action(
            helper_instance_id="helper",
            claim_id="claim:retire",
            claimed_at="T1",
            expires_at="T2",
        )
        self.assertEqual(
            claimed.graph.operator_actions[retire.action_id].status,
            OperatorActionState.CLAIMED_LOCAL,
        )
        completed = coordinator.record_operator_action_local_prepared(
            action_id=retire.action_id,
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T3",
        )
        self.assertEqual(
            completed.graph.operator_actions[retire.action_id].status,
            OperatorActionState.COMPLETED,
        )

    def test_changed_packet_input_cannot_reuse_bound_session(self):
        coordinator = runtime()
        p = planner(coordinator)
        p.plan_service_existing(
            task_id="task:research-iterate",
            action_id="action:instant-leaf",
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

        with self.assertRaisesRegex(
            RuntimeError,
            "operator_dispatch_process_owned_elsewhere",
        ):
            p.plan_service_existing(
                task_id="task:research-iterate",
                action_id="action:different",
                action_generation=0,
                process_id=PROCESS_ID,
                process_generation=0,
                worker_slot_id=SLOT_ID,
                session_generation=0,
                executor_id=PROFILE.executor_id,
                packet_input=packet_input(
                    objective="Different objective must produce a new packet."
                ),
                priority_rank=11,
                queue_sequence=2,
                created_at="T1",
            )


if __name__ == "__main__":
    unittest.main()
