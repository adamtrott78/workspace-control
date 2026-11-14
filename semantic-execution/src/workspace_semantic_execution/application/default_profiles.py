"""Conservative initial executor profiles and factories.

Profiles record only known properties. Unprovisioned institutional hardware is
represented explicitly as UNKNOWN and cannot be selected until calibrated.
"""
from __future__ import annotations

from ..domain import (
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    InvocationMode,
    MemoryResetPolicy,
    PrivacyClass,
    SessionMode,
)


def openai_chat_instant_current_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="openai-chat-instant-current",
        provider_id="openai",
        model_id="gpt-6-sol",
        surface_id="chatgpt-chat",
        harness_id="workspace-human-operator-bridge-v1",
        toolset_id="chatgpt-connected-tools-observed",
        capabilities=frozenset(
            {
                "reasoning.bounded",
                "connected_tools",
                "github.read",
                "github.write_branch",
            }
        ),
        invocation_mode=InvocationMode.HUMAN_ASSISTED,
        session_mode=SessionMode.PERSISTENT_CHAT,
        lifecycle=ExecutorLifecycle.INTERACTIVE_CHAT,
        memory_reset_policy=MemoryResetPolicy.PROVIDER_MANAGED,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.PROVIDER_REMOTE,
        privacy_classes=frozenset(
            {PrivacyClass.PUBLIC, PrivacyClass.INTERNAL}
        ),
        context_capacity=None,
        resource_classes=frozenset({"REMOTE_MODEL_INFERENCE"}),
        usage_pool_ids=("openai-chat-subscription",),
        scarcity_rank=20,
        human_launch_required=True,
        calibration_ref=(
            "architecture/"
            "workspace-semantic-execution-instant-executor-contract.v0.1.md"
        ),
    )


def unprovisioned_institutional_llm_profile() -> ExecutorProfile:
    """Placeholder proving machine-executor portability without inventing facts."""
    return ExecutorProfile(
        executor_id="institutional-llm-unprovisioned",
        provider_id="institutional-unknown",
        model_id="UNKNOWN",
        surface_id="machine-api",
        harness_id="workspace-machine-llm-v1",
        toolset_id="UNKNOWN",
        capabilities=frozenset(),
        invocation_mode=InvocationMode.PROGRAMMATIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.UNKNOWN,
        memory_reset_policy=MemoryResetPolicy.UNKNOWN,
        availability=ExecutorAvailability.UNKNOWN,
        locality=ExecutorLocality.UNKNOWN,
        privacy_classes=frozenset({PrivacyClass.UNKNOWN}),
        context_capacity=None,
        resource_classes=frozenset(),
        usage_pool_ids=(),
        scarcity_rank=10,
        human_launch_required=False,
        calibration_ref=None,
    )


def machine_llm_profile(
    *,
    executor_id: str,
    provider_id: str,
    model_id: str,
    harness_id: str,
    toolset_id: str,
    capabilities: frozenset[str],
    session_mode: SessionMode,
    lifecycle: ExecutorLifecycle,
    memory_reset_policy: MemoryResetPolicy,
    availability: ExecutorAvailability,
    locality: ExecutorLocality,
    privacy_classes: frozenset[PrivacyClass],
    resource_classes: frozenset[str],
    context_capacity: int | None,
    usage_pool_ids: tuple[str, ...] = (),
    scarcity_rank: int = 10,
    calibration_ref: str | None = None,
) -> ExecutorProfile:
    """Create a fully specified programmatic LLM executor profile.

    The caller must supply measured/authorized properties; this factory does not
    infer hardware, context, quantization, model capability, or availability.
    """
    if session_mode not in {
        SessionMode.STATELESS,
        SessionMode.SESSION_SCOPED,
    }:
        raise ValueError("machine_llm_session_mode_required")
    if lifecycle not in {
        ExecutorLifecycle.PERSISTENT_SERVICE,
        ExecutorLifecycle.EPHEMERAL_INVOCATION,
        ExecutorLifecycle.BATCH_JOB,
    }:
        raise ValueError("machine_llm_lifecycle_required")
    if memory_reset_policy == MemoryResetPolicy.UNKNOWN:
        raise ValueError("machine_llm_memory_reset_policy_must_be_known")

    return ExecutorProfile(
        executor_id=executor_id,
        provider_id=provider_id,
        model_id=model_id,
        surface_id="machine-api",
        harness_id=harness_id,
        toolset_id=toolset_id,
        capabilities=capabilities,
        invocation_mode=InvocationMode.PROGRAMMATIC,
        session_mode=session_mode,
        lifecycle=lifecycle,
        memory_reset_policy=memory_reset_policy,
        availability=availability,
        locality=locality,
        privacy_classes=privacy_classes,
        context_capacity=context_capacity,
        resource_classes=resource_classes,
        usage_pool_ids=usage_pool_ids,
        scarcity_rank=scarcity_rank,
        human_launch_required=False,
        calibration_ref=calibration_ref,
    )


def initial_executor_profiles() -> tuple[ExecutorProfile, ...]:
    """Return the conservative boot registry.

    The institutional placeholder is intentionally UNKNOWN/ineligible until
    concrete deployment facts are supplied.
    """
    return (
        openai_chat_instant_current_profile(),
        unprovisioned_institutional_llm_profile(),
    )
