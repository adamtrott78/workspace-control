"""E3-C2 bounded no-model resource/accounting soak.

The claim-bearing rules are frozen in
architecture/workspace-semantic-execution-research-iterate-e3-c2-review.v0.1.json.
This harness reuses the accepted E2 deterministic recovery canary unchanged.
"""
from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

CANARY_PATH = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "research_iterate_e2_recovery_canary_v1.py"
)
OBSERVER_PATH = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "resource_observer_v1.py"
)

CYCLES = 1000
SAMPLE_EVERY = 10
WARMUP_CYCLES = 100
SAMPLING_INTERVAL_SECONDS = 10.0
GPU_MODULE_PREFIXES = ("torch", "tensorflow", "cupy", "pynvml")


class E3C2SoakError(RuntimeError):
    pass


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise E3C2SoakError(f"module_load_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _gpu_modules() -> set[str]:
    return {
        name for name in sys.modules
        if name.split(".", 1)[0] in GPU_MODULE_PREFIXES
    }


def _metric_value(sample: dict[str, object], name: str):
    metric = sample["process_tree"][name]
    if metric["status"] == "UNAVAILABLE":
        return None
    value = metric["value"]
    return None if value is None else float(value)


def _available_values(
    samples: Iterable[dict[str, object]], name: str
) -> list[float]:
    result: list[float] = []
    for sample in samples:
        value = _metric_value(sample, name)
        if value is not None:
            result.append(value)
    return result


def _summary(values: list[float]) -> dict[str, object]:
    if not values:
        return {"status": "UNAVAILABLE", "count": 0}
    return {
        "status": "AVAILABLE",
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def _three_window_growth(values: list[float]) -> dict[str, object]:
    if len(values) < 3:
        return {
            "status": "UNAVAILABLE",
            "reason": "fewer_than_three_available_samples",
            "monotonic_growth": None,
        }
    cut1 = len(values) // 3
    cut2 = (2 * len(values)) // 3
    windows = [values[:cut1], values[cut1:cut2], values[cut2:]]
    if any(not window for window in windows):
        return {
            "status": "UNAVAILABLE",
            "reason": "empty_chronological_window",
            "monotonic_growth": None,
        }
    medians = [statistics.median(window) for window in windows]
    minima = [min(window) for window in windows]
    growth = (
        medians[0] < medians[1] < medians[2]
        and minima[0] < minima[1] < minima[2]
    )
    return {
        "status": "AVAILABLE",
        "window_sizes": [len(window) for window in windows],
        "window_medians": medians,
        "window_minima": minima,
        "monotonic_growth": growth,
    }


def _cycle(canary):
    original = canary.RuntimeCoordinator
    created = []

    class CapturingRuntimeCoordinator(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(self)

    canary.RuntimeCoordinator = CapturingRuntimeCoordinator
    try:
        result = canary.run_e2_recovery_canary()
    finally:
        canary.RuntimeCoordinator = original
    if not created:
        raise E3C2SoakError("accepted_canary_created_no_runtime")
    return result, created[-1].snapshot()


def _check_cycle(report: dict[str, object]) -> list[str]:
    failures: list[str] = []
    expected_true = (
        "worker_process_loss_injected",
        "session_loss_injected",
        "old_operator_action_staled",
        "late_old_candidate_rejected_without_mutation",
        "orchestrator_runtime_restarted",
        "durable_state_rehydrated_without_chat_memory",
        "replacement_session_created",
        "replacement_packet_recompiled_from_typed_state",
        "replacement_worker_completed",
        "final_rehydration_completed",
    )
    if report.get("result") != "PASS":
        failures.append("cycle_result_not_pass")
    if report.get("process_generation") != {"before": 0, "after": 1}:
        failures.append("process_generation_not_0_to_1")
    if report.get("session_generation") != {"before": 0, "after": 1}:
        failures.append("session_generation_not_0_to_1")
    for key in expected_true:
        if report.get(key) is not True:
            failures.append(f"{key}_not_true")
    if report.get("manual_state_relay") is not False:
        failures.append("manual_state_relay_not_false")
    if report.get("chat_transcript_in_durable_graph") is not False:
        failures.append("chat_transcript_in_durable_graph_not_false")
    return failures


def _check_terminal(sample: dict[str, object]) -> list[str]:
    failures: list[str] = []
    durable = sample["durable_state"]
    if durable.get("status") != "AVAILABLE":
        return ["durable_state_unavailable"]
    if durable["reasoning_processes"]["by_state_generation"] != {
        "COMPLETED@1": 1
    }:
        failures.append("terminal_process_state_mismatch")
    if durable["executor_sessions"]["by_state_generation"] != {"READY@1": 1}:
        failures.append("terminal_session_state_mismatch")
    if durable["operator_actions"]["by_state"] != {
        "COMPLETED": 1,
        "STALE": 1,
    }:
        failures.append("terminal_action_state_mismatch")
    if durable["operator_actions"]["ready_manual_cycles"] != 0:
        failures.append("terminal_ready_manual_nonzero")
    if durable["operator_actions"]["sent_unconfirmed_current_binding"] != 0:
        failures.append("terminal_sent_unconfirmed_nonzero")
    if durable["operator_actions"]["awaiting_durable_ack_total"] != 0:
        failures.append("terminal_awaiting_ack_nonzero")
    objects = durable["objects"]
    if objects.get("matches") is not True:
        failures.append("terminal_object_count_mismatch")
    return failures


def _check_discrete(
    samples: list[dict[str, object]],
    cleanup: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    names = (
        "process_count",
        "thread_count",
        "file_descriptor_count",
        "managed_child_process_count",
    )
    evidence: dict[str, object] = {}
    failures: list[str] = []
    for name in names:
        values = _available_values(samples, name)
        entry: dict[str, object] = {
            "count": len(values),
            "values": sorted(set(values)),
            "invariant": len(values) == len(samples) and len(set(values)) == 1,
        }
        cleanup_value = _metric_value(cleanup, name)
        entry["cleanup_value"] = cleanup_value
        entry["cleanup_lte_steady_max"] = (
            cleanup_value is not None
            and bool(values)
            and cleanup_value <= max(values)
        )
        if not entry["invariant"]:
            failures.append(f"{name}_not_invariant")
        if not entry["cleanup_lte_steady_max"]:
            failures.append(f"{name}_cleanup_growth")
        evidence[name] = entry
    return evidence, failures


def run_e3_c2_soak(
    *,
    cycles: int = CYCLES,
    sample_every: int = SAMPLE_EVERY,
    warmup_cycles: int = WARMUP_CYCLES,
) -> tuple[dict[str, object], dict[str, object]]:
    if cycles != CYCLES or sample_every != SAMPLE_EVERY or warmup_cycles != WARMUP_CYCLES:
        raise E3C2SoakError("claim_bearing_bounds_are_frozen")

    canary = _load("e3_c2_accepted_e2_canary", CANARY_PATH)
    observer_module = _load("e3_c2_resource_observer", OBSERVER_PATH)
    observer = observer_module.ResourceObserver(
        root_pid=os.getpid(),
        sampling_interval_seconds=SAMPLING_INTERVAL_SECONDS,
    )
    gpu_before = _gpu_modules()
    failures: list[str] = []
    recovery_cycles = 0
    final_snapshot = None

    observer.begin_phase("bounded_no_model_soak")
    observer.sample(phase="baseline")
    for index in range(1, cycles + 1):
        try:
            cycle_report, final_snapshot = _cycle(canary)
            cycle_failures = _check_cycle(cycle_report)
            if cycle_failures:
                failures.extend(
                    f"cycle_{index}:{item}" for item in cycle_failures
                )
            else:
                recovery_cycles += 1
        except Exception as exc:
            failures.append(f"cycle_{index}:exception:{type(exc).__name__}:{exc}")
            break

        if index % sample_every == 0 and final_snapshot is not None:
            sample = observer.sample(
                final_snapshot,
                state_backend="in_memory",
                expected_object_counts={
                    "processes": 1,
                    "executor_sessions": 1,
                    "operator_actions": 2,
                },
                phase=f"cycle-{index}",
            )
            failures.extend(
                f"cycle_{index}:{item}" for item in _check_terminal(sample)
            )

    observer.end_phase("bounded_no_model_soak")
    if final_snapshot is None:
        raise E3C2SoakError("no_final_snapshot")

    pre_cleanup = observer.sample(
        final_snapshot,
        state_backend="in_memory",
        expected_object_counts={
            "processes": 1,
            "executor_sessions": 1,
            "operator_actions": 2,
        },
        phase="pre-cleanup",
    )
    gc.collect()
    cleanup = observer.sample(
        final_snapshot,
        state_backend="in_memory",
        expected_object_counts={
            "processes": 1,
            "executor_sessions": 1,
            "operator_actions": 2,
        },
        phase="cleanup",
    )
    failures.extend(f"cleanup:{item}" for item in _check_terminal(cleanup))

    report = observer.report()
    cycle_samples = [
        sample for sample in report["samples"]
        if isinstance(sample.get("phase"), str)
        and sample["phase"].startswith("cycle-")
    ]
    steady = [
        sample for sample in cycle_samples
        if int(sample["phase"].split("-", 1)[1]) > warmup_cycles
    ]

    discrete, discrete_failures = _check_discrete(steady, cleanup)
    failures.extend(discrete_failures)

    required_metrics = (
        "cpu_user_delta_seconds",
        "cpu_system_delta_seconds",
        "rss_bytes",
        "peak_rss_bytes",
    )
    metric_summaries: dict[str, object] = {}
    for name in required_metrics:
        values = _available_values(steady, name)
        metric_summaries[name] = _summary(values)
        if len(values) != len(steady):
            failures.append(f"{name}_missing_steady_samples")

    rss_growth = _three_window_growth(_available_values(steady, "rss_bytes"))
    if rss_growth.get("monotonic_growth") is True:
        failures.append("rss_monotonic_growth")
    pss_values = _available_values(steady, "pss_bytes")
    pss_growth = _three_window_growth(pss_values)
    if pss_growth.get("monotonic_growth") is True:
        failures.append("pss_monotonic_growth")

    gpu_after = _gpu_modules()
    new_gpu_modules = sorted(gpu_after - gpu_before)
    if new_gpu_modules:
        failures.append("gpu_modules_loaded")

    phase = next(
        item for item in report["phases"]
        if item["name"] == "bounded_no_model_soak"
    )
    report_json = observer_module.canonical_json(report)
    report_sha256 = hashlib.sha256(report_json.encode("utf-8")).hexdigest()

    summary = {
        "schema_version": 1,
        "artifact_id": "workspace-semantic-execution-e3-c2-soak-v1",
        "result": "PASS" if not failures else "FAIL",
        "bounds": {
            "cycles": cycles,
            "sample_every_cycles": sample_every,
            "warmup_cycles": warmup_cycles,
            "sampling_interval_seconds": SAMPLING_INTERVAL_SECONDS,
        },
        "model_calls": 0,
        "human_service_cycles": 0,
        "gpu_use": False,
        "padataset_access": False,
        "recovery_cycles_completed": recovery_cycles,
        "cycle_sample_count": len(cycle_samples),
        "steady_sample_count": len(steady),
        "terminal_contract": {
            "process": {"COMPLETED@1": 1},
            "session": {"READY@1": 1},
            "actions": {"COMPLETED": 1, "STALE": 1},
            "ready_manual_cycles": 0,
            "sent_unconfirmed_current_binding": 0,
            "awaiting_durable_ack_total": 0,
        },
        "resource_summaries": metric_summaries,
        "discrete_resource_evidence": discrete,
        "rss_three_window_growth": rss_growth,
        "pss_three_window_growth": pss_growth,
        "sampling": report["sampling"],
        "phase_duration_seconds": phase["duration_seconds"],
        "pre_cleanup_process_tree": pre_cleanup["process_tree"],
        "cleanup_process_tree": cleanup["process_tree"],
        "new_gpu_modules": new_gpu_modules,
        "resource_report_sha256": report_sha256,
        "failures": failures,
    }
    return summary, report


def main() -> int:
    summary, report = run_e3_c2_soak()
    canonical = lambda value: json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    print("E3_C2_SUMMARY=" + canonical(summary))
    print("E3_C2_REPORT=" + canonical(report))
    if summary["result"] != "PASS":
        raise E3C2SoakError(canonical(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
