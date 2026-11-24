"""Application coordinator over infrastructure-neutral state/runtime ports."""
from __future__ import annotations

from collections.abc import Callable

from ..domain import (
    DomainKernel,
    EffectReceipt,
    ProcessState,
    ExecutorSession,
    OperatorAction,
    OperatorActionKernel,
    OperatorActionState,
    PacketSourceKernel,
    ReasoningProcess,
    SemanticPacketSource,
    ValidationResult,
    WorkContract,
    WorkDisposition,
    WorkerResultKind,
    WorkerResultKernel,
    WorkerResultPublication,
    SchedulerDispatchKernel,
    SchedulerDispatchSpec,
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

    def classify_work(
        self,
        process_id: str,
        *,
        disposition: WorkDisposition,
        reason: str,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "process.classified",
            lambda graph: DomainKernel.classify_work(
                graph,
                process_id,
                disposition=disposition,
                reason=reason,
                lease_id=lease_id,
                expected_generation=expected_generation,
            ),
        )

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

    def register_executor_session(self, *, slot_id: str, executor_id: str, session_id: str) -> StateSnapshot:
        return self._apply("session.registered", lambda graph: DomainKernel.register_executor_session(graph, slot_id=slot_id, executor_id=executor_id, session_id=session_id))

    def bind_executor_session(self, *, slot_id: str, expected_session_generation: int, process_id: str, process_generation: int, packet_sha256: str) -> StateSnapshot:
        return self._apply("session.bound", lambda graph: DomainKernel.bind_executor_session(graph, slot_id=slot_id, expected_session_generation=expected_session_generation, process_id=process_id, process_generation=process_generation, packet_sha256=packet_sha256))

    def acknowledge_executor_session(self, *, slot_id: str, expected_session_generation: int, process_id: str, process_generation: int, ack_id: str) -> StateSnapshot:
        return self._apply("session.acknowledged", lambda graph: DomainKernel.acknowledge_executor_session(graph, slot_id=slot_id, expected_session_generation=expected_session_generation, process_id=process_id, process_generation=process_generation, ack_id=ack_id))

    def invalidate_executor_session(self, *, slot_id: str, expected_session_generation: int, reason: str) -> StateSnapshot:
        return self._apply("session.invalidated", lambda graph: DomainKernel.invalidate_executor_session(graph, slot_id=slot_id, expected_session_generation=expected_session_generation, reason=reason))

    def replace_executor_session(self, *, slot_id: str, expected_session_generation: int, session_id: str) -> StateSnapshot:
        return self._apply("session.replaced", lambda graph: DomainKernel.replace_executor_session(graph, slot_id=slot_id, expected_session_generation=expected_session_generation, session_id=session_id))

    def retire_executor_session(self, *, slot_id: str, expected_session_generation: int, reason: str) -> StateSnapshot:
        return self._apply("session.retired", lambda graph: DomainKernel.retire_executor_session(graph, slot_id=slot_id, expected_session_generation=expected_session_generation, reason=reason))

    def plan_operator_dispatch(
        self,
        *,
        packet_source: SemanticPacketSource,
        action: OperatorAction,
        slot_id: str,
        expected_session_generation: int,
        process_id: str,
        process_generation: int,
        packet_sha256: str,
        worker_id: str,
        lease_id: str,
    ) -> StateSnapshot:
        def transition(graph: WorkGraph) -> WorkGraph:
            process = graph.processes.get(process_id)
            if process is None:
                raise RuntimeError(f"unknown_process:{process_id}")
            if process.generation != process_generation:
                raise RuntimeError(
                    "stale_generation:"
                    f"expected={process_generation}:"
                    f"current={process.generation}"
                )

            next_graph = graph
            if process.state in {
                ProcessState.READY,
                ProcessState.READY_TO_RESUME,
            }:
                next_graph = DomainKernel.claim(
                    next_graph,
                    process_id,
                    worker_id=worker_id,
                    lease_id=lease_id,
                    expected_generation=process_generation,
                )
                next_graph = DomainKernel.start(
                    next_graph,
                    process_id,
                    lease_id=lease_id,
                    expected_generation=process_generation,
                )
            elif process.state == ProcessState.RUNNING:
                if (
                    process.worker_id != worker_id
                    or process.lease_id != lease_id
                ):
                    raise RuntimeError(
                        "operator_dispatch_process_owned_elsewhere"
                    )
            else:
                raise RuntimeError(
                    "operator_dispatch_process_not_dispatchable:"
                    f"{process.state.value}"
                )

            next_graph = PacketSourceKernel.register(
                next_graph,
                packet_source,
            )
            next_graph = DomainKernel.bind_executor_session(
                next_graph,
                slot_id=slot_id,
                expected_session_generation=expected_session_generation,
                process_id=process_id,
                process_generation=process_generation,
                packet_sha256=packet_sha256,
            )
            return OperatorActionKernel.enqueue(
                next_graph,
                action,
            )

        return self._apply(
            "operator_dispatch.planned",
            transition,
        )

    def accept_worker_result(
        self,
        *,
        publication: WorkerResultPublication,
        worker_id: str,
        lease_id: str,
    ) -> StateSnapshot:
        def transition(graph: WorkGraph) -> WorkGraph:
            existing = graph.worker_results.get(
                publication.publication_id
            )
            if existing is not None:
                if existing == publication:
                    return graph
                raise RuntimeError(
                    "worker_result_publication_conflict"
                )

            action = graph.operator_actions.get(
                publication.action_id
            )
            if action is None:
                raise RuntimeError("worker_result_action_unknown")
            if (
                action.generation
                != publication.action_generation
                or action.reasoning_process_id
                != publication.process_id
                or action.process_generation
                != publication.process_generation
                or action.executor_id
                != publication.executor_id
                or action.worker_slot_id
                != publication.worker_slot_id
                or action.session_generation
                != publication.session_generation
                or action.payload_sha256
                != publication.packet_sha256
            ):
                raise RuntimeError(
                    "worker_result_action_binding_mismatch"
                )
            if action.status != OperatorActionState.AWAITING_DURABLE_ACK:
                raise RuntimeError(
                    "worker_result_action_not_awaiting_ack:"
                    f"{action.status.value}"
                )

            if action.payload_ref is None:
                raise RuntimeError(
                    "worker_result_packet_source_missing"
                )
            source = graph.packet_sources.get(action.payload_ref)
            if source is None:
                raise RuntimeError(
                    "worker_result_packet_source_missing"
                )
            if (
                source.process_id != publication.process_id
                or source.process_generation
                != publication.process_generation
                or source.executor_id != publication.executor_id
                or source.packet_sha256
                != publication.packet_sha256
            ):
                raise RuntimeError(
                    "worker_result_packet_binding_mismatch"
                )

            process = graph.processes.get(publication.process_id)
            if process is None:
                raise RuntimeError("worker_result_process_unknown")
            if (
                process.generation
                != publication.process_generation
                or process.state != ProcessState.RUNNING
                or process.worker_id != worker_id
                or process.lease_id != lease_id
            ):
                raise RuntimeError(
                    "worker_result_process_binding_mismatch"
                )

            session = graph.executor_sessions.get(
                publication.worker_slot_id
            )
            if (
                session is None
                or session.session_generation
                != publication.session_generation
                or session.executor_id != publication.executor_id
                or session.bound_process_id
                != publication.process_id
                or session.bound_process_generation
                != publication.process_generation
                or session.bound_packet_sha256
                != publication.packet_sha256
            ):
                raise RuntimeError(
                    "worker_result_session_binding_mismatch"
                )

            next_graph = WorkerResultKernel.register(
                graph,
                publication,
            )

            if publication.kind == WorkerResultKind.RESULT:
                next_graph = DomainKernel.classify_work(
                    next_graph,
                    publication.process_id,
                    disposition=WorkDisposition.EXECUTABLE,
                    reason="durable_worker_result",
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
                assert publication.result_payload_ref is not None
                assert publication.result_payload_sha256 is not None
                next_graph = DomainKernel.record_effect(
                    next_graph,
                    publication.process_id,
                    receipt=EffectReceipt(
                        action_id=publication.action_id,
                        idempotency_key=(
                            "worker-result:"
                            f"{publication.publication_id}"
                        ),
                        target_ref=publication.result_payload_ref,
                        effect_hash=publication.result_payload_sha256,
                        executor_id=publication.executor_id,
                        generation=publication.process_generation,
                        observed_at=publication.observed_at,
                    ),
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
                next_graph = DomainKernel.propose_terminal(
                    next_graph,
                    publication.process_id,
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
            elif publication.kind == WorkerResultKind.TOO_LARGE:
                next_graph = DomainKernel.classify_work(
                    next_graph,
                    publication.process_id,
                    disposition=WorkDisposition.TOO_LARGE,
                    reason=publication.reason or "worker_too_large",
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
                children = tuple(
                    DomainKernel.create_process(
                        child.process_id,
                        dependencies=child.dependencies,
                        work_contract=WorkContract(
                            objective=child.objective,
                            mandatory_constraints=(
                                child.mandatory_constraints
                            ),
                            provenance_refs=child.provenance_refs,
                            authority_refs=child.authority_refs,
                            validator_contracts=(
                                child.validator_contracts
                            ),
                            output_schema_refs=(
                                child.output_schema_refs
                            ),
                        ),
                    )
                    for child in publication.children
                )
                next_graph = DomainKernel.decompose(
                    next_graph,
                    publication.process_id,
                    children=children,
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
            elif (
                publication.kind
                == WorkerResultKind.INTRINSICALLY_DIFFICULT
            ):
                next_graph = DomainKernel.classify_work(
                    next_graph,
                    publication.process_id,
                    disposition=(
                        WorkDisposition.INTRINSICALLY_DIFFICULT
                    ),
                    reason=(
                        publication.reason
                        or "worker_intrinsically_difficult"
                    ),
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
            elif publication.kind == WorkerResultKind.WAIT_EXTERNAL:
                next_graph = DomainKernel.wait_external(
                    next_graph,
                    publication.process_id,
                    wait_key=publication.wait_key or "",
                    lease_id=lease_id,
                    expected_generation=publication.process_generation,
                )
            else:
                raise RuntimeError("worker_result_kind_unknown")

            next_graph = DomainKernel.acknowledge_executor_session(
                next_graph,
                slot_id=publication.worker_slot_id,
                expected_session_generation=(
                    publication.session_generation
                ),
                process_id=publication.process_id,
                process_generation=publication.process_generation,
                ack_id=publication.publication_id,
            )
            next_graph = OperatorActionKernel.record_durable_ack(
                next_graph,
                action_id=publication.action_id,
                generation=publication.action_generation,
                ack_id=publication.publication_id,
            )
            return OperatorActionKernel.complete_acknowledged(
                next_graph,
                action_id=publication.action_id,
                generation=publication.action_generation,
                completed_at=publication.observed_at,
            )

        return self._apply(
            "worker_result.accepted",
            transition,
        )

    def register_scheduler_dispatch(
        self,
        spec: SchedulerDispatchSpec,
    ) -> StateSnapshot:
        return self._apply(
            "scheduler_dispatch.registered",
            lambda graph: SchedulerDispatchKernel.register(
                graph,
                spec,
            ),
        )

    def enqueue_operator_action(self, action: OperatorAction) -> StateSnapshot:
        return self._apply(
            "operator_action.enqueued",
            lambda graph: OperatorActionKernel.enqueue(graph, action),
        )

    def claim_next_operator_action(
        self,
        *,
        helper_instance_id: str,
        claim_id: str,
        claimed_at: str,
        expires_at: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.claimed",
            lambda graph: OperatorActionKernel.claim_next(
                graph,
                helper_instance_id=helper_instance_id,
                claim_id=claim_id,
                claimed_at=claimed_at,
                expires_at=expires_at,
            ),
        )

    def record_operator_action_local_prepared(
        self,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
        observed_at: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.local_prepared",
            lambda graph: OperatorActionKernel.record_local_prepared(
                graph,
                action_id=action_id,
                generation=generation,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
                observed_at=observed_at,
            ),
        )

    def record_operator_action_local_failure(
        self,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.local_failure",
            lambda graph: OperatorActionKernel.record_local_failure(
                graph,
                action_id=action_id,
                generation=generation,
                failure_code=failure_code,
                failure_message=failure_message,
            ),
        )

    def record_operator_action_blocked(
        self,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.blocked",
            lambda graph: OperatorActionKernel.record_blocked(
                graph,
                action_id=action_id,
                generation=generation,
                failure_code=failure_code,
                failure_message=failure_message,
            ),
        )

    def record_operator_action_durable_ack(
        self,
        *,
        action_id: str,
        generation: int,
        ack_id: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.acknowledged",
            lambda graph: OperatorActionKernel.record_durable_ack(
                graph,
                action_id=action_id,
                generation=generation,
                ack_id=ack_id,
            ),
        )

    def complete_acknowledged_operator_action(
        self,
        *,
        action_id: str,
        generation: int,
        completed_at: str,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.completed",
            lambda graph: OperatorActionKernel.complete_acknowledged(
                graph,
                action_id=action_id,
                generation=generation,
                completed_at=completed_at,
            ),
        )

    def expire_operator_action_claim(
        self,
        *,
        action_id: str,
        generation: int,
    ) -> StateSnapshot:
        return self._apply(
            "operator_action.claim_expired",
            lambda graph: OperatorActionKernel.expire_claim(
                graph,
                action_id=action_id,
                generation=generation,
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
