from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-operator-enter-minimize-ready-notify.v0.1.json"
A8_REVIEW = ROOT / "architecture/workspace-semantic-execution-operator-a8-pending-ack-recovery.v0.1.json"


class OperatorEnterMinimizeReadyNotifyTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(
            ["git", "rev-parse", spec],
            cwd=ROOT,
            text=True,
        ).strip()

    def git_show(self, ref: str, path: str) -> str:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            cwd=ROOT,
            text=True,
        )

    def test_review_binds_exact_successor_source(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]
        self.assertEqual(
            self.git(f'{source["source_head"]}:operator-bridge/src'),
            source["operator_bridge_src_tree"],
        )
        self.assertEqual(
            self.git("HEAD:operator-bridge/src"),
            source["operator_bridge_src_tree"],
        )
        for path, expected_blob in source["exact_blobs"].items():
            self.assertEqual(
                self.git(f'{source["source_head"]}:{path}'),
                expected_blob,
            )
            self.assertEqual(self.git(f"HEAD:{path}"), expected_blob)

    def test_historical_a8_binding_remains_immutable(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        a8 = json.loads(A8_REVIEW.read_text(encoding="utf-8"))
        historical = review["historical_a8"]
        self.assertTrue(historical["immutable"])
        self.assertEqual(
            historical["source_head"],
            a8["candidate_source"]["source_head"],
        )
        self.assertEqual(
            historical["src_tree"],
            a8["candidate_source"]["operator_bridge_src_tree"],
        )
        self.assertEqual(
            self.git(f'{historical["source_head"]}:operator-bridge/src'),
            historical["src_tree"],
        )

    def test_enter_minimize_is_deferred_and_does_not_become_durable_success(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]["source_head"]
        gate = self.git_show(
            source,
            "operator-bridge/src/WorkspaceOperator/Windows/Hotkey/HumanSubmitConfirmationGate.cs",
        )
        tray = self.git_show(
            source,
            "operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs",
        )
        self.assertIn("Confirmed?.Invoke(this, EventArgs.Empty)", gate)
        self.assertIn(
            "_humanSubmitConfirmation.Confirmed += HumanSubmitConfirmed",
            tray,
        )
        self.assertIn("Interval = 250", tray)
        self.assertIn("ProcessHumanSubmitUiEffects();", tray)
        self.assertIn("MinimizeAfterHumanSubmit()", tray)
        self.assertIn(
            "Do not minimize from inside the low-level keyboard hook callback.",
            tray,
        )
        self.assertIn(
            "Durable acknowledgment still controls progress.",
            tray,
        )

    def test_ready_alert_is_edge_triggered_without_forced_focus(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]["source_head"]
        tray = self.git_show(
            source,
            "operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs",
        )
        status = self.git_show(
            source,
            "operator-bridge/src/WorkspaceOperator/Windows/WorkloadStatusPresentation.cs",
        )
        self.assertIn("WorkloadStatusPresentation.BecameReady(", tray)
        self.assertIn(
            "New worker action ready — press Ctrl+Space to service.",
            tray,
        )
        self.assertIn(
            "previous.ReadyManualCycles == 0",
            status,
        )
        self.assertIn(
            "current.ReadyManualCycles > 0",
            status,
        )

    def test_waiting_ack_check_leaves_worker_minimized(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        source = review["candidate_source"]["source_head"]
        tray = self.git_show(
            source,
            "operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs",
        )
        start = tray.index("if (workload.SentUnconfirmed > 0)")
        end = tray.index("else if (workload.ReadyManualCycles > 0)", start)
        waiting_branch = tray[start:end]
        self.assertIn(
            "Worker Firefox remains minimized.",
            waiting_branch,
        )
        self.assertNotIn(
            "ForegroundPreparedWorkerWindow()",
            waiting_branch,
        )
        self.assertNotIn(
            "Nothing needs service",
            waiting_branch,
        )

    def test_review_grants_zero_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        gate = review["authority_gate"]
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_authority_required"])
        self.assertTrue(gate["no_silent_retry"])


if __name__ == "__main__":
    unittest.main()
