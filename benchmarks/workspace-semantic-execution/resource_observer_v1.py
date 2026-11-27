"""Read-only E3 resource/accounting observer for semantic-execution canaries."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.domain import (  # noqa: E402
    OperatorActionKernel,
    OperatorActionState,
    OperatorHumanRequirement,
)


SCHEMA_VERSION = 1
REPORT_ID = "workspace-semantic-execution-e3-resource-observer-v1"
_AVAILABLE = "AVAILABLE"
_PARTIAL = "PARTIAL"
_UNAVAILABLE = "UNAVAILABLE"


def _metric(
    value: object | None = None,
    *,
    status: str = _AVAILABLE,
    reason: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {"status": status, "value": value}
    if reason is not None:
        result["reason"] = reason
    return result


def canonical_json(value: object) -> str:
    """Return deterministic JSON bytes-as-text for an already-captured report."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _counter(items: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return dict(sorted(counts.items()))


def _state_generation_counter(
    records: Iterable[tuple[str, int]],
) -> dict[str, int]:
    return _counter(f"{state}@{generation}" for state, generation in records)


def _expected_counts(
    actual: Mapping[str, int],
    expected: Mapping[str, int] | None,
) -> dict[str, object]:
    if expected is None:
        return {
            "status": _UNAVAILABLE,
            "reason": "expected_object_counts_not_supplied",
            "actual": dict(sorted(actual.items())),
            "expected": None,
            "matches": None,
        }
    normalized = {str(key): int(value) for key, value in expected.items()}
    return {
        "status": _AVAILABLE,
        "actual": dict(sorted(actual.items())),
        "expected": dict(sorted(normalized.items())),
        "matches": all(actual.get(key) == value for key, value in normalized.items()),
    }


def durable_accounting(
    snapshot: object | None,
    *,
    state_backend: str = "UNKNOWN",
    expected_object_counts: Mapping[str, int] | None = None,
) -> dict[str, object]:
    """Project a StateSnapshot into counts only; never mutate the graph."""
    if snapshot is None:
        return {
            "status": _UNAVAILABLE,
            "reason": "state_snapshot_not_supplied",
            "state_backend": state_backend,
        }

    version = getattr(snapshot, "version", None)
    graph = getattr(snapshot, "graph", None)
    if version is None or graph is None:
        return {
            "status": _UNAVAILABLE,
            "reason": "invalid_state_snapshot",
            "state_backend": state_backend,
        }

    processes = list(graph.processes.values())
    sessions = list(graph.executor_sessions.values())
    actions = list(graph.operator_actions.values())

    process_records = [
        (_enum_value(process.state), int(process.generation))
        for process in processes
    ]
    session_records = [
        (_enum_value(session.state), int(session.session_generation))
        for session in sessions
    ]
    action_records = [
        (_enum_value(action.status), int(action.generation))
        for action in actions
    ]

    ready_manual = 0
    sent_unconfirmed = 0
    awaiting_ack_total = 0
    for action in actions:
        if action.status == OperatorActionState.QUEUED:
            if (
                action.human_requirement != OperatorHumanRequirement.NONE
                and OperatorActionKernel.binding_is_current(
                    graph,
                    action,
                    require_bound_session=(
                        action.human_requirement
                        == OperatorHumanRequirement.PASTE_AND_SUBMIT
                    ),
                )
            ):
                ready_manual += 1
        elif action.status == OperatorActionState.AWAITING_DURABLE_ACK:
            awaiting_ack_total += 1
            if OperatorActionKernel.binding_is_current(
                graph,
                action,
                require_bound_session=False,
            ):
                sent_unconfirmed += 1

    actual_counts = {
        "processes": len(processes),
        "executor_sessions": len(sessions),
        "operator_actions": len(actions),
        "packet_sources": len(graph.packet_sources),
        "worker_results": len(graph.worker_results),
        "scheduler_dispatches": len(graph.scheduler_dispatches),
    }

    return {
        "status": _AVAILABLE,
        "state_backend": state_backend,
        "graph_version": int(version),
        "event_seq": int(graph.event_seq),
        "objects": _expected_counts(actual_counts, expected_object_counts),
        "reasoning_processes": {
            "total": len(processes),
            "by_state": _counter(state for state, _ in process_records),
            "by_generation": _counter(
                str(generation) for _, generation in process_records
            ),
            "by_state_generation": _state_generation_counter(process_records),
        },
        "executor_sessions": {
            "total": len(sessions),
            "by_state": _counter(state for state, _ in session_records),
            "by_generation": _counter(
                str(generation) for _, generation in session_records
            ),
            "by_state_generation": _state_generation_counter(session_records),
        },
        "operator_actions": {
            "total": len(actions),
            "by_state": _counter(state for state, _ in action_records),
            "by_generation": _counter(
                str(generation) for _, generation in action_records
            ),
            "ready_manual_cycles": ready_manual,
            "sent_unconfirmed_current_binding": sent_unconfirmed,
            "awaiting_durable_ack_total": awaiting_ack_total,
        },
    }


@dataclass(frozen=True)
class _PidSample:
    pid: int
    start_ticks: int
    user_ticks: int
    system_ticks: int
    rss_bytes: int | None
    peak_rss_bytes: int | None
    pss_bytes: int | None
    thread_count: int | None
    fd_count: int | None
    children: tuple[int, ...]
    children_available: bool


def _parse_stat(text: str) -> tuple[int, int, int]:
    rparen = text.rfind(")")
    if rparen < 0:
        raise ValueError("proc_stat_comm_missing")
    fields = text[rparen + 2 :].split()
    if len(fields) <= 19:
        raise ValueError("proc_stat_too_short")
    return int(fields[11]), int(fields[12]), int(fields[19])


def _parse_status_value_kib(status: Mapping[str, str], key: str) -> int | None:
    value = status.get(key)
    if value is None:
        return None
    fields = value.split()
    if not fields:
        return None
    number = int(fields[0])
    unit = fields[1].lower() if len(fields) > 1 else "kb"
    if unit not in {"kb", "kib"}:
        return None
    return number * 1024


def _parse_status(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


class ResourceObserver:
    """Best-effort Linux /proc observer with explicit missing-data accounting."""

    def __init__(
        self,
        *,
        root_pid: int | None = None,
        proc_root: Path | str = "/proc",
        sampling_interval_seconds: float = 1.0,
        clock_ticks_per_second: int | None = None,
        monotonic_clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], str] | None = None,
    ) -> None:
        if sampling_interval_seconds <= 0:
            raise ValueError("sampling_interval_seconds_must_be_positive")
        self.root_pid = int(root_pid if root_pid is not None else os.getpid())
        self.proc_root = Path(proc_root)
        self.sampling_interval_seconds = float(sampling_interval_seconds)
        self.clock_ticks_per_second = int(
            clock_ticks_per_second
            if clock_ticks_per_second is not None
            else os.sysconf("SC_CLK_TCK")
        )
        if self.clock_ticks_per_second <= 0:
            raise ValueError("clock_ticks_per_second_must_be_positive")
        self._monotonic = monotonic_clock
        self._wall_clock = wall_clock or (
            lambda: datetime.now(timezone.utc).isoformat()
        )
        self._samples: list[dict[str, object]] = []
        self._phases: list[dict[str, object]] = []
        self._phase_starts: dict[str, tuple[str, float]] = {}
        self._previous_cpu: dict[tuple[int, int], tuple[int, int]] | None = None
        self._last_sample_monotonic: float | None = None
        self._gap_count = 0
        self._missing_sample_count = 0

    def begin_phase(self, name: str) -> None:
        if not name or name in self._phase_starts:
            raise ValueError(f"phase_already_started_or_invalid:{name}")
        self._phase_starts[name] = (self._wall_clock(), self._monotonic())

    def end_phase(self, name: str) -> dict[str, object]:
        started = self._phase_starts.pop(name, None)
        if started is None:
            raise ValueError(f"phase_not_started:{name}")
        ended_at = self._wall_clock()
        ended_mono = self._monotonic()
        phase = {
            "name": name,
            "started_at": started[0],
            "ended_at": ended_at,
            "duration_seconds": max(0.0, ended_mono - started[1]),
        }
        self._phases.append(phase)
        return dict(phase)

    def _read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            return None

    def _read_pid(self, pid: int) -> _PidSample | None:
        base = self.proc_root / str(pid)
        stat_text = self._read_text(base / "stat")
        status_text = self._read_text(base / "status")
        if stat_text is None or status_text is None:
            return None

        try:
            user_ticks, system_ticks, start_ticks = _parse_stat(stat_text)
        except (ValueError, IndexError):
            return None

        status = _parse_status(status_text)
        rss = _parse_status_value_kib(status, "VmRSS")
        peak_rss = _parse_status_value_kib(status, "VmHWM")
        threads_raw = status.get("Threads")
        try:
            thread_count = (
                int(threads_raw.split()[0]) if threads_raw is not None else None
            )
        except (ValueError, IndexError):
            thread_count = None

        try:
            fd_count = sum(1 for _ in (base / "fd").iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            fd_count = None

        pss = None
        smaps = self._read_text(base / "smaps_rollup")
        if smaps is not None:
            pss = _parse_status_value_kib(_parse_status(smaps), "Pss")

        children_path = base / "task" / str(pid) / "children"
        children_text = self._read_text(children_path)
        if children_text is None:
            children: tuple[int, ...] = ()
            children_available = False
        else:
            try:
                children = tuple(
                    int(value) for value in children_text.split() if value
                )
                children_available = True
            except ValueError:
                children = ()
                children_available = False

        return _PidSample(
            pid=pid,
            start_ticks=start_ticks,
            user_ticks=user_ticks,
            system_ticks=system_ticks,
            rss_bytes=rss,
            peak_rss_bytes=peak_rss,
            pss_bytes=pss,
            thread_count=thread_count,
            fd_count=fd_count,
            children=children,
            children_available=children_available,
        )

    def _process_tree(self) -> tuple[list[_PidSample], bool]:
        queue = [self.root_pid]
        seen: set[int] = set()
        records: list[_PidSample] = []
        enumeration_complete = True
        while queue:
            pid = queue.pop(0)
            if pid in seen:
                continue
            seen.add(pid)
            record = self._read_pid(pid)
            if record is None:
                enumeration_complete = False
                continue
            records.append(record)
            if not record.children_available:
                enumeration_complete = False
            for child in record.children:
                if child not in seen:
                    queue.append(child)
        records.sort(key=lambda item: item.pid)
        return records, enumeration_complete

    @staticmethod
    def _aggregate_metric(
        records: list[_PidSample],
        attribute: str,
    ) -> dict[str, object]:
        values = [getattr(record, attribute) for record in records]
        available = [int(value) for value in values if value is not None]
        missing = len(values) - len(available)
        if not available:
            return _metric(
                None,
                status=_UNAVAILABLE,
                reason=f"{attribute}_unavailable_for_all_processes",
            )
        if missing:
            return _metric(
                sum(available),
                status=_PARTIAL,
                reason=f"{attribute}_unavailable_for_{missing}_processes",
            )
        return _metric(sum(available))

    def _cpu_delta(
        self,
        records: list[_PidSample],
    ) -> tuple[dict[str, object], dict[str, object]]:
        current = {
            (record.pid, record.start_ticks): (
                record.user_ticks,
                record.system_ticks,
            )
            for record in records
        }
        previous = self._previous_cpu
        self._previous_cpu = current
        if previous is None:
            reason = "baseline_not_established"
            return (
                _metric(None, status=_UNAVAILABLE, reason=reason),
                _metric(None, status=_UNAVAILABLE, reason=reason),
            )

        user_ticks = 0
        system_ticks = 0
        partial_reasons: list[str] = []
        for identity, values in current.items():
            before = previous.get(identity)
            if before is None:
                user_ticks += max(0, values[0])
                system_ticks += max(0, values[1])
                if identity[0] == self.root_pid:
                    partial_reasons.append("root_process_identity_changed")
            else:
                user_ticks += max(0, values[0] - before[0])
                system_ticks += max(0, values[1] - before[1])

        disappeared = set(previous) - set(current)
        if disappeared:
            partial_reasons.append(
                f"{len(disappeared)}_processes_exited_between_samples"
            )

        status = _PARTIAL if partial_reasons else _AVAILABLE
        reason = ",".join(sorted(partial_reasons)) or None
        scale = float(self.clock_ticks_per_second)
        return (
            _metric(user_ticks / scale, status=status, reason=reason),
            _metric(system_ticks / scale, status=status, reason=reason),
        )

    def _sampling_gap(self, now_mono: float) -> dict[str, object]:
        if self._last_sample_monotonic is None:
            self._last_sample_monotonic = now_mono
            return {
                "elapsed_since_previous_seconds": _metric(
                    None,
                    status=_UNAVAILABLE,
                    reason="first_sample",
                ),
                "gap_detected": False,
                "estimated_missing_samples": 0,
            }

        elapsed = max(0.0, now_mono - self._last_sample_monotonic)
        self._last_sample_monotonic = now_mono
        gap = elapsed > self.sampling_interval_seconds * 1.5
        missing = 0
        if gap:
            missing = max(
                1,
                int(round(elapsed / self.sampling_interval_seconds)) - 1,
            )
            self._gap_count += 1
            self._missing_sample_count += missing
        return {
            "elapsed_since_previous_seconds": _metric(elapsed),
            "gap_detected": gap,
            "estimated_missing_samples": missing,
        }

    def sample(
        self,
        snapshot: object | None = None,
        *,
        state_backend: str = "UNKNOWN",
        expected_object_counts: Mapping[str, int] | None = None,
        phase: str | None = None,
    ) -> dict[str, object]:
        observed_at = self._wall_clock()
        now_mono = self._monotonic()
        records, enumeration_complete = self._process_tree()
        cpu_user, cpu_system = self._cpu_delta(records)

        if records:
            process_count = _metric(len(records))
            if enumeration_complete:
                child_count = _metric(max(0, len(records) - 1))
            else:
                child_count = _metric(
                    max(0, len(records) - 1),
                    status=_PARTIAL,
                    reason="process_tree_enumeration_incomplete",
                )
        else:
            process_count = _metric(
                None,
                status=_UNAVAILABLE,
                reason="root_process_unavailable",
            )
            child_count = _metric(
                None,
                status=_UNAVAILABLE,
                reason="root_process_unavailable",
            )

        sample = {
            "sample_index": len(self._samples),
            "observed_at": observed_at,
            "phase": phase,
            "sampling": self._sampling_gap(now_mono),
            "process_tree": {
                "root_pid": self.root_pid,
                "process_count": process_count,
                "managed_child_process_count": child_count,
                "cpu_user_delta_seconds": cpu_user,
                "cpu_system_delta_seconds": cpu_system,
                "rss_bytes": self._aggregate_metric(records, "rss_bytes"),
                "peak_rss_bytes": self._aggregate_metric(
                    records, "peak_rss_bytes"
                ),
                "peak_rss_semantics": "SUM_OF_PER_PROCESS_VM_HWM",
                "pss_bytes": self._aggregate_metric(records, "pss_bytes"),
                "thread_count": self._aggregate_metric(
                    records, "thread_count"
                ),
                "file_descriptor_count": self._aggregate_metric(
                    records, "fd_count"
                ),
            },
            "durable_state": durable_accounting(
                snapshot,
                state_backend=state_backend,
                expected_object_counts=expected_object_counts,
            ),
        }
        self._samples.append(sample)
        return json.loads(canonical_json(sample))

    def report(self) -> dict[str, object]:
        unfinished = [
            {
                "name": name,
                "started_at": started[0],
                "status": "OPEN",
            }
            for name, started in sorted(self._phase_starts.items())
        ]
        report = {
            "schema_version": SCHEMA_VERSION,
            "report_id": REPORT_ID,
            "observer": {
                "root_pid": self.root_pid,
                "proc_root": str(self.proc_root),
                "sampling_interval_seconds": self.sampling_interval_seconds,
                "requires_root": False,
                "gpu_telemetry": "FORBIDDEN_NOT_COLLECTED",
                "padataset_access": "FORBIDDEN_NOT_USED",
            },
            "sampling": {
                "sample_count": len(self._samples),
                "gap_count": self._gap_count,
                "estimated_missing_sample_count": self._missing_sample_count,
            },
            "phases": list(self._phases),
            "open_phases": unfinished,
            "samples": list(self._samples),
        }
        return json.loads(canonical_json(report))
