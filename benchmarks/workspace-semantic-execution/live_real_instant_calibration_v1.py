#!/usr/bin/env python3
"""Bounded real-ChatGPT Instant calibration over the reviewed private route.

This harness never reads ChatGPT page content and never automates credentials,
typing, submission, or model selection. The Windows Operator Bridge prepares
managed Firefox bindings and the human performs Ctrl+Space -> Ctrl+V -> Enter.

Real worker results return through the isolated GitHub candidate branch. Each
candidate commit is bound to one exact path, action/process/session generation,
and packet SHA. The second quantum intentionally omits a continuity token that
was present only in the first conversation turn; recovering it proves useful
persistent-chat reuse. A stale generation is then fenced deterministically and
a replacement session generation completes one final bounded quantum.
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
    PostgresEventLedger,
    PostgresStateStore,
    RecordingTelemetry,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorRegistry,
    FindingRecord,
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
from workspace_semantic_execution.operator_bridge_server import (  # noqa: E402
    OperatorBridgeServerConfig,
    build_operator_bridge_server,
)


PROFILE = openai_chat_instant_current_profile()
VALIDATOR_ID = "validator:stage12-real-instant-v1"
CANDIDATE_REPOSITORY = "adamtrott78/workspace-control"
CANDIDATE_REF = "refs/heads/worker-result-candidates-v1"
CANDIDATE_BRANCH = "worker-result-candidates-v1"
REPO_URL = "https://github.com/adamtrott78/workspace-control.git"


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


class CandidateWatcher:
    def __init__(self, *, branch: str = CANDIDATE_BRANCH) -> None:
        self._branch = branch
        self._root = Path(
            tempfile.mkdtemp(prefix="stage12-candidate-watch-")
        )
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

    def refresh(self) -> str:
        self._run(
            "fetch",
            "--quiet",
            "--force",
            "--depth=2",
            "origin",
            f"refs/heads/{self._branch}:"
            f"refs/remotes/origin/{self._branch}",
        )
        return str(
            self._run(
                "rev-parse",
                f"refs/remotes/origin/{self._branch}",
            )
        ).strip()

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

            parent = str(
                self._run("rev-parse", f"{head}^")
            ).strip()
            if parent != baseline_head:
                raise RuntimeError(
                    "candidate_branch_non_single_commit_advance:"
                    f"baseline={baseline_head}:parent={parent}:head={head}"
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

            raw = self._run(
                "show",
                f"{head}:{path}",
                text=False,
            )
            assert isinstance(raw, bytes)
            return head, raw

        raise RuntimeError(
            f"candidate_wait_timeout:{path}:{timeout_seconds}s"
        )


class CalibrationValidator:
    def __init__(self) -> None:
        self._expected: dict[str, tuple[str, str, frozenset[str]]] = {}

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
                and publication.result_payload_sha256
                == payload_sha256
                and frozenset(publication.evidence_refs)
                == evidence_refs
                and publication.packet_sha256
                == packet_source.packet_sha256
            )
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=passed,
            evidence_ref=(
                f"stage12:validated:{publication.action_id}"
                if passed
                else f"stage12:rejected:{publication.action_id}"
            ),
            observed_at="stage12-validator",
        )


def _result_instructions(
    *,
    path: str,
    payload_ref: str,
    payload_sha256: str,
    evidence_refs: tuple[str, ...],
    extra: str,
) -> tuple[FindingRecord, ...]:
    return (
        FindingRecord(
            finding_id="candidate-location",
            text=(
                "Use the connected GitHub tool directly. Repository "
                f"{CANDIDATE_REPOSITORY}; branch {CANDIDATE_BRANCH}; "
                f"path {path}. Create exactly one JSON file at that path "
                "and modify no other path. Do not ask the human to relay "
                "candidate JSON or a commit SHA."
            ),
        ),
        FindingRecord(
            finding_id="candidate-result-values",
            text=(
                "Publish kind=RESULT with result_payload_ref="
                f"{payload_ref} and result_payload_sha256="
                f"{payload_sha256}. evidence_refs must contain exactly: "
                + ", ".join(evidence_refs)
                + ". "
                + extra
            ),
        ),
    )


def _packet_input(
    *,
    process_id: str,
    source_checkpoint: str,
    objective: str,
    path: str,
    payload_ref: str,
    payload_sha256: str,
    evidence_refs: tuple[str, ...],
    extra: str,
) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=process_id,
        source_checkpoint=source_checkpoint,
        objective=objective,
        findings=_result_instructions(
            path=path,
            payload_ref=payload_ref,
            payload_sha256=payload_sha256,
            evidence_refs=evidence_refs,
            extra=extra,
        ),
        constraints=(
            "Use normal connected GitHub tooling only; no API keys or credentials.",
            "Do not modify task capsules, authority/policy state, source branches, or runtime control state.",
            "Do not ask the human to copy, relay, or interpret the result candidate.",
            "Do not use browser-page automation or inspect ChatGPT page content.",
            "Publish exactly one candidate JSON at the declared candidate path.",
        ),
        evidence_refs=("stage12:real-account-calibration",),
        authority_refs=("scope:stage12-candidate-publication-only",),
        allowed_actions=("publish-exact-worker-result-candidate",),
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate and stop",
    )


def _wait_action_status(
    *,
    store: PostgresStateStore,
    action_id: str,
    status: OperatorActionState,
    timeout_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        graph = store.load().graph
        action = graph.operator_actions.get(action_id)
        if action is not None and action.status == status:
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"action_status_timeout:{action_id}:{status.value}"
    )


def _ingest_candidate(
    *,
    runtime: RuntimeCoordinator,
    validator: CalibrationValidator,
    target_ref: str,
    immutable_revision: str,
    raw_bytes: bytes,
) -> None:
    outcome = WorkerResultCandidateAdapter(
        intake=WorkerResultIntakeService(
            runtime=runtime,
            validators={VALIDATOR_ID: validator},
        )
    ).ingest(
        __import__(
            "workspace_semantic_execution.adapters",
            fromlist=["ImmutableWorkerResultCandidate"],
        ).ImmutableWorkerResultCandidate(
            target_ref=target_ref,
            immutable_revision=immutable_revision,
            raw_bytes=raw_bytes,
        )
    )
    if (
        outcome.process_state != ProcessState.COMPLETED
        or outcome.validation is None
        or not outcome.validation.passed
    ):
        raise RuntimeError(
            f"candidate_validation_failed:{outcome.process_state.value}"
        )


def run_calibration(
    *,
    postgres_dsn: str,
    expected_tailscale_login: str,
    serve_port: int,
    candidate_timeout_seconds: int,
) -> dict[str, object]:
    token = uuid.uuid4().hex
    short = token[:12]
    state_key = f"stage12-real-instant:{token}"
    slot_id = f"stage12-instant-slot:{token}"
    process_q1 = f"stage12-q1:{token}"
    process_q2 = f"stage12-q2:{token}"
    process_q3 = f"stage12-q3:{token}"
    continuity_token = f"stage12-continuity-{uuid.uuid4().hex}"

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
                DomainKernel.create_process(process_q1),
                DomainKernel.create_process(process_q2),
                DomainKernel.create_process(process_q3),
            ]
        )
    )
    broker = PersistentExecutorSessionBroker(runtime)
    broker.ensure_session(
        profile=PROFILE,
        slot_id=slot_id,
        session_id=f"stage12-chat:{token}:g0",
    )
    registry = ExecutorRegistry((PROFILE,))
    planner = OperatorDispatchPlanner(
        runtime=runtime,
        registry=registry,
    )
    validator = CalibrationValidator()
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
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    candidate_commits: dict[str, str] = {}
    try:
        def plan_quantum(
            *,
            phase: str,
            process_id: str,
            process_generation: int,
            session_generation: int,
            sequence: int,
            objective: str,
            evidence_refs: tuple[str, ...],
            extra: str,
        ):
            action_id = (
                f"action:stage12:{phase}:{token}:"
                f"pg{process_generation}:sg{session_generation}"
            )
            path = (
                f"worker-results/stage12/{token}/"
                f"{phase}.json"
            )
            payload_ref = (
                f"stage12://{token}/{phase}/result"
            )
            payload_sha = _sha256_text(
                f"stage12:{token}:{phase}:accepted"
            )
            validator.expect(
                action_id=action_id,
                payload_ref=payload_ref,
                payload_sha256=payload_sha,
                evidence_refs=set(evidence_refs),
            )
            planned = planner.plan_service_existing(
                task_id="workspace-semantic-execution-migration-v1",
                action_id=action_id,
                action_generation=0,
                process_id=process_id,
                process_generation=process_generation,
                worker_slot_id=slot_id,
                session_generation=session_generation,
                executor_id=PROFILE.executor_id,
                packet_input=_packet_input(
                    process_id=process_id,
                    source_checkpoint=(
                        f"stage12-real-instant@{phase}"
                    ),
                    objective=objective,
                    path=path,
                    payload_ref=payload_ref,
                    payload_sha256=payload_sha,
                    evidence_refs=evidence_refs,
                    extra=extra,
                ),
                priority_rank=1,
                queue_sequence=sequence,
                created_at=f"stage12-{sequence}",
                result_publication_target_ref=(
                    _candidate_target(path)
                ),
            )
            return planned, path

        q1_marker = f"stage12:q1:{short}"
        q1, q1_path = plan_quantum(
            phase="q1",
            process_id=process_q1,
            process_generation=0,
            session_generation=0,
            sequence=1,
            objective=(
                "Perform the first bounded real-Instant calibration quantum. "
                "Use the connected GitHub tool to publish the exact candidate. "
                "Also retain the following continuity evidence ref only in "
                "this conversation for the next turn: "
                f"continuity:{continuity_token}. Do NOT include that "
                "continuity ref in the q1 candidate."
            ),
            evidence_refs=(q1_marker,),
            extra=(
                "Retain the continuity evidence ref from the objective in "
                "conversation context for the next turn, but do not publish "
                "it in q1."
            ),
        )
        baseline = watcher.refresh()
        print(
            "STAGE12_Q1_READY="
            "Press Ctrl+Space, then Ctrl+V, then Enter in the managed "
            "Firefox ChatGPT worker.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=q1.action.action_id,
            status=OperatorActionState.AWAITING_DURABLE_ACK,
            timeout_seconds=candidate_timeout_seconds,
        )
        q1_commit, q1_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=q1_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        _ingest_candidate(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(q1_path),
            immutable_revision=q1_commit,
            raw_bytes=q1_raw,
        )
        candidate_commits["q1"] = q1_commit
        if store.load().graph.executor_sessions[slot_id].state != ExecutorSessionState.READY:
            raise RuntimeError("q1_session_not_ready")
        print("STAGE12_Q1_REAL_INSTANT=PASS", flush=True)

        q2_marker = f"stage12:q2:{short}"
        q2_continuity = f"continuity:{continuity_token}"
        q2, q2_path = plan_quantum(
            phase="q2",
            process_id=process_q2,
            process_generation=0,
            session_generation=0,
            sequence=2,
            objective=(
                "Perform the second bounded calibration quantum in the SAME "
                "managed conversation. Publish the exact q2 candidate. "
                "Recover the continuity evidence ref that the preceding turn "
                "told you to retain. It is intentionally NOT present in this "
                "packet. Do not read GitHub, another chat, or any external "
                "source to recover that continuity ref."
            ),
            evidence_refs=(q2_marker, q2_continuity),
            extra=(
                "The continuity evidence ref is intentionally omitted from "
                "this packet. Recover it only from the immediately preceding "
                "conversation context and include it as the second evidence_ref."
            ),
        )
        baseline = watcher.refresh()
        print(
            "STAGE12_Q2_REUSE_READY="
            "Press Ctrl+Space, then Ctrl+V, then Enter. This must reuse "
            "the same managed chat/session generation.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=q2.action.action_id,
            status=OperatorActionState.AWAITING_DURABLE_ACK,
            timeout_seconds=candidate_timeout_seconds,
        )
        q2_commit, q2_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=q2_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        _ingest_candidate(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(q2_path),
            immutable_revision=q2_commit,
            raw_bytes=q2_raw,
        )
        candidate_commits["q2"] = q2_commit
        print("STAGE12_PERSISTENT_SESSION_REUSE=PASS", flush=True)

        stale, stale_path = plan_quantum(
            phase="stale-g0",
            process_id=process_q3,
            process_generation=0,
            session_generation=0,
            sequence=3,
            objective=(
                "This packet is a stale-generation probe and must never "
                "be serviced after recovery."
            ),
            evidence_refs=(f"stage12:stale:{short}",),
            extra="This candidate must never be published.",
        )
        runtime.recover(
            process_q3,
            expected_generation=0,
            reason="stage12_stale_session_fence",
        )
        graph = runtime.snapshot().graph
        if (
            graph.operator_actions[stale.action.action_id].status
            != OperatorActionState.STALE
        ):
            raise RuntimeError("stale_action_not_fenced")
        if (
            graph.executor_sessions[slot_id].state
            != ExecutorSessionState.NEEDS_REPLACEMENT
        ):
            raise RuntimeError("stale_session_not_marked_for_replacement")

        old_contract = stale.packet_source.result_publication
        if old_contract is None:
            raise RuntimeError("stale_publication_contract_missing")
        late_bytes = json.dumps(
            {
                "publication_id": old_contract.publication_id,
                "action_id": stale.action.action_id,
                "action_generation": 0,
                "process_id": process_q3,
                "process_generation": 0,
                "executor_id": PROFILE.executor_id,
                "worker_slot_id": slot_id,
                "session_generation": 0,
                "packet_sha256": stale.packet.packet_sha256,
                "kind": "RESULT",
                "observed_at": "stage12-late-old-generation",
                "result_payload_ref": (
                    f"stage12://{token}/stale-g0/result"
                ),
                "result_payload_sha256": _sha256_text(
                    f"stage12:{token}:stale-g0:accepted"
                ),
                "evidence_refs": [f"stage12:stale:{short}"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        version_before_late = runtime.snapshot().version
        try:
            _ingest_candidate(
                runtime=runtime,
                validator=validator,
                target_ref=_candidate_target(stale_path),
                immutable_revision="d" * 40,
                raw_bytes=late_bytes,
            )
        except Exception:
            pass
        else:
            raise RuntimeError("late_old_generation_candidate_accepted")
        if runtime.snapshot().version != version_before_late:
            raise RuntimeError("late_old_generation_mutated_state")
        print("STAGE12_STALE_SESSION_FENCE=PASS", flush=True)

        broker.replace(
            slot_id=slot_id,
            expected_session_generation=1,
            session_id=f"stage12-chat:{token}:g1",
        )
        q3_marker = f"stage12:q3-replacement:{short}"
        q3, q3_path = plan_quantum(
            phase="q3-replacement",
            process_id=process_q3,
            process_generation=1,
            session_generation=1,
            sequence=4,
            objective=(
                "Perform one bounded replacement-session calibration quantum "
                "after the old generation was fenced. Use only this packet "
                "and publish the exact q3 replacement candidate. Do not rely "
                "on prior-conversation continuity."
            ),
            evidence_refs=(q3_marker,),
            extra=(
                "This is session_generation=1 replacement work. Do not use "
                "or claim continuity from the retired/stale generation."
            ),
        )
        baseline = watcher.refresh()
        print(
            "STAGE12_Q3_REPLACEMENT_READY="
            "Press Ctrl+Space, then Ctrl+V, then Enter. A replacement "
            "managed session generation must be used.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=q3.action.action_id,
            status=OperatorActionState.AWAITING_DURABLE_ACK,
            timeout_seconds=candidate_timeout_seconds,
        )
        q3_commit, q3_raw = watcher.wait_for_exact_candidate(
            baseline_head=baseline,
            path=q3_path,
            timeout_seconds=candidate_timeout_seconds,
        )
        _ingest_candidate(
            runtime=runtime,
            validator=validator,
            target_ref=_candidate_target(q3_path),
            immutable_revision=q3_commit,
            raw_bytes=q3_raw,
        )
        candidate_commits["q3_replacement"] = q3_commit

        retire = planner.plan_retire_session(
            task_id="workspace-semantic-execution-migration-v1",
            action_id=f"action:stage12:retire:{token}:sg1",
            action_generation=0,
            worker_slot_id=slot_id,
            session_generation=1,
            executor_id=PROFILE.executor_id,
            priority_rank=1,
            queue_sequence=5,
            created_at="stage12-5",
            reason="stage12_calibration_complete",
        )
        print(
            "STAGE12_FINAL_RETIRE_READY="
            "Press Ctrl+Space once to close the final managed Firefox "
            "worker tab.",
            flush=True,
        )
        _wait_action_status(
            store=store,
            action_id=retire.action_id,
            status=OperatorActionState.COMPLETED,
            timeout_seconds=candidate_timeout_seconds,
        )

        final = store.load().graph
        session = final.executor_sessions[slot_id]
        if (
            final.processes[process_q1].state != ProcessState.COMPLETED
            or final.processes[process_q2].state != ProcessState.COMPLETED
            or final.processes[process_q3].state != ProcessState.COMPLETED
            or session.state != ExecutorSessionState.RETIRED
            or session.session_generation != 1
        ):
            raise RuntimeError("stage12_final_state_mismatch")

        queued = [
            action
            for action in final.operator_actions.values()
            if action.status == OperatorActionState.QUEUED
        ]
        awaiting = [
            action
            for action in final.operator_actions.values()
            if action.status == OperatorActionState.AWAITING_DURABLE_ACK
        ]
        if queued or awaiting:
            raise RuntimeError("stage12_final_operator_work_not_empty")

        report = {
            "schema": "workspace-semantic-stage12-real-instant.v1",
            "result": "PASS",
            "real_chatgpt_account": True,
            "credential_automation": False,
            "browser_page_content_scraping": False,
            "automatic_typing_or_submission": False,
            "operator_sequence": "Ctrl+Space -> Ctrl+V -> Enter",
            "candidate_branch": CANDIDATE_BRANCH,
            "candidate_commits": candidate_commits,
            "q1_real_instant": True,
            "persistent_session_reuse": True,
            "continuity_cache_probe": True,
            "stale_session_fencing": True,
            "late_old_generation_rejected_without_mutation": True,
            "replacement_session_generation": 1,
            "final_session_state": session.state.value,
            "final_process_states": {
                "q1": final.processes[process_q1].state.value,
                "q2": final.processes[process_q2].state.value,
                "q3_replacement": final.processes[process_q3].state.value,
            },
        }
        print(
            "STAGE12_REAL_INSTANT_CALIBRATION="
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


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--serve-port", type=int, required=True)
    result.add_argument(
        "--candidate-timeout-seconds",
        type=int,
        default=900,
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if not (1024 <= args.serve_port <= 65535):
        raise SystemExit("--serve-port must be 1024..65535")
    if not (60 <= args.candidate_timeout_seconds <= 3600):
        raise SystemExit(
            "--candidate-timeout-seconds must be 60..3600"
        )

    run_calibration(
        postgres_dsn=_required_env(
            "SEMANTIC_EXECUTION_POSTGRES_DSN"
        ),
        expected_tailscale_login=_required_env(
            "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"
        ),
        serve_port=args.serve_port,
        candidate_timeout_seconds=args.candidate_timeout_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
