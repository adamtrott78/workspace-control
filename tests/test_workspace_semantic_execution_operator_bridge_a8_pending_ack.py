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
            self.git(f'{source["source_head"]}:operator-bridge/src'),
            source["operator_bridge_src_tree"],
        )
        self.assertTrue(review["historical_a7"]["immutable"])
        self.assertEqual(
            self.git(f'{review["historical_a7"]["accepted_checkpoint"]}:operator-bridge/src'),
            review["historical_a7"]["src_tree"],
        )

    def test_pending_unconfirmed_is_not_true_idle(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]["source_head"]
        tray = subprocess.check_output(
            ["git", "show", f"{source}:operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs"],
            cwd=ROOT,
            text=True,
        )
        status = subprocess.check_output(
            ["git", "show", f"{source}:operator-bridge/src/WorkspaceOperator/Windows/WorkloadStatusPresentation.cs"],
            cwd=ROOT,
            text=True,
        )
        self.assertIn("NoActionMayMinimize(workload)", tray)
        self.assertIn("awaiting durable acknowledgment", tray)
        self.assertIn("ForegroundPreparedWorkerWindow()", tray)
        self.assertIn(
            "snapshot.ReadyManualCycles == 0 && snapshot.SentUnconfirmed == 0",
            status,
        )

    def test_review_grants_zero_live_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        gate = review["authority_gate"]
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_authority_required"])
        self.assertTrue(gate["no_silent_retry"])


if __name__ == "__main__":
    unittest.main()
