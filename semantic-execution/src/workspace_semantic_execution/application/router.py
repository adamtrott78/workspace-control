"""Deterministic executor eligibility and scarcity routing."""
from __future__ import annotations

from dataclasses import dataclass

from ..domain import (
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorExclusion,
    ExecutorProfile,
    RoutingDecision,
)


@dataclass(frozen=True)
class ExecutorRegistry:
    profiles: tuple[ExecutorProfile, ...]

    def __post_init__(self) -> None:
        ids = [profile.executor_id for profile in self.profiles]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_executor_id")

    def get(self, executor_id: str) -> ExecutorProfile:
        for profile in self.profiles:
            if profile.executor_id == executor_id:
                return profile
        raise KeyError(executor_id)


def _exclusion_reasons(
    profile: ExecutorProfile,
    requirement: ExecutionRequirement,
) -> tuple[str, ...]:
    reasons: list[str] = []

    if profile.availability == ExecutorAvailability.UNKNOWN:
        reasons.append("AVAILABILITY_UNKNOWN")
    elif profile.availability == ExecutorAvailability.UNAVAILABLE:
        reasons.append("UNAVAILABLE")

    missing = sorted(
        requirement.required_capabilities - profile.capabilities
    )
    if missing:
        reasons.append("MISSING_CAPABILITIES:" + ",".join(missing))

    if (
        requirement.allowed_invocation_modes
        and profile.invocation_mode not in requirement.allowed_invocation_modes
    ):
        reasons.append("INVOCATION_MODE_INCOMPATIBLE")

    if (
        requirement.allowed_session_modes
        and profile.session_mode not in requirement.allowed_session_modes
    ):
        reasons.append("SESSION_MODE_INCOMPATIBLE")

    if (
        requirement.allowed_localities
        and profile.locality not in requirement.allowed_localities
    ):
        reasons.append("LOCALITY_INCOMPATIBLE")

    if requirement.privacy_class not in profile.privacy_classes:
        reasons.append("PRIVACY_CLASS_UNSUPPORTED")

    if requirement.minimum_context_capacity is not None:
        if profile.context_capacity is None:
            reasons.append("CONTEXT_CAPACITY_UNKNOWN")
        elif profile.context_capacity < requirement.minimum_context_capacity:
            reasons.append("CONTEXT_CAPACITY_INSUFFICIENT")

    missing_resources = sorted(
        requirement.required_resource_classes - profile.resource_classes
    )
    if missing_resources:
        reasons.append(
            "MISSING_RESOURCE_CLASSES:" + ",".join(missing_resources)
        )

    if (
        requirement.require_human_launch is not None
        and profile.human_launch_required
        != requirement.require_human_launch
    ):
        reasons.append("HUMAN_LAUNCH_REQUIREMENT_MISMATCH")

    return tuple(reasons)


def route_executor(
    registry: ExecutorRegistry,
    *,
    requirement_id: str,
    requirement: ExecutionRequirement,
) -> RoutingDecision:
    if not requirement_id:
        raise ValueError("requirement_id_required")

    eligible: list[ExecutorProfile] = []
    exclusions: list[ExecutorExclusion] = []

    for profile in registry.profiles:
        reasons = _exclusion_reasons(profile, requirement)
        if reasons:
            exclusions.append(
                ExecutorExclusion(
                    executor_id=profile.executor_id,
                    reasons=reasons,
                )
            )
        else:
            eligible.append(profile)

    eligible.sort(
        key=lambda profile: (
            0
            if profile.availability == ExecutorAvailability.AVAILABLE
            else 1,
            profile.scarcity_rank,
            profile.executor_id,
        )
    )
    exclusions.sort(key=lambda item: item.executor_id)

    selected = eligible[0] if eligible else None
    if selected is None:
        return RoutingDecision(
            requirement_id=requirement_id,
            selected_executor_id=None,
            eligible_executor_ids=(),
            exclusions=tuple(exclusions),
            outcome="NO_ELIGIBLE_EXECUTOR",
            rationale=(
                "No executor satisfied all known capability, lifecycle, "
                "privacy, context, resource, and availability constraints."
            ),
        )

    return RoutingDecision(
        requirement_id=requirement_id,
        selected_executor_id=selected.executor_id,
        eligible_executor_ids=tuple(
            profile.executor_id for profile in eligible
        ),
        exclusions=tuple(exclusions),
        outcome="SELECTED",
        rationale=(
            "Selected the lowest-scarcity known eligible executor; "
            "UNKNOWN availability/capability is never treated as capacity."
        ),
    )
