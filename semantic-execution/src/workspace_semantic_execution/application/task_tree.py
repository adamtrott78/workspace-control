"""Typed recursive task-tree orchestration over the production runtime."""
from __future__ import annotations

from dataclasses import dataclass

from ..domain import (
    DomainKernel,
    ProcessState,
    WorkContract,
    WorkDisposition,
)
from ..ports import StateSnapshot
from .runtime import RuntimeCoordinator


@dataclass(frozen=True)
class ChildWorkSpec:
    """Local child objective plus obligations that may only strengthen parent ones."""

    process_id: str
    objective: str
    dependencies: tuple[str, ...] = ()
    mandatory_constraints: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    validator_contracts: tuple[str, ...] = ()
    output_schema_refs: tuple[str, ...] = ()

    def contract(self) -> WorkContract:
        return WorkContract(
            objective=self.objective,
            mandatory_constraints=self.mandatory_constraints,
            provenance_refs=self.provenance_refs,
            authority_refs=self.authority_refs,
            validator_contracts=self.validator_contracts,
            output_schema_refs=self.output_schema_refs,
        )


@dataclass(frozen=True)
class TaskTreeStatus:
    process_id: str
    state: ProcessState
    disposition: WorkDisposition
    generation: int
    children: tuple[str, ...]
    dependencies: tuple[str, ...]
    escalation_required: bool


class TaskTreeCoordinator:
    """Application service for classification, decomposition and fan-in.

    The service deliberately delegates all invariants to DomainKernel through
    RuntimeCoordinator. It cannot drop inherited obligations or manufacture
    authority.
    """

    def __init__(self, runtime: RuntimeCoordinator) -> None:
        self._runtime = runtime

    def classify(
        self,
        process_id: str,
        *,
        disposition: WorkDisposition,
        reason: str,
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        return self._runtime.classify_work(
            process_id,
            disposition=disposition,
            reason=reason,
            lease_id=lease_id,
            expected_generation=expected_generation,
        )

    def decompose(
        self,
        process_id: str,
        *,
        children: tuple[ChildWorkSpec, ...],
        lease_id: str,
        expected_generation: int,
    ) -> StateSnapshot:
        if not children:
            raise ValueError("children_required")
        child_processes = tuple(
            DomainKernel.create_process(
                child.process_id,
                dependencies=child.dependencies,
                work_contract=child.contract(),
            )
            for child in children
        )
        return self._runtime.decompose(
            process_id,
            children=child_processes,
            lease_id=lease_id,
            expected_generation=expected_generation,
        )

    def refresh_fan_in(self, *, event_id: str) -> StateSnapshot:
        return self._runtime.refresh_dependency_waits(event_id=event_id)

    def status(self, process_id: str) -> TaskTreeStatus:
        process = self._runtime.snapshot().graph.processes[process_id]
        return TaskTreeStatus(
            process_id=process.process_id,
            state=process.state,
            disposition=process.disposition,
            generation=process.generation,
            children=process.children,
            dependencies=process.dependencies,
            escalation_required=(
                process.disposition
                == WorkDisposition.INTRINSICALLY_DIFFICULT
            ),
        )
