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

class GPT6InstantScreeningTests(unittest.TestCase):
    def test_supplementary_arm_is_registered(self):
        arm = RUNSET["executor_configurations"]["supplementary_instant_controls"]["B6_gpt6_instant_persistent_chat"]
        self.assertEqual(arm["model_family"], "GPT-6")
        self.assertEqual(arm["chat_configuration"], "Instant")
        self.assertEqual(arm["surface"], "ChatGPT chat")

    def test_slot_is_ready_and_non_claim_bearing(self):
        self.assertEqual(RUN["status"], "READY")
        self.assertFalse(RUN["claim_bearing"])
        self.assertEqual(RUN["arm"], "B6_gpt6_instant_persistent_chat")

    def test_slot_requires_clean_memory_off_session(self):
        expected = RUN["expected_executor"]
        self.assertEqual(expected["model_family"], "GPT-6")
        self.assertEqual(expected["chat_configuration"], "Instant")
        self.assertEqual(expected["memory_mode"], "disabled_regular_chat")

    def test_public_inputs_exclude_oracle(self):
        public = json.dumps(RUN["public_inputs"], sort_keys=True).lower()
        self.assertNotIn("oracle", public)

if __name__ == "__main__":
    unittest.main()
