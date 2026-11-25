from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

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
from workspace_semantic_execution.application import (  # noqa: E402
    DurableOperatorPacketMaterializer,
    ExecutorRegistry,
    OperatorActionService,
    OperatorDispatchPlanner,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    WorkerResultIntakeService,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutorSessionState,
    OperatorActionState,
    ProcessState,
    WorkContract,
)

TOKEN = "63e9b17e492c4ed3a36d20c83172abf3"
CANDIDATE_COMMIT = "968db0800e9dcdee6e5a784889d74653276fb184"
PACKET_SHA256 = "f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b"
RAW_SHA256 = "896b4fb08a4a73f5913a1dc028a4118971274795051fa90230b77d8c616c734f"
FIXTURE = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "e3_a9_root_candidate_968db080.json"
)
HARNESS = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "live_research_iterate_e2.py"
)


def _load_e2_harness():
    spec = importlib.util.spec_from_file_location("e3_a9_e2_harness", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _replay_state():
    e2 = _load_e2_harness()
    root_id = f"research-iterate-e2:{TOKEN}"
    source_id = f"{root_id}.source"
    analysis_id = f"{root_id}.analysis"
    shell_id = f"{root_id}.workspace-shell"
    slot_id = f"e2-instant-slot:{TOKEN}"
    root_path = f"worker-results/e2/{TOKEN}/root-decompose.json"
    action_id = f"action:e2:{TOKEN}:root-decompose"
    marker = f"e2:root-decompose:{TOKEN[:12]}"

    root_contract = WorkContract(
        objective="Research the objective and synthesize a validated answer.",
        mandatory_constraints=(
            "no write-capable external effects",
            "preserve exact evidence provenance",
        ),
        provenance_refs=(f"research-engine@{e2.RESEARCH_ENGINE_SHA}",),
        authority_refs=("scope:research-read-only",),
        validator_contracts=(e2.VALIDATOR_ID,),
        output_schema_refs=("schema:research-e2-synthesis-v1",),
    )

    runtime = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    root_id,
                    work_contract=root_contract,
                )
            ]
        )
    )
    broker = PersistentExecutorSessionBroker(runtime)
    broker.ensure_session(
        profile=e2.PROFILE,
        slot_id=slot_id,
        session_id=f"e2-chat:{TOKEN}:g0",
    )

    registry = ExecutorRegistry((e2.PROFILE,))
    planner = OperatorDispatchPlanner(
        runtime=runtime,
        registry=registry,
        compiler=e2.SemanticPacketCompiler(),
    )
    target_ref = e2._candidate_target(root_path)
    planned = planner.plan_service_existing(
        task_id="workspace-semantic-execution-migration-v1",
        action_id=action_id,
        action_generation=0,
        process_id=root_id,
        process_generation=0,
        worker_slot_id=slot_id,
        session_generation=0,
        executor_id=e2.PROFILE.executor_id,
        packet_input=e2._root_packet(
            root_id=root_id,
            source_id=source_id,
            analysis_id=analysis_id,
            shell_id=shell_id,
            path=root_path,
            marker=marker,
        ),
        priority_rank=10,
        queue_sequence=1,
        created_at="e2-1",
        result_publication_target_ref=target_ref,
    )
    assert planned.packet.packet_sha256 == PACKET_SHA256

    service = OperatorActionService(
        runtime=runtime,
        packet_materializer=DurableOperatorPacketMaterializer(
            runtime=runtime,
            registry=registry,
        ),
    )
    claimed = service.claim_next(
        helper_instance_id="e3-a9-replay-helper",
        claim_id="e3-a9-replay-claim",
        claimed_at="e3-a9-claim",
        expires_at="e3-a9-expiry",
    )
    assert claimed is not None
    assert claimed.action.status == OperatorActionState.CLAIMED_LOCAL
    awaiting = service.record_local_prepared(
        action_id=action_id,
        generation=0,
        worker_slot_id=slot_id,
        session_generation=0,
        observed_at="e3-a9-local-prepared",
    )
    assert awaiting.status == OperatorActionState.AWAITING_DURABLE_ACK
    return e2, runtime, root_id, slot_id, action_id, target_ref


def test_e3_a9_exact_root_packet_reproduces_a8_sha() -> None:
    _, runtime, root_id, slot_id, action_id, _ = _replay_state()
    graph = runtime.snapshot().graph
    action = graph.operator_actions[action_id]
    assert action.payload_sha256 == PACKET_SHA256
    assert graph.processes[root_id].state == ProcessState.RUNNING
    assert graph.executor_sessions[slot_id].state == ExecutorSessionState.BOUND
    assert action.status == OperatorActionState.AWAITING_DURABLE_ACK
    assert graph.worker_results == {}


def test_e3_a9_exact_candidate_replay_passes_immutable_intake() -> None:
    _, runtime, root_id, slot_id, action_id, target_ref = _replay_state()
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RAW_SHA256

    outcome = WorkerResultCandidateAdapter(
        intake=WorkerResultIntakeService(runtime=runtime)
    ).ingest(
        ImmutableWorkerResultCandidate(
            target_ref=target_ref,
            immutable_revision=CANDIDATE_COMMIT,
            raw_bytes=raw,
        )
    )

    assert outcome.process_state == ProcessState.WAITING_DEPENDENCIES
    graph = runtime.snapshot().graph
    assert len(graph.worker_results) == 1
    assert graph.processes[root_id].state == ProcessState.WAITING_DEPENDENCIES
    assert len(graph.processes[root_id].children) == 3
    assert graph.executor_sessions[slot_id].state == ExecutorSessionState.READY
    assert graph.operator_actions[action_id].status == OperatorActionState.COMPLETED


def test_e3_a9_future_packets_bind_validated_schema_provenance() -> None:
    e2 = _load_e2_harness()
    params = e2._operator_params(
        task_id="workspace-semantic-execution-migration-v1",
        action_id="action:a9:schema-provenance",
        slot_id="a9-schema-slot",
        sequence=1,
        target_ref="github-candidate://example",
    )
    assert (
        e2.WORKER_RESULT_SCHEMA_PROVENANCE_HEAD
        == "c6dd247faaee12f1d8ade2cb53c60de41e3c3cdc"
    )
    assert (
        e2.WORKER_RESULT_SCHEMA_BLOB
        == "b84d362a8adbb1bf4a47f1dfc4f0b8089487a3c1"
    )
    assert params.result_publication_schema_ref == e2.WORKER_RESULT_SCHEMA_REF
    assert "worker-result-candidates-v1" not in params.result_publication_schema_ref


def test_e3_a9_wrapper_emits_compact_error_before_resource_report() -> None:
    wrapper = (
        ROOT
        / "benchmarks"
        / "workspace-semantic-execution"
        / "live_research_iterate_e3_a8_v1.py"
    ).read_text(encoding="utf-8")
    marker = '"E3_A9_EXECUTION_ERROR=" + execution_error'
    report = "resource_report = observer.report()"
    assert marker in wrapper
    assert report in wrapper
    assert wrapper.index(marker) < wrapper.index(report)
