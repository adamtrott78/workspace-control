"""Application coordinator over infrastructure-neutral state/runtime ports."""
from __future__ import annotations

from collections.abc import Callable

from ..domain import (
    DomainKernel,
    EffectReceipt,
    ProcessState,
    ReasoningProcess,
    ValidationResult,
    WorkGraph,
)
from ..ports import (
    ClockPort,
    EventLedgerPort,
    RuntimeEvent,
    StateSnapshot,
    StateStorePort,
    TelemetryPort,
    TelemetryRecord,
)


GraphTransition = Callable[[WorkGraph], WorkGraph]


class RuntimeCoordinator:
    """Transactional application service over the pure domain kernel.

    The coordinator never retries a stale CAS implicitly. A caller must reload
    state and make an evidence-based retry/decomposition decision.
    """

    def __init__(
        self,
        *,
        state_store: StateStorePort,
        event_ledger: EventLedgerPort,
        telemetry: TelemetryPort,
        clock: ClockPort,
    ) -> None:
        self._state_store = state_store
        self._event_ledger = event_ledger
        self._telemetry = telemetry
        self._clock = clock

    def initialize(self, graph: WorkGraph) -> StateSnapshot:
        snapshot = self._state_store.initialize(graph)
        self._record(
            "runtime.initialized",
            version=snapshot.version,
        )
        return snapshot

    def snapshot(self) -> StateSnapshot:
        return self._state_store.load()

    def _record(self, name: str, **attributes: object) -> None:
        self._telemetry.record(
            TelemetryRecord(
                name=name,
                observed_at=self._clock.now(),
                attributes=dict(attributes),
            )
        )

    def _apply(
        self,
        name: str,
        transition: GraphTransition,
    ) -> StateSnapshot:
        before = self._state_store.load()
        next_graph = transition(before.graph)
        after = self._state_store.compare_and_swap(
            expected_version=before.version,
            graph=next_graph,
        )
        self._record(
            name,
            before_version=before.version,
            after_version=after.version,
        )
        return after

    def claim(
        self,
        process_id: str,
        *,
        worker_id: str,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.claimed",
            lambda graph: DomainKernel.claim(
                graph,
                process_id,
                worker_id=worker_id,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

    def start(
        self,
        process_id: str,
        *,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.started",
            lambda graph: DomainKernel.start(
                graph,
                process_id,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

    def wait_external(
        self,
        process_id: str,
        *,
        wait_key: str,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        snapshot = self._apply(
            "process.wait_external",
            lambda graph: DomainKernel.wait_external(
                graph,
                process_id,
                wait_key=wait_key,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )
        # This is an event-ledger reconciliation at the wait boundary, not
        # polling. It handles an event that arrived before the waiter persisted.
        resumed = self._resume_wait_key(wait_key)
        return resumed or snapshot

    def publish_external_event(
        self,
        event: RuntimeEvent,
    ) -> StateSnapshot:
        inserted = self._event_ledger.publish_event(event)
        if not inserted:
            self._record(
                "runtime.event_duplicate",
                event_id=event.event_id,
                wait_key=event.wait_key,
            )
            return self._state_store.load()

        self._record(
            "runtime.event_published",
            event_id=event.event_id,
            wait_key=event.wait_key,
        )
        resumed = self._resume_wait_key(event.wait_key)
        if resumed is None:
            self._record(
                "runtime.event_unmatched",
                event_id=event.event_id,
                wait_key=event.wait_key,
            )
            return self._state_store.load()
        return resumed

    def reconcile_published_events(self) -> StateSnapshot:
        """Startup/recovery reconciliation; never a background polling loop."""
        before = self._state_store.load()
        next_graph = before.graph
        matched_event_ids: list[str] = []

        for process in sorted(
            next_graph.processes.values(),
            key=lambda item: item.process_id,
        ):
            if process.state != ProcessState.WAITING_EXTERNAL:
                continue
            if process.wait_key is None:
                continue
            event = self._event_ledger.find_event(wait_key=process.wait_key)
            if event is None:
                continue
            next_graph = DomainKernel.wake_external(
                next_graph,
                process.process_id,
                wait_key=process.wait_key,
                event_id=event.event_id,
            )
            matched_event_ids.append(event.event_id)

        if not matched_event_ids:
            self._record(
                "runtime.reconcile_noop",
                version=before.version,
            )
            return before

        after = self._state_store.compare_and_swap(
            expected_version=before.version,
            graph=next_graph,
        )
        self._record(
            "runtime.reconciled",
            before_version=before.version,
            after_version=after.version,
            event_ids=tuple(matched_event_ids),
        )
        return after

    def _resume_wait_key(
        self,
        wait_key: str,
    ) -> StateSnapshot | None:
        before = self._state_store.load()
        event = self._event_ledger.find_event(wait_key=wait_key)
        if event is None:
            return None

        next_graph = before.graph
        matched: list[str] = []
        for process in sorted(
            next_graph.processes.values(),
            key=lambda item: item.process_id,
        ):
            if (
                process.state == ProcessState.WAITING_EXTERNAL
                and process.wait_key == wait_key
            ):
                next_graph = DomainKernel.wake_external(
                    next_graph,
                    process.process_id,
                    wait_key=wait_key,
                    event_id=event.event_id,
                )
                matched.append(process.process_id)

        if not matched:
            return None

        after = self._state_store.compare_and_swap(
            expected_version=before.version,
            graph=next_graph,
        )
        self._record(
            "process.external_wake",
            wait_key=wait_key,
            event_id=event.event_id,
            process_ids=tuple(matched),
            before_version=before.version,
            after_version=after.version,
        )
        return after

    def decompose(
        self,
        process_id: str,
        *,
        children: tuple[ReasoningProcess, ...],
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.decomposed",
            lambda graph: DomainKernel.decompose(
                graph,
                process_id,
                children=children,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

    def refresh_dependency_waits(
        self,
        *,
        event_id: str,
    ) -> StateSnapshot:
        return self._apply(
            "process.dependencies_refreshed",
            lambda graph: DomainKernel.refresh_dependency_waits(
                graph,
                event_id=event_id,
            ),
        )

    def recover(
        self,
        process_id: str,
        *,
        expected_generation: int,
        reason: str,
    ) -> StateSnapshot:
        return self._apply(
            "process.recovered",
            lambda graph: DomainKernel.recover(
                graph,
                process_id,
                expected_generation=expected_generation,
                reason=reason,
            ),
        )

    def record_effect(
        self,
        process_id: str,
        *,
        receipt: EffectReceipt,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.effect_recorded",
            lambda graph: DomainKernel.record_effect(
                graph,
                process_id,
                receipt=receipt,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

    def propose_terminal(
        self,
        process_id: str,
        *,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.terminal_proposed",
            lambda graph: DomainKernel.propose_terminal(
                graph,
                process_id,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

    def begin_validation(self, process_id: str) -> StateSnapshot:
        return self._apply(
            "process.validation_started",
            lambda graph: DomainKernel.begin_validation(
                graph,
                process_id,
            ),
        )

    def record_validation(
        self,
        process_id: str,
        *,
        result: ValidationResult,
    ) -> StateSnapshot:
        return self._apply(
            "process.validation_recorded",
            lambda graph: DomainKernel.record_validation(
                graph,
                process_id,
                result=result,
            ),
        )
