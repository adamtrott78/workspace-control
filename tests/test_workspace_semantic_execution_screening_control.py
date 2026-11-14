"""Contract checks for screening control-evaluator secrecy."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"benchmarks/workspace-semantic-execution"
CONTROL=json.loads((BASE/"screening_control_evaluator_v1.json").read_text())

class ScreeningControlEvaluatorTests(unittest.TestCase):
    def test_all_matrix_fixtures_have_oracle_binding(self):
        expected={
            "research-iterate-timeout-control-p0-v1",
            "research-iterate-shard-rollout-p1-v1",
            "research-iterate-retry-pooling-v1",
            "research-iterate-cross-region-feedback-p3-v1",
        }
        self.assertEqual(set(CONTROL["fixture_oracle_bindings"]), expected)

    def test_control_never_publishes_expected_answer(self):
        forbidden=set(CONTROL["worker_visible_publication"]["forbidden_publication"])
        self.assertIn("expected_hypothesis", forbidden)
        validator=set(CONTROL["worker_visible_publication"]["validator_fields"])
        self.assertNotIn("expected_hypothesis", validator)

    def test_screening_is_non_claim_bearing(self):
        self.assertFalse(CONTROL["claim_bearing"])
        self.assertIn("does not count", CONTROL["screening_claim_boundary"])

if __name__=="__main__":
    unittest.main()
