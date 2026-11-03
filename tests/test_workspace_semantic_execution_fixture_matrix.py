"""Regression tests for the P0-P3 resumable-reasoning fixture matrix."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/workspace-semantic-execution"
HARNESS_PATH = BASE / "resumable_reasoning_pilot_v1.py"
MATRIX_PATH = BASE / "resumable_reasoning_fixture_matrix_v1.json"

spec = importlib.util.spec_from_file_location("resumable_reasoning_pilot_v1", HARNESS_PATH)
harness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(harness)

MATRIX = json.loads(MATRIX_PATH.read_text())


class FixtureMatrixTests(unittest.TestCase):
    def _load(self, relpath: str):
        return json.loads((ROOT / relpath).read_text())

    def test_matrix_contains_exactly_p0_through_p3(self):
        phenotypes = [item["phenotype"] for item in MATRIX["fixtures"]]
        self.assertEqual(
            phenotypes,
            [
                "P0_easy_control",
                "P1_horizon_heavy_decomposable",
                "P2_reasoning_heavy_coupled",
                "P3_mixed_long_hard",
            ],
        )

    def test_all_public_fixtures_exclude_oracle_truth(self):
        for entry in MATRIX["fixtures"]:
            fixture = self._load(entry["fixture"]["path"])
            oracle = self._load(entry["oracle"]["path"])
            serialized = json.dumps(fixture, sort_keys=True)
            self.assertEqual(fixture["visibility"], "worker_visible")
            self.assertEqual(
                oracle["visibility"],
                "evaluator_only_do_not_supply_to_reasoning_worker",
            )
            self.assertNotIn("expected_hypothesis", serialized)
            self.assertNotIn("experiment_results", serialized)
            self.assertNotEqual(entry["fixture"]["blob_sha"], entry["oracle"]["blob_sha"])

    def test_all_public_fixtures_expose_exact_terminal_output_schema(self):
        for entry in MATRIX["fixtures"]:
            fixture = self._load(entry["fixture"]["path"])
            schema = fixture["worker_contract"]["terminal_output_schema"]
            self.assertIn("experiment_id", schema["observed_results"])
            self.assertIn("result_hash", schema["observed_results"])
            self.assertIn("raw 64-character SHA-256 hash string", schema["observed_results"])

    def test_every_fixture_has_a_constructive_passing_submission(self):
        for entry in MATRIX["fixtures"]:
            fixture = self._load(entry["fixture"]["path"])
            oracle = self._load(entry["oracle"]["path"])
            criteria = oracle["terminal_criteria"]

            chosen = []
            for group in criteria["required_experiment_groups"]:
                candidate = group[0]
                if candidate not in chosen:
                    chosen.append(candidate)

            for experiment_id in oracle["experiment_results"]:
                if len(chosen) >= criteria["minimum_unique_experiments"]:
                    break
                if experiment_id not in chosen:
                    chosen.append(experiment_id)

            observed = {
                experiment_id: harness.content_hash(
                    oracle["experiment_results"][experiment_id]
                )
                for experiment_id in chosen
            }
            submission = {
                "final_hypothesis": criteria["expected_hypothesis"],
                "rejected_hypotheses": list(criteria["required_rejected_hypotheses"]),
                "observed_results": observed,
                "addressed_observations": list(
                    criteria["required_addressed_observations"]
                ),
                "rationale": "Constructive contract-valid submission for regression testing.",
            }
            result = harness.evaluate_research_iterate(fixture, oracle, submission)
            self.assertTrue(result["passed"], (entry["phenotype"], result))

    def test_p1_is_horizon_heavy_and_decomposable_by_contract(self):
        entry = next(x for x in MATRIX["fixtures"] if x["phenotype"].startswith("P1_"))
        fixture = self._load(entry["fixture"]["path"])
        profile = self._load(entry["taxonomy_profile"]["path"])
        self.assertGreaterEqual(
            fixture["worker_contract"]["minimum_experiment_cycles_before_terminal_claim"],
            7,
        )
        self.assertEqual(profile["decomposability"]["separability"], "MOSTLY_SEPARABLE")
        self.assertGreaterEqual(profile["horizon_load"]["dependency_width"], 6)
        self.assertEqual(profile["decomposability"]["synthesis_coupling"], "LOW")

    def test_p3_requires_leaf_evidence_plus_coupled_residual(self):
        entry = next(x for x in MATRIX["fixtures"] if x["phenotype"].startswith("P3_"))
        fixture = self._load(entry["fixture"]["path"])
        oracle = self._load(entry["oracle"]["path"])
        leaves = {item.get("leaf") for item in fixture["experiment_catalog"]}
        self.assertTrue({"region-1", "region-2", "region-3", "region-4"}.issubset(leaves))
        self.assertIn("coupled-residual", leaves)
        groups = oracle["terminal_criteria"]["required_experiment_groups"]
        self.assertIn(["E_global_retry_reset"], groups)

    def test_comparison_plan_does_not_use_p0_as_intrinsic_difficulty_fixture(self):
        q3 = next(
            item for item in MATRIX["paired_comparisons"]
            if item["question"] == "Q3_intrinsic_reasoning_boundary"
        )
        self.assertNotIn("P0_easy_control", q3["fixtures"])
        self.assertNotIn("P1_horizon_heavy_decomposable", q3["fixtures"])
        self.assertIn("P2_reasoning_heavy_coupled", q3["fixtures"])
        self.assertIn("P3_mixed_long_hard", q3["fixtures"])


if __name__ == "__main__":
    unittest.main()
