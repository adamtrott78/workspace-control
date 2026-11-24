"""Claim-bearing readiness gate for frozen policy experiment runsets.

The benchmark matrix is useful for mechanics and non-claim-bearing screening,
but policy promotion must be bound to an explicitly completed claim-bearing
runset generation. This module prevents superseded, screening-only, or
provenance-refrozen-but-incomplete runs from entering promotion evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .._compat import StrEnum
from .experiments import (
    PolicyRunTrace,
    ResearchPolicyExperimentReport,
    build_research_policy_report,
)


class RunsetReadinessError(RuntimeError):
    """Fail-closed runset promotion-readiness error."""


class RunsetReadinessState(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class RunsetReadinessAudit:
    matrix_id: str
    runset_id: str
    state: RunsetReadinessState
    source_checkpoint_sha: str | None
    claim_bearing_run_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def promotion_ready(self) -> bool:
        return self.state == RunsetReadinessState.READY


def _required_mapping(
    raw: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise RunsetReadinessError(
            f"{key}:required_object"
        )
    return value


def _required_string(
    raw: Mapping[str, Any],
    key: str,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise RunsetReadinessError(
            f"{key}:required_nonempty_string"
        )
    return value


def _git_sha(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(
            ch not in "0123456789abcdef"
            for ch in value
        )
    ):
        raise RunsetReadinessError(
            f"{field}:invalid_git_sha"
        )
    return value


def audit_policy_runset_readiness(
    *,
    matrix: Mapping[str, Any],
    runset: Mapping[str, Any],
    matrix_blob_sha: str,
) -> RunsetReadinessAudit:
    """Require explicit completion evidence before a runset can drive promotion."""

    matrix_id = _required_string(matrix, "matrix_id")
    runset_id = _required_string(runset, "runset_id")
    bound_matrix = _required_mapping(
        _required_mapping(runset, "frozen_inputs"),
        "fixture_matrix",
    )
    bound_matrix_sha = _git_sha(
        bound_matrix.get("blob_sha"),
        field="frozen_inputs.fixture_matrix.blob_sha",
    )
    supplied_matrix_sha = _git_sha(
        matrix_blob_sha,
        field="matrix_blob_sha",
    )
    reasons: list[str] = []
    if bound_matrix_sha != supplied_matrix_sha:
        reasons.append("MATRIX_BLOB_BINDING_MISMATCH")

    stages = runset.get("execution_stages")
    if not isinstance(stages, list):
        raise RunsetReadinessError(
            "execution_stages:required_array"
        )
    screening = next(
        (
            item
            for item in stages
            if isinstance(item, Mapping)
            and item.get("id") == "protocol_screening"
        ),
        None,
    )
    scored = next(
        (
            item
            for item in stages
            if isinstance(item, Mapping)
            and item.get("id") == "scored_replicates"
        ),
        None,
    )
    if screening is None or scored is None:
        raise RunsetReadinessError(
            "required_runset_stages_missing"
        )

    screening_status = screening.get("status")
    if screening_status != "COMPLETE":
        reasons.append("PROTOCOL_SCREENING_NOT_COMPLETE")

    if scored.get("claim_bearing") is not True:
        reasons.append("SCORED_REPLICATES_NOT_CLAIM_BEARING")
    if scored.get("status") != "COMPLETE":
        reasons.append("SCORED_REPLICATES_NOT_COMPLETE")

    promotion = runset.get("promotion_readiness")
    source_checkpoint: str | None = None
    claim_ids: tuple[str, ...] = ()
    if not isinstance(promotion, Mapping):
        reasons.append("PROMOTION_READINESS_MANIFEST_MISSING")
    else:
        if promotion.get("status") != "READY":
            reasons.append("PROMOTION_READINESS_NOT_READY")
        if promotion.get("hard_gates_passed") is not True:
            reasons.append("PROMOTION_HARD_GATES_NOT_PASSED")
        if promotion.get("protocol_frozen") is not True:
            reasons.append("PROMOTION_PROTOCOL_NOT_FROZEN")
        try:
            source_checkpoint = _git_sha(
                promotion.get("source_checkpoint_sha"),
                field=(
                    "promotion_readiness."
                    "source_checkpoint_sha"
                ),
            )
        except RunsetReadinessError:
            reasons.append(
                "PROMOTION_SOURCE_CHECKPOINT_INVALID"
            )

        raw_ids = promotion.get("claim_bearing_run_ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            reasons.append("CLAIM_BEARING_RUN_IDS_MISSING")
        elif any(
            not isinstance(item, str) or not item
            for item in raw_ids
        ):
            reasons.append("CLAIM_BEARING_RUN_IDS_INVALID")
        elif len(raw_ids) != len(set(raw_ids)):
            reasons.append("CLAIM_BEARING_RUN_IDS_DUPLICATED")
        else:
            claim_ids = tuple(sorted(raw_ids))

        scored_checkpoint = scored.get("source_checkpoint_sha")
        if source_checkpoint is not None:
            if (
                not isinstance(scored_checkpoint, str)
                or scored_checkpoint != source_checkpoint
            ):
                reasons.append(
                    "SCORED_REPLICATE_CHECKPOINT_MISMATCH"
                )
        scored_ids = scored.get("completed_run_ids")
        if claim_ids:
            if (
                not isinstance(scored_ids, list)
                or set(scored_ids) != set(claim_ids)
            ):
                reasons.append(
                    "SCORED_REPLICATE_RUN_SET_MISMATCH"
                )

    top_status = runset.get("status")
    if (
        isinstance(top_status, str)
        and (
            "IN_PROGRESS" in top_status
            or "PENDING" in top_status
            or "SUPERSEDED" in top_status
        )
    ):
        reasons.append("RUNSET_STATUS_NOT_TERMINAL")

    return RunsetReadinessAudit(
        matrix_id=matrix_id,
        runset_id=runset_id,
        state=(
            RunsetReadinessState.READY
            if not reasons
            else RunsetReadinessState.NOT_READY
        ),
        source_checkpoint_sha=source_checkpoint,
        claim_bearing_run_ids=claim_ids,
        reasons=tuple(sorted(set(reasons))),
    )


def build_claim_bearing_policy_report(
    *,
    audit: RunsetReadinessAudit,
    matrix: Mapping[str, Any],
    traces: Iterable[PolicyRunTrace],
    economics_records,
    policies: Iterable[str],
    weekly_limit_id: str,
    phenotypes: Iterable[str] | None = None,
    minimum_validator_score: float = 0.80,
) -> ResearchPolicyExperimentReport:
    """Build a promotion-grade report only from the audited claim-bearing set."""

    if not audit.promotion_ready:
        raise RunsetReadinessError(
            "runset_not_promotion_ready:"
            + ",".join(audit.reasons)
        )
    traces_tuple = tuple(traces)
    allowed = set(audit.claim_bearing_run_ids)
    seen: set[str] = set()
    for trace in traces_tuple:
        if trace.run_id not in allowed:
            raise RunsetReadinessError(
                f"trace_not_claim_bearing:{trace.run_id}"
            )
        if (
            audit.source_checkpoint_sha is None
            or trace.source_checkpoint_sha
            != audit.source_checkpoint_sha
        ):
            raise RunsetReadinessError(
                f"trace_checkpoint_mismatch:{trace.run_id}"
            )
        if trace.run_id in seen:
            raise RunsetReadinessError(
                f"duplicate_claim_bearing_trace:{trace.run_id}"
            )
        seen.add(trace.run_id)
    if seen != allowed:
        missing = ",".join(sorted(allowed - seen))
        raise RunsetReadinessError(
            f"claim_bearing_trace_set_incomplete:{missing}"
        )

    return build_research_policy_report(
        matrix=matrix,
        traces=traces_tuple,
        economics_records=economics_records,
        policies=policies,
        phenotypes=phenotypes,
        weekly_limit_id=weekly_limit_id,
        minimum_validator_score=minimum_validator_score,
    )
