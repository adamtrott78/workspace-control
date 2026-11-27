"""Frozen P0-P3 Research Engine policy experiment accounting tests."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.economics import (  # noqa: E402
    ExecutionTokenUsage,
    PolicyExperimentError,
    PolicyRunTrace,
    WasteClass,
    build_execution_economics,
    build_research_policy_report,
    evaluate_holdout_promotion,
    holdout_rows_from_report,
    parse_frozen_research_work_bank,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


MATRIX_PATH = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "resumable_reasoning_fixture_matrix_v1.json"
)
MATRIX = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
LIMIT_ID = "codex"
RESET = int(
    datetime(
        2026, 11, 22, 12, 0, tzinfo=timezone.utc
    ).timestamp()
)
SOURCE_CHECKPOINT = "052cf8224ec5a725e09207bde0bef8e43cefe8cb"
POLICY_B = "B_instant_persistent_chat"
POLICY_C = "C_instant_stateless_resume"


def usage(used: int) -> UsageSnapshot:
    return UsageSnapshot(
        captured_at="2026-11-15T12:00:00+00:00",
        ordinary_usage_allowed=True,
        rate_limit_buckets=(
            RateLimitBucketSnapshot(
                limit_id=LIMIT_ID,
                limit_name="Codex",
                normal_model_slug="gpt-test",
                plan_type="plus",
                windows=(
                    RateLimitWindowSnapshot(
                        source_role="weekly",
                        used_percent=used,
                        window_duration_mins=10080,
                        resets_at=RESET,
                        window_class=(
                            RateLimitWindowClass.WEEKLY
                        ),
                    ),
                ),
            ),
        ),
        token_summary=AccountTokenUsageSummary(
            lifetime_tokens=None,
            peak_daily_tokens=None,
            longest_running_turn_sec=None,
            current_streak_days=None,
            longest_streak_days=None,
        ),
        daily_usage_buckets=None,
        thread_usage=None,
    )


def economics(
    *,
    execution_id: str,
    run_id: str,
    executor_id: str,
    before: int,
    cost: int,
    passed: bool,
    score: float,
):
    return build_execution_economics(
        execution_id=execution_id,
        work_item_id=run_id,
        parent_execution_id=None,
        executor_id=executor_id,
        model_id="model",
        surface_id="chat",
        started_at="2026-11-15T12:00:00+00:00",
        ended_at="2026-11-15T12:01:00+00:00",
        token_usage=ExecutionTokenUsage(
            input_tokens=100,
            output_tokens=20,
            total_tokens=120,
        ),
        model_invocations=1,
        tool_calls=0,
        retries=0,
        decomposition_depth=0,
        children_spawned=0,
        validator_passed=passed,
        validator_score=score,
        waste_class=WasteClass.PRODUCTIVE_REASONING,
        usage_before=usage(before),
        usage_after=usage(before + cost),
    )


def traces_and_economics(
    *,
    b_cost: int = 3,
    c_cost: int = 2,
    c_score: float = 1.0,
    c_failure_phenotype: str | None = None,
    zero_cost_pair: tuple[str, str] | None = None,
):
    fixtures = parse_frozen_research_work_bank(MATRIX)
    traces = []
    records = []
    counter = 0
    for fixture in fixtures:
        for policy, cost, score in (
            (POLICY_B, b_cost, 1.0),
            (POLICY_C, c_cost, c_score),
        ):
            counter += 1
            run_id = (
                f"economics-{fixture.phenotype}-"
                f"{policy}"
            )
            execution_id = f"exec-{counter}"
            passed = not (
                policy == POLICY_C
                and fixture.phenotype
                == c_failure_phenotype
            )
            actual_cost = (
                0
                if zero_cost_pair
                == (policy, fixture.phenotype)
                else cost
            )
            traces.append(
                PolicyRunTrace(
                    run_id=run_id,
                    policy_id=policy,
                    phenotype=fixture.phenotype,
                    fixture_id=fixture.fixture_id,
                    fixture_blob_sha=(
                        fixture.fixture_blob_sha
                    ),
                    oracle_blob_sha=fixture.oracle_blob_sha,
                    source_checkpoint_sha=SOURCE_CHECKPOINT,
                    validator_id=(
                        "research_iterate_objective_v1"
                    ),
                    validator_passed=passed,
                    validator_score=score,
                    validator_evidence_ref=(
                        f"validator:{run_id}"
                    ),
                    economics_execution_id=execution_id,
                )
            )
            records.append(
                economics(
                    execution_id=execution_id,
                    run_id=run_id,
                    executor_id=policy,
                    before=5 + counter * 5,
                    cost=actual_cost,
                    passed=passed,
                    score=score,
                )
            )
    return traces, records


class FrozenWorkBankTests(unittest.TestCase):
    def test_matrix_parses_exact_four_provenance_bound_fixtures(self):
        fixtures = parse_frozen_research_work_bank(MATRIX)

        self.assertEqual(len(fixtures), 4)
        self.assertEqual(
            {item.phenotype for item in fixtures},
            {
                "P0_easy_control",
                "P1_horizon_heavy_decomposable",
                "P2_reasoning_heavy_coupled",
                "P3_mixed_long_hard",
            },
        )
        p2 = next(
            item
            for item in fixtures
            if item.phenotype
            == "P2_reasoning_heavy_coupled"
        )
        self.assertEqual(
            p2.fixture_blob_sha,
            "389fd2ecd5bfe78e8258ecccb03dea759c043296",
        )
        self.assertEqual(
            p2.oracle_blob_sha,
            "acc914d4fa9862a7f1ad0eabac21dbbf7aa84d68",
        )


class PolicyExperimentTests(unittest.TestCase):
    def test_matched_objective_quality_report_recommends_lower_allowance_policy(self):
        traces, records = traces_and_economics()

        report = build_research_policy_report(
            matrix=MATRIX,
            traces=traces,
            economics_records=records,
            policies=(POLICY_B, POLICY_C),
            weekly_limit_id=LIMIT_ID,
        )

        self.assertTrue(report.matched_task_sets)
        self.assertEqual(
            report.recommended_policy_id,
            POLICY_C,
        )
        self.assertEqual(
            report.recommendation_reason,
            "LOWEST_COMPARABLE_ALLOWANCE_WITH_OBJECTIVE_QUALITY_GATE",
        )
        summaries = {
            item.policy_id: item
            for item in report.summaries
        }
        self.assertEqual(
            summaries[POLICY_B].total_weekly_allowance_points,
            12,
        )
        self.assertEqual(
            summaries[POLICY_C].total_weekly_allowance_points,
            8,
        )
        self.assertTrue(
            summaries[POLICY_C].quality_gate_passed
        )

    def test_zero_meter_delta_remains_unknown_and_blocks_recommendation(self):
        traces, records = traces_and_economics(
            zero_cost_pair=(
                POLICY_C,
                "P2_reasoning_heavy_coupled",
            )
        )

        report = build_research_policy_report(
            matrix=MATRIX,
            traces=traces,
            economics_records=records,
            policies=(POLICY_B, POLICY_C),
            weekly_limit_id=LIMIT_ID,
        )

        self.assertIsNone(report.recommended_policy_id)
        self.assertEqual(
            report.recommendation_reason,
            "ALLOWANCE_COMPARISON_UNKNOWN",
        )
        c_summary = next(
            item
            for item in report.summaries
            if item.policy_id == POLICY_C
        )
        self.assertFalse(c_summary.allowance_comparable)
        unknown = [
            item
            for item in report.accounting
            if (
                item.trace.policy_id == POLICY_C
                and item.trace.phenotype
                == "P2_reasoning_heavy_coupled"
            )
        ]
        self.assertEqual(
            unknown[0].allowance_state,
            "BELOW_METER_RESOLUTION",
        )

    def test_objective_validator_failure_blocks_cheaper_policy(self):
        traces, records = traces_and_economics(
            c_failure_phenotype="P3_mixed_long_hard"
        )

        report = build_research_policy_report(
            matrix=MATRIX,
            traces=traces,
            economics_records=records,
            policies=(POLICY_B, POLICY_C),
            weekly_limit_id=LIMIT_ID,
        )

        self.assertIsNone(report.recommended_policy_id)
        self.assertEqual(
            report.recommendation_reason,
            "QUALITY_GATE_INCOMPLETE_OR_FAILED",
        )

    def test_fixture_blob_drift_fails_closed(self):
        traces, records = traces_and_economics()
        bad = list(traces)
        first = bad[0]
        bad[0] = PolicyRunTrace(
            run_id=first.run_id,
            policy_id=first.policy_id,
            phenotype=first.phenotype,
            fixture_id=first.fixture_id,
            fixture_blob_sha="0" * 40,
            oracle_blob_sha=first.oracle_blob_sha,
            source_checkpoint_sha=first.source_checkpoint_sha,
            validator_id=first.validator_id,
            validator_passed=first.validator_passed,
            validator_score=first.validator_score,
            validator_evidence_ref=(
                first.validator_evidence_ref
            ),
            economics_execution_id=(
                first.economics_execution_id
            ),
        )

        with self.assertRaisesRegex(
            PolicyExperimentError,
            "trace_provenance_mismatch",
        ):
            build_research_policy_report(
                matrix=MATRIX,
                traces=bad,
                economics_records=records,
                policies=(POLICY_B, POLICY_C),
                weekly_limit_id=LIMIT_ID,
            )

    def test_economics_work_identity_mismatch_fails_closed(self):
        traces, records = traces_and_economics()
        first = records[0]
        records[0] = build_execution_economics(
            execution_id=first.execution_id,
            work_item_id="wrong-run",
            parent_execution_id=None,
            executor_id=first.executor_id,
            model_id=first.model_id,
            surface_id=first.surface_id,
            started_at=first.started_at,
            ended_at=first.ended_at,
            token_usage=first.token_usage,
            model_invocations=first.model_invocations,
            tool_calls=first.tool_calls,
            retries=first.retries,
            decomposition_depth=first.decomposition_depth,
            children_spawned=first.children_spawned,
            validator_passed=first.validator_passed,
            validator_score=first.validator_score,
            waste_class=first.waste_class,
            usage_before=first.usage_before,
            usage_after=first.usage_after,
        )

        with self.assertRaisesRegex(
            PolicyExperimentError,
            "economics_work_identity_mismatch",
        ):
            build_research_policy_report(
                matrix=MATRIX,
                traces=traces,
                economics_records=records,
                policies=(POLICY_B, POLICY_C),
                weekly_limit_id=LIMIT_ID,
            )

    def test_report_produces_holdout_rows_for_governor_promotion(self):
        traces, records = traces_and_economics()
        report = build_research_policy_report(
            matrix=MATRIX,
            traces=traces,
            economics_records=records,
            policies=(POLICY_B, POLICY_C),
            weekly_limit_id=LIMIT_ID,
        )

        rows = holdout_rows_from_report(report)
        self.assertEqual(len(rows), 8)
        promotion = evaluate_holdout_promotion(
            baseline_policy_id=POLICY_B,
            candidate_policy_id=POLICY_C,
            results=rows,
            minimum_tasks=4,
        )
        self.assertTrue(promotion.promote)


if __name__ == "__main__":
    unittest.main()
