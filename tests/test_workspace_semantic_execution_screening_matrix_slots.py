"""Contract checks for instantiated non-claim-bearing A-E/P0-P3 screening slots."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "6b0ada4e0a9e9f29cd281d82e1fc786df8895982"
HARNESS_BLOB = "ff55438e933e91dad3057167c2243f0ef4933df2"

SLOTS = [
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/A_frontier_long_horizon/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/C_instant_stateless_resume/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/D_instant_decompose_critic/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/E_hybrid_escalation/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/A_frontier_long_horizon/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/B_instant_persistent_chat/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/C_instant_stateless_resume/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/D_instant_decompose_critic/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/E_hybrid_escalation/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/A_frontier_long_horizon/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/B_instant_persistent_chat/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/C_instant_stateless_resume/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/D_instant_decompose_critic/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/E_hybrid_escalation/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/A_frontier_long_horizon/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/B_instant_persistent_chat/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/C_instant_stateless_resume/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/D_instant_decompose_critic/screen-001.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/E_hybrid_escalation/screen-001.json",
]

class ScreeningMatrixSlotTests(unittest.TestCase):
    def _load(self, relpath: str):
        return json.loads((ROOT / relpath).read_text())

    def test_exactly_nineteen_new_primary_slots_are_instantiated(self):
        self.assertEqual(len(SLOTS), 19)
        self.assertEqual(len(set(SLOTS)), 19)

    def test_all_slots_are_non_claim_bearing_frozen_and_in_valid_lifecycle_state(self):
        valid_statuses = {
            "READY", "RUNNING", "WAITING_EXTERNAL", "READY_TO_RESUME",
            "TERMINAL_CANDIDATE", "COMPLETED", "FAILED", "SUPERSEDED",
        }
        for relpath in SLOTS:
            run = self._load(relpath)
            self.assertIn(run["status"], valid_statuses)
            self.assertFalse(run["claim_bearing"])
            self.assertEqual(run["source_checkpoint_sha"], SOURCE)
            self.assertEqual(run["public_inputs"]["harness_blob_sha"], HARNESS_BLOB)
            self.assertEqual(run["allowed_mutation_paths"], [relpath])
            self.assertNotIn("oracle", json.dumps(run["public_inputs"]).lower())
            self.assertTrue(any("oracle" in x.lower() for x in run["forbidden_inputs"]))

    def test_stateless_arm_requires_fresh_chat_each_quantum(self):
        for relpath in [p for p in SLOTS if "/C_instant_stateless_resume/" in p]:
            run = self._load(relpath)
            self.assertEqual(run["expected_executor"]["continuity"], "fresh_chat_per_reasoning_quantum")
            self.assertTrue(run["contamination_policy"]["per_quantum_or_role_new_session_required"])
            self.assertTrue(run["treatment_state"]["resume_requires_new_chat"])

    def test_decompose_critic_arm_preserves_decomposer_first_and_no_frontier(self):
        for relpath in [p for p in SLOTS if "/D_instant_decompose_critic/" in p]:
            run = self._load(relpath)
            first = run["treatment_state"]["role_queue"][0]
            self.assertEqual(first["role"], "decomposer")
            self.assertIn(first["status"], {"READY", "COMPLETE", "COMPLETED"})
            if first["status"] in {"COMPLETE", "COMPLETED"} and "decision" in first:
                self.assertIsInstance(first["decision"], str)
            self.assertIn("independent_critic", run["expected_executor"]["roles"])
            self.assertIn("No frontier escalation", run["treatment_contract"]["escalation_policy"])

    def test_hybrid_arm_is_evidence_gated_before_high(self):
        for relpath in [p for p in SLOTS if "/E_hybrid_escalation/" in p]:
            run = self._load(relpath)
            self.assertEqual(run["treatment_state"]["escalation_status"], "NOT_REQUESTED")
            self.assertEqual(run["expected_executor"]["escalation_chat_configuration"], "High")
            self.assertIn("INTRINSICALLY_DIFFICULT", run["treatment_contract"]["escalation_policy"])
            self.assertIn("TOO_LARGE", run["treatment_contract"]["decomposition_policy"])

    def test_frontier_control_uses_matched_surface_high(self):
        for relpath in [p for p in SLOTS if "/A_frontier_long_horizon/" in p]:
            run = self._load(relpath)
            self.assertEqual(run["expected_executor"]["model_family"], "GPT-5.6 Sol")
            self.assertEqual(run["expected_executor"]["chat_configuration"], "High")
            self.assertEqual(run["expected_executor"]["surface"], "ChatGPT chat")

if __name__ == "__main__":
    unittest.main()
