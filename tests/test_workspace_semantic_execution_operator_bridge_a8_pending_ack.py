from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-operator-a8-pending-ack-recovery.v0.1.json"


class OperatorA8PendingAckRecoveryTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def test_successor_review_binds_exact_source_and_keeps_a7_historical(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]
        self.assertEqual(
            source["source_head"],
            "b97a4c7b9309d413ced7eea14fe87b5864ad0c5b",
        )
        self.assertEqual(
            source["operator_bridge_src_tree"],
            "f3fd3b2c65b5780b511af9a90477d3a6bbfee873",
        )
        self.assertTrue(review["historical_a7"]["immutable"])
        baseline = json.loads(
            (ROOT / "architecture/workspace-operator-bridge-a7-frontend-baseline.v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            baseline["accepted_checkpoint"],
            review["historical_a7"]["accepted_checkpoint"],
        )
        self.assertEqual(
            baseline["exact_runtime_bindings"]["operator-bridge/src_tree"],
            review["historical_a7"]["src_tree"],
        )

    def test_pending_unconfirmed_is_not_true_idle(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        contract = review["behavioral_contract"]
        self.assertIn("SentUnconfirmed>0", contract["pending_unconfirmed"])
        self.assertIn("never minimize", contract["pending_unconfirmed"])
        self.assertIn("ReadyManualCycles=0", contract["true_idle"])
        self.assertIn("SentUnconfirmed=0", contract["true_idle"])
        self.assertIn("HTTP 204", contract["empty_claim_status_refresh"])

    def test_review_grants_zero_live_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        gate = review["authority_gate"]
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_authority_required"])
        self.assertTrue(gate["no_silent_retry"])


if __name__ == "__main__":
    unittest.main()
