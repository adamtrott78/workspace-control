"""Token/context economy contracts for model-backed execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from .._compat import StrEnum


class ContextMode(StrEnum):
    REF_ONLY = "REF_ONLY"
    DELTA = "DELTA"
    SELECTED = "SELECTED"
    FULL_RECOVERY = "FULL_RECOVERY"


class ReasoningProfile(StrEnum):
    NO_MODEL = "NO_MODEL"
    ECONOMY = "ECONOMY"
    STANDARD = "STANDARD"
    DEEP = "DEEP"


class CommunicationMode(StrEnum):
    MACHINE_MINIMAL = "MACHINE_MINIMAL"
    CONCISE = "CONCISE"
    NORMAL = "NORMAL"
    USER_FACING = "USER_FACING"


@dataclass(frozen=True)
class TokenBudget:
    """Fail-closed per-invocation token/context envelope.

    These are controller budgets, not execution authority. A budget may reduce
    model/context/output use but can never widen capabilities or authority.
    """

    context_mode: ContextMode
    reasoning_profile: ReasoningProfile
    communication_mode: CommunicationMode
    max_inline_tokens: int
    max_retrieved_tokens: int
    max_output_tokens: int
    allow_model_call: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("max_inline_tokens", self.max_inline_tokens),
            ("max_retrieved_tokens", self.max_retrieved_tokens),
            ("max_output_tokens", self.max_output_tokens),
        ):
            if value < 0:
                raise ValueError(f"{name}_must_be_nonnegative")
        if not self.allow_model_call:
            if self.reasoning_profile != ReasoningProfile.NO_MODEL:
                raise ValueError("no_model_call_requires_no_model_profile")
            if self.max_output_tokens != 0:
                raise ValueError("no_model_call_requires_zero_output_budget")


@dataclass(frozen=True)
class ContextPlan:
    context_mode: ContextMode
    base_checkpoint: str | None = None
    required_refs: tuple[str, ...] = ()
    optional_refs: tuple[str, ...] = ()
    delta_refs: tuple[str, ...] = ()
    omitted_optional_refs: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class TokenEconomyObservation:
    """Measured usage for one attempt; unknown fields remain None."""

    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    reasoning_tokens: int | None = None
    visible_output_tokens: int | None = None
    allowance_delta: float | None = None
    model_calls: int = 0
    model_calls_while_waiting: int = 0

    def __post_init__(self) -> None:
        numeric = (
            self.input_tokens,
            self.cached_input_tokens,
            self.reasoning_tokens,
            self.visible_output_tokens,
        )
        if any(value is not None and value < 0 for value in numeric):
            raise ValueError("token_observation_must_be_nonnegative")
        if self.model_calls < 0 or self.model_calls_while_waiting < 0:
            raise ValueError("model_call_counts_must_be_nonnegative")
        if self.model_calls_while_waiting > self.model_calls:
            raise ValueError("waiting_model_calls_exceed_total")
