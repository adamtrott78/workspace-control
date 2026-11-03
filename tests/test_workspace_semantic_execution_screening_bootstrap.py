"""Contract checks for clean screening worker bootstrap/state."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/workspace-semantic-execution"
BOOT = json.loads((BASE / "screening_worker_bootstrap_v1.json").read_text())
RUN = json.loads((BASE / "runs/screening-v1/P0/B_instant_persistent_chat/screen-002.json").read_text())
PREDECESSOR = json.loads((BASE / "runs/screening-v1/P0/B_instant_persistent_chat/screen-001.json").read_text())

class ScreeningBootstrapTests(unittest.TestCase):
    def test_active_slot_is_non_claim_bearing_and_has_valid_lifecycle_state(self):
        self.assertFalse(RUN["claim_bearing"])
        self.assertIn(
            RUN["status"],
            {"READY", "RUNNING", "WAITING_EXTERNAL", "READY_TO_RESUME", "TERMINAL_CANDIDATE", "COMPLETED"},
        )
        self.assertEqual(RUN["arm"], "B_instant_persistent_chat")
        self.assertEqual(RUN["phenotype"], "P0_easy_control")

    def test_contaminated_predecessor_is_preserved(self):
        self.assertEqual(PREDECESSOR["status"], "CONTAMINATED_SESSION")
        self.assertEqual(PREDECESSOR["metrics"]["reasoning_invocations"], 0)
        self.assertEqual(PREDECESSOR["metrics"]["experiment_requests"], 0)

    def test_worker_has_no_oracle_path_in_public_inputs(self):
        public = json.dumps(RUN["public_inputs"], sort_keys=True)
        self.assertNotIn("oracle", public.lower())
        self.assertTrue(any("p0_oracle" in x for x in RUN["forbidden_inputs"]))

    def test_no_polling_and_no_self_validation_rules_are_explicit(self):
        rules = "\n".join(BOOT["worker_rules"])
        self.assertIn("Do not poll", rules)
        self.assertIn("may not self-validate", rules)

    def test_active_slot_state_is_internally_consistent(self):
        if RUN["status"] == "READY":
            self.assertEqual(RUN["external_results"], {})
            self.assertEqual(RUN["validator_results"], [])
            self.assertIsNone(RUN["terminal_submission"])
        if RUN["status"] == "WAITING_EXTERNAL":
            self.assertIsNotNone(RUN["pending_external"])
        if RUN["status"] == "READY_TO_RESUME":
            self.assertIsNone(RUN["pending_external"])
            self.assertTrue(RUN["external_results"])
        if RUN["status"] == "COMPLETED":
            self.assertIsNone(RUN["pending_external"])
            self.assertTrue(RUN["validator_results"])
            self.assertTrue(RUN["validator_results"][-1]["passed"])

    def test_session_isolation_keeps_github_available(self):
        contract = BOOT["session_isolation_contract"]
        self.assertEqual(contract["required_chat_type"], "brand_new_regular_chat")
        self.assertEqual(contract["memory_setting"], "disabled_before_chat_start")
        self.assertIn("GitHub", contract["required_plugins"])
        invalid = "\n".join(contract["forbidden_chat_modes"])
        self.assertIn("Unpersonalized Temporary Chat", invalid)
        self.assertIn("Personalized Temporary Chat", invalid)

    def test_unobservable_launch_properties_may_use_explicit_user_attestation(self):
        contract = BOOT["session_isolation_contract"]
        allowed = set(contract["user_attestation_allowed_for"])
        self.assertEqual(
            allowed,
            {
                "brand_new_regular_chat",
                "memory_disabled_before_chat_start",
                "selected_model_and_chat_configuration",
            },
        )
        self.assertIn("explicit user attestation", contract["attestation_rule"].lower())
        self.assertIn("CONTAMINATED_SESSION", contract["contamination_rule"])

    def test_terminal_candidate_rule_requires_raw_result_hash_mapping(self):
        rules = "\n".join(BOOT["worker_rules"])
        self.assertIn("observed_results MUST be an object mapping experiment_id", rules)
        self.assertIn("raw 64-character SHA-256 hash string", rules)

    def test_clean_worker_connector_surface_is_bounded(self):
        rules = "\n".join(BOOT["worker_rules"])
        self.assertIn("connector other than GitHub", rules)
        self.assertIn("Memory/personal_context", rules)

if __name__ == "__main__":
    unittest.main()
