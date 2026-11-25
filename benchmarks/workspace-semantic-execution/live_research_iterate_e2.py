#!/usr/bin/env python3
"""Live integrated Research-Iterate E2 proving harness.

The harness uses the reviewed Operator Bridge for human-assisted ChatGPT
Instant actions, a deterministic exact-source reader for the frozen Research
Engine source, and one harmless read-only Workspace Shell capability probe.
It never reads ChatGPT page content and never automates typing/submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import quote
import uuid

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ImmutableWorkerResultCandidate,
    PostgresEventLedger,
    PostgresStateStore,
    ReadOnlyRepositoryExecutor,
    RecordingTelemetry,
    RepositoryReadPostconditionValidator,
    StaticAuthorityEvaluator,
    StaticRepositoryReader,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorDispatchCoordinator,
    ExecutorDispatchRequest,
    ExecutorRegistry,
    FindingRecord,
    OperatorDispatchParameters,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    TaskTreeCoordinator,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    DomainKernel,
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    ExecutorSessionState,
    InvocationMode,
    MemoryResetPolicy,
    OperatorActionState,
    PrivacyClass,
    ProcessState,
    SessionMode,
    ValidationResult,
    WorkContract,
)
from workspace_semantic_execution.operator_bridge_server import (  # noqa: E402
    OperatorBridgeServerConfig,
    build_operator_bridge_server,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    RepositoryFileObservation,
)

PROFILE = openai_chat_instant_current_profile()
VALIDATOR_ID = "validator:research-iterate-e2-live-v1"
CANDIDATE_REPOSITORY = "adamtrott78/workspace-control"
CANDIDATE_REF = "refs/heads/worker-result-candidates-v1"
CANDIDATE_BRANCH = "worker-result-candidates-v1"
REPO_URL = "https://github.com/adamtrott78/workspace-control.git"
GITHUB_PLUGIN_MENTION = "@github"
WORKSPACE_SHELL_PLUGIN_MENTION = "@Workspace Shell"
WORKER_RESULT_SCHEMA_PROVENANCE_HEAD = "c6dd247faaee12f1d8ade2cb53c60de41e3c3cdc"
WORKER_RESULT_SCHEMA_PATH = (
    "architecture/workspace-semantic-execution-worker-result.v0.1.json"
)
WORKER_RESULT_SCHEMA_BLOB = "b84d362a8adbb1bf4a47f1dfc4f0b8089487a3c1"
WORKER_RESULT_SCHEMA_REF = (
    f"github://{CANDIDATE_REPOSITORY}@{WORKER_RESULT_SCHEMA_PROVENANCE_HEAD}/"
    f"{WORKER_RESULT_SCHEMA_PATH}#blob={WORKER_RESULT_SCHEMA_BLOB}"
)

RESEARCH_ENGINE_SHA = "1031861c03b2af8cff5cf72939bbbc83a95e65a4"
SOURCE_BLOB_SHA = "0d051fa50960708e0e773f6871c7e924c5796394"
SOURCE_PATH = "src/research_engine/orchestration.py"
SOURCE_TARGET = (
    "repo://adamtrott78/research-engine@"
    f"{RESEARCH_ENGINE_SHA}/{SOURCE_PATH}"
)
FROZEN_SOURCE = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "backend"
    / "research-engine-1031861"
    / "orchestration.py"
)
SHELL_EXPECTED_EVIDENCE = frozenset(
    {
        "workspace-shell:mcp-transport:HTTPS_MTLS_REQUIRED",
        "workspace-shell:uids:41010:41010:41011:41012",
        "workspace-shell:launcher-socket:1:660:0:41010",
        "workspace-shell:broker-socket:1:660:0:41010",
        "workspace-shell:receipt-root:1:750:0:41010",
    }
)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name}:required")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate_target(path: str) -> str:
    return (
        f"github-candidate://{CANDIDATE_REPOSITORY}/"
        f"ref/{quote(CANDIDATE_REF, safe='')}/"
        f"path/{quote(path, safe='/')}"
    )


def _objective_with_plugin_mentions(
    objective: str,
    *,
    plugin_mentions: tuple[str, ...],
) -> str:
    ordered: list[str] = []
    for mention in plugin_mentions:
        if (
            not mention.startswith("@")
            or mention != mention.strip()
            or "\n" in mention
            or "\r" in mention
        ):
            raise ValueError(f"invalid_plugin_mention:{mention!r}")
        if mention not in ordered:
            ordered.append(mention)
    if not ordered:
        return objective
    return "\n".join(ordered) + "\n\n" + objective


class CandidateWatcher:
    def __init__(self) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="e2-candidate-watch-"))
        self._run("init", "-q")
        self._run("remote", "add", "origin", REPO_URL)
        self.refresh()

    def close(self) -> None:
        import shutil
        shutil.rmtree(self._root, ignore_errors=True)

    def _run(self, *args: str, text: bool = True) -> str | bytes:
        completed = subprocess.run(
            ["git", "-C", str(self._root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
        )
        return completed.stdout

    def _remote_head(self) -> str:
        raw = str(
            self._run(
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{CANDIDATE_BRANCH}",
            )
        ).strip()
        parts = raw.split()
        if len(parts) != 2:
            raise RuntimeError(f"candidate_remote_head_invalid:{raw!r}")
        return parts[0]

    def refresh(self) -> str:
        observed = self._remote_head()
        self._run(
            "fetch",
            "--quiet",
            "--force",
            "--depth=2",
            "origin",
            f"refs/heads/{CANDIDATE_BRANCH}:"
            f"refs/remotes/origin/{CANDIDATE_BRANCH}",
        )
        fetched = str(
            self._run(
                "rev-parse",
                f"refs/remotes/origin/{CANDIDATE_BRANCH}",
            )
        ).strip()
        if fetched != observed:
            raise RuntimeError(
                "candidate_branch_fetch_visibility_mismatch:"
                f"{observed}:{fetched}"
            )
        return observed

    def wait_for_exact_candidate(
        self,
        *,
        baseline_head: str,
        path: str,
        timeout_seconds: int,
    ) -> tuple[str, bytes]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            head = self.refresh()
            if head == baseline_head:
                time.sleep(1.0)
                continue
            parent = str(self._run("rev-parse", f"{head}^")).strip()
            if parent != baseline_head:
                raise RuntimeError(
                    "candidate_branch_non_single_commit_advance:"
                    f"{baseline_head}:{parent}:{head}"
                )
            changed = [
                line.strip()
                for line in str(
                    self._run(
                        "diff-tree",
                        "--no-commit-id",
                        "--name-only",
                        "-r",
                        head,
                    )
                ).splitlines()
                if line.strip()
            ]
            if changed != [path]:
                raise RuntimeError(
                    f"candidate_commit_path_mismatch:{changed!r}"
                )
            raw = self._run("show", f"{head}:{path}", text=False)
            assert isinstance(raw, bytes)
            return head, raw
        raise RuntimeError(f"candidate_wait_timeout:{path}")


class E2Validator:
    def __init__(self) -> None:
        self._expected: dict[
            str, tuple[str, str, frozenset[str]]
        ] = {}

    def expect(
        self,
        *,
        action_id: str,
        payload_ref: str,
        payload_sha256: str,
        evidence_refs: set[str],
    ) -> None:
        self._expected[action_id] = (
            payload_ref,
            payload_sha256,
            frozenset(evidence_refs),
        )

    def validate(self, publication, packet_source):
        expected = self._expected.get(publication.action_id)
        passed = False
        if expected is not None:
            payload_ref, payload_sha256, evidence_refs = expected
            passed = (
                publication.result_payload_ref == payload_ref
                and publication.result_payload_sha256 == payload_sha256
                and frozenset(publication.evidence_refs)
                == evidence_refs
                and publication.packet_sha256
                == packet_source.packet_sha256
            )
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=passed,
            evidence_ref=(
                f"e2:validated:{publication.action_id}"
                if passed
                else f"e2:rejected:{publication.action_id}"
            ),
            observed_at="e2-validator",
        )


def read_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="research-engine-exact-source-read",
        provider_id="workspace-control",
        model_id="none",
        surface_id="machine",
        harness_id="repository-read-only-v1",
        toolset_id="repository-read-only",
        capabilities=frozenset({"repository.read_exact"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.LOCAL_HOST,
        privacy_classes=frozenset(
            {PrivacyClass.PUBLIC, PrivacyClass.INTERNAL}
        ),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
    )


def instant_requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"reasoning.bounded"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.HUMAN_ASSISTED}
        ),
        allowed_session_modes=frozenset(
            {SessionMode.PERSISTENT_CHAT}
        ),
        privacy_class=PrivacyClass.INTERNAL,
        require_human_launch=True,
    )


def deterministic_read_requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"repository.read_exact"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.DETERMINISTIC}
        ),
        allowed_session_modes=frozenset({SessionMode.NONE}),
        privacy_class=PrivacyClass.INTERNAL,
        required_resource_classes=frozenset({"CPU"}),
        require_human_launch=False,
    )


def _wait_action_status(
    *,
    store: PostgresStateStore,
    action_id: str,
    timeout_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        action = store.load().graph.operator_actions.get(action_id)
        if (
            action is not None
            and action.status
            == OperatorActionState.AWAITING_DURABLE_ACK
        ):
            return
        time.sleep(0.5)
    raise RuntimeError(f"action_status_timeout:{action_id}")


def _ingest(
    *,
    runtime: RuntimeCoordinator,
    validator: E2Validator,
    target_ref: str,
    revision: str,
    raw: bytes,
):
    return WorkerResultCandidateAdapter(
        intake=WorkerResultIntakeService(
            runtime=runtime,
            validators={VALIDATOR_ID: validator},
        )
    ).ingest(
        ImmutableWorkerResultCandidate(
            target_ref=target_ref,
            immutable_revision=revision,
            raw_bytes=raw,
        )
    )


def _supervisor_projection(
    *,
    store: PostgresStateStore,
    root_process_id: str,
) -> dict[str, object]:
    """Rebuild a content-free Supervisor S1 view from durable state only."""
    graph = store.load().graph
    root = graph.processes[root_process_id]
    states: dict[str, int] = {}
    unresolved: list[str] = []
    validated: list[str] = []
    for process_id, process in sorted(graph.processes.items()):
        states[process.state.value] = states.get(process.state.value, 0) + 1
        if process.state == ProcessState.COMPLETED:
            validated.append(process_id)
        else:
            unresolved.append(process_id)

    service_actions = [
        action
        for action in graph.operator_actions.values()
        if action.status in {
            OperatorActionState.QUEUED,
            OperatorActionState.AWAITING_DURABLE_ACK,
        }
    ]
    provenance = (
        list(root.work_contract.provenance_refs)
        if root.work_contract is not None
        else []
    )
    return {
        "mission_id": root_process_id,
        "mission_state": root.state.value,
        "process_state_counts": states,
        "unresolved_processes": unresolved,
        "validated_processes": validated,
        "critical_path": unresolved[0] if unresolved else None,
        "manual_service_cycles_ready_or_unconfirmed": len(service_actions),
        "pending_human_judgment_decisions": 0,
        "provenance_refs": provenance,
        "authority_mutations": 0,
        "conversation_memory_authoritative": False,
    }

def _candidate_location(path: str) -> FindingRecord:
    return FindingRecord(
        finding_id="candidate-location",
        text=(
            "Use the connected GitHub tool only for publication. Repository "
            f"{CANDIDATE_REPOSITORY}; branch {CANDIDATE_BRANCH}; path {path}. "
            "Create exactly one JSON candidate at that path and modify no "
            "other path. Do not ask the human to relay JSON or a commit SHA."
        ),
    )


def _result_packet(
    *,
    process_id: str,
    checkpoint: str,
    objective: str,
    path: str,
    payload_ref: str,
    payload_sha256: str,
    evidence_instruction: str,
    plugin_mentions: tuple[str, ...] = (GITHUB_PLUGIN_MENTION,),
    extra_constraints: tuple[str, ...] = (),
    allowed_actions: tuple[str, ...] = ("publish-exact-worker-result-candidate",),
) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=process_id,
        source_checkpoint=checkpoint,
        objective=_objective_with_plugin_mentions(
            objective,
            plugin_mentions=plugin_mentions,
        ),
        findings=(
            _candidate_location(path),
            FindingRecord(
                finding_id="candidate-result-values",
                text=(
                    "Publish kind=RESULT with result_payload_ref="
                    f"{payload_ref} and result_payload_sha256="
                    f"{payload_sha256}. {evidence_instruction}"
                ),
            ),
        ),
        constraints=(
            "No API keys or credentials.",
            "Do not modify task capsules, authority/policy state, source branches, or runtime control state.",
            "Do not inspect ChatGPT page content or automate typing/submission.",
            "Publish exactly one candidate JSON at the declared path.",
            *extra_constraints,
        ),
        evidence_refs=(f"research-engine@{RESEARCH_ENGINE_SHA}",),
        authority_refs=("scope:research-read-only",),
        allowed_actions=allowed_actions,
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate and stop",
    )


def _root_packet(
    *,
    root_id: str,
    source_id: str,
    analysis_id: str,
    shell_id: str,
    path: str,
    marker: str,
) -> PacketCompilationInput:
    child_text = json.dumps(
        [
            {
                "process_id": source_id,
                "objective": "Observe the exact frozen Research Engine orchestration source.",
                "validator_contracts": [
                    RepositoryReadPostconditionValidator.VALIDATOR_ID
                ],
                "output_schema_refs": [
                    "schema:exact-source-observation-v1"
                ],
            },
            {
                "process_id": analysis_id,
                "objective": "Analyze the exact-source evidence for synthesis-relevant workflow constraints.",
                "validator_contracts": [VALIDATOR_ID],
                "output_schema_refs": ["schema:e2-analysis-v1"],
            },
            {
                "process_id": shell_id,
                "objective": "Prove the connected Workspace Shell read-only runtime-inventory capability.",
                "validator_contracts": [VALIDATOR_ID],
                "output_schema_refs": ["schema:e2-shell-probe-v1"],
            },
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
    return PacketCompilationInput(
        process_id=root_id,
        source_checkpoint="research-iterate-e2@root",
        objective=_objective_with_plugin_mentions(
            "This mission is deliberately larger than one reasoning quantum. "
            "Return TOO_LARGE with the exact three child process contracts "
            "provided in the findings. Do not solve the mission directly.",
            plugin_mentions=(GITHUB_PLUGIN_MENTION,),
        ),
        findings=(
            _candidate_location(path),
            FindingRecord(
                finding_id="decomposition-shape",
                text=(
                    "Publish kind=TOO_LARGE with reason="
                    "'independent source, analysis, and capability work'. "
                    f"evidence_refs must contain exactly {marker}. "
                    "children must be exactly the following JSON array, with "
                    f"no extra child: {child_text}"
                ),
            ),
        ),
        constraints=(
            "No write-capable external effects.",
            "Preserve exact evidence provenance.",
            "Do not inspect ChatGPT page content.",
            "Publish exactly one candidate JSON at the declared path.",
        ),
        evidence_refs=(f"research-engine@{RESEARCH_ENGINE_SHA}",),
        authority_refs=("scope:research-read-only",),
        allowed_actions=("publish-exact-worker-result-candidate",),
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish decomposition candidate and stop",
    )


def _operator_params(
    *,
    task_id: str,
    action_id: str,
    slot_id: str,
    sequence: int,
    target_ref: str,
    session_generation: int = 0,
) -> OperatorDispatchParameters:
    return OperatorDispatchParameters(
        task_id=task_id,
        action_id=action_id,
        action_generation=0,
        worker_slot_id=slot_id,
        session_generation=session_generation,
        priority_rank=10,
        queue_sequence=sequence,
        created_at=f"e2-{sequence}",
        result_publication_target_ref=target_ref,
        result_publication_schema_ref=WORKER_RESULT_SCHEMA_REF,
    )


def run_e2(
    *,
    postgres_dsn: str,
    expected_tailscale_login: str,
    serve_port: int,
    candidate_timeout_seconds: int,
) -> dict[str, object]:
    token = uuid.uuid4().hex
    short = token[:12]
    task_id = "workspace-semantic-execution-migration-v1"
    root_id = f"research-iterate-e2:{token}"
    source_id = f"{root_id}.source"
    analysis_id = f"{root_id}.analysis"
    shell_id = f"{root_id}.workspace-shell"
    slot_id = f"e2-instant-slot:{token}"
    state_key = f"research-iterate-e2:{token}"

    root_contract = WorkContract(
        objective="Research the objective and synthesize a validated answer.",
        mandatory_constraints=(
            "no write-capable external effects",
            "preserve exact evidence provenance",
        ),
        provenance_refs=(f"research-engine@{RESEARCH_ENGINE_SHA}",),
        authority_refs=("scope:research-read-only",),
        validator_contracts=(VALIDATOR_ID,),
        output_schema_refs=("schema:research-e2-synthesis-v1",),
    )

    runtime = RuntimeCoordinator(
        state_store=PostgresStateStore(
            postgres_dsn,
            state_key=state_key,
        ),
        event_ledger=PostgresEventLedger(postgres_dsn),
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
        profile=PROFILE,
        slot_id=slot_id,
        session_id=f"e2-chat:{token}:g0",
    )

    observation = RepositoryFileObservation(
        repository="adamtrott78/research-engine",
        revision=RESEARCH_ENGINE_SHA,
        path=SOURCE_PATH,
        blob_id=SOURCE_BLOB_SHA,
        content=FROZEN_SOURCE.read_bytes(),
    )
    reader = StaticRepositoryReader((observation,))
    deterministic = read_profile()
    read_executor = ReadOnlyRepositoryExecutor(
        reader=reader,
        clock=FakeClock(seconds=20),
    )
    read_validator = RepositoryReadPostconditionValidator(
        reader=reader,
        clock=FakeClock(seconds=30),
    )
    source_action = CandidateAction(
        action_id=f"read:e2:{short}:research-engine-orchestration",
        process_id=source_id,
        process_generation=0,
        target_ref=SOURCE_TARGET,
        executor_type="REPOSITORY_READ_ONLY",
        idempotency_key=f"research-iterate-e2:{token}:source",
        preconditions=(
            "exact immutable Research Engine SHA",
            "read-only source observation",
        ),
        expected_effect="observe exact Research Engine orchestration bytes",
        postcondition_validator=(
            RepositoryReadPostconditionValidator.VALIDATOR_ID
        ),
    )
    source_authority = AuthorityDecision(
        decision_id=f"authority:e2:{short}:source",
        outcome=AuthorityOutcome.ALLOW,
        action_id=source_action.action_id,
        process_id=source_id,
        process_generation=0,
        target_ref=SOURCE_TARGET,
        authority_scope_ref="scope:research-read-only",
    )

    validator = E2Validator()
    registry = ExecutorRegistry((deterministic, PROFILE))
    dispatcher = ExecutorDispatchCoordinator(
        runtime=runtime,
        registry=registry,
        packet_compiler=SemanticPacketCompiler(),
        authority_evaluator=StaticAuthorityEvaluator(
            {source_action.action_id: source_authority}
        ),
        executor_ports={
            deterministic.executor_id: read_executor,
        },
        validators={
            RepositoryReadPostconditionValidator.VALIDATOR_ID:
                read_validator,
        },
    )
    tree = TaskTreeCoordinator(runtime)
    store = PostgresStateStore(postgres_dsn, state_key=state_key)
    watcher = CandidateWatcher()

    server = build_operator_bridge_server(
        OperatorBridgeServerConfig(
            postgres_dsn=postgres_dsn,
            expected_tailscale_login=expected_tailscale_login,
            state_key=state_key,
            port=serve_port,
        )
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    candidate_commits: dict[str, str] = {}
    routing_trace: list[str] = []
    try:
        root_path = f"worker-results/e2/{token}/root-decompose.json"
        root_action_id = f"action:e2:{token}:root-decompose"
        root_marker = f"e2:root-decompose:{short}"
        root_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=root_id,
                expected_generation=0,
                requirement_id="e2:root-decompose",
                requirement=instant_requirement(),
                packet_input=_root_packet(
                    root_id=root_id,
                    source_id=source_id,
                    analysis_id=analysis_id,
                    shell_id=shell_id,
                    path=root_path,
                    marker=root_marker,
                ),
                operator=_operator_params(
                    task_id=task_id,
                    action_id=root_action_id,
                    slot_id=slot_id,
                    sequence=1,
                    target_ref=_candidate_target(root_path),
                ),
            )
        )
        routing_trace.append(root_dispatch.routing.selected_executor_id)
        root_planned = root_dispatch.operator_dispatch
        if root_planned is None:
            raise RuntimeError("root_operator_dispatch_missing")
        baseline = watcher.refresh()
        print(
            "E2_ROOT_DECOMPOSE_READY=Press Ctrl+Space, then Ctrl+V, then Enter.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=root_action_id,
            timeout_seconds=candidate_timeout_seconds,
        )
        root_commit, root_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=root_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        root_json = json.loads(root_raw)
        if root_json.get("kind") != "TOO_LARGE":
            raise RuntimeError("e2_root_not_too_large")
        if root_json.get("evidence_refs") != [root_marker]:
            raise RuntimeError("e2_root_evidence_mismatch")
        child_ids = [
            child.get("process_id")
            for child in root_json.get("children", [])
        ]
        if child_ids != [source_id, analysis_id, shell_id]:
            raise RuntimeError(
                f"e2_root_children_mismatch:{child_ids!r}"
            )
        root_outcome = _ingest(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(root_path),
            revision=root_commit,
            raw=root_raw,
        )
        if root_outcome.process_state != ProcessState.WAITING_DEPENDENCIES:
            raise RuntimeError(
                "e2_root_not_waiting_dependencies:"
                f"{root_outcome.process_state.value}"
            )
        candidate_commits["root_decompose"] = root_commit
        print("E2_ROOT_DECOMPOSE=PASS", flush=True)

        fresh_supervisor_store = PostgresStateStore(
            postgres_dsn,
            state_key=state_key,
        )
        supervisor_after_decompose = _supervisor_projection(
            store=fresh_supervisor_store,
            root_process_id=root_id,
        )
        if (
            supervisor_after_decompose["mission_state"]
            != ProcessState.WAITING_DEPENDENCIES.value
            or supervisor_after_decompose["authority_mutations"] != 0
            or supervisor_after_decompose[
                "conversation_memory_authoritative"
            ]
        ):
            raise RuntimeError("e2_supervisor_rehydration_mismatch")
        print("E2_SUPERVISOR_S1_REHYDRATION=PASS", flush=True)

        graph = runtime.snapshot().graph
        for child_id in (source_id, analysis_id, shell_id):
            contract = graph.processes[child_id].work_contract
            if contract is None:
                raise RuntimeError(f"e2_child_contract_missing:{child_id}")
            if (
                "no write-capable external effects"
                not in contract.mandatory_constraints
                or f"research-engine@{RESEARCH_ENGINE_SHA}"
                not in contract.provenance_refs
                or "scope:research-read-only"
                not in contract.authority_refs
            ):
                raise RuntimeError(
                    f"e2_child_inheritance_mismatch:{child_id}"
                )
        print("E2_CHILD_CONTRACT_INHERITANCE=PASS", flush=True)

        source_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=source_id,
                expected_generation=0,
                requirement_id="e2:source",
                requirement=deterministic_read_requirement(),
                packet_input=PacketCompilationInput(
                    process_id=source_id,
                    source_checkpoint=(
                        f"research-engine@{RESEARCH_ENGINE_SHA}"
                    ),
                    objective=(
                        "Observe the exact immutable Research Engine "
                        "orchestration source."
                    ),
                    constraints=("read-only exact source",),
                    evidence_refs=(SOURCE_TARGET,),
                    authority_refs=("scope:research-read-only",),
                    allowed_actions=("read-exact-source",),
                    validator_contract=(
                        RepositoryReadPostconditionValidator.VALIDATOR_ID
                    ),
                    output_schema="schema:exact-source-observation-v1",
                    next_safe_boundary=(
                        "return independently validated receipt"
                    ),
                ),
                worker_id=f"e2-deterministic:{token}",
                lease_id=f"lease:e2:{token}:source",
                candidate_action=source_action,
            )
        )
        routing_trace.append(source_dispatch.routing.selected_executor_id)
        source_result = source_dispatch.coordinated_result
        if (
            source_result is None
            or not source_result.completed
            or not source_result.validation.passed
        ):
            raise RuntimeError("e2_exact_source_failed")
        print("E2_EXACT_SOURCE=PASS", flush=True)
        tree.refresh_fan_in(event_id=f"e2:{token}:source-complete")

        analysis_g0_path = f"worker-results/e2/{token}/analysis-g0-stale.json"
        analysis_g0_action_id = f"action:e2:{token}:analysis-g0"
        analysis_marker = f"e2:analysis:{short}"
        analysis_payload_ref = f"e2://{token}/analysis/result"
        analysis_payload_sha = _sha256_text(
            f"e2:{token}:analysis:accepted"
        )
        validator.expect(
            action_id=analysis_g0_action_id,
            payload_ref=analysis_payload_ref,
            payload_sha256=analysis_payload_sha,
            evidence_refs={
                analysis_marker,
                source_result.validation.evidence_ref,
            },
        )
        analysis_g0_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=analysis_id,
                expected_generation=0,
                requirement_id="e2:analysis-g0",
                requirement=instant_requirement(),
                packet_input=_result_packet(
                    process_id=analysis_id,
                    checkpoint="research-iterate-e2@analysis-g0",
                    objective=(
                        "Analyze the Research Engine exact-source evidence. "
                        "This worker is deliberately subject to a recovery "
                        "fault immediately after human submission; still "
                        "publish the exact candidate from this packet."
                    ),
                    path=analysis_g0_path,
                    payload_ref=analysis_payload_ref,
                    payload_sha256=analysis_payload_sha,
                    evidence_instruction=(
                        "evidence_refs must contain exactly "
                        f"{analysis_marker} and "
                        f"{source_result.validation.evidence_ref}."
                    ),
                    extra_constraints=(
                        "Do not rely on conversation continuity for correctness.",
                    ),
                ),
                operator=_operator_params(
                    task_id=task_id,
                    action_id=analysis_g0_action_id,
                    slot_id=slot_id,
                    sequence=2,
                    target_ref=_candidate_target(analysis_g0_path),
                    session_generation=0,
                ),
            )
        )
        routing_trace.append(
            analysis_g0_dispatch.routing.selected_executor_id
        )
        analysis_g0 = analysis_g0_dispatch.operator_dispatch
        if analysis_g0 is None:
            raise RuntimeError("analysis_g0_operator_dispatch_missing")
        baseline = watcher.refresh()
        print(
            "E2_ANALYSIS_G0_READY=Press Ctrl+Space, then Ctrl+V, then Enter. "
            "This serviced worker will be deliberately fenced immediately "
            "after local submission.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=analysis_g0_action_id,
            timeout_seconds=candidate_timeout_seconds,
        )
        print("E2_FAULT_INJECTION_ARMED=PASS", flush=True)

        runtime.recover(
            analysis_id,
            expected_generation=0,
            reason="e2_deliberate_worker_session_process_loss",
        )
        fenced_graph = runtime.snapshot().graph
        fenced_process = fenced_graph.processes[analysis_id]
        fenced_session = fenced_graph.executor_sessions[slot_id]
        fenced_action = fenced_graph.operator_actions[analysis_g0_action_id]
        if (
            fenced_process.generation != 1
            or fenced_process.state != ProcessState.READY_TO_RESUME
            or fenced_session.state
            != ExecutorSessionState.NEEDS_REPLACEMENT
            or fenced_session.session_generation != 1
            or fenced_action.status != OperatorActionState.STALE
        ):
            raise RuntimeError("e2_fault_fence_state_mismatch")
        print("E2_WORKER_PROCESS_SESSION_FENCE=PASS", flush=True)

        # Deliberately discard the orchestration/application objects. Rebuild
        # them from PostgreSQL only; conversation memory and old Python
        # coordinator objects are not recovery sources.
        store = PostgresStateStore(
            postgres_dsn,
            state_key=state_key,
        )
        runtime = RuntimeCoordinator(
            state_store=store,
            event_ledger=PostgresEventLedger(postgres_dsn),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=40),
        )
        rehydrated_graph = runtime.snapshot().graph
        source_process = rehydrated_graph.processes[source_id]
        if (
            source_process.state != ProcessState.COMPLETED
            or not source_process.validations
            or not source_process.validations[-1].passed
        ):
            raise RuntimeError("e2_rehydrated_source_evidence_missing")
        source_validation_evidence = (
            source_process.validations[-1].evidence_ref
        )
        if (
            rehydrated_graph.processes[analysis_id].generation != 1
            or rehydrated_graph.executor_sessions[slot_id].session_generation
            != 1
            or rehydrated_graph.operator_actions[
                analysis_g0_action_id
            ].status
            != OperatorActionState.STALE
        ):
            raise RuntimeError("e2_runtime_rehydration_state_mismatch")

        validator = E2Validator()
        dispatcher = ExecutorDispatchCoordinator(
            runtime=runtime,
            registry=registry,
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator(
                {source_action.action_id: source_authority}
            ),
            executor_ports={
                deterministic.executor_id: read_executor,
            },
            validators={
                RepositoryReadPostconditionValidator.VALIDATOR_ID:
                    read_validator,
            },
        )
        tree = TaskTreeCoordinator(runtime)
        broker = PersistentExecutorSessionBroker(runtime)

        supervisor_after_loss = _supervisor_projection(
            store=PostgresStateStore(
                postgres_dsn,
                state_key=state_key,
            ),
            root_process_id=root_id,
        )
        if (
            supervisor_after_loss["mission_state"]
            != ProcessState.WAITING_DEPENDENCIES.value
            or supervisor_after_loss["authority_mutations"] != 0
            or supervisor_after_loss[
                "conversation_memory_authoritative"
            ]
        ):
            raise RuntimeError("e2_supervisor_rehydration_after_loss_mismatch")
        print("E2_RUNTIME_REHYDRATION_FROM_POSTGRES=PASS", flush=True)
        print("E2_SUPERVISOR_REHYDRATION_AFTER_LOSS=PASS", flush=True)

        stale_commit, stale_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=analysis_g0_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        version_before_stale = runtime.snapshot().version
        try:
            _ingest(
                runtime=runtime,
                validator=validator,
                target_ref=_candidate_target(analysis_g0_path),
                revision=stale_commit,
                raw=stale_raw,
            )
        except Exception:
            pass
        else:
            raise RuntimeError("e2_stale_worker_candidate_accepted")
        if runtime.snapshot().version != version_before_stale:
            raise RuntimeError("e2_stale_worker_candidate_mutated_state")
        candidate_commits["analysis_stale_g0"] = stale_commit
        print(
            f"E2_STALE_WORKER_CANDIDATE_OBSERVED={stale_commit}",
            flush=True,
        )
        print(
            "E2_STALE_RESULT_REJECTED_WITHOUT_MUTATION=PASS",
            flush=True,
        )

        replacement = broker.replace(
            slot_id=slot_id,
            expected_session_generation=1,
            session_id=f"e2-chat:{token}:g1",
        )
        if (
            replacement.state != ExecutorSessionState.READY
            or replacement.session_generation != 1
        ):
            raise RuntimeError("e2_replacement_session_not_ready")
        print("E2_SESSION_REPLACEMENT=PASS", flush=True)

        analysis_g1_path = f"worker-results/e2/{token}/analysis-g1.json"
        analysis_g1_action_id = f"action:e2:{token}:analysis-g1"
        validator.expect(
            action_id=analysis_g1_action_id,
            payload_ref=analysis_payload_ref,
            payload_sha256=analysis_payload_sha,
            evidence_refs={
                analysis_marker,
                source_validation_evidence,
            },
        )
        analysis_g1_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=analysis_id,
                expected_generation=1,
                requirement_id="e2:analysis-g1-replacement",
                requirement=instant_requirement(),
                packet_input=_result_packet(
                    process_id=analysis_id,
                    checkpoint="research-iterate-e2@analysis-g1",
                    objective=(
                        "Resume the analysis leaf from durable mission state "
                        "after the previous worker/session generation was "
                        "fenced. Use this packet and exact-source provenance; "
                        "do not rely on the retired chat generation."
                    ),
                    path=analysis_g1_path,
                    payload_ref=analysis_payload_ref,
                    payload_sha256=analysis_payload_sha,
                    evidence_instruction=(
                        "evidence_refs must contain exactly "
                        f"{analysis_marker} and "
                        f"{source_validation_evidence}."
                    ),
                    extra_constraints=(
                        "The previous worker/session generation is stale.",
                        "Recover from durable packet state only.",
                    ),
                ),
                operator=_operator_params(
                    task_id=task_id,
                    action_id=analysis_g1_action_id,
                    slot_id=slot_id,
                    sequence=3,
                    target_ref=_candidate_target(analysis_g1_path),
                    session_generation=1,
                ),
            )
        )
        routing_trace.append(
            analysis_g1_dispatch.routing.selected_executor_id
        )
        if analysis_g1_dispatch.operator_dispatch is None:
            raise RuntimeError("analysis_g1_operator_dispatch_missing")
        baseline = watcher.refresh()
        print(
            "E2_ANALYSIS_G1_REPLACEMENT_READY="
            "Press Ctrl+Space, then Ctrl+V, then Enter. "
            "A replacement managed session generation must be used.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=analysis_g1_action_id,
            timeout_seconds=candidate_timeout_seconds,
        )
        analysis_commit, analysis_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=analysis_g1_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        analysis_outcome = _ingest(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(analysis_g1_path),
            revision=analysis_commit,
            raw=analysis_raw,
        )
        if analysis_outcome.process_state != ProcessState.COMPLETED:
            raise RuntimeError("e2_analysis_replacement_not_completed")
        candidate_commits["analysis_replacement_g1"] = analysis_commit
        print("E2_ANALYSIS_RECOVERY=PASS", flush=True)
        tree.refresh_fan_in(event_id=f"e2:{token}:analysis-complete")

        shell_path = f"worker-results/e2/{token}/workspace-shell.json"
        shell_action_id = f"action:e2:{token}:workspace-shell"
        shell_marker = f"e2:workspace-shell:{short}"
        shell_payload_ref = f"e2://{token}/workspace-shell/runtime-inventory"
        shell_payload_sha = _sha256_text(
            f"e2:{token}:workspace-shell:accepted"
        )
        shell_expected = set(SHELL_EXPECTED_EVIDENCE)
        shell_expected.add(shell_marker)
        validator.expect(
            action_id=shell_action_id,
            payload_ref=shell_payload_ref,
            payload_sha256=shell_payload_sha,
            evidence_refs=shell_expected,
        )
        shell_instruction = (
            "First call connected Workspace Shell read-only inspection with "
            "task_id=workspace-semantic-execution-migration-v1, "
            "target=workspace-shell, operation=runtime_inventory. "
            "Do not call Workspace Shell exec or reviewed-helper tools. "
            "Do not use GitHub to read source or discover expected values; "
            "GitHub is permitted only for the candidate publication. "
            "From the returned result object derive these evidence_refs "
            "without guessing: "
            f"{shell_marker}; "
            "workspace-shell:mcp-transport:<mcp_transport>; "
            "workspace-shell:uids:<current_uid>:<configured_frontend_uid>:"
            "<configured_worker_uid>:<configured_tunnel_uid>; "
            "workspace-shell:launcher-socket:<exists-as-1-or-0>:<mode>:<uid>:<gid>; "
            "workspace-shell:broker-socket:<exists-as-1-or-0>:<mode>:<uid>:<gid>; "
            "workspace-shell:receipt-root:<exists-as-1-or-0>:<mode>:<uid>:<gid>. "
            "Publish exactly those six evidence_refs."
        )
        shell_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=shell_id,
                expected_generation=0,
                requirement_id="e2:workspace-shell-probe",
                requirement=instant_requirement(),
                packet_input=_result_packet(
                    process_id=shell_id,
                    checkpoint="research-iterate-e2@workspace-shell",
                    objective=(
                        "Perform the bounded Workspace Shell read-only "
                        "capability probe, then publish its exact evidence."
                    ),
                    path=shell_path,
                    payload_ref=shell_payload_ref,
                    payload_sha256=shell_payload_sha,
                    evidence_instruction=shell_instruction,
                    plugin_mentions=(
                        WORKSPACE_SHELL_PLUGIN_MENTION,
                        GITHUB_PLUGIN_MENTION,
                    ),
                    extra_constraints=(
                        "Workspace Shell capability is strictly read-only for this leaf.",
                        "workspace_shell_exec and workspace_shell_run_reviewed_helper are prohibited.",
                    ),
                    allowed_actions=(
                        "inspect-workspace-shell-runtime-inventory",
                        "publish-exact-worker-result-candidate",
                    ),
                ),
                operator=_operator_params(
                    task_id=task_id,
                    action_id=shell_action_id,
                    slot_id=slot_id,
                    sequence=4,
                    target_ref=_candidate_target(shell_path),
                    session_generation=1,
                ),
            )
        )
        routing_trace.append(shell_dispatch.routing.selected_executor_id)
        shell_planned = shell_dispatch.operator_dispatch
        if shell_planned is None:
            raise RuntimeError("shell_operator_dispatch_missing")
        if not shell_planned.packet.text.lstrip().startswith(
            "@Workspace Shell\n@github\n\n"
        ):
            raise RuntimeError("e2_shell_literal_plugin_prefix_mismatch")
        for hidden in SHELL_EXPECTED_EVIDENCE:
            if hidden in shell_planned.packet.text:
                raise RuntimeError(
                    "e2_shell_expected_value_disclosed_in_packet"
                )
        print("E2_WORKSPACE_SHELL_EXPECTED_VALUES_HIDDEN=PASS", flush=True)
        baseline = watcher.refresh()
        print(
            "E2_WORKSPACE_SHELL_READY=Press Ctrl+Space, then Ctrl+V, then Enter.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=shell_action_id,
            timeout_seconds=candidate_timeout_seconds,
        )
        shell_commit, shell_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=shell_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        shell_outcome = _ingest(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(shell_path),
            revision=shell_commit,
            raw=shell_raw,
        )
        if shell_outcome.process_state != ProcessState.COMPLETED:
            raise RuntimeError("e2_workspace_shell_probe_not_completed")
        candidate_commits["workspace_shell"] = shell_commit
        print("E2_WORKSPACE_SHELL_READ_ONLY_PROBE=PASS", flush=True)

        tree.refresh_fan_in(event_id=f"e2:{token}:shell-complete")
        graph = runtime.snapshot().graph
        if graph.processes[root_id].state != ProcessState.READY_TO_RESUME:
            raise RuntimeError(
                "e2_root_not_ready_after_fanin:"
                f"{graph.processes[root_id].state.value}"
            )
        print("E2_FAN_IN=PASS", flush=True)

        source_receipt = next(
            iter(graph.processes[source_id].effect_receipts.values())
        )
        analysis_receipt = next(
            iter(graph.processes[analysis_id].effect_receipts.values())
        )
        shell_receipt = next(
            iter(graph.processes[shell_id].effect_receipts.values())
        )

        synthesis_path = f"worker-results/e2/{token}/synthesis.json"
        synthesis_action_id = f"action:e2:{token}:synthesis"
        synthesis_marker = f"e2:synthesis:{short}"
        synthesis_payload_ref = f"e2://{token}/synthesis/result"
        synthesis_payload_sha = _sha256_text(
            f"e2:{token}:synthesis:accepted"
        )
        synthesis_evidence = {
            synthesis_marker,
            source_validation_evidence,
            source_receipt.target_ref,
            analysis_receipt.target_ref,
            shell_receipt.target_ref,
        }
        validator.expect(
            action_id=synthesis_action_id,
            payload_ref=synthesis_payload_ref,
            payload_sha256=synthesis_payload_sha,
            evidence_refs=synthesis_evidence,
        )
        synthesis_dispatch = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=root_id,
                expected_generation=0,
                requirement_id="e2:synthesis",
                requirement=instant_requirement(),
                packet_input=_result_packet(
                    process_id=root_id,
                    checkpoint="research-iterate-e2@synthesis",
                    objective=(
                        "Synthesize the validated exact-source, analysis, "
                        "and Workspace Shell capability evidence into the "
                        "final E2 mission result. Do not add unsupported "
                        "claims."
                    ),
                    path=synthesis_path,
                    payload_ref=synthesis_payload_ref,
                    payload_sha256=synthesis_payload_sha,
                    evidence_instruction=(
                        "evidence_refs must contain exactly: "
                        + ", ".join(sorted(synthesis_evidence))
                        + "."
                    ),
                ),
                operator=_operator_params(
                    task_id=task_id,
                    action_id=synthesis_action_id,
                    slot_id=slot_id,
                    sequence=5,
                    target_ref=_candidate_target(synthesis_path),
                    session_generation=1,
                ),
            )
        )
        routing_trace.append(
            synthesis_dispatch.routing.selected_executor_id
        )
        if synthesis_dispatch.operator_dispatch is None:
            raise RuntimeError("synthesis_operator_dispatch_missing")
        baseline = watcher.refresh()
        print(
            "E2_SYNTHESIS_READY=Press Ctrl+Space, then Ctrl+V, then Enter.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=synthesis_action_id,
            timeout_seconds=candidate_timeout_seconds,
        )
        synthesis_commit, synthesis_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=synthesis_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        synthesis_outcome = _ingest(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(synthesis_path),
            revision=synthesis_commit,
            raw=synthesis_raw,
        )
        if synthesis_outcome.process_state != ProcessState.COMPLETED:
            raise RuntimeError("e2_synthesis_not_completed")
        candidate_commits["synthesis"] = synthesis_commit

        final = runtime.snapshot().graph
        for process_id in (
            root_id,
            source_id,
            analysis_id,
            shell_id,
        ):
            if final.processes[process_id].state != ProcessState.COMPLETED:
                raise RuntimeError(
                    f"e2_process_not_complete:{process_id}:"
                    f"{final.processes[process_id].state.value}"
                )
        final_session = final.executor_sessions[slot_id]
        if (
            final.processes[analysis_id].generation != 1
            or final_session.session_generation != 1
            or final_session.state != ExecutorSessionState.READY
            or final.operator_actions[analysis_g0_action_id].status
            != OperatorActionState.STALE
            or final.operator_actions[analysis_g1_action_id].status
            != OperatorActionState.COMPLETED
        ):
            raise RuntimeError("e2_final_recovery_state_mismatch")

        queued = [
            a for a in final.operator_actions.values()
            if a.status in {
                OperatorActionState.QUEUED,
                OperatorActionState.AWAITING_DURABLE_ACK,
            }
        ]
        if queued:
            raise RuntimeError("e2_operator_work_not_empty")

        supervisor_final = _supervisor_projection(
            store=PostgresStateStore(
                postgres_dsn,
                state_key=state_key,
            ),
            root_process_id=root_id,
        )
        if (
            supervisor_final["mission_state"]
            != ProcessState.COMPLETED.value
            or supervisor_final["unresolved_processes"]
            or supervisor_final["authority_mutations"] != 0
        ):
            raise RuntimeError("e2_supervisor_final_projection_mismatch")
        print(
            "E2_SUPERVISOR_S1_FINAL="
            + json.dumps(
                supervisor_final,
                sort_keys=True,
                separators=(",", ":"),
            ),
            flush=True,
        )

        report = {
            "schema": "workspace-semantic-research-iterate-e2.v1",
            "result": "PASS",
            "candidate_branch": CANDIDATE_BRANCH,
            "candidate_commits": candidate_commits,
            "root_decomposition": True,
            "worker_process_loss_injected": True,
            "process_generation_recovered": "0->1",
            "persistent_session_loss_injected": True,
            "session_generation_replaced": "0->1",
            "stale_worker_candidate_observed": True,
            "stale_worker_result_rejected_without_mutation": True,
            "orchestrator_objects_discarded_and_rehydrated": True,
            "durable_recovery_source": "PostgreSQL",
            "replacement_session_completed": True,
            "child_contract_inheritance": True,
            "deterministic_exact_source": True,
            "instant_analysis": True,
            "workspace_shell_read_only_probe": True,
            "workspace_shell_literal_prefix": "@Workspace Shell",
            "github_literal_prefix": "@github",
            "workspace_shell_exec_used": False,
            "workspace_shell_reviewed_helper_used": False,
            "fanin": True,
            "instant_synthesis": True,
            "supervisor_s1_read_only_projection": True,
            "supervisor_s1_fresh_store_rehydration": True,
            "routing_trace": routing_trace,
            "manual_durable_state_relay": False,
            "browser_page_content_scraping": False,
            "automatic_typing_or_submission": False,
            "paid_api_fallback": False,
        }
        print(
            "E2_RESEARCH_ITERATE="
            + json.dumps(
                report,
                sort_keys=True,
                separators=(",", ":"),
            ),
            flush=True,
        )
        return report
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        watcher.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve-port", type=int, default=8765)
    parser.add_argument(
        "--candidate-timeout-seconds",
        type=int,
        default=1200,
    )
    args = parser.parse_args()
    report = run_e2(
        postgres_dsn=_required_env("SEMANTIC_EXECUTION_POSTGRES_DSN"),
        expected_tailscale_login=_required_env(
            "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"
        ),
        serve_port=args.serve_port,
        candidate_timeout_seconds=args.candidate_timeout_seconds,
    )
    return 0 if report.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
