"""Contract checks for the semantic-execution experiment taxonomy."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "benchmarks/workspace-semantic-execution/experiment_taxonomy_v1.json"
PROFILE_PATH = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_research_fixture_v1.taxonomy.json"
BENCHMARK_PATH = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_v1.json"


class ExperimentTaxonomyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = json.loads(TAXONOMY_PATH.read_text())
        cls.profile = json.loads(PROFILE_PATH.read_text())
        cls.benchmark = json.loads(BENCHMARK_PATH.read_text())

    def test_domain_axis_remains_open_world(self):
        axis = self.taxonomy["fixture_axes"]["domain_workflow"]
        self.assertEqual(axis["type"], "open_extension_tags")
        self.assertFalse(axis["core_enum"])

    def test_size_and_intrinsic_difficulty_are_not_collapsed(self):
        questions = self.taxonomy["experiment_question_classes"]
        self.assertIn("Q2_decomposition_effect", questions)
        self.assertIn("Q3_intrinsic_reasoning_boundary", questions)
        self.assertNotEqual(
            questions["Q2_decomposition_effect"]["causal_factor"],
            questions["Q3_intrinsic_reasoning_boundary"]["causal_factor"],
        )
        intrinsic_rule = self.taxonomy["empirical_labels"]["INTRINSICALLY_DIFFICULT"]["assignment_rule"]
        self.assertIn("After reasonable decomposition", intrinsic_rule)

    def test_quality_and_mechanics_suites_are_distinct(self):
        suites = self.taxonomy["benchmark_suites"]
        self.assertTrue(suites["S1_reasoning_quality_boundary"]["terminal_claims_allowed"])
        self.assertFalse(suites["S2_orchestration_mechanics"]["terminal_claims_allowed"])
        self.assertTrue(suites["S3_authority_safety"]["hard_gate"])
        self.assertTrue(suites["S4_open_world_generalization"]["architecture_freeze_gate"])

    def test_efficiency_cannot_compensate_for_quality_or_safety(self):
        rules = self.taxonomy["experimental_design_rules"]
        self.assertIn("quality and hard safety gates", rules["quality_first_rule"])
        suite = self.taxonomy["benchmark_suites"]["S5_resource_routing"]
        self.assertIn("S1", suite["prerequisite"])
        self.assertIn("S3", suite["prerequisite"])

    def test_executor_arm_is_more_than_model_name(self):
        dimensions = self.taxonomy["arm_dimensions"]
        self.assertIn("surface", dimensions["executor_identity"])
        self.assertIn("harness", dimensions["executor_identity"])
        self.assertIn("toolset", dimensions["executor_identity"])
        self.assertEqual(dimensions["rule"], "A model name alone is not an experimental arm.")

    def test_current_pilot_is_not_misclassified_as_decomposition_fixture(self):
        self.assertEqual(
            self.profile["phenotype"]["primary"],
            "P2_reasoning_heavy_coupled",
        )
        weak = self.profile["unsupported_or_weak_questions"]
        self.assertIn("Q2_decomposition_effect", weak)
        self.assertIn("not a good primary decomposition-benefit fixture", weak["Q2_decomposition_effect"])

    def test_current_pilot_oracle_is_not_worker_visible(self):
        contamination = self.profile["contamination_generalization"]
        self.assertEqual(contamination["worker_oracle_exposure"], "NONE_REQUIRED")
        self.assertFalse(contamination["authoring_session_eligible"])
        self.assertEqual(self.profile["validator"]["evaluator_isolation"], "HIDDEN_STATIC")

    def test_benchmark_references_taxonomy_and_claim_limit(self):
        ref = self.benchmark["experiment_taxonomy"]
        self.assertEqual(
            ref["path"],
            "benchmarks/workspace-semantic-execution/experiment_taxonomy_v1.json",
        )
        self.assertEqual(ref["current_pilot_primary_phenotype"], "P2_reasoning_heavy_coupled")
        self.assertIn("cannot alone establish", ref["claim_limit"])


if __name__ == "__main__":
    unittest.main()
