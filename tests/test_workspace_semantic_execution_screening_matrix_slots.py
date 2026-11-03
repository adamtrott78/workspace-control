"""Contract checks for active provenance-refrozen A-E/P0-P3 screening slots."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "052cf8224ec5a725e09207bde0bef8e43cefe8cb"
HARNESS_BLOB = "ff55438e933e91dad3057167c2243f0ef4933df2"
PROFILE_BLOBS = {
    "P0": "b887ff6e05e1076b44ac874d38d48ba8956bc109",
    "P1": "11aea24d489b119518d514382dfd48047a7998b1",
    "P2": "4416013ea8f553d3a971f592ce0fbf7faf30c59e",
    "P3": "54c63ee2d0fd7990312517fd90d2d1197cf75df1",
}

SLOTS = [
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/A_frontier_long_horizon/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/B_instant_persistent_chat/screen-004.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/C_instant_stateless_resume/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/D_instant_decompose_critic/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P0/E_hybrid_escalation/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/A_frontier_long_horizon/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/B_instant_persistent_chat/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/C_instant_stateless_resume/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/D_instant_decompose_critic/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P1/E_hybrid_escalation/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/A_frontier_long_horizon/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/B_instant_persistent_chat/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/C_instant_stateless_resume/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/D_instant_decompose_critic/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P2/E_hybrid_escalation/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/A_frontier_long_horizon/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/B_instant_persistent_chat/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/C_instant_stateless_resume/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/D_instant_decompose_critic/screen-002.json",
    "benchmarks/workspace-semantic-execution/runs/screening-v1/P3/E_hybrid_escalation/screen-002.json",
]

class ScreeningMatrixSlotTests(unittest.TestCase):
    def _load(self, relpath: str):
        return json.loads((ROOT / relpath).read_text())

    def test_exactly_twenty_active_primary_slots_are_instantiated(self):
        self.assertEqual(len(SLOTS), 20)
        self.assertEqual(len(set(SLOTS)), 20)

    def test_all_active_slots_are_non_claim_bearing_refrozen_and_in_valid_lifecycle_state(self):
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
            phenotype = relpath.split("/")[4]
            self.assertEqual(
                run["public_inputs"]["taxonomy_profile_blob_sha"],
                PROFILE_BLOBS[phenotype],
            )
            self.assertEqual(run["allowed_mutation_paths"], [relpath])
            self.assertNotIn("oracle", json.dumps(run["public_inputs"]).lower())
            self.assertTrue(any("oracle" in x.lower() for x in run["forbidden_inputs"]))

    def test_stateless_arm_requires_fresh_chat_each_quantum(self):
        for relpath in [p for p in SLOTS if "/C_instant_stateless_resume/" in p]:
            run = self._load(relpath)
            self.assertEqual(run["expected_executor"]["continuity"], "fresh_chat_per_reasoning_quantum")
            self.assertTrue(run["contamination_policy"]["per_quantum_or_role_new_session_required"])
            self.assertTrue(run["treatment_state"]["resume_requires_new_chat"])
            self.assertGreaterEqual(run["treatment_state"]["quantum_index"], 0)

    def test_decompose_critic_arm_preserves_decomposer_first_and_no_frontier(self):
        for relpath in [p for p in SLOTS if "/D_instant_decompose_critic/" in p]:
            run = self._load(relpath)
            first = run["treatment_state"]["role_queue"][0]
            self.assertEqual(first["role"], "decomposer")
            self.assertIn(first["status"], {"READY", "COMPLETE", "COMPLETED"})
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
