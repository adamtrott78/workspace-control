"""E3-A9 diagnostic successor around the accepted E2 topology.

This module is inert on import. It preserves the accepted E2/A8 bytes, binds
worker-result schema provenance to the validated A8 review head, and emits a
compact exception marker before the large resource report. Any future live run
remains separately authority-gated.
"""
from __future__ import annotations

import argparse
import builtins
from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

E2_PATH = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "live_research_iterate_e2.py"
)
OBSERVER_PATH = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "resource_observer_v1.py"
)
CANDIDATE_BASELINE = "fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f"
WORKER_RESULT_SCHEMA_PROVENANCE_HEAD = "c6dd247faaee12f1d8ade2cb53c60de41e3c3cdc"
WORKER_RESULT_SCHEMA_PATH = (
    "architecture/workspace-semantic-execution-worker-result.v0.1.json"
)
WORKER_RESULT_SCHEMA_BLOB = "b84d362a8adbb1bf4a47f1dfc4f0b8089487a3c1"
WORKER_RESULT_SCHEMA_REF = (
    "github://adamtrott78/workspace-control@"
    f"{WORKER_RESULT_SCHEMA_PROVENANCE_HEAD}/"
    f"{WORKER_RESULT_SCHEMA_PATH}#blob={WORKER_RESULT_SCHEMA_BLOB}"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class E3LiveError(RuntimeError):
    pass


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise E3LiveError(f"module_load_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_a9_schema_provenance(e2):
    original = e2._operator_params

    def a9_operator_params(**kwargs):
        return replace(
            original(**kwargs),
            result_publication_schema_ref=WORKER_RESULT_SCHEMA_REF,
        )

    e2._operator_params = a9_operator_params
    return original


def _required_sha(name: str, value: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise E3LiveError(f"{name}_must_be_exact_sha")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PhaseTracker:
    _TRANSITIONS = (
        ("E2_ROOT_DECOMPOSE=PASS", "supervisor_rehydration"),
        ("E2_SUPERVISOR_S1_REHYDRATION=PASS", "child_contracts"),
        ("E2_CHILD_CONTRACT_INHERITANCE=PASS", "exact_source_read"),
        ("E2_EXACT_SOURCE=PASS", "generation0_service"),
        ("E2_FAULT_INJECTION_ARMED=PASS", "fault_fence"),
        ("E2_WORKER_PROCESS_SESSION_FENCE=PASS", "postgres_rehydration"),
        ("E2_RUNTIME_REHYDRATION_FROM_POSTGRES=PASS", "replacement_generation"),
        ("E2_ANALYSIS_RECOVERY=PASS", "workspace_shell"),
        ("E2_WORKSPACE_SHELL_READ_ONLY_PROBE=PASS", "fan_in"),
        ("E2_FAN_IN=PASS", "synthesis"),
        ("E2_RESEARCH_ITERATE=", "complete"),
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start = time.monotonic()
        self._phase_start = self._start
        self._phase = "root_decomposition"
        self._intervals: list[dict[str, object]] = []
        self._markers: list[dict[str, object]] = []

    def phase(self) -> str:
        with self._lock:
            return self._phase

    def observe(self, line: str) -> None:
        matched = None
        for prefix, next_phase in self._TRANSITIONS:
            if line.startswith(prefix):
                matched = (prefix, next_phase)
                break
        if matched is None:
            return
        now = time.monotonic()
        with self._lock:
            elapsed = max(0.0, now - self._start)
            self._markers.append({
                "marker": matched[0],
                "observed_at": _utc_now(),
                "elapsed_seconds": elapsed,
                "phase_before": self._phase,
                "phase_after": matched[1],
            })
            self._intervals.append({
                "phase": self._phase,
                "duration_seconds": max(0.0, now - self._phase_start),
            })
            self._phase = matched[1]
            self._phase_start = now

    def finish(self) -> dict[str, object]:
        now = time.monotonic()
        with self._lock:
            intervals = list(self._intervals)
            if self._phase != "complete":
                intervals.append({
                    "phase": self._phase,
                    "duration_seconds": max(0.0, now - self._phase_start),
                })
            return {
                "elapsed_seconds": max(0.0, now - self._start),
                "markers": list(self._markers),
                "phase_intervals": intervals,
                "final_phase": self._phase,
            }


def _terminal_projection(snapshot) -> dict[str, object]:
    if snapshot is None:
        return {"status": "UNAVAILABLE", "reason": "no_final_snapshot"}
    graph = snapshot.graph
    process_states = sorted(
        f"{process.state.value}@{process.generation}"
        for process in graph.processes.values()
    )
    session_states = sorted(
        f"{session.state.value}@{session.session_generation}"
        for session in graph.executor_sessions.values()
    )
    action_states = sorted(
        action.status.value for action in graph.operator_actions.values()
    )
    ready = 0
    awaiting = 0
    for action in graph.operator_actions.values():
        if action.status.value == "QUEUED":
            ready += 1
        if action.status.value == "AWAITING_DURABLE_ACK":
            awaiting += 1
    return {
        "status": "AVAILABLE",
        "graph_version": snapshot.version,
        "process_states": process_states,
        "session_states": session_states,
        "operator_action_states": action_states,
        "queued_actions": ready,
        "awaiting_durable_ack_actions": awaiting,
    }


def run_e3_live(
    *,
    source_head: str,
    review_head: str,
    authority_head: str,
    candidate_baseline: str,
    serve_port: int,
    candidate_timeout_seconds: int,
    sample_interval_seconds: float = 1.0,
) -> tuple[dict[str, object], dict[str, object] | None]:
    source_head = _required_sha("source_head", source_head)
    review_head = _required_sha("review_head", review_head)
    authority_head = _required_sha("authority_head", authority_head)
    candidate_baseline = _required_sha(
        "candidate_baseline", candidate_baseline
    )
    if candidate_baseline != CANDIDATE_BASELINE:
        raise E3LiveError("candidate_baseline_mismatch")

    e2 = _load("e3_a9_accepted_e2_topology", E2_PATH)
    original_operator_params = _install_a9_schema_provenance(e2)
    observer_module = _load("e3_live_resource_observer", OBSERVER_PATH)
    observer = observer_module.ResourceObserver(
        root_pid=os.getpid(),
        sampling_interval_seconds=sample_interval_seconds,
    )
    tracker = PhaseTracker()
    created_runtimes = []
    runtime_lock = threading.Lock()
    sample_errors: list[str] = []
    stop = threading.Event()

    original_runtime = e2.RuntimeCoordinator

    class CapturingRuntimeCoordinator(original_runtime):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            with runtime_lock:
                created_runtimes.append(self)

    def latest_snapshot():
        with runtime_lock:
            runtime = created_runtimes[-1] if created_runtimes else None
        if runtime is None:
            return None
        try:
            return runtime.snapshot()
        except Exception as exc:
            sample_errors.append(
                f"snapshot:{type(exc).__name__}:{exc}"
            )
            return None

    original_print = getattr(e2, "print", None)

    def tracked_print(*args, **kwargs):
        sep = kwargs.get("sep", " ")
        line = sep.join(str(value) for value in args)
        tracker.observe(line)
        builtins.print(*args, **kwargs)

    e2.RuntimeCoordinator = CapturingRuntimeCoordinator
    e2.print = tracked_print

    def sampler() -> None:
        while not stop.wait(sample_interval_seconds):
            try:
                observer.sample(
                    latest_snapshot(),
                    state_backend="postgresql",
                    phase=tracker.phase(),
                )
            except Exception as exc:
                sample_errors.append(
                    f"observer:{type(exc).__name__}:{exc}"
                )

    observer.begin_phase("e3_live_research_iterate")
    observer.sample(
        None,
        state_backend="postgresql",
        phase=tracker.phase(),
    )
    thread = threading.Thread(
        target=sampler,
        name="e3-resource-observer",
        daemon=True,
    )
    thread.start()

    e2_report = None
    execution_error = None
    try:
        e2_report = e2.run_e2(
            postgres_dsn=e2._required_env(
                "SEMANTIC_EXECUTION_POSTGRES_DSN"
            ),
            expected_tailscale_login=e2._required_env(
                "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"
            ),
            serve_port=serve_port,
            candidate_timeout_seconds=candidate_timeout_seconds,
        )
    except Exception as exc:
        execution_error = f"{type(exc).__name__}:{exc}"
        print("E3_A9_EXECUTION_ERROR=" + execution_error, flush=True)
    finally:
        stop.set()
        thread.join(timeout=max(5.0, sample_interval_seconds * 2))
        final_snapshot = latest_snapshot()
        try:
            observer.sample(
                final_snapshot,
                state_backend="postgresql",
                expected_object_counts={
                    "processes": 4,
                    "executor_sessions": 1,
                    "operator_actions": 5,
                },
                phase="cleanup",
            )
        except Exception as exc:
            sample_errors.append(
                f"final_observer:{type(exc).__name__}:{exc}"
            )
        observer.end_phase("e3_live_research_iterate")
        e2._operator_params = original_operator_params
        e2.RuntimeCoordinator = original_runtime
        if original_print is None:
            delattr(e2, "print")
        else:
            e2.print = original_print

    resource_report = observer.report()
    terminal = _terminal_projection(final_snapshot)
    phase_timing = tracker.finish()
    final_ok = (
        execution_error is None
        and isinstance(e2_report, dict)
        and e2_report.get("result") == "PASS"
        and not sample_errors
        and terminal.get("status") == "AVAILABLE"
        and terminal.get("process_states")
        == ["COMPLETED@0", "COMPLETED@0", "COMPLETED@0", "COMPLETED@1"]
        and terminal.get("session_states") == ["READY@1"]
        and terminal.get("queued_actions") == 0
        and terminal.get("awaiting_durable_ack_actions") == 0
    )
    report = {
        "schema_version": 1,
        "artifact_id": "workspace-semantic-execution-e3-a9-live-resource-v1",
        "result": "PASS" if final_ok else "FAIL",
        "bindings": {
            "source_head": source_head,
            "review_head": review_head,
            "authority_head": authority_head,
            "candidate_baseline": candidate_baseline,
        },
        "accepted_topology": "research-iterate-e2-a9-diagnostic-successor",
        "model_path": "real_instant_existing_e2_actions",
        "observer_sample_interval_seconds": sample_interval_seconds,
        "phase_timing": phase_timing,
        "terminal_projection": terminal,
        "sampling": resource_report["sampling"],
        "resource_report": resource_report,
        "sample_errors": sample_errors,
        "execution_error": execution_error,
        "e2_result": None if e2_report is None else e2_report.get("result"),
        "automatic_typing_or_submission": False,
        "browser_page_content_scraping": False,
        "gpu_telemetry": False,
        "padataset_access": False,
        "paid_api_fallback": False,
        "workspace_shell_authority_widened": False,
    }
    return report, e2_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--review-head", required=True)
    parser.add_argument("--authority-head", required=True)
    parser.add_argument("--candidate-baseline", required=True)
    parser.add_argument("--serve-port", type=int, default=8765)
    parser.add_argument(
        "--candidate-timeout-seconds",
        type=int,
        default=1200,
    )
    parser.add_argument(
        "--sample-interval-seconds",
        type=float,
        default=1.0,
    )
    args = parser.parse_args()
    report, _ = run_e3_live(
        source_head=args.source_head,
        review_head=args.review_head,
        authority_head=args.authority_head,
        candidate_baseline=args.candidate_baseline,
        serve_port=args.serve_port,
        candidate_timeout_seconds=args.candidate_timeout_seconds,
        sample_interval_seconds=args.sample_interval_seconds,
    )
    print(
        "E3_A9_LIVE_RESOURCE_REPORT="
        + json.dumps(report, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
