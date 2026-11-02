"""Contract checks for clean screening worker bootstrap/state."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/workspace-semantic-execution"
BOOT = json.loads((BASE / "screening_worker_bootstrap_v1.json").read_text())
RUN = json.loads((BASE / "runs/screening-v1/P0/B_instant_persistent_chat/screen-001.json").read_text())

class ScreeningBootstrapTests(unittest.TestCase):
    def test_first_slot_is_non_claim_bearing_and_ready(self):
        self.assertFalse(RUN["claim_bearing"])
        self.assertEqual(RUN["status"], "READY")
        self.assertEqual(RUN["arm"], "B_instant_persistent_chat")
        self.assertEqual(RUN["phenotype"], "P0_easy_control")

    def test_worker_has_no_oracle_path_in_public_inputs(self):
        public = json.dumps(RUN["public_inputs"], sort_keys=True)
        self.assertNotIn("oracle", public.lower())
        self.assertTrue(any("p0_oracle" in x for x in RUN["forbidden_inputs"]))

    def test_no_polling_and_no_self_validation_rules_are_explicit(self):
        rules = "\n".join(BOOT["worker_rules"])
        self.assertIn("Do not poll", rules)
        self.assertIn("may not self-validate", rules)

    def test_slot_has_no_evaluator_result_at_creation(self):
        self.assertEqual(RUN["external_results"], {})
        self.assertEqual(RUN["validator_results"], [])
        self.assertIsNone(RUN["terminal_submission"])

    def test_clean_worker_connector_surface_is_bounded(self):
        rules = "\n".join(BOOT["worker_rules"])
        self.assertIn("connector other than GitHub", rules)
        self.assertIn("Memory/personal_context", rules)

if __name__ == "__main__":
    unittest.main()
