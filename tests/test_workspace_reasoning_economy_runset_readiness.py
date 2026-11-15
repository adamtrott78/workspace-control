"""Claim-bearing runset readiness tests for Reasoning Economy."""
from __future__ import annotations

from copy import deepcopy
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
    PolicyRunTrace,
    RunsetReadinessError,
    RunsetReadinessState,
    WasteClass,
    audit_policy_runset_readiness,
    build_claim_bearing_policy_report,
    build_execution_economics,
    parse_frozen_research_work_bank,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


BASE = ROOT / "benchmarks" / "workspace-semantic-execution"
MATRIX = json.loads(
    (BASE / "resumable_reasoning_fixture_matrix_v1.json").read_text(
        encoding="utf-8"
    )
)
RUNSET = json.loads(
    (BASE / "resumable_reasoning_matrix_runset_v1.json").read_text(
        encoding="utf-8"
    )
)
MATRIX_BLOB_SHA = "2fa11f2905a42a60fb58b7cf7feb0ac29d589bab"
SOURCE_CHECKPOINT = "1" * 40
LIMIT_ID = "codex"
POLICY_B = "B_instant_persistent_chat"
POLICY_C = "C_instant_stateless_resume"
RESET = int(
    datetime(2026, 11, 22, 12, tzinfo=timezone.utc).timestamp()
)


def ready_runset():
    runset = deepcopy(RUNSET)
    runset["status"] = "CLAIM_BEARING_COMPLETE"
    screening = next(
        item
        for item in runset["execution_stages"]
        if item["id"] == "protocol_screening"
    )
    scored = next(
        item
        for item in runset["execution_stages"]
        if item["id"] == "scored_replicates"
    )
    screening["status"] = "COMPLETE"
    scored["status"] = "COMPLETE"
    scored["source_checkpoint_sha"] = SOURCE_CHECKPOINT
    scored["completed_run_ids"] = [
        "claim-P0-B",
        "claim-P0-C",
    ]
    runset["promotion_readiness"] = {
        "status": "READY",
        "hard_gates_passed": True,
        "protocol_frozen": True,
        "source_checkpoint_sha": SOURCE_CHECKPOINT,
        "claim_bearing_run_ids": [
            "claim-P0-B",
            "claim-P0-C",
        ],
    }
    return runset


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
                        window_class=RateLimitWindowClass.WEEKLY,
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


def economics(execution_id: str, run_id: str, executor_id: str, cost: int):
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
        validator_passed=True,
        validator_score=1.0,
        waste_class=WasteClass.PRODUCTIVE_REASONING,
        usage_before=usage(10),
        usage_after=usage(10 + cost),
    )


def traces():
    fixture = next(
        item
        for item in parse_frozen_research_work_bank(MATRIX)
        if item.phenotype == "P0_easy_control"
    )
    rows = []
    for run_id, policy, execution_id in (
        ("claim-P0-B", POLICY_B, "exec-B"),
        ("claim-P0-C", POLICY_C, "exec-C"),
    ):
        rows.append(
            PolicyRunTrace(
                run_id=run_id,
                policy_id=policy,
                phenotype=fixture.phenotype,
                fixture_id=fixture.fixture_id,
                fixture_blob_sha=fixture.fixture_blob_sha,
                oracle_blob_sha=fixture.oracle_blob_sha,
                source_checkpoint_sha=SOURCE_CHECKPOINT,
                validator_id="research_iterate_objective_v1",
                validator_passed=True,
                validator_score=1.0,
                validator_evidence_ref=f"validator:{run_id}",
                economics_execution_id=execution_id,
            )
        )
    return rows


class RunsetReadinessTests(unittest.TestCase):
    def test_current_refrozen_screening_runset_is_explicitly_not_promotion_ready(self):
        audit = audit_policy_runset_readiness(
            matrix=MATRIX,
            runset=RUNSET,
            matrix_blob_sha=MATRIX_BLOB_SHA,
        )

        self.assertEqual(
            audit.state,
            RunsetReadinessState.NOT_READY,
        )
        self.assertFalse(audit.promotion_ready)
        self.assertIn(
            "PROTOCOL_SCREENING_NOT_COMPLETE",
            audit.reasons,
        )
        self.assertIn(
            "SCORED_REPLICATES_NOT_COMPLETE",
            audit.reasons,
        )
        self.assertIn(
            "PROMOTION_READINESS_MANIFEST_MISSING",
            audit.reasons,
        )
        self.assertIn(
            "RUNSET_STATUS_NOT_TERMINAL",
            audit.reasons,
        )

    def test_non_ready_runset_cannot_build_claim_bearing_report(self):
        audit = audit_policy_runset_readiness(
            matrix=MATRIX,
            runset=RUNSET,
            matrix_blob_sha=MATRIX_BLOB_SHA,
        )
        with self.assertRaisesRegex(
            RunsetReadinessError,
            "runset_not_promotion_ready",
        ):
            build_claim_bearing_policy_report(
                audit=audit,
                matrix=MATRIX,
                traces=(),
                economics_records=(),
                policies=(POLICY_B, POLICY_C),
                weekly_limit_id=LIMIT_ID,
            )

    def test_explicit_completed_claim_bearing_manifest_can_be_ready(self):
        audit = audit_policy_runset_readiness(
            matrix=MATRIX,
            runset=ready_runset(),
            matrix_blob_sha=MATRIX_BLOB_SHA,
        )

        self.assertTrue(audit.promotion_ready)
        self.assertEqual(
            audit.source_checkpoint_sha,
            SOURCE_CHECKPOINT,
        )
        self.assertEqual(
            audit.claim_bearing_run_ids,
            ("claim-P0-B", "claim-P0-C"),
        )

    def test_claim_bearing_report_requires_exact_checkpoint_and_run_set(self):
        audit = audit_policy_runset_readiness(
            matrix=MATRIX,
            runset=ready_runset(),
            matrix_blob_sha=MATRIX_BLOB_SHA,
        )
        rows = traces()
        bad = list(rows)
        first = bad[0]
        bad[0] = PolicyRunTrace(
            run_id=first.run_id,
            policy_id=first.policy_id,
            phenotype=first.phenotype,
            fixture_id=first.fixture_id,
            fixture_blob_sha=first.fixture_blob_sha,
            oracle_blob_sha=first.oracle_blob_sha,
            source_checkpoint_sha="2" * 40,
            validator_id=first.validator_id,
            validator_passed=first.validator_passed,
            validator_score=first.validator_score,
            validator_evidence_ref=first.validator_evidence_ref,
            economics_execution_id=first.economics_execution_id,
        )
        with self.assertRaisesRegex(
            RunsetReadinessError,
            "trace_checkpoint_mismatch",
        ):
            build_claim_bearing_policy_report(
                audit=audit,
                matrix=MATRIX,
                traces=bad,
                economics_records=(
                    economics("exec-B", "claim-P0-B", POLICY_B, 3),
                    economics("exec-C", "claim-P0-C", POLICY_C, 2),
                ),
                policies=(POLICY_B, POLICY_C),
                phenotypes=("P0_easy_control",),
                weekly_limit_id=LIMIT_ID,
            )

    def test_ready_claim_bearing_set_can_feed_objective_economics_report(self):
        audit = audit_policy_runset_readiness(
            matrix=MATRIX,
            runset=ready_runset(),
            matrix_blob_sha=MATRIX_BLOB_SHA,
        )
        report = build_claim_bearing_policy_report(
            audit=audit,
            matrix=MATRIX,
            traces=traces(),
            economics_records=(
                economics("exec-B", "claim-P0-B", POLICY_B, 3),
                economics("exec-C", "claim-P0-C", POLICY_C, 2),
            ),
            policies=(POLICY_B, POLICY_C),
            phenotypes=("P0_easy_control",),
            weekly_limit_id=LIMIT_ID,
        )

        self.assertTrue(report.matched_task_sets)
        self.assertEqual(report.recommended_policy_id, POLICY_C)


if __name__ == "__main__":
    unittest.main()
