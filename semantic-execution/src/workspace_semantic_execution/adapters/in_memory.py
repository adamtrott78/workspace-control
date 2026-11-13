"""Deterministic in-memory adapters for semantic-execution tests and spikes."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from ..domain import (
    ActionSpec,
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    DomainKernel,
    EffectReceipt,
    ExecutorAvailability,
    ExecutorProfile,
    WorkGraph,
)
from ..ports import (
    DurableWorkConflict,
    DurableWorkRequest,
    DurableWorkState,
    DurableWorkStatus,
    RuntimeEvent,
    StateConflict,
    StateNotInitialized,
    StateSnapshot,
    TelemetryRecord,
)


class InMemoryStateStore:
    def __init__(self) -> None:
        self._snapshot: StateSnapshot | None = None

    def initialize(self, graph: WorkGraph) -> StateSnapshot:
        if self._snapshot is not None:
            raise StateConflict("state_already_initialized")
        DomainKernel.validate(graph)
        self._snapshot = StateSnapshot(
            version=0,
            graph=deepcopy(graph),
        )
        return deepcopy(self._snapshot)

    def load(self) -> StateSnapshot:
        if self._snapshot is None:
            raise StateNotInitialized("state_not_initialized")
        return deepcopy(self._snapshot)

    def compare_and_swap(
        self,
        *,
        expected_version: int,
        graph: WorkGraph,
    ) -> StateSnapshot:
        if self._snapshot is None:
            raise StateNotInitialized("state_not_initialized")
        if expected_version != self._snapshot.version:
            raise StateConflict(
                "stale_state_version:"
                f"expected={expected_version}:current={self._snapshot.version}"
            )
        DomainKernel.validate(graph)
        self._snapshot = StateSnapshot(
            version=self._snapshot.version + 1,
            graph=deepcopy(graph),
        )
        return deepcopy(self._snapshot)


class InMemoryEventLedger:
    def __init__(self) -> None:
        self._events_by_id: dict[str, RuntimeEvent] = {}
        self._order: list[str] = []

    def publish_event(self, event: RuntimeEvent) -> bool:
        if not event.event_id or not event.wait_key or not event.observed_at:
            raise ValueError("runtime_event_required_fields")
        existing = self._events_by_id.get(event.event_id)
        if existing is not None:
            if existing != event:
                raise ValueError("conflicting_duplicate_runtime_event")
            return False
        self._events_by_id[event.event_id] = deepcopy(event)
        self._order.append(event.event_id)
        return True

    def find_event(self, *, wait_key: str) -> RuntimeEvent | None:
        if not wait_key:
            raise ValueError("wait_key_required")
        for event_id in self._order:
            event = self._events_by_id[event_id]
            if event.wait_key == wait_key:
                return deepcopy(event)
        return None


class InMemoryDurableRuntime:
    """Reference implementation of idempotent bounded work submission."""

    def __init__(self) -> None:
        self._requests: dict[str, DurableWorkRequest] = {}
        self._statuses: dict[str, DurableWorkStatus] = {}

    def submit(self, request: DurableWorkRequest) -> bool:
        if not request.work_id or not request.work_kind or not request.queue_name:
            raise ValueError("durable_work_required_fields")
        existing = self._requests.get(request.work_id)
        if existing is not None:
            if existing != request:
                raise DurableWorkConflict("conflicting_durable_work_id")
            return False
        self._requests[request.work_id] = deepcopy(request)
        self._statuses[request.work_id] = DurableWorkStatus(
            work_id=request.work_id,
            state=DurableWorkState.ENQUEUED,
        )
        return True

    def get_status(self, *, work_id: str) -> DurableWorkStatus | None:
        status = self._statuses.get(work_id)
        return deepcopy(status) if status is not None else None

    def mark_running(self, *, work_id: str) -> DurableWorkStatus:
        if work_id not in self._requests:
            raise KeyError(work_id)
        status = DurableWorkStatus(
            work_id=work_id,
            state=DurableWorkState.RUNNING,
        )
        self._statuses[work_id] = status
        return deepcopy(status)

    def complete(
        self,
        *,
        work_id: str,
        result_ref: str,
    ) -> DurableWorkStatus:
        if work_id not in self._requests:
            raise KeyError(work_id)
        if not result_ref:
            raise ValueError("result_ref_required")
        status = DurableWorkStatus(
            work_id=work_id,
            state=DurableWorkState.COMPLETED,
            result_ref=result_ref,
        )
        self._statuses[work_id] = status
        return deepcopy(status)

    def fail(
        self,
        *,
        work_id: str,
        error: str,
    ) -> DurableWorkStatus:
        if work_id not in self._requests:
            raise KeyError(work_id)
        if not error:
            raise ValueError("error_required")
        status = DurableWorkStatus(
            work_id=work_id,
            state=DurableWorkState.FAILED,
            error=error,
        )
        self._statuses[work_id] = status
        return deepcopy(status)


class FakeClock:
    def __init__(self, *, seconds: float = 0.0) -> None:
        self._seconds = float(seconds)

    def now(self) -> str:
        return f"T+{self._seconds:012.3f}"

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("clock_cannot_move_backward")
        self._seconds += float(seconds)


class RecordingTelemetry:
    def __init__(self) -> None:
        self.records: list[TelemetryRecord] = []

    def record(self, record: TelemetryRecord) -> None:
        self.records.append(deepcopy(record))


class DeterministicSemanticProjection:
    def project(self, graph: WorkGraph) -> dict[str, object]:
        DomainKernel.validate(graph)
        return {
            "event_seq": graph.event_seq,
            "processes": [
                {
                    "process_id": process.process_id,
                    "state": process.state.value,
                    "generation": process.generation,
                    "dependencies": list(process.dependencies),
                    "children": list(process.children),
                    "wait_key": process.wait_key,
                    "effect_receipt_keys": sorted(
                        process.effect_receipts
                    ),
                    "latest_validation_passed": (
                        process.validations[-1].passed
                        if process.validations
                        else None
                    ),
                }
                for process in sorted(
                    graph.processes.values(),
                    key=lambda item: item.process_id,
                )
            ],
        }


class StaticAuthorityEvaluator:
    """Returns only explicitly preloaded authority decisions.

    Missing decisions return UNKNOWN bound to the candidate's exact identity.
    """

    def __init__(
        self,
        decisions: dict[str, AuthorityDecision] | None = None,
    ) -> None:
        self._decisions = deepcopy(decisions or {})

    def evaluate(self, candidate: CandidateAction) -> AuthorityDecision:
        decision = self._decisions.get(candidate.action_id)
        if decision is not None:
            return deepcopy(decision)
        return AuthorityDecision(
            decision_id=f"unknown:{candidate.action_id}",
            outcome=AuthorityOutcome.UNKNOWN,
            action_id=candidate.action_id,
            process_id=candidate.process_id,
            process_generation=candidate.process_generation,
            target_ref=candidate.target_ref,
            authority_scope_ref=None,
        )


class DeterministicFakeExecutor:
    """No external effect; produces a deterministic receipt for port testing."""

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self.invocations: list[tuple[ActionSpec, str]] = []

    def execute(
        self,
        action: ActionSpec,
        *,
        executor: ExecutorProfile,
    ) -> EffectReceipt:
        if executor.availability not in {
            ExecutorAvailability.AVAILABLE,
            ExecutorAvailability.DEGRADED,
        }:
            raise RuntimeError("executor_not_available")
        payload = {
            "action_id": action.action_id,
            "process_id": action.process_id,
            "process_generation": action.process_generation,
            "target_ref": action.target_ref,
            "executor_id": executor.executor_id,
            "expected_effect": action.expected_effect,
        }
        effect_hash = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.invocations.append((deepcopy(action), executor.executor_id))
        return EffectReceipt(
            action_id=action.action_id,
            idempotency_key=action.idempotency_key,
            target_ref=action.target_ref,
            effect_hash=effect_hash,
            executor_id=executor.executor_id,
            generation=action.process_generation,
            observed_at=self._clock.now(),
        )
