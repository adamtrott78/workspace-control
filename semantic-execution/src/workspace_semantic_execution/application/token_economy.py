"""Deterministic context/reasoning/output budget planning."""
from __future__ import annotations

from dataclasses import dataclass

from ..domain import (
    CommunicationMode,
    ContextMode,
    ContextPlan,
    InvocationMode,
    ReasoningProfile,
    SessionMode,
    TokenBudget,
)


@dataclass(frozen=True)
class TokenEconomyRequest:
    required_refs: tuple[str, ...] = ()
    optional_refs: tuple[str, ...] = ()
    delta_refs: tuple[str, ...] = ()
    base_checkpoint: str | None = None
    session_has_base_checkpoint: bool = False
    recovery_required: bool = False
    broad_context_required: bool = False
    waiting_external: bool = False
    invocation_mode: InvocationMode = InvocationMode.PROGRAMMATIC
    session_mode: SessionMode = SessionMode.STATELESS
    user_facing: bool = False
    deep_reasoning_required: bool = False


@dataclass(frozen=True)
class TokenEconomyDecision:
    budget: TokenBudget
    context: ContextPlan


class TokenEconomyPlanner:
    """Choose the smallest sufficient model/context/output envelope.

    The planner never grants capabilities or authority. It only constrains
    context, reasoning, communication, and whether a model call may occur.
    """

    ECONOMY_INLINE = 3000
    ECONOMY_RETRIEVAL = 12000
    ECONOMY_OUTPUT = 500
    STANDARD_INLINE = 6000
    STANDARD_RETRIEVAL = 24000
    STANDARD_OUTPUT = 1500
    DEEP_INLINE = 12000
    DEEP_RETRIEVAL = 48000
    DEEP_OUTPUT = 4000

    def plan(self, request: TokenEconomyRequest) -> TokenEconomyDecision:
        if request.waiting_external:
            return TokenEconomyDecision(
                budget=TokenBudget(
                    context_mode=ContextMode.REF_ONLY,
                    reasoning_profile=ReasoningProfile.NO_MODEL,
                    communication_mode=CommunicationMode.MACHINE_MINIMAL,
                    max_inline_tokens=0,
                    max_retrieved_tokens=0,
                    max_output_tokens=0,
                    allow_model_call=False,
                ),
                context=ContextPlan(
                    context_mode=ContextMode.REF_ONLY,
                    base_checkpoint=request.base_checkpoint,
                    required_refs=request.required_refs,
                    optional_refs=(),
                    omitted_optional_refs=request.optional_refs,
                    rationale=(
                        "WAITING_EXTERNAL is a control-plane state; model budget is zero.",
                    ),
                ),
            )

        if request.invocation_mode == InvocationMode.DETERMINISTIC:
            return TokenEconomyDecision(
                budget=TokenBudget(
                    context_mode=ContextMode.REF_ONLY,
                    reasoning_profile=ReasoningProfile.NO_MODEL,
                    communication_mode=CommunicationMode.MACHINE_MINIMAL,
                    max_inline_tokens=0,
                    max_retrieved_tokens=0,
                    max_output_tokens=0,
                    allow_model_call=False,
                ),
                context=ContextPlan(
                    context_mode=ContextMode.REF_ONLY,
                    base_checkpoint=request.base_checkpoint,
                    required_refs=request.required_refs,
                    optional_refs=(),
                    omitted_optional_refs=request.optional_refs,
                    rationale=("Deterministic execution requires no model invocation.",),
                ),
            )

        context_mode = self._context_mode(request)
        reasoning = (
            ReasoningProfile.DEEP
            if request.deep_reasoning_required
            else ReasoningProfile.ECONOMY
        )
        communication = (
            CommunicationMode.USER_FACING
            if request.user_facing
            else CommunicationMode.MACHINE_MINIMAL
        )

        if reasoning == ReasoningProfile.DEEP:
            limits = (
                self.DEEP_INLINE,
                self.DEEP_RETRIEVAL,
                self.DEEP_OUTPUT,
            )
        else:
            limits = (
                self.ECONOMY_INLINE,
                self.ECONOMY_RETRIEVAL,
                self.ECONOMY_OUTPUT,
            )

        selected_optional = (
            request.optional_refs
            if context_mode in {ContextMode.SELECTED, ContextMode.FULL_RECOVERY}
            else ()
        )
        omitted_optional = tuple(
            ref for ref in request.optional_refs if ref not in selected_optional
        )
        delta_refs = request.delta_refs if context_mode == ContextMode.DELTA else ()

        rationale = [f"context_mode={context_mode.value}"]
        if request.recovery_required:
            rationale.append("recovery_requires_full_reconstructable_context")
        elif context_mode == ContextMode.DELTA:
            rationale.append("session already binds the declared base checkpoint")
        elif context_mode == ContextMode.REF_ONLY:
            rationale.append("leaf work starts from content-addressed references")
        if reasoning == ReasoningProfile.DEEP:
            rationale.append("deep reasoning explicitly required")

        return TokenEconomyDecision(
            budget=TokenBudget(
                context_mode=context_mode,
                reasoning_profile=reasoning,
                communication_mode=communication,
                max_inline_tokens=limits[0],
                max_retrieved_tokens=limits[1],
                max_output_tokens=limits[2],
                allow_model_call=True,
            ),
            context=ContextPlan(
                context_mode=context_mode,
                base_checkpoint=request.base_checkpoint,
                required_refs=request.required_refs,
                optional_refs=selected_optional,
                delta_refs=delta_refs,
                omitted_optional_refs=omitted_optional,
                rationale=tuple(rationale),
            ),
        )

    @staticmethod
    def _context_mode(request: TokenEconomyRequest) -> ContextMode:
        if request.recovery_required:
            return ContextMode.FULL_RECOVERY
        if (
            request.session_mode in {
                SessionMode.PERSISTENT_CHAT,
                SessionMode.SESSION_SCOPED,
            }
            and request.session_has_base_checkpoint
            and request.base_checkpoint
        ):
            return ContextMode.DELTA
        if request.broad_context_required:
            return ContextMode.SELECTED
        return ContextMode.REF_ONLY
