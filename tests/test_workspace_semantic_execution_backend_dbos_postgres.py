"""Dedicated DBOS + PostgreSQL integration spike.

Ordinary repository validation skips this module unless
SEMANTIC_EXECUTION_INTEGRATION=1. The dedicated semantic-execution workflow
installs pinned DBOS/PostgreSQL dependencies and supplies a disposable database.
"""
from __future__ import annotations

import ast
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import textwrap
import time
from threading import Thread
import unittest
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    DBOSDurableRuntime,
    FakeClock,
    GitHubCandidateEventService,
    GitHubCandidateObservation,
    ImmutableWorkerResultCandidate,
    PostgresEventLedger,
    PostgresStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.application import (  # noqa: E402
    DurableOperatorPacketMaterializer,
    ExecutorDispatchCoordinator,
    ExecutorRegistry,
    OperatorActionService,
    OperatorDispatchPlanner,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    ProductionSchedulerService,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutionRequirement,
    ExecutorSessionState,
    InvocationMode,
    OperatorAckMode,
    OperatorAction,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    PrivacyClass,
    ProcessState,
    SchedulerDispatchSpec,
    SchedulerOperatorSpec,
    SchedulerPacketSpec,
    SessionMode,
    ValidationResult,
    WorkerResultKind,
    WorkerResultPublication,
)
from workspace_semantic_execution.operator_bridge_server import (  # noqa: E402
    OperatorBridgeServerConfig,
    build_operator_bridge_server,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    DurableWorkConflict,
    DurableWorkRequest,
    DurableWorkState,
    RuntimeEvent,
    StateConflict,
)


RUN_INTEGRATION = os.environ.get("SEMANTIC_EXECUTION_INTEGRATION") == "1"
POSTGRES_DSN = os.environ.get("SEMANTIC_EXECUTION_POSTGRES_DSN", "")
DBOS_DSN = os.environ.get("DBOS_SYSTEM_DATABASE_URL", "")


@unittest.skipUnless(
    RUN_INTEGRATION and POSTGRES_DSN,
    "dedicated semantic-execution PostgreSQL integration only",
)
class PostgresAdapterIntegrationTests(unittest.TestCase):
    def test_state_store_cas_survives_adapter_reinstantiation(self):
        state_key = f"state-{uuid.uuid4()}"
        first_store = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("R")]
        )
        initialized = first_store.initialize(graph)
        self.assertEqual(initialized.version, 0)

        stale = first_store.load()
        claimed = DomainKernel.claim(
            stale.graph,
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        current = first_store.compare_and_swap(
            expected_version=stale.version,
            graph=claimed,
        )
        self.assertEqual(current.version, 1)

        restarted_store = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        reread = restarted_store.load()
        self.assertEqual(reread.version, 1)
        self.assertEqual(reread.graph.processes["R"].worker_id, "W1")

        with self.assertRaises(StateConflict):
            restarted_store.compare_and_swap(
                expected_version=stale.version,
                graph=stale.graph,
            )

    def test_persistent_session_slot_survives_adapter_reinstantiation(self):
        state_key = f"session-{uuid.uuid4()}"
        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph([DomainKernel.create_process("R")])
        )
        broker1 = PersistentExecutorSessionBroker(coordinator1)
        profile = openai_chat_instant_current_profile()
        broker1.ensure_session(
            profile=profile,
            slot_id="instant-slot",
            session_id="session-a",
        )
        broker1.bind(
            profile=profile,
            slot_id="instant-slot",
            expected_session_generation=0,
            process_id="R",
            process_generation=0,
            packet_sha256="a" * 64,
        )

        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        restored = coordinator2.snapshot().graph.executor_sessions["instant-slot"]
        self.assertEqual(restored.state, ExecutorSessionState.BOUND)
        self.assertEqual(restored.session_generation, 0)
        self.assertEqual(restored.bound_process_id, "R")
        self.assertEqual(restored.bound_packet_sha256, "a" * 64)

        recovered = coordinator2.recover(
            "R",
            expected_generation=0,
            reason="restart-fence",
        )
        fenced = recovered.graph.executor_sessions["instant-slot"]
        self.assertEqual(
            fenced.state,
            ExecutorSessionState.NEEDS_REPLACEMENT,
        )
        self.assertEqual(fenced.session_generation, 1)
        self.assertIsNone(fenced.bound_process_id)

    def test_operator_action_queue_survives_adapter_reinstantiation(self):
        state_key = f"operator-action-{uuid.uuid4()}"
        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph([DomainKernel.create_process("R")])
        )
        broker = PersistentExecutorSessionBroker(coordinator1)
        profile = openai_chat_instant_current_profile()
        broker.ensure_session(
            profile=profile,
            slot_id="instant-slot",
            session_id="session-a",
        )
        broker.bind(
            profile=profile,
            slot_id="instant-slot",
            expected_session_generation=0,
            process_id="R",
            process_generation=0,
            packet_sha256="a" * 64,
        )
        service1 = OperatorActionService(runtime=coordinator1)
        service1.enqueue(
            OperatorAction(
                action_id="action-1",
                generation=0,
                action_type=OperatorActionType.SERVICE_EXISTING,
                status=OperatorActionState.QUEUED,
                priority_rank=10,
                queue_sequence=1,
                created_at="T0",
                task_id="task",
                reasoning_process_id="R",
                process_generation=0,
                worker_slot_id="instant-slot",
                session_generation=0,
                executor_id=profile.executor_id,
                payload_ref="semantic-packet://R/0",
                payload_sha256="a" * 64,
                human_requirement=OperatorHumanRequirement.PASTE_AND_SUBMIT,
                ack_mode=OperatorAckMode.DURABLE_EVENT,
                post_local_success=OperatorPostLocalSuccess.AWAIT_DURABLE_ACK,
            )
        )

        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        restored = coordinator2.snapshot().graph.operator_actions["action-1"]
        self.assertEqual(restored.status, OperatorActionState.QUEUED)
        self.assertEqual(restored.worker_slot_id, "instant-slot")
        self.assertEqual(restored.payload_sha256, "a" * 64)

        claimed = coordinator2.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim-1",
            claimed_at="T1",
            expires_at="T2",
        )
        self.assertEqual(
            claimed.graph.operator_actions["action-1"].status,
            OperatorActionState.CLAIMED_LOCAL,
        )

    def test_packet_source_and_operator_dispatch_survive_adapter_reinstantiation(self):
        state_key = f"packet-{uuid.uuid4()}"
        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("packet-process")]
            )
        )
        profile = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((profile,))
        broker = PersistentExecutorSessionBroker(coordinator1)
        broker.ensure_session(
            profile=profile,
            slot_id="packet-slot",
            session_id="packet-session",
        )
        planned = OperatorDispatchPlanner(
            runtime=coordinator1,
            registry=registry,
        ).plan_service_existing(
            task_id="task:packet",
            action_id="action:packet",
            action_generation=0,
            process_id="packet-process",
            process_generation=0,
            worker_slot_id="packet-slot",
            session_generation=0,
            executor_id=profile.executor_id,
            packet_input=PacketCompilationInput(
                process_id="packet-process",
                source_checkpoint="checkpoint:packet",
                objective="Resume from durable typed packet state.",
                constraints=("no packet text at rest",),
                evidence_refs=("evidence:packet",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("report-result",),
                validator_contract="validator:packet",
                next_safe_boundary="return typed result",
            ),
            priority_rank=10,
            queue_sequence=1,
            created_at="T0",
        )

        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        restored = coordinator2.snapshot().graph
        action = restored.operator_actions["action:packet"]
        source = restored.packet_sources[action.payload_ref]

        self.assertEqual(source, planned.packet_source)
        self.assertEqual(
            source.packet_sha256,
            planned.packet.packet_sha256,
        )
        materialized = DurableOperatorPacketMaterializer(
            runtime=coordinator2,
            registry=registry,
        ).materialize(action)
        self.assertEqual(materialized, planned.packet)

    def test_production_operator_bridge_server_claims_postgres_backed_packet(self):
        state_key = f"server-{uuid.uuid4()}"
        store = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator = RuntimeCoordinator(
            state_store=store,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("server-process")]
            )
        )
        profile = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((profile,))
        broker = PersistentExecutorSessionBroker(coordinator)
        broker.ensure_session(
            profile=profile,
            slot_id="server-slot",
            session_id="server-session",
        )
        planned = OperatorDispatchPlanner(
            runtime=coordinator,
            registry=registry,
        ).plan_service_existing(
            task_id="task:server",
            action_id="action:server",
            action_generation=0,
            process_id="server-process",
            process_generation=0,
            worker_slot_id="server-slot",
            session_generation=0,
            executor_id=profile.executor_id,
            packet_input=PacketCompilationInput(
                process_id="server-process",
                source_checkpoint="checkpoint:server",
                objective="Serve one exact durable packet.",
                constraints=("localhost backend only",),
                evidence_refs=("evidence:server",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("report-result",),
                validator_contract="validator:server",
                next_safe_boundary="return typed result",
            ),
            priority_rank=1,
            queue_sequence=1,
            created_at="T0",
        )

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = int(probe.getsockname()[1])
        self.assertGreaterEqual(port, 1024)

        identity = "operator@example.invalid"
        server = build_operator_bridge_server(
            OperatorBridgeServerConfig(
                postgres_dsn=POSTGRES_DSN,
                expected_tailscale_login=identity,
                state_key=state_key,
                port=port,
            )
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status_request = Request(
                f"http://127.0.0.1:{port}/operator-bridge/v1/status",
                headers={"Tailscale-User-Login": identity},
                method="GET",
            )
            with urlopen(status_request, timeout=2) as response:
                status = json.loads(response.read().decode("utf-8"))
            self.assertEqual(status["readyManualCycles"], 1)
            self.assertEqual(status["sentUnconfirmed"], 0)

            body = json.dumps(
                {
                    "helperInstanceId": "integration-helper",
                    "claimId": "integration-claim",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                }
            ).encode("utf-8")
            claim_request = Request(
                f"http://127.0.0.1:{port}/operator-bridge/v1/actions/claim",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Tailscale-User-Login": identity,
                },
                method="POST",
            )
            with urlopen(claim_request, timeout=2) as response:
                claimed = json.loads(response.read().decode("utf-8"))
            self.assertEqual(claimed["actionId"], "action:server")
            self.assertEqual(
                claimed["payloadSha256"],
                planned.packet.packet_sha256,
            )
            self.assertEqual(
                claimed["packetText"],
                planned.packet.text,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_instant_candidate_full_loop_survives_postgres_restart(self):
        state_key = f"instant-e2e-{uuid.uuid4()}"
        process_id = "instant-postgres-process"
        slot_id = "instant-postgres-slot"
        action_id = "action:instant-postgres"
        validator_id = "validator:instant-postgres"
        target_ref = (
            "github-candidate://adamtrott78/workspace-control/"
            "worker-results/candidates/instant-postgres.json"
        )
        identity = "operator@example.invalid"

        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process(process_id)]
            )
        )
        profile = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((profile,))
        PersistentExecutorSessionBroker(coordinator1).ensure_session(
            profile=profile,
            slot_id=slot_id,
            session_id="instant-postgres-session",
        )
        planned = OperatorDispatchPlanner(
            runtime=coordinator1,
            registry=registry,
        ).plan_service_existing(
            task_id="task:instant-postgres",
            action_id=action_id,
            action_generation=0,
            process_id=process_id,
            process_generation=0,
            worker_slot_id=slot_id,
            session_generation=0,
            executor_id=profile.executor_id,
            packet_input=PacketCompilationInput(
                process_id=process_id,
                source_checkpoint="checkpoint:instant-postgres",
                objective="Complete the durable Instant candidate loop.",
                constraints=("candidate-only publication",),
                evidence_refs=("evidence:instant-postgres",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("publish-candidate-result",),
                validator_contract=validator_id,
                output_schema="WORKER_RESULT_V1",
                next_safe_boundary="publish immutable candidate",
            ),
            priority_rank=1,
            queue_sequence=1,
            created_at="T0",
            result_publication_target_ref=target_ref,
        )

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = int(probe.getsockname()[1])
        server = build_operator_bridge_server(
            OperatorBridgeServerConfig(
                postgres_dsn=POSTGRES_DSN,
                expected_tailscale_login=identity,
                state_key=state_key,
                port=port,
            )
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            claim_body = json.dumps(
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-instant-postgres",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                }
            ).encode("utf-8")
            claim_request = Request(
                (
                    f"http://127.0.0.1:{port}/"
                    "operator-bridge/v1/actions/claim"
                ),
                data=claim_body,
                headers={
                    "Content-Type": "application/json",
                    "Tailscale-User-Login": identity,
                },
                method="POST",
            )
            with urlopen(claim_request, timeout=2) as response:
                claimed = json.loads(response.read().decode("utf-8"))
            self.assertEqual(claimed["actionId"], action_id)
            self.assertEqual(
                claimed["packetText"],
                planned.packet.text,
            )

            prepared_body = json.dumps(
                {
                    "generation": 0,
                    "workerSlotId": slot_id,
                    "sessionGeneration": 0,
                }
            ).encode("utf-8")
            prepared_request = Request(
                (
                    f"http://127.0.0.1:{port}/"
                    "operator-bridge/v1/actions/"
                    f"{quote(action_id, safe='')}/local-prepared"
                ),
                data=prepared_body,
                headers={
                    "Content-Type": "application/json",
                    "Tailscale-User-Login": identity,
                },
                method="POST",
            )
            with urlopen(prepared_request, timeout=2) as response:
                prepared = json.loads(response.read().decode("utf-8"))
            self.assertEqual(
                prepared["status"],
                "AWAITING_DURABLE_ACK",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )

        class Validator:
            def validate(self, publication, packet_source):
                self.packet_sha256 = packet_source.packet_sha256
                return ValidationResult(
                    validator_id=validator_id,
                    passed=True,
                    evidence_ref="evidence:instant-postgres-valid",
                    observed_at="T5",
                )

        contract = planned.packet_source.result_publication
        self.assertIsNotNone(contract)
        assert contract is not None
        candidate_bytes = json.dumps(
            {
                "publication_id": contract.publication_id,
                "action_id": action_id,
                "action_generation": 0,
                "process_id": process_id,
                "process_generation": 0,
                "executor_id": profile.executor_id,
                "worker_slot_id": slot_id,
                "session_generation": 0,
                "packet_sha256": planned.packet.packet_sha256,
                "kind": "RESULT",
                "observed_at": "T4",
                "result_payload_ref": (
                    "github://instant-postgres-result@blob"
                ),
                "result_payload_sha256": "e" * 64,
                "evidence_refs": (
                    ["github://instant-postgres-evidence@blob"]
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        validator = Validator()
        outcome = WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=coordinator2,
                validators={validator_id: validator},
            )
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=target_ref,
                immutable_revision="f" * 40,
                raw_bytes=candidate_bytes,
            )
        )

        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)
        self.assertEqual(
            validator.packet_sha256,
            planned.packet.packet_sha256,
        )
        store3 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        restored = store3.load().graph
        self.assertEqual(
            restored.processes[process_id].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            restored.operator_actions[action_id].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            restored.executor_sessions[slot_id].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(
            restored.worker_results[
                contract.publication_id
            ].source_ref,
            f"{target_ref}@{'f' * 40}",
        )

    def test_worker_result_intake_survives_postgres_adapter_reinstantiation(self):
        state_key = f"result-{uuid.uuid4()}"
        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("result-process")]
            )
        )
        profile = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((profile,))
        PersistentExecutorSessionBroker(coordinator1).ensure_session(
            profile=profile,
            slot_id="result-slot",
            session_id="result-session",
        )
        planned = OperatorDispatchPlanner(
            runtime=coordinator1,
            registry=registry,
        ).plan_service_existing(
            task_id="task:result",
            action_id="action:result",
            action_generation=0,
            process_id="result-process",
            process_generation=0,
            worker_slot_id="result-slot",
            session_generation=0,
            executor_id=profile.executor_id,
            packet_input=PacketCompilationInput(
                process_id="result-process",
                source_checkpoint="checkpoint:result",
                objective="Return a durable result publication.",
                constraints=("no consumer UI scraping",),
                evidence_refs=("evidence:result-input",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("publish-worker-result",),
                validator_contract="validator:result-integration",
                next_safe_boundary="publish immutable result",
            ),
            priority_rank=1,
            queue_sequence=1,
            created_at="T0",
        )
        coordinator1.claim_next_operator_action(
            helper_instance_id="integration-helper",
            claim_id="result-claim",
            claimed_at="T1",
            expires_at="T2",
        )
        coordinator1.record_operator_action_local_prepared(
            action_id="action:result",
            generation=0,
            worker_slot_id="result-slot",
            session_generation=0,
            observed_at="T1.5",
        )

        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )

        class Validator:
            def validate(self, publication, packet_source):
                self.last_packet_sha256 = packet_source.packet_sha256
                return ValidationResult(
                    validator_id="validator:result-integration",
                    passed=True,
                    evidence_ref="evidence:validated-result",
                    observed_at="T4",
                )

        validator = Validator()
        item = WorkerResultPublication(
            publication_id="publication:result",
            source_ref="github://worker-result@immutable-blob",
            source_sha256="a" * 64,
            action_id="action:result",
            action_generation=0,
            process_id="result-process",
            process_generation=0,
            executor_id=profile.executor_id,
            worker_slot_id="result-slot",
            session_generation=0,
            packet_sha256=planned.packet.packet_sha256,
            kind=WorkerResultKind.RESULT,
            observed_at="T3",
            result_payload_ref="github://result-payload@immutable-blob",
            result_payload_sha256="b" * 64,
            evidence_refs=("evidence:worker-result",),
        )
        outcome = WorkerResultIntakeService(
            runtime=coordinator2,
            validators={
                "validator:result-integration": validator
            },
        ).ingest(item)

        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)
        self.assertEqual(
            validator.last_packet_sha256,
            planned.packet.packet_sha256,
        )

        store3 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        restored = store3.load().graph
        self.assertEqual(
            restored.worker_results[item.publication_id],
            item,
        )
        self.assertEqual(
            restored.operator_actions["action:result"].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            restored.executor_sessions["result-slot"].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(
            restored.processes["result-process"].state,
            ProcessState.COMPLETED,
        )

    def test_production_scheduler_candidate_loop_survives_postgres_restarts(self):
        state_key = f"scheduler-{uuid.uuid4()}"
        process_id = "scheduler-postgres-process"
        slot_id = "scheduler-postgres-slot"
        dispatch_id = "scheduler-postgres-dispatch"
        action_id = "action:scheduler-postgres"
        validator_id = "validator:scheduler-postgres"
        repository = "adamtrott78/workspace-control"
        candidate_ref = "refs/heads/worker-result-candidates-v1"
        candidate_path = (
            "worker-results/candidates/"
            "scheduler-postgres-process.json"
        )

        store1 = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        runtime1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        runtime1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process(process_id)]
            )
        )
        profile = openai_chat_instant_current_profile()
        PersistentExecutorSessionBroker(runtime1).ensure_session(
            profile=profile,
            slot_id=slot_id,
            session_id="scheduler-postgres-session",
        )
        dispatcher1 = ExecutorDispatchCoordinator(
            runtime=runtime1,
            registry=ExecutorRegistry((profile,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator(),
            executor_ports={},
            validators={},
        )
        scheduler1 = ProductionSchedulerService(
            runtime=runtime1,
            dispatcher=dispatcher1,
        )
        spec = SchedulerDispatchSpec(
            dispatch_id=dispatch_id,
            process_id=process_id,
            process_generation=0,
            requirement_id="requirement:scheduler-postgres",
            requirement=ExecutionRequirement(
                required_capabilities=frozenset(
                    {"reasoning.bounded"}
                ),
                allowed_invocation_modes=frozenset(
                    {InvocationMode.HUMAN_ASSISTED}
                ),
                allowed_session_modes=frozenset(
                    {SessionMode.PERSISTENT_CHAT}
                ),
                privacy_class=PrivacyClass.INTERNAL,
                require_human_launch=True,
            ),
            packet=SchedulerPacketSpec(
                source_checkpoint="scheduler-postgres@0",
                objective="Return one immutable candidate.",
                constraints=("candidate-only publication",),
                evidence_refs=("evidence:scheduler-postgres",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("publish-candidate-result",),
                validator_contract=validator_id,
                output_schema="WORKER_RESULT_V1",
                next_safe_boundary="publish immutable candidate JSON",
            ),
            operator=SchedulerOperatorSpec(
                task_id="scheduler-postgres-task",
                action_id=action_id,
                action_generation=0,
                worker_slot_id=slot_id,
                session_generation=0,
                priority_rank=10,
                queue_sequence=1,
                created_at="T0",
                candidate_repository=repository,
                candidate_ref=candidate_ref,
                candidate_path=candidate_path,
            ),
        )
        scheduler1.register(spec)

        store2 = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        runtime2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        dispatcher2 = ExecutorDispatchCoordinator(
            runtime=runtime2,
            registry=ExecutorRegistry((profile,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator(),
            executor_ports={},
            validators={},
        )
        tick = ProductionSchedulerService(
            runtime=runtime2,
            dispatcher=dispatcher2,
        ).run_once()
        self.assertEqual(tick.outcome, "DISPATCHED")
        self.assertEqual(tick.dispatch_id, dispatch_id)
        self.assertEqual(tick.dispatch_mode, "OPERATOR_ACTION")

        runtime2.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="scheduler-postgres-claim",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime2.record_operator_action_local_prepared(
            action_id=action_id,
            generation=0,
            worker_slot_id=slot_id,
            session_generation=0,
            observed_at="T1.5",
        )
        graph2 = runtime2.snapshot().graph
        action = graph2.operator_actions[action_id]
        source = graph2.packet_sources[action.payload_ref]
        publication_contract = source.result_publication
        self.assertIsNotNone(publication_contract)
        assert publication_contract is not None

        candidate_bytes = json.dumps(
            {
                "publication_id": (
                    publication_contract.publication_id
                ),
                "action_id": action_id,
                "action_generation": 0,
                "process_id": process_id,
                "process_generation": 0,
                "executor_id": profile.executor_id,
                "worker_slot_id": slot_id,
                "session_generation": 0,
                "packet_sha256": action.payload_sha256,
                "kind": "RESULT",
                "observed_at": "T3",
                "result_payload_ref": (
                    "github://scheduler-postgres-result@blob"
                ),
                "result_payload_sha256": "a" * 64,
                "evidence_refs": [
                    "github://scheduler-postgres-evidence@blob"
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        commit_sha = "b" * 40

        class Reader:
            def read_exact(
                self,
                *,
                repository: str,
                ref: str,
                path: str,
                commit_sha: str,
            ):
                return GitHubCandidateObservation(
                    repository=repository,
                    ref=ref,
                    path=path,
                    commit_sha=commit_sha,
                    content=candidate_bytes,
                )

        class Validator:
            def validate(self, publication, packet_source):
                return ValidationResult(
                    validator_id=validator_id,
                    passed=True,
                    evidence_ref=(
                        "validated:scheduler-postgres:"
                        f"{publication.source_sha256}"
                    ),
                    observed_at="T4",
                )

        store3 = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        runtime3 = RuntimeCoordinator(
            state_store=store3,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=20),
        )
        outcome = GitHubCandidateEventService(
            runtime=runtime3,
            intake=WorkerResultIntakeService(
                runtime=runtime3,
                validators={validator_id: Validator()},
            ),
            reader=Reader(),
        ).ingest(
            dispatch_id=dispatch_id,
            commit_sha=commit_sha,
        )
        self.assertEqual(
            outcome.process_state,
            ProcessState.COMPLETED,
        )

        store4 = PostgresStateStore(
            POSTGRES_DSN,
            state_key=state_key,
        )
        restored = store4.load().graph
        self.assertEqual(
            restored.scheduler_dispatches[dispatch_id],
            spec,
        )
        self.assertEqual(
            restored.processes[process_id].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            restored.operator_actions[action_id].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            restored.executor_sessions[slot_id].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(len(restored.worker_results), 1)

    def test_external_event_is_immutable_and_visible_after_restart(self):
        ledger1 = PostgresEventLedger(POSTGRES_DSN)
        event_id = f"event-{uuid.uuid4()}"
        wait_key = f"wait-{uuid.uuid4()}"
        event = RuntimeEvent(
            event_id=event_id,
            wait_key=wait_key,
            observed_at="T1",
            payload_ref="artifact:1",
        )
        self.assertTrue(ledger1.publish_event(event))
        self.assertFalse(ledger1.publish_event(event))

        ledger2 = PostgresEventLedger(POSTGRES_DSN)
        self.assertEqual(
            ledger2.find_event(wait_key=wait_key),
            event,
        )

        with self.assertRaises(ValueError):
            ledger2.publish_event(
                RuntimeEvent(
                    event_id=event_id,
                    wait_key=wait_key,
                    observed_at="DIFFERENT",
                    payload_ref="artifact:1",
                )
            )

    def test_semantic_wait_resumes_after_process_restart_without_polling(self):
        state_key = f"restart-{uuid.uuid4()}"
        wait_key = f"experiment-{uuid.uuid4()}"
        event_id = f"event-{uuid.uuid4()}"

        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        ledger1 = PostgresEventLedger(POSTGRES_DSN)
        telemetry1 = RecordingTelemetry()
        coordinator1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=ledger1,
            telemetry=telemetry1,
            clock=FakeClock(),
        )
        coordinator1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("R")]
            )
        )
        coordinator1.claim(
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        coordinator1.start(
            "R",
            lease_id="L",
            expected_generation=0,
        )
        waiting = coordinator1.wait_external(
            "R",
            wait_key=wait_key,
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(
            waiting.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        # Recreate every application object except the durable PostgreSQL data.
        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        ledger2 = PostgresEventLedger(POSTGRES_DSN)
        telemetry2 = RecordingTelemetry()
        coordinator2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=ledger2,
            telemetry=telemetry2,
            clock=FakeClock(seconds=10),
        )
        before_event = coordinator2.reconcile_published_events()
        self.assertEqual(
            before_event.graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )

        resumed = coordinator2.publish_external_event(
            RuntimeEvent(
                event_id=event_id,
                wait_key=wait_key,
                observed_at="T10",
                payload_ref="experiment:result",
            )
        )
        self.assertEqual(
            resumed.graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )


@unittest.skipUnless(
    RUN_INTEGRATION and DBOS_DSN,
    "dedicated semantic-execution DBOS process-recovery integration only",
)
class DBOSProcessRecoveryIntegrationTests(unittest.TestCase):
    def test_inflight_workflow_recovers_after_abrupt_process_death(self):
        work_id = f"dbos-recovery-{uuid.uuid4()}"
        queue_name = "semantic-execution-recovery"
        probe = textwrap.dedent(
            r"""
            import json
            import os
            import sys
            import time

            from dbos import DBOS, DBOSConfig
            from workspace_semantic_execution.adapters import DBOSDurableRuntime
            from workspace_semantic_execution.ports import (
                DurableWorkRequest,
                DurableWorkState,
            )

            mode = sys.argv[1]
            dsn = sys.argv[2]
            work_id = sys.argv[3]
            queue_name = sys.argv[4]

            def recoverable_workflow(envelope):
                DBOS.sleep(5.0)
                return {
                    "result_ref": (
                        "recovered:"
                        + envelope["work_kind"]
                        + ":"
                        + str(envelope["payload"]["value"])
                    )
                }

            workflow_fn = DBOS.workflow()(recoverable_workflow)
            config: DBOSConfig = {
                "name": "workspace-semantic-execution-recovery-probe",
                "application_version": "0.1.0",
                "system_database_url": dsn,
                "dbos_system_schema": "dbos_semantic_execution_recovery_test",
            }
            DBOS(config=config)
            DBOS.launch()
            DBOS.register_queue(queue_name)

            runtime = DBOSDurableRuntime(
                workflow_fn=workflow_fn,
                registered_queues=frozenset({queue_name}),
            )
            request = DurableWorkRequest(
                work_id=work_id,
                work_kind="recovery_probe",
                payload={"value": "v1"},
                queue_name=queue_name,
            )

            if mode == "submit-crash":
                runtime.submit(request)
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    status = runtime.get_status(work_id=work_id)
                    if status is not None and status.state == DurableWorkState.RUNNING:
                        print("PROBE_INFLIGHT=PASS", flush=True)
                        os._exit(23)
                    time.sleep(0.02)
                print("PROBE_INFLIGHT=TIMEOUT", flush=True)
                os._exit(24)

            if mode == "recover":
                deadline = time.monotonic() + 15.0
                while time.monotonic() < deadline:
                    status = runtime.get_status(work_id=work_id)
                    if status is not None and status.state == DurableWorkState.COMPLETED:
                        print(
                            "PROBE_RECOVERED="
                            + json.dumps(
                                {
                                    "work_id": status.work_id,
                                    "state": status.state.value,
                                    "result_ref": status.result_ref,
                                },
                                sort_keys=True,
                            ),
                            flush=True,
                        )
                        DBOS.destroy(destroy_registry=True)
                        raise SystemExit(0)
                    if status is not None and status.state in {
                        DurableWorkState.FAILED,
                        DurableWorkState.CANCELLED,
                    }:
                        print(
                            "PROBE_RECOVERY_TERMINAL_FAILURE="
                            + status.state.value,
                            flush=True,
                        )
                        DBOS.destroy(destroy_registry=True)
                        raise SystemExit(25)
                    time.sleep(0.05)
                print("PROBE_RECOVERY_TIMEOUT", flush=True)
                DBOS.destroy(destroy_registry=True)
                raise SystemExit(26)

            raise SystemExit(27)
            """
        )
        env = os.environ.copy()
        prior_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(SRC)
            if not prior_pythonpath
            else str(SRC) + os.pathsep + prior_pythonpath
        )

        crashed = subprocess.run(
            [
                sys.executable,
                "-c",
                probe,
                "submit-crash",
                DBOS_DSN,
                work_id,
                queue_name,
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(
            crashed.returncode,
            23,
            msg=crashed.stdout + "\n" + crashed.stderr,
        )
        self.assertIn("PROBE_INFLIGHT=PASS", crashed.stdout)

        recovered = subprocess.run(
            [
                sys.executable,
                "-c",
                probe,
                "recover",
                DBOS_DSN,
                work_id,
                queue_name,
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=25,
            check=False,
        )
        self.assertEqual(
            recovered.returncode,
            0,
            msg=recovered.stdout + "\n" + recovered.stderr,
        )
        self.assertIn('"state": "COMPLETED"', recovered.stdout)
        self.assertIn(
            '"result_ref": "recovered:recovery_probe:v1"',
            recovered.stdout,
        )


@unittest.skipUnless(
    RUN_INTEGRATION and POSTGRES_DSN,
    "dedicated semantic-execution PostgreSQL integration only",
)
class E2PostgresRecoveryIntegrationTests(unittest.TestCase):
    """E2-C2: recovery across fresh PostgreSQL-backed app instances."""

    def test_worker_session_and_runtime_loss_recovers_from_postgres(self):
        state_key = f"e2-recovery-{uuid.uuid4()}"
        process_id = "research-iterate-e2.postgres-leaf"
        slot_id = "research-iterate-e2.postgres-slot"
        validator_id = "validator:research-iterate-e2-postgres"
        profile = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((profile,))

        def packet_input():
            return PacketCompilationInput(
                process_id=process_id,
                source_checkpoint="research-iterate-e2@postgres-recovery",
                objective=(
                    "Complete this leaf from durable PostgreSQL state after "
                    "worker, session, and application-runtime replacement."
                ),
                constraints=(
                    "conversation memory is cache only",
                    "stale generations must not mutate durable state",
                    "no manual durable-state relay",
                ),
                evidence_refs=("e2:postgres-recovery-input",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("publish-worker-result",),
                validator_contract=validator_id,
                output_schema="WORKER_RESULT_V1",
                next_safe_boundary="publish immutable candidate result",
            )

        def candidate_bytes(planned, *, result_hash: str) -> bytes:
            contract = planned.packet_source.result_publication
            self.assertIsNotNone(contract)
            assert contract is not None
            return json.dumps(
                {
                    "publication_id": contract.publication_id,
                    "action_id": planned.action.action_id,
                    "action_generation": planned.action.generation,
                    "process_id": process_id,
                    "process_generation": planned.action.process_generation,
                    "executor_id": profile.executor_id,
                    "worker_slot_id": slot_id,
                    "session_generation": planned.action.session_generation,
                    "packet_sha256": planned.packet.packet_sha256,
                    "kind": "RESULT",
                    "observed_at": "T-worker",
                    "result_payload_ref": "e2://postgres-recovery/result",
                    "result_payload_sha256": result_hash,
                    "evidence_refs": ["e2:postgres-replacement-output"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

        class Validator:
            def validate(self, publication, packet_source):
                return ValidationResult(
                    validator_id=validator_id,
                    passed=True,
                    evidence_ref=(
                        "e2-postgres-validation:"
                        f"{publication.publication_id}"
                    ),
                    observed_at="T-validation",
                )

        store1 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        runtime1 = RuntimeCoordinator(
            state_store=store1,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        runtime1.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process(process_id)]
            )
        )
        broker1 = PersistentExecutorSessionBroker(runtime1)
        broker1.ensure_session(
            profile=profile,
            slot_id=slot_id,
            session_id="e2-postgres-session-g0",
        )
        first = OperatorDispatchPlanner(
            runtime=runtime1,
            registry=registry,
        ).plan_service_existing(
            task_id="workspace-semantic-execution-migration-v1",
            action_id="action:e2:postgres:g0",
            action_generation=0,
            process_id=process_id,
            process_generation=0,
            worker_slot_id=slot_id,
            session_generation=0,
            executor_id=profile.executor_id,
            packet_input=packet_input(),
            priority_rank=10,
            queue_sequence=1,
            created_at="T0",
            result_publication_target_ref=(
                "github-candidate://adamtrott78/workspace-control/"
                "worker-results/e2/postgres/g0.json"
            ),
        )
        runtime1.claim_next_operator_action(
            helper_instance_id="e2-postgres-helper",
            claim_id="claim:e2:postgres:g0",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime1.record_operator_action_local_prepared(
            action_id=first.action.action_id,
            generation=0,
            worker_slot_id=slot_id,
            session_generation=0,
            observed_at="T1.5",
        )
        old_candidate = ImmutableWorkerResultCandidate(
            target_ref=first.packet_source.result_publication.target_ref,
            immutable_revision="a" * 40,
            raw_bytes=candidate_bytes(first, result_hash="b" * 64),
        )

        recovered = runtime1.recover(
            process_id,
            expected_generation=0,
            reason="e2_injected_postgres_worker_loss",
        )
        self.assertEqual(
            recovered.graph.processes[process_id].generation,
            1,
        )
        self.assertEqual(
            recovered.graph.processes[process_id].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(
            recovered.graph.executor_sessions[slot_id].state,
            ExecutorSessionState.NEEDS_REPLACEMENT,
        )
        self.assertEqual(
            recovered.graph.executor_sessions[slot_id].session_generation,
            1,
        )
        self.assertEqual(
            recovered.graph.operator_actions[first.action.action_id].status,
            OperatorActionState.STALE,
        )

        # Fresh application objects: only PostgreSQL state survives.
        store2 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        runtime2 = RuntimeCoordinator(
            state_store=store2,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        restored = runtime2.snapshot()
        self.assertEqual(
            restored.graph.processes[process_id].generation,
            1,
        )
        self.assertEqual(
            restored.graph.executor_sessions[slot_id].session_generation,
            1,
        )
        self.assertEqual(
            restored.graph.operator_actions[first.action.action_id].status,
            OperatorActionState.STALE,
        )

        version_before_late = restored.version
        with self.assertRaisesRegex(
            RuntimeError,
            "worker_result_action_not_awaiting_ack|"
            "worker_result_action_binding_mismatch|"
            "worker_result_process_binding_mismatch",
        ):
            WorkerResultCandidateAdapter(
                intake=WorkerResultIntakeService(
                    runtime=runtime2,
                    validators={validator_id: Validator()},
                )
            ).ingest(old_candidate)
        self.assertEqual(runtime2.snapshot().version, version_before_late)
        self.assertEqual(runtime2.snapshot().graph.worker_results, {})

        broker2 = PersistentExecutorSessionBroker(runtime2)
        replacement = broker2.replace(
            slot_id=slot_id,
            expected_session_generation=1,
            session_id="e2-postgres-session-g1",
        )
        self.assertEqual(replacement.state, ExecutorSessionState.READY)

        second = OperatorDispatchPlanner(
            runtime=runtime2,
            registry=registry,
        ).plan_service_existing(
            task_id="workspace-semantic-execution-migration-v1",
            action_id="action:e2:postgres:g1",
            action_generation=0,
            process_id=process_id,
            process_generation=1,
            worker_slot_id=slot_id,
            session_generation=1,
            executor_id=profile.executor_id,
            packet_input=packet_input(),
            priority_rank=10,
            queue_sequence=2,
            created_at="T3",
            result_publication_target_ref=(
                "github-candidate://adamtrott78/workspace-control/"
                "worker-results/e2/postgres/g1.json"
            ),
        )
        self.assertNotEqual(
            first.packet.packet_sha256,
            second.packet.packet_sha256,
        )
        self.assertIn('"process_generation": 1', second.packet.text)
        self.assertIn('"session_generation": 1', second.packet.text)

        runtime2.claim_next_operator_action(
            helper_instance_id="e2-postgres-helper",
            claim_id="claim:e2:postgres:g1",
            claimed_at="T4",
            expires_at="T5",
        )
        runtime2.record_operator_action_local_prepared(
            action_id=second.action.action_id,
            generation=0,
            worker_slot_id=slot_id,
            session_generation=1,
            observed_at="T4.5",
        )
        contract = second.packet_source.result_publication
        self.assertIsNotNone(contract)
        assert contract is not None
        outcome = WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=runtime2,
                validators={validator_id: Validator()},
            )
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=contract.target_ref,
                immutable_revision="c" * 40,
                raw_bytes=candidate_bytes(second, result_hash="d" * 64),
            )
        )
        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)

        # A third fresh application instance must see terminal durable truth.
        store3 = PostgresStateStore(POSTGRES_DSN, state_key=state_key)
        runtime3 = RuntimeCoordinator(
            state_store=store3,
            event_ledger=PostgresEventLedger(POSTGRES_DSN),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=20),
        )
        final = runtime3.snapshot().graph
        self.assertEqual(
            final.processes[process_id].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            final.operator_actions[first.action.action_id].status,
            OperatorActionState.STALE,
        )
        self.assertEqual(
            final.operator_actions[second.action.action_id].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            final.executor_sessions[slot_id].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(
            final.executor_sessions[slot_id].session_generation,
            1,
        )
        self.assertEqual(len(final.worker_results), 1)


@unittest.skipUnless(
    RUN_INTEGRATION and DBOS_DSN,
    "dedicated semantic-execution DBOS integration only",
)
class DBOSDurableRuntimeIntegrationTests(unittest.TestCase):
    queue_name = "semantic-execution-test"

    @classmethod
    def setUpClass(cls) -> None:
        from dbos import DBOS, DBOSConfig  # type: ignore[import-not-found]

        def bounded_dispatch(envelope):
            return {
                "result_ref": (
                    "result:"
                    + envelope["work_kind"]
                    + ":"
                    + str(envelope["payload"].get("value", "none"))
                )
            }

        cls.DBOS = DBOS
        cls.workflow_fn = staticmethod(DBOS.workflow()(bounded_dispatch))
        config: DBOSConfig = {
            "name": "workspace-semantic-execution-spike",
            "application_version": "0.1.0",
            "system_database_url": DBOS_DSN,
            "dbos_system_schema": "dbos_semantic_execution_test",
        }
        DBOS(config=config)
        DBOS.launch()
        DBOS.register_queue(cls.queue_name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.DBOS.destroy(destroy_registry=True)

    def adapter(self) -> DBOSDurableRuntime:
        return DBOSDurableRuntime(
            workflow_fn=self.workflow_fn,
            registered_queues=frozenset({self.queue_name}),
        )

    def wait_terminal(
        self,
        runtime: DBOSDurableRuntime,
        work_id: str,
        *,
        timeout: float = 15.0,
    ):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = runtime.get_status(work_id=work_id)
            if status is not None and status.state in {
                DurableWorkState.COMPLETED,
                DurableWorkState.FAILED,
                DurableWorkState.CANCELLED,
            }:
                return status
            time.sleep(0.05)
        self.fail(f"durable work did not reach terminal state: {work_id}")

    def test_same_work_id_is_idempotent_and_conflicting_input_fails_closed(self):
        runtime = self.adapter()
        work_id = f"dbos-{uuid.uuid4()}"
        request = DurableWorkRequest(
            work_id=work_id,
            work_kind="reasoning_quantum",
            payload={"value": "v1"},
            queue_name=self.queue_name,
        )

        first = runtime.submit(request)
        self.assertEqual(first.work_id, work_id)
        duplicate = runtime.submit(request)
        self.assertEqual(duplicate.work_id, work_id)

        final = self.wait_terminal(runtime, work_id)
        self.assertEqual(final.state, DurableWorkState.COMPLETED)
        self.assertEqual(
            final.result_ref,
            "result:reasoning_quantum:v1",
        )

        conflicting = DurableWorkRequest(
            work_id=work_id,
            work_kind="reasoning_quantum",
            payload={"value": "v2"},
            queue_name=self.queue_name,
        )
        with self.assertRaises(DurableWorkConflict):
            runtime.submit(conflicting)

    def test_unknown_queue_fails_before_dbos_submission(self):
        runtime = self.adapter()
        with self.assertRaises(ValueError):
            runtime.submit(
                DurableWorkRequest(
                    work_id=f"dbos-{uuid.uuid4()}",
                    work_kind="reasoning_quantum",
                    payload={"value": "v"},
                    queue_name="not-registered",
                )
            )

    def test_adapter_never_calls_dbos_recv_for_semantic_external_waits(self):
        path = (
            SRC
            / "workspace_semantic_execution"
            / "adapters"
            / "dbos_runtime.py"
        )
        tree = ast.parse(path.read_text(), filename=str(path))
        recv_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "recv"
        ]
        self.assertEqual(recv_calls, [])


if __name__ == "__main__":
    unittest.main()
