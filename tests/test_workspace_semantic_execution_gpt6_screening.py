"""Contract checks for supplementary GPT-6 Instant screening."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/workspace-semantic-execution"
RUNSET = json.loads((BASE / "resumable_reasoning_matrix_runset_v1.json").read_text())
RUN = json.loads(
    (BASE / "runs/screening-v1/P0/B6_gpt6_instant_persistent_chat/screen-001.json").read_text()
)
ACTIVE = json.loads(
    (BASE / "runs/screening-v1/P0/B6_gpt6_instant_persistent_chat/screen-002.json").read_text()
)

class GPT6InstantScreeningTests(unittest.TestCase):
    def test_supplementary_arm_is_registered(self):
        arm = RUNSET["executor_configurations"]["supplementary_instant_controls"]["B6_gpt6_instant_persistent_chat"]
        self.assertEqual(arm["model_family"], "GPT-6")
        self.assertEqual(arm["chat_configuration"], "Instant")
        self.assertEqual(arm["surface"], "ChatGPT chat")

    def test_slot_is_completed_non_claim_bearing_and_objectively_validated(self):
        self.assertEqual(RUN["status"], "COMPLETED")
        self.assertFalse(RUN["claim_bearing"])
        self.assertEqual(RUN["arm"], "B6_gpt6_instant_persistent_chat")
        self.assertIsNone(RUN["pending_external"])
        self.assertTrue(RUN["validator_results"])
        self.assertTrue(RUN["validator_results"][-1]["passed"])
        self.assertEqual(RUN["validator_results"][-1]["score"], 1.0)
        self.assertEqual(RUN["validator_results"][-1]["violations"], [])

    def test_clarified_re_screen_slot_is_ready_and_bound_to_validated_protocol(self):
        self.assertEqual(ACTIVE["status"], "READY")
        self.assertFalse(ACTIVE["claim_bearing"])
        self.assertEqual(ACTIVE["source_checkpoint_sha"], "6b0ada4e0a9e9f29cd281d82e1fc786df8895982")
        self.assertEqual(
            ACTIVE["public_inputs"]["fixture_blob_sha"],
            "b33e0afa98d0051e5f41241eead770622c2c9eb0",
        )
        self.assertEqual(ACTIVE["expected_executor"]["model_family"], "GPT-6")

    def test_slot_requires_clean_memory_off_session(self):
        expected = RUN["expected_executor"]
        self.assertEqual(expected["model_family"], "GPT-6")
        self.assertEqual(expected["chat_configuration"], "Instant")
        self.assertEqual(expected["memory_mode"], "disabled_regular_chat")

    def test_slot_accepts_explicit_user_attestation_for_unobservable_ui_state(self):
        contract = RUN["contamination_policy"]["user_attestation_contract"]
        self.assertIn(
            "GPT-6 Instant was selected for this conversation",
            contract["required_statements"],
        )
        self.assertIn(
            "Memory was disabled before this conversation was opened",
            contract["required_statements"],
        )
        self.assertIn("Explicit user attestation", contract["acceptance"])

    def test_public_inputs_exclude_oracle(self):
        public = json.dumps(RUN["public_inputs"], sort_keys=True).lower()
        self.assertNotIn("oracle", public)

if __name__ == "__main__":
    unittest.main()
