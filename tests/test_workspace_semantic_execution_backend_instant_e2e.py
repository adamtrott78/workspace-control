"""Complete fake-worker Instant bridge loop acceptance tests."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ImmutableWorkerResultCandidate,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.adapters.operator_bridge_http import (  # noqa: E402
    OperatorBridgeHttpConfig,
    build_operator_bridge_http_server,
)
from workspace_semantic_execution.application import (  # noqa: E402
    DurableOperatorPacketMaterializer,
    ExecutorRegistry,
    OperatorActionService,
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
)


IDENTITY_HEADER = "Tailscale-User-Login"
IDENTITY = "operator@example.invalid"
PROCESS_ID = "instant-e2e-leaf"
SLOT_ID = "instant-e2e-slot"
ACTION_ID = "action:instant-e2e"
VALIDATOR_ID = "validator:instant-e2e"
TARGET_REF = (
    "github-candidate://adamtrott78/workspace-control/"
    "worker-results/candidates/instant-e2e.json"
)
PROFILE = openai_chat_instant_current_profile()
REGISTRY = ExecutorRegistry((PROFILE,))


class PassingValidator:
    def __init__(self) -> None:
        self.calls = 0

    def validate(self, publication, packet_source):
        self.calls += 1
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=True,
            evidence_ref="validator-evidence:instant-e2e",
            observed_at="T5",
        )


def build_runtime():
    runtime = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    PersistentExecutorSessionBroker(runtime).ensure_session(
        profile=PROFILE,
        slot_id=SLOT_ID,
        session_id="chat-session-instant-e2e",
    )
    return runtime


@contextmanager
def running_server(service):
    server = build_operator_bridge_http_server(
        service=service,
        config=OperatorBridgeHttpConfig(
            expected_identity_header=IDENTITY_HEADER,
            expected_identity_value=IDENTITY,
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request_json(base_url, method, path, payload=None):
    data = None
    headers = {IDENTITY_HEADER: IDENTITY}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=2) as response:
        raw = response.read()
        return response.status, (
            None if not raw else json.loads(raw.decode("utf-8"))
        )


class InstantCandidatePublicationE2ETests(unittest.TestCase):
    def test_full_fake_worker_loop_uses_candidate_state_not_consumer_ui(self):
        runtime = build_runtime()
        planned = OperatorDispatchPlanner(
            runtime=runtime,
            registry=REGISTRY,
        ).plan_service_existing(
            task_id="task:instant-e2e",
            action_id=ACTION_ID,
            action_generation=0,
            process_id=PROCESS_ID,
            process_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            executor_id=PROFILE.executor_id,
            packet_input=PacketCompilationInput(
                process_id=PROCESS_ID,
                source_checkpoint="task@exact-sha",
                objective="Return one exact durable candidate result.",
                constraints=(
                    "do not scrape consumer UI",
                    "do not mutate authoritative task state",
                ),
                evidence_refs=("evidence:instant-e2e",),
                authority_refs=("scope:proposal-only",),
                allowed_actions=("publish-candidate-result",),
                validator_contract=VALIDATOR_ID,
                output_schema="WORKER_RESULT_V1",
                next_safe_boundary=(
                    "publish immutable candidate JSON only"
                ),
            ),
            priority_rank=10,
            queue_sequence=1,
            created_at="T0",
            result_publication_target_ref=TARGET_REF,
        )

        contract = planned.packet_source.result_publication
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(
            contract.publication_id,
            f"worker-result:{ACTION_ID}:0",
        )
        self.assertEqual(contract.target_ref, TARGET_REF)
        self.assertTrue(contract.candidate_only)
        self.assertIn(TARGET_REF, planned.packet.text)
        self.assertIn(
            contract.schema_ref,
            planned.packet.text,
        )
        self.assertIn(
            "Do not modify task capsules",
            planned.packet.text,
        )
        self.assertNotIn(
            planned.packet.packet_sha256,
            planned.packet.canonical_payload_json,
            "canonical payload must not self-reference its digest",
        )

        service = OperatorActionService(
            runtime=runtime,
            packet_materializer=DurableOperatorPacketMaterializer(
                runtime=runtime,
                registry=REGISTRY,
            ),
        )
        with running_server(service) as base:
            status, status_body = request_json(
                base,
                "GET",
                "/operator-bridge/v1/status",
            )
            self.assertEqual(status, 200)
            self.assertEqual(
                status_body,
                {"readyManualCycles": 1, "sentUnconfirmed": 0},
            )

            _, claimed = request_json(
                base,
                "POST",
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "instant-e2e-claim",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            self.assertEqual(claimed["actionId"], ACTION_ID)
            self.assertEqual(
                claimed["packetText"],
                planned.packet.text,
            )
            self.assertEqual(
                claimed["payloadSha256"],
                planned.packet.packet_sha256,
            )

            action_path = quote(ACTION_ID, safe="")
            _, prepared = request_json(
                base,
                "POST",
                (
                    "/operator-bridge/v1/actions/"
                    f"{action_path}/local-prepared"
                ),
                {
                    "generation": 0,
                    "workerSlotId": SLOT_ID,
                    "sessionGeneration": 0,
                },
            )
            self.assertEqual(
                prepared["status"],
                "AWAITING_DURABLE_ACK",
            )

        worker_json = json.dumps(
            {
                "publication_id": contract.publication_id,
                "action_id": ACTION_ID,
                "action_generation": 0,
                "process_id": PROCESS_ID,
                "process_generation": 0,
                "executor_id": PROFILE.executor_id,
                "worker_slot_id": SLOT_ID,
                "session_generation": 0,
                "packet_sha256": planned.packet.packet_sha256,
                "kind": "RESULT",
                "observed_at": "T4",
                "result_payload_ref": (
                    "github://worker-result-payload@blob"
                ),
                "result_payload_sha256": "b" * 64,
                "evidence_refs": (
                    ["github://worker-result-evidence@blob"]
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        validator = PassingValidator()
        outcome = WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={VALIDATOR_ID: validator},
            )
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=TARGET_REF,
                immutable_revision="a" * 40,
                raw_bytes=worker_json,
            )
        )

        self.assertEqual(outcome.process_state, ProcessState.COMPLETED)
        self.assertEqual(validator.calls, 1)
        graph = runtime.snapshot().graph
        self.assertEqual(
            graph.processes[PROCESS_ID].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            graph.operator_actions[ACTION_ID].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            graph.executor_sessions[SLOT_ID].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(
            graph.worker_results[
                contract.publication_id
            ].source_ref,
            f"{TARGET_REF}@{'a' * 40}",
        )

        with running_server(service) as base:
            _, final_status = request_json(
                base,
                "GET",
                "/operator-bridge/v1/status",
            )
        self.assertEqual(
            final_status,
            {"readyManualCycles": 0, "sentUnconfirmed": 0},
        )

    def test_wrong_candidate_target_is_rejected_before_state_mutation(self):
        runtime = build_runtime()
        planned = OperatorDispatchPlanner(
            runtime=runtime,
            registry=REGISTRY,
        ).plan_service_existing(
            task_id="task:instant-e2e",
            action_id=ACTION_ID,
            action_generation=0,
            process_id=PROCESS_ID,
            process_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            executor_id=PROFILE.executor_id,
            packet_input=PacketCompilationInput(
                process_id=PROCESS_ID,
                source_checkpoint="task@exact-sha",
                objective="Reject candidate from wrong path.",
                validator_contract=VALIDATOR_ID,
                next_safe_boundary="publish immutable candidate",
            ),
            priority_rank=10,
            queue_sequence=1,
            created_at="T0",
            result_publication_target_ref=TARGET_REF,
        )
        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime.record_operator_action_local_prepared(
            action_id=ACTION_ID,
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T2",
        )
        contract = planned.packet_source.result_publication
        assert contract is not None
        raw = json.dumps(
            {
                "publication_id": contract.publication_id,
                "action_id": ACTION_ID,
                "action_generation": 0,
                "process_id": PROCESS_ID,
                "process_generation": 0,
                "executor_id": PROFILE.executor_id,
                "worker_slot_id": SLOT_ID,
                "session_generation": 0,
                "packet_sha256": planned.packet.packet_sha256,
                "kind": "RESULT",
                "observed_at": "T3",
                "result_payload_ref": "github://result@blob",
                "result_payload_sha256": "c" * 64,
            }
        ).encode("utf-8")
        version_before = runtime.snapshot().version

        with self.assertRaisesRegex(
            RuntimeError,
            "worker_result_publication_contract_mismatch",
        ):
            WorkerResultCandidateAdapter(
                intake=WorkerResultIntakeService(
                    runtime=runtime,
                    validators={
                        VALIDATOR_ID: PassingValidator()
                    },
                )
            ).ingest(
                ImmutableWorkerResultCandidate(
                    target_ref=(
                        "github-candidate://adamtrott78/"
                        "workspace-control/worker-results/"
                        "candidates/wrong.json"
                    ),
                    immutable_revision="d" * 40,
                    raw_bytes=raw,
                )
            )

        self.assertEqual(runtime.snapshot().version, version_before)
        self.assertEqual(runtime.snapshot().graph.worker_results, {})


if __name__ == "__main__":
    unittest.main()
