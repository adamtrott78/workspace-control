"""Executor, resource, and session semantics for the domain layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class InvocationMode(StrEnum):
    HUMAN_ASSISTED = "HUMAN_ASSISTED"
    PROGRAMMATIC = "PROGRAMMATIC"
    DETERMINISTIC = "DETERMINISTIC"
    HUMAN_JUDGMENT = "HUMAN_JUDGMENT"


class SessionMode(StrEnum):
    STATELESS = "STATELESS"
    PERSISTENT_CHAT = "PERSISTENT_CHAT"
    SESSION_SCOPED = "SESSION_SCOPED"
    PERSISTENT_SERVICE = "PERSISTENT_SERVICE"
    BATCH_QUEUED = "BATCH_QUEUED"
    NONE = "NONE"


class ExecutorAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ExecutorLocality(StrEnum):
    PROVIDER_REMOTE = "PROVIDER_REMOTE"
    INSTITUTIONAL_REMOTE = "INSTITUTIONAL_REMOTE"
    LOCAL_HOST = "LOCAL_HOST"
    HUMAN = "HUMAN"
    UNKNOWN = "UNKNOWN"


class PrivacyClass(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExecutorProfile:
    executor_id: str
    provider_id: str
    model_id: str
    surface_id: str
    harness_id: str
    toolset_id: str
    capabilities: frozenset[str]
    invocation_mode: InvocationMode
    session_mode: SessionMode
    availability: ExecutorAvailability
    locality: ExecutorLocality
    privacy_classes: frozenset[PrivacyClass]
    context_capacity: int | None = None
    resource_classes: frozenset[str] = field(default_factory=frozenset)
    usage_pool_ids: tuple[str, ...] = ()
    scarcity_rank: int = 100
    human_launch_required: bool = False
    calibration_ref: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.executor_id,
            self.provider_id,
            self.model_id,
            self.surface_id,
            self.harness_id,
            self.toolset_id,
        )
        if not all(required):
            raise ValueError("executor_identity_fields_required")
        if self.context_capacity is not None and self.context_capacity <= 0:
            raise ValueError("context_capacity_must_be_positive")
        if self.scarcity_rank < 0:
            raise ValueError("scarcity_rank_must_be_nonnegative")


@dataclass(frozen=True)
class ExecutionRequirement:
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    allowed_invocation_modes: frozenset[InvocationMode] = field(
        default_factory=frozenset
    )
    allowed_session_modes: frozenset[SessionMode] = field(
        default_factory=frozenset
    )
    allowed_localities: frozenset[ExecutorLocality] = field(
        default_factory=frozenset
    )
    privacy_class: PrivacyClass = PrivacyClass.PUBLIC
    minimum_context_capacity: int | None = None
    required_resource_classes: frozenset[str] = field(default_factory=frozenset)
    require_human_launch: bool | None = None

    def __post_init__(self) -> None:
        if (
            self.minimum_context_capacity is not None
            and self.minimum_context_capacity <= 0
        ):
            raise ValueError("minimum_context_capacity_must_be_positive")


@dataclass(frozen=True)
class ExecutorExclusion:
    executor_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RoutingDecision:
    requirement_id: str
    selected_executor_id: str | None
    eligible_executor_ids: tuple[str, ...]
    exclusions: tuple[ExecutorExclusion, ...]
    outcome: str
    rationale: str
