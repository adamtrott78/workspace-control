"""Reasoning Economy executor admission over validated base eligibility."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..application.executor_dispatch import (
    ExecutorSelectionPolicyDecision,
)
from ..domain import ExecutorProfile, RoutingDecision, WorkDisposition
from ..ports import UsageSnapshot
from .governor import (
    BillingMode,
    GovernorCandidate,
    GovernorOutcome,
    WeeklyBudgetPolicy,
    decide_weekly_route,
)
from .ledger import ExecutionEconomics


@dataclass(frozen=True)
class ExecutorEconomicsBinding:
    executor_id: str
    billing_mode: BillingMode
    weekly_limit_id: str | None

    def validate(self) -> None:
        if not self.executor_id:
            raise ValueError(
                "economics_binding_executor_id_required"
            )
        if (
            self.billing_mode == BillingMode.INCLUDED_SUBSCRIPTION
            and not self.weekly_limit_id
        ):
            raise ValueError(
                "economics_binding_weekly_limit_id_required"
            )


class ReasoningEconomyAdmissionPolicy:
    """Apply budget/quality policy only after normal executor eligibility."""

    def __init__(
        self,
        *,
        budget_policy: WeeklyBudgetPolicy,
        bindings: Iterable[ExecutorEconomicsBinding],
        current_usage: UsageSnapshot,
        usage_history: Iterable[UsageSnapshot],
        economics_records: Iterable[ExecutionEconomics],
    ) -> None:
        budget_policy.validate()
        self._budget_policy = budget_policy
        self._current_usage = current_usage
        self._usage_history = tuple(usage_history)
        self._economics_records = tuple(economics_records)

        indexed: dict[str, ExecutorEconomicsBinding] = {}
        for binding in bindings:
            binding.validate()
            if binding.executor_id in indexed:
                raise ValueError(
                    "duplicate_executor_economics_binding"
                )
            indexed[binding.executor_id] = binding
        self._bindings = indexed

    def select(
        self,
        *,
        requirement_id: str,
        eligible_profiles: tuple[ExecutorProfile, ...],
        base_routing: RoutingDecision,
        disposition: WorkDisposition,
    ) -> ExecutorSelectionPolicyDecision:
        if not requirement_id:
            raise ValueError("requirement_id_required")
        if not eligible_profiles:
            return ExecutorSelectionPolicyDecision(
                selected_executor_id=None,
                outcome="NO_ELIGIBLE_EXECUTOR",
                rationale="Base router supplied no eligible profiles.",
            )
        if (
            base_routing.selected_executor_id is None
            or base_routing.selected_executor_id
            not in {item.executor_id for item in eligible_profiles}
        ):
            raise ValueError(
                "base_routing_selection_not_in_eligible_profiles"
            )

        # Any scarce/provider usage pool must have an explicit economics
        # binding. Unknown accounting is not silently treated as free.
        for profile in eligible_profiles:
            if (
                profile.usage_pool_ids
                and profile.executor_id not in self._bindings
            ):
                return ExecutorSelectionPolicyDecision(
                    selected_executor_id=None,
                    outcome="MISSING_ECONOMICS_BINDING",
                    rationale=(
                        "Eligible executor has a usage pool but no "
                        "Reasoning Economy billing/meter binding: "
                        f"{profile.executor_id}"
                    ),
                )

        base_profile = next(
            item
            for item in eligible_profiles
            if item.executor_id
            == base_routing.selected_executor_id
        )
        base_binding = self._bindings.get(
            base_profile.executor_id
        )
        if (
            base_binding is None
            and not base_profile.usage_pool_ids
        ):
            return ExecutorSelectionPolicyDecision(
                selected_executor_id=base_profile.executor_id,
                outcome="BASE_UNMETERED_PATH",
                rationale=(
                    "Base-selected executor is outside configured scarce "
                    "subscription usage pools; normal capability/scarcity "
                    "routing remains authoritative."
                ),
            )

        candidates = []
        for profile in eligible_profiles:
            binding = self._bindings.get(profile.executor_id)
            if binding is None:
                # No configured scarce meter and not base-selected. It cannot
                # be promoted by this policy because its economics are unknown.
                continue
            candidates.append(
                GovernorCandidate(
                    executor_id=profile.executor_id,
                    scarcity_rank=profile.scarcity_rank,
                    billing_mode=binding.billing_mode,
                    weekly_limit_id=binding.weekly_limit_id,
                )
            )

        decision = decide_weekly_route(
            disposition=disposition,
            current_usage=self._current_usage,
            usage_history=self._usage_history,
            candidates=tuple(candidates),
            economics_records=self._economics_records,
            policy=self._budget_policy,
        )
        if (
            decision.outcome == GovernorOutcome.SELECTED
            and decision.selected_executor_id is not None
        ):
            return ExecutorSelectionPolicyDecision(
                selected_executor_id=decision.selected_executor_id,
                outcome=decision.outcome.value,
                rationale=(
                    decision.reason
                    + "; weekly allowance and objective quality "
                    "admission passed."
                ),
            )

        return ExecutorSelectionPolicyDecision(
            selected_executor_id=None,
            outcome=decision.outcome.value,
            rationale=decision.reason,
        )
