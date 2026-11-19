"""Frozen Research Engine/research-iterate policy experiment accounting.

This adapter never invents model cost from token counts. It joins exact
benchmark run identity + objective validator evidence to ExecutionEconomics
only when the weekly subscription allowance delta is comparable.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Iterable, Mapping

from .governor import HoldoutTaskResult
from .ledger import ExecutionEconomics


class PolicyExperimentError(RuntimeError):
    """Fail-closed policy experiment provenance/accounting error."""


@dataclass(frozen=True)
class FrozenResearchFixture:
    phenotype: str
    fixture_id: str
    fixture_path: str
    fixture_blob_sha: str
    oracle_path: str
    oracle_blob_sha: str
    taxonomy_path: str
    taxonomy_blob_sha: str
    primary_signal: str

    @property
    def fixture_ref(self) -> str:
        return f"{self.fixture_path}@{self.fixture_blob_sha}"

    @property
    def oracle_ref(self) -> str:
        return f"{self.oracle_path}@{self.oracle_blob_sha}"


@dataclass(frozen=True)
class PolicyRunTrace:
    run_id: str
    policy_id: str
    phenotype: str
    fixture_id: str
    fixture_blob_sha: str
    oracle_blob_sha: str
    source_checkpoint_sha: str
    validator_id: str
    validator_passed: bool
    validator_score: float
    validator_evidence_ref: str
    economics_execution_id: str


@dataclass(frozen=True)
class PolicyRunAccounting:
    trace: PolicyRunTrace
    weekly_allowance_points: int | None
    allowance_state: str
    verified_progress_per_point: float | None


@dataclass(frozen=True)
class PolicyExperimentSummary:
    policy_id: str
    phenotype_count: int
    validator_pass_rate: float
    mean_validator_score: float
    minimum_validator_score: float
    quality_gate_passed: bool
    allowance_comparable: bool
    total_weekly_allowance_points: int | None
    verified_progress_per_point: float | None


@dataclass(frozen=True)
class ResearchPolicyExperimentReport:
    matrix_id: str
    phenotypes: tuple[str, ...]
    policies: tuple[str, ...]
    matched_task_sets: bool
    summaries: tuple[PolicyExperimentSummary, ...]
    accounting: tuple[PolicyRunAccounting, ...]
    recommended_policy_id: str | None
    recommendation_reason: str


def _required_string(
    raw: Mapping[str, Any],
    key: str,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise PolicyExperimentError(
            f"{key}:required_nonempty_string"
        )
    return value


def _blob_binding(
    raw: Mapping[str, Any],
    key: str,
) -> tuple[str, str]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise PolicyExperimentError(f"{key}:required_object")
    path = _required_string(value, "path")
    sha = _required_string(value, "blob_sha")
    if len(sha) != 40 or any(
        ch not in "0123456789abcdef"
        for ch in sha
    ):
        raise PolicyExperimentError(
            f"{key}.blob_sha:invalid_git_sha"
        )
    return path, sha


def parse_frozen_research_work_bank(
    matrix: Mapping[str, Any],
) -> tuple[FrozenResearchFixture, ...]:
    matrix_id = _required_string(matrix, "matrix_id")
    if matrix.get("family") != "research_iterate":
        raise PolicyExperimentError(
            f"{matrix_id}:unsupported_family"
        )
    raw_fixtures = matrix.get("fixtures")
    if not isinstance(raw_fixtures, list) or not raw_fixtures:
        raise PolicyExperimentError(
            f"{matrix_id}:fixtures_required"
        )

    fixtures: list[FrozenResearchFixture] = []
    seen_phenotypes: set[str] = set()
    seen_fixture_ids: set[str] = set()
    for raw in raw_fixtures:
        if not isinstance(raw, Mapping):
            raise PolicyExperimentError(
                "fixture_entry:required_object"
            )
        phenotype = _required_string(raw, "phenotype")
        fixture_id = _required_string(raw, "fixture_id")
        if phenotype in seen_phenotypes:
            raise PolicyExperimentError(
                f"duplicate_phenotype:{phenotype}"
            )
        if fixture_id in seen_fixture_ids:
            raise PolicyExperimentError(
                f"duplicate_fixture_id:{fixture_id}"
            )
        seen_phenotypes.add(phenotype)
        seen_fixture_ids.add(fixture_id)
        fixture_path, fixture_sha = _blob_binding(
            raw, "fixture"
        )
        oracle_path, oracle_sha = _blob_binding(
            raw, "oracle"
        )
        taxonomy_path, taxonomy_sha = _blob_binding(
            raw, "taxonomy_profile"
        )
        fixtures.append(
            FrozenResearchFixture(
                phenotype=phenotype,
                fixture_id=fixture_id,
                fixture_path=fixture_path,
                fixture_blob_sha=fixture_sha,
                oracle_path=oracle_path,
                oracle_blob_sha=oracle_sha,
                taxonomy_path=taxonomy_path,
                taxonomy_blob_sha=taxonomy_sha,
                primary_signal=_required_string(
                    raw, "primary_signal"
                ),
            )
        )
    return tuple(fixtures)


def allowed_policy_ids(
    matrix: Mapping[str, Any],
) -> frozenset[str]:
    comparisons = matrix.get("paired_comparisons")
    if not isinstance(comparisons, list):
        raise PolicyExperimentError(
            "paired_comparisons:required_array"
        )
    values: set[str] = set()
    for item in comparisons:
        if not isinstance(item, Mapping):
            raise PolicyExperimentError(
                "paired_comparison:required_object"
            )
        arms = item.get("arms")
        if not isinstance(arms, list) or len(arms) != 2:
            raise PolicyExperimentError(
                "paired_comparison.arms:expected_pair"
            )
        for arm in arms:
            if not isinstance(arm, str) or not arm:
                raise PolicyExperimentError(
                    "paired_comparison.arm:invalid"
                )
            values.add(arm)
    return frozenset(values)


def _index_economics(
    records: Iterable[ExecutionEconomics],
) -> dict[str, ExecutionEconomics]:
    indexed: dict[str, ExecutionEconomics] = {}
    for record in records:
        if record.execution_id in indexed:
            raise PolicyExperimentError(
                f"duplicate_execution_id:{record.execution_id}"
            )
        indexed[record.execution_id] = record
    return indexed


def build_research_policy_report(
    *,
    matrix: Mapping[str, Any],
    traces: Iterable[PolicyRunTrace],
    economics_records: Iterable[ExecutionEconomics],
    policies: Iterable[str],
    phenotypes: Iterable[str] | None = None,
    weekly_limit_id: str,
    minimum_validator_score: float = 0.80,
) -> ResearchPolicyExperimentReport:
    if not weekly_limit_id:
        raise PolicyExperimentError(
            "weekly_limit_id_required"
        )
    if not 0.0 <= minimum_validator_score <= 1.0:
        raise PolicyExperimentError(
            "minimum_validator_score_invalid"
        )

    fixtures = parse_frozen_research_work_bank(matrix)
    by_phenotype = {
        item.phenotype: item
        for item in fixtures
    }
    selected_phenotypes = tuple(
        sorted(
            by_phenotype
            if phenotypes is None
            else set(phenotypes)
        )
    )
    if not selected_phenotypes:
        raise PolicyExperimentError("phenotypes_required")
    for phenotype in selected_phenotypes:
        if phenotype not in by_phenotype:
            raise PolicyExperimentError(
                f"unknown_phenotype:{phenotype}"
            )

    selected_policies = tuple(sorted(set(policies)))
    if len(selected_policies) < 2:
        raise PolicyExperimentError(
            "at_least_two_policies_required"
        )
    allowed = allowed_policy_ids(matrix)
    for policy_id in selected_policies:
        if policy_id not in allowed:
            raise PolicyExperimentError(
                f"policy_not_in_frozen_matrix:{policy_id}"
            )

    economics = _index_economics(economics_records)
    indexed: dict[
        tuple[str, str],
        PolicyRunTrace,
    ] = {}
    accounting: list[PolicyRunAccounting] = []
    for trace in traces:
        if trace.policy_id not in selected_policies:
            continue
        if trace.phenotype not in selected_phenotypes:
            continue
        key = (trace.policy_id, trace.phenotype)
        if key in indexed:
            raise PolicyExperimentError(
                "duplicate_policy_phenotype_trace:"
                f"{trace.policy_id}:{trace.phenotype}"
            )
        fixture = by_phenotype[trace.phenotype]
        if (
            trace.fixture_id != fixture.fixture_id
            or trace.fixture_blob_sha
            != fixture.fixture_blob_sha
            or trace.oracle_blob_sha
            != fixture.oracle_blob_sha
        ):
            raise PolicyExperimentError(
                f"trace_provenance_mismatch:{trace.run_id}"
            )
        if (
            not trace.source_checkpoint_sha
            or len(trace.source_checkpoint_sha) != 40
            or any(
                ch not in "0123456789abcdef"
                for ch in trace.source_checkpoint_sha
            )
        ):
            raise PolicyExperimentError(
                f"trace_source_checkpoint_invalid:{trace.run_id}"
            )
        if trace.validator_id != "research_iterate_objective_v1":
            raise PolicyExperimentError(
                f"unexpected_validator:{trace.run_id}"
            )
        if not 0.0 <= trace.validator_score <= 1.0:
            raise PolicyExperimentError(
                f"validator_score_invalid:{trace.run_id}"
            )
        if not trace.validator_evidence_ref:
            raise PolicyExperimentError(
                f"validator_evidence_required:{trace.run_id}"
            )
        record = economics.get(trace.economics_execution_id)
        if record is None:
            allowance_points = None
            allowance_state = "ECONOMICS_MISSING"
            efficiency = None
        else:
            if record.work_item_id != trace.run_id:
                raise PolicyExperimentError(
                    f"economics_work_identity_mismatch:{trace.run_id}"
                )
            if record.validator_passed is not trace.validator_passed:
                raise PolicyExperimentError(
                    f"economics_validator_pass_mismatch:{trace.run_id}"
                )
            if (
                record.validator_score is None
                or abs(
                    record.validator_score
                    - trace.validator_score
                ) > 1e-12
            ):
                raise PolicyExperimentError(
                    f"economics_validator_score_mismatch:{trace.run_id}"
                )
            allowance_points = (
                record.usage_delta.known_weekly_delta_points(
                    limit_id=weekly_limit_id
                )
            )
            if allowance_points is None:
                allowance_state = "UNKNOWN_ALLOWANCE"
                efficiency = None
            elif allowance_points <= 0:
                # Meter resolution zero is deliberately not treated as free.
                allowance_points = None
                allowance_state = "BELOW_METER_RESOLUTION"
                efficiency = None
            else:
                allowance_state = "COMPARABLE"
                efficiency = (
                    record.verified_progress_per_weekly_allowance_point(
                        limit_id=weekly_limit_id
                    )
                )
        indexed[key] = trace
        accounting.append(
            PolicyRunAccounting(
                trace=trace,
                weekly_allowance_points=allowance_points,
                allowance_state=allowance_state,
                verified_progress_per_point=efficiency,
            )
        )

    expected_keys = {
        (policy_id, phenotype)
        for policy_id in selected_policies
        for phenotype in selected_phenotypes
    }
    matched = set(indexed) == expected_keys

    by_key_accounting = {
        (item.trace.policy_id, item.trace.phenotype): item
        for item in accounting
    }
    summaries: list[PolicyExperimentSummary] = []
    for policy_id in selected_policies:
        rows = [
            by_key_accounting[(policy_id, phenotype)]
            for phenotype in selected_phenotypes
            if (policy_id, phenotype) in by_key_accounting
        ]
        if not rows:
            continue
        scores = [
            row.trace.validator_score
            if row.trace.validator_passed
            else 0.0
            for row in rows
        ]
        pass_rate = sum(
            1 for row in rows
            if row.trace.validator_passed
        ) / len(rows)
        quality_gate = (
            len(rows) == len(selected_phenotypes)
            and all(row.trace.validator_passed for row in rows)
            and min(scores) >= minimum_validator_score
        )
        allowance_comparable = (
            len(rows) == len(selected_phenotypes)
            and all(
                row.allowance_state == "COMPARABLE"
                for row in rows
            )
        )
        total_allowance = (
            sum(
                int(row.weekly_allowance_points)
                for row in rows
            )
            if allowance_comparable
            else None
        )
        progress = sum(scores)
        efficiency = (
            progress / total_allowance
            if (
                total_allowance is not None
                and total_allowance > 0
            )
            else None
        )
        summaries.append(
            PolicyExperimentSummary(
                policy_id=policy_id,
                phenotype_count=len(rows),
                validator_pass_rate=pass_rate,
                mean_validator_score=mean(scores),
                minimum_validator_score=min(scores),
                quality_gate_passed=quality_gate,
                allowance_comparable=allowance_comparable,
                total_weekly_allowance_points=total_allowance,
                verified_progress_per_point=efficiency,
            )
        )

    recommended = None
    reason = "NO_RECOMMENDATION"
    if matched and len(summaries) == len(selected_policies):
        eligible = [
            item
            for item in summaries
            if item.quality_gate_passed
            and item.allowance_comparable
            and item.total_weekly_allowance_points is not None
        ]
        if len(eligible) == len(summaries):
            ordered = sorted(
                eligible,
                key=lambda item: (
                    int(item.total_weekly_allowance_points),
                    -item.mean_validator_score,
                    item.policy_id,
                ),
            )
            if (
                len(ordered) >= 2
                and ordered[0].total_weekly_allowance_points
                < ordered[1].total_weekly_allowance_points
            ):
                recommended = ordered[0].policy_id
                reason = (
                    "LOWEST_COMPARABLE_ALLOWANCE_WITH_"
                    "OBJECTIVE_QUALITY_GATE"
                )
            else:
                reason = "NO_STRICT_ALLOWANCE_IMPROVEMENT"
        elif any(
            not item.quality_gate_passed
            for item in summaries
        ):
            reason = "QUALITY_GATE_INCOMPLETE_OR_FAILED"
        else:
            reason = "ALLOWANCE_COMPARISON_UNKNOWN"
    elif not matched:
        reason = "UNMATCHED_POLICY_TASK_SETS"

    return ResearchPolicyExperimentReport(
        matrix_id=_required_string(matrix, "matrix_id"),
        phenotypes=selected_phenotypes,
        policies=selected_policies,
        matched_task_sets=matched,
        summaries=tuple(summaries),
        accounting=tuple(
            sorted(
                accounting,
                key=lambda item: (
                    item.trace.policy_id,
                    item.trace.phenotype,
                ),
            )
        ),
        recommended_policy_id=recommended,
        recommendation_reason=reason,
    )


def holdout_rows_from_report(
    report: ResearchPolicyExperimentReport,
) -> tuple[HoldoutTaskResult, ...]:
    rows: list[HoldoutTaskResult] = []
    for item in report.accounting:
        if item.allowance_state != "COMPARABLE":
            raise PolicyExperimentError(
                "holdout_requires_comparable_allowance"
            )
        assert item.weekly_allowance_points is not None
        rows.append(
            HoldoutTaskResult(
                policy_id=item.trace.policy_id,
                work_item_id=item.trace.phenotype,
                validator_passed=item.trace.validator_passed,
                validator_score=item.trace.validator_score,
                weekly_allowance_points=(
                    item.weekly_allowance_points
                ),
            )
        )
    return tuple(rows)
