"""Infrastructure-neutral ports for Workspace Semantic Execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..domain import (
    ActionSpec,
    AuthorityDecision,
    CandidateAction,
    EffectReceipt,
    ExecutorProfile,
    WorkGraph,
)


@dataclass(frozen=True)
class StateSnapshot:
    version: int
    graph: WorkGraph


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    wait_key: str
    observed_at: str
    payload_ref: str | None = None


@dataclass(frozen=True)
class TelemetryRecord:
    name: str
    observed_at: str
    attributes: dict[str, Any] = field(default_factory=dict)


class StateConflict(RuntimeError):
    """Compare-and-swap rejected a stale expected version."""


class StateNotInitialized(RuntimeError):
    """State store has no initialized graph."""


class StateStorePort(Protocol):
    def initialize(self, graph: WorkGraph) -> StateSnapshot: ...

    def load(self) -> StateSnapshot: ...

    def compare_and_swap(
        self,
        *,
        expected_version: int,
        graph: WorkGraph,
    ) -> StateSnapshot: ...


class DurableRuntimePort(Protocol):
    def publish_event(self, event: RuntimeEvent) -> bool: ...

    def find_event(self, *, wait_key: str) -> RuntimeEvent | None: ...


class AuthorityEvaluatorPort(Protocol):
    def evaluate(self, candidate: CandidateAction) -> AuthorityDecision: ...


class ExecutorPort(Protocol):
    def execute(
        self,
        action: ActionSpec,
        *,
        executor: ExecutorProfile,
    ) -> EffectReceipt: ...


class SemanticProjectionPort(Protocol):
    def project(self, graph: WorkGraph) -> dict[str, Any]: ...


class TelemetryPort(Protocol):
    def record(self, record: TelemetryRecord) -> None: ...


class ClockPort(Protocol):
    def now(self) -> str: ...
